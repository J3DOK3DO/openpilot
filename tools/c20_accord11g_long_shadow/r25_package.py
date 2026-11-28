"""Offline exact-commit package gate. A source archive is never an installable release."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile

from .native_preflight import elf_machine
from .r25_gate import START, _git, evaluate

MAX_ARCHIVE = 1_500_000_000
ROOT = Path('openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/c_generated_code')
REQUIRED_ARM = (ROOT / 'acados_ocp_solver_pyx.so', ROOT / 'libacados.so',
                ROOT / 'libacados_ocp_solver_long.so', ROOT / 'libblasfeo.so', ROOT / 'libhpipm.so',
                ROOT / 'libqpOASES_e.so.3.1')
REQUIRED_MODELS = (Path('openpilot/selfdrive/modeld/models/driving_tinygrad.pkl'),
                   Path('openpilot/selfdrive/modeld/models/dmonitoring_model_tinygrad.pkl'))


def _digest(path: Path) -> str:
  sha = hashlib.sha256()
  with path.open('rb') as stream:
    while block := stream.read(1024 * 1024):
      sha.update(block)
  return sha.hexdigest()


def _build_artifact(repo: Path, name: str) -> bool:
  path = Path(name)
  if (path.is_absolute() or '..' in path.parts or not name.startswith('openpilot/') or
      name.startswith(('openpilot/selfdrive/car/', 'openpilot/selfdrive/controls/controls', 'openpilot/system/manager/'))):
    return False
  full = repo / path
  return (full.is_file() and not full.is_symlink() and
          (path.suffix in ('.so', '.pkl', '.bin', '.thneed', '.dlc') or elf_machine(full) == 'aarch64'))


def candidate(repo: Path, build_receipt: Path | None = None) -> dict:
  repo = repo.resolve()
  gate = evaluate(repo)
  reasons = []
  if gate['git'] != 'CLEAN' or gate['head'] == START:
    reasons.append('exact C20 implementation commit pending')
  if gate['source_audit'] != 'PASS' or gate['reasons']:
    reasons.append('source or provenance gate rejected')
  if not gate['exact_prebuilt_receipt']:
    reasons.append('exact-commit prebuilt receipt missing or stale')
  for path in REQUIRED_ARM:
    full = repo / path
    if full.is_symlink() or elf_machine(full) != 'aarch64':
      reasons.append(f'ARM64 product binary absent or incompatible: {path}')
  for path in REQUIRED_MODELS:
    full = repo / path
    if full.is_symlink() or not full.is_file() or full.stat().st_size == 0:
      reasons.append(f'compiled product model absent: {path}')
  if build_receipt is None:
    reasons.append('independent product build receipt not supplied')
  else:
    try:
      receipt = json.loads(build_receipt.read_text())
      artifacts = receipt['artifacts_sha256']
      source_revision = receipt['source_revision']
      if (type(source_revision) is not str or re.fullmatch(r'[0-9a-f]{40}', source_revision) is None or
          type(artifacts) is not dict or len(artifacts) > 500):
        raise ValueError('invalid build receipt source or artifact inventory')
      names = set(artifacts)
      changed = set(_git(repo, 'diff', '--name-only', source_revision, gate['head']).splitlines())
      if (set(receipt) != {'schema_version', 'source_revision', 'revision', 'build_system', 'build_exit', 'architecture', 'artifacts_sha256'} or
          receipt['schema_version'] != 1 or receipt['revision'] != gate['head'] or
          _git(repo, 'merge-base', source_revision, gate['head']) != source_revision or
          changed - names - {'prebuilt', 'prebuilt.json'} or
          receipt['build_system'] != 'scons' or receipt['build_exit'] != 0 or receipt['architecture'] != 'aarch64' or
          not {str(p) for p in (*REQUIRED_ARM, *REQUIRED_MODELS)} <= names or
          any(not _build_artifact(repo, name) or artifacts[name] != _digest(repo / name) for name in names)):
        reasons.append('product build receipt mismatch')
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
      reasons.append('product build receipt unavailable or malformed')
  # The full release build has additional dependencies; this only admits packaging.
  return {'schema_version': 1, 'revision': gate['head'], 'status': 'PACKAGE_ELIGIBLE_UNVERIFIED_DEVICE' if not reasons else 'BLOCKED',
          'reasons': reasons, 'installable': False, 'on_device_acceptance': 'NOT_RUN', 'active_longitudinal': 'NO_GO'}


def build(repo: Path, output: Path, build_receipt: Path | None = None) -> dict:
  result = candidate(repo, build_receipt)
  if result['status'] != 'PACKAGE_ELIGIBLE_UNVERIFIED_DEVICE':
    raise ValueError('; '.join(result['reasons']))
  repo = repo.resolve()
  output = output.resolve()
  if output.is_relative_to(repo) or output.exists() or output.parent.is_symlink():
    raise ValueError('output must be a new path outside the checkout')
  # Git archives committed sources only. No working-tree bytes can enter this archive.
  try:
    subprocess.run(['git', '-C', str(repo), 'archive', '--format=tar', '--output='+str(output), result['revision']],
                   check=True, timeout=120)
    if not output.is_file() or output.stat().st_size > MAX_ARCHIVE:
      raise ValueError('archive absent or exceeds bounded size')
    record = {**result, 'archive_sha256': _digest(output), 'archive_bytes': output.stat().st_size,
              'classification': 'OFFLINE_PACKAGE_UNVERIFIED_INSTALLATION'}
    output.with_suffix(output.suffix + '.json').write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
    return record
  except BaseException:
    output.unlink(missing_ok=True)
    raise


def verify(output: Path) -> dict:
  sidecar = output.with_suffix(output.suffix + '.json')
  record = json.loads(sidecar.read_text())
  if (record.get('classification') != 'OFFLINE_PACKAGE_UNVERIFIED_INSTALLATION' or record.get('installable') is not False or
      not output.is_file() or output.is_symlink() or output.stat().st_size != record.get('archive_bytes') or
      output.stat().st_size > MAX_ARCHIVE or _digest(output) != record.get('archive_sha256')):
    raise ValueError('archive identity or classification mismatch')
  with tarfile.open(output, 'r:') as archive:
    names = set()
    links = []
    total = 0
    for member in archive:
      path = Path(member.name)
      if (member.name in names or path.is_absolute() or '..' in path.parts or
          not (member.isfile() or member.issym() or member.isdir()) or member.size > MAX_ARCHIVE):
        raise ValueError('unsafe or duplicate archive member')
      total += member.size
      if total > MAX_ARCHIVE:
        raise ValueError('archive expanded size exceeds bound')
      if member.issym():
        target = Path(member.linkname)
        if target.is_absolute():
          raise ValueError('absolute archive symlink')
        stack = list(path.parent.parts)
        for part in target.parts:
          if part == '..':
            if not stack:
              raise ValueError('escaping archive symlink')
            stack.pop()
          elif part != '.':
            stack.append(part)
        links.append('/'.join(stack))
      names.add(member.name)
    if any(target not in names for target in links):
      raise ValueError('archive symlink target absent')
    if not all(str(path) in names for path in (*REQUIRED_ARM, *REQUIRED_MODELS)):
      raise ValueError('required product artifacts absent from archive')
  return record


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('action', choices=('candidate', 'build', 'verify'))
  parser.add_argument('--repo', type=Path, default=Path.cwd())
  parser.add_argument('--output', type=Path)
  parser.add_argument('--build-receipt', type=Path)
  args = parser.parse_args()
  if args.action != 'candidate' and args.output is None:
    parser.error('--output required')
  result = candidate(args.repo, args.build_receipt) if args.action == 'candidate' else build(args.repo, args.output, args.build_receipt) if args.action == 'build' else verify(args.output)
  print(json.dumps(result, sort_keys=True, indent=2))

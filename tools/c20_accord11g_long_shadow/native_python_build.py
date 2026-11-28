"""Explicit offline x86 build and read-only verification of frozen C19 generated MPC.

Import has no build, solver, or source checkout side effects. Compiler artifacts
are restricted to the external campaign evidence directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sysconfig

from .native_host import GENERATED, LIBS, digest, header_tree_digest
from .native_preflight import elf_machine
from .platform_receipt import BASELINE

C19 = Path('/home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124')
CACHE = Path('/home/jdkd/.cache/uv/archive-v0/JcZjHB62Lhiu78Ir/comma_deps_acados-0.2.2.post103.data/purelib/acados/install')
EVIDENCE = Path('/home/jdkd/C20_RESEARCH_EVIDENCE_R15_R19_20261128')


def paths(output: Path) -> tuple[Path, Path, Path, Path]:
  expected = EVIDENCE / 'native'
  if output != expected or output.resolve() != expected or output.resolve().is_relative_to(C19):
    raise ValueError('native output must be the external campaign native directory without links')
  current = Path(output.anchor)
  for part in output.parts[1:]:
    current /= part
    if current.is_symlink():
      raise ValueError('linked native output path component')
  root = C19 / GENERATED
  solib = output / 'libacados_ocp_solver_long.so'
  ext = output / ('acados_ocp_solver_pyx' + sysconfig.get_config_var('EXT_SUFFIX'))
  if any(p.is_symlink() for p in (solib, ext, output/'python_build_receipt.json',
       *(output/f'build_{i}.{suffix}' for i in range(2) for suffix in ('stdout', 'stderr')))):
    raise ValueError('linked native output artifact')
  return root, solib, ext, CACHE / 'lib'


def source_files(root: Path) -> list[Path]:
  files = [root / 'acados_solver_long.c', root / 'acados_ocp_solver_pyx.c']
  for name in ('long_model', 'long_cost', 'long_constraints'):
    files.extend(sorted((root / name).glob('*.c')))
  files.extend(sorted(root.glob('*.h')))
  for name in ('long_model', 'long_cost', 'long_constraints'):
    files.extend(sorted((root / name).glob('*.h')))
  if len(files) != 23 or any(p.is_symlink() or not p.is_file() for p in files):
    raise ValueError('generated source set incomplete')
  return files


def source_hashes(root: Path) -> dict[str, str]:
  return {str(p.relative_to(root)): digest(p) for p in source_files(root)}


def commands(root: Path, solib: Path, ext: Path, output: Path, lib: Path) -> list[list[str]]:
  import numpy  # Explicit build path only.
  inc = CACHE / 'include'
  flags = ['-I' + str(p) for p in (inc, inc/'acados', inc/'blasfeo/include', inc/'hpipm/include', root)]
  sources = [root/'acados_solver_long.c']
  for name in ('long_model', 'long_cost', 'long_constraints'):
    sources.extend(sorted((root/name).glob('*.c')))
  return [
    ['gcc', '-O0', '-fPIC', '-std=c99', '-shared', *flags, '-o', str(solib), *map(str, sources),
     '-L'+str(lib), '-Wl,-rpath,'+str(lib), '-lacados', '-lhpipm', '-lblasfeo', '-lm'],
    ['gcc', '-O0', '-fPIC', '-std=c99', '-shared', *flags, '-I'+sysconfig.get_paths()['include'],
     '-I'+numpy.get_include(), '-o', str(ext), str(root/'acados_ocp_solver_pyx.c'),
     '-L'+str(output), '-L'+str(lib), '-Wl,-rpath,'+str(output), '-Wl,-rpath,'+str(lib),
     '-lacados_ocp_solver_long', '-lacados', '-lhpipm', '-lblasfeo', '-lm']]


def _git(*args: str) -> str:
  return subprocess.check_output(['git', '-C', str(C19), *args], text=True, timeout=5).strip()


def _provenance(root: Path, lib: Path) -> dict:
  return {'source_commit': BASELINE, 'generated_source_sha256': source_hashes(root),
          'cached_library_sha256': {name: digest(lib/name) for name in LIBS},
          'cached_headers_tree_sha256': header_tree_digest(CACHE/'include')}


def build(output: Path = EVIDENCE/'native') -> dict:
  root, solib, ext, lib = paths(output)
  # A restarted build must not leave its previous successful receipt current.
  (output/'python_build_receipt.json').unlink(missing_ok=True)
  if platform.machine().lower() != 'x86_64' or _git('rev-parse', 'HEAD') != BASELINE or _git('status', '--porcelain', '--untracked-files=all'):
    raise ValueError('clean pinned frozen C19 and x86_64 required')
  if any(elf_machine(lib/name) != 'x86_64' for name in LIBS):
    raise ValueError('cached library architecture mismatch')
  provenance = _provenance(root, lib)
  output.mkdir(parents=True, exist_ok=True)
  cmds = commands(root, solib, ext, output, lib)
  receipt = {'schema_version': 1, 'classification': 'C19_PYTHON_MPC_NATIVE_X86_BUILD',
             **provenance, 'commands': cmds,
             'compiler': subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
             'python_version': platform.python_version(), 'outputs_sha256': {}, 'logs_sha256': {},
             'build_exits': []}
  for index, command in enumerate(cmds):
    result = subprocess.run(command, capture_output=True, timeout=60, check=False)
    for suffix, contents in (('stdout', result.stdout), ('stderr', result.stderr)):
      if len(contents) > 128 * 1024:
        raise ValueError('compiler output bound exceeded')
      path = output/f'build_{index}.{suffix}'
      path.write_bytes(contents)
      receipt['logs_sha256'][path.name] = digest(path)
    receipt['build_exits'].append(result.returncode)
    if result.returncode:
      break
  if len(receipt['build_exits']) == 2 and receipt['build_exits'] == [0, 0]:
    receipt['outputs_sha256'] = {p.name: digest(p) for p in (solib, ext)}
    receipt['elf_machine'] = {p.name: elf_machine(p) for p in (solib, ext)}
    receipt['dynamic_dependencies'] = {}
    for p in (solib, ext):
      dynamic = subprocess.check_output(['readelf', '-d', str(p)], text=True, timeout=5)
      receipt['dynamic_dependencies'][p.name] = [line.strip() for line in dynamic.splitlines()
                                                if 'NEEDED' in line or 'RUNPATH' in line]
  else:
    receipt['classification'] = 'C19_PYTHON_MPC_NATIVE_X86_BUILD_FAILED'
  (output/'python_build_receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
  return receipt


def verify(output: Path = EVIDENCE/'native', expected_sha256: str | None = None) -> dict:
  root, solib, ext, lib = paths(output)
  receipt_file = output/'python_build_receipt.json'
  try:
    receipt = json.loads(receipt_file.read_text())
  except (OSError, UnicodeError, ValueError) as exc:
    return {'status': 'REJECTED', 'reasons': ['build receipt unreadable or malformed: '+type(exc).__name__]}
  if type(receipt) is not dict:
    return {'status': 'REJECTED', 'reasons': ['build receipt is not an object'], 'receipt_sha256': digest(receipt_file)}
  reasons = []
  getdict = lambda key: receipt[key] if type(receipt.get(key)) is dict else {}
  required = {'schema_version', 'classification', 'source_commit', 'generated_source_sha256',
              'cached_library_sha256', 'cached_headers_tree_sha256', 'commands', 'compiler',
              'python_version', 'outputs_sha256', 'logs_sha256', 'build_exits', 'elf_machine',
              'dynamic_dependencies'}
  if type(receipt) is not dict or set(receipt) != required or receipt.get('schema_version') != 1:
    reasons.append('build receipt schema mismatch')
  if expected_sha256 is not None and digest(receipt_file) != expected_sha256:
    reasons.append('receipt digest mismatch')
  if _git('rev-parse', 'HEAD') != BASELINE or _git('status', '--porcelain', '--untracked-files=all'):
    reasons.append('frozen source revision or cleanliness mismatch')
  if any(receipt.get(key) != value for key, value in _provenance(root, lib).items()):
    reasons.append('source or dependency hash mismatch')
  if receipt.get('commands') != commands(root, solib, ext, output, lib):
    reasons.append('compiler command mismatch')
  if receipt.get('build_exits') != [0, 0] or receipt.get('classification') != 'C19_PYTHON_MPC_NATIVE_X86_BUILD':
    reasons.append('build exit or classification mismatch')
  if (receipt.get('compiler') != subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0]
      or receipt.get('python_version') != platform.python_version()):
    reasons.append('compiler or Python environment mismatch')
  for p in (solib, ext):
    if not p.is_file() or p.is_symlink() or getdict('outputs_sha256').get(p.name) != digest(p) or elf_machine(p) != 'x86_64':
      reasons.append('native binary mismatch: '+p.name)
    if getdict('elf_machine').get(p.name) != elf_machine(p):
      reasons.append('recorded ELF machine mismatch: '+p.name)
    if p.is_file():
      dynamic = subprocess.check_output(['readelf', '-d', str(p)], text=True, timeout=5)
      needed = [line.strip() for line in dynamic.splitlines() if 'NEEDED' in line or 'RUNPATH' in line]
      if getdict('dynamic_dependencies').get(p.name) != needed:
        reasons.append('dynamic dependency mismatch: '+p.name)
  for name, sha in getdict('logs_sha256').items():
    p = output/name
    if name not in ('build_0.stdout', 'build_0.stderr', 'build_1.stdout', 'build_1.stderr') or not p.is_file() or digest(p) != sha:
      reasons.append('build log mismatch: '+name)
  if len(getdict('logs_sha256')) != 4:
    reasons.append('build log set incomplete')
  return {'status': 'VERIFIED_LOCAL_BUILD' if not reasons else 'REJECTED', 'reasons': reasons,
          'receipt_sha256': digest(receipt_file), 'generated_source_sha256': receipt.get('generated_source_sha256')}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('operation', choices=('build', 'verify'))
  parser.add_argument('--expected-sha256')
  args = parser.parse_args()
  result = build() if args.operation == 'build' else verify(expected_sha256=args.expected_sha256)
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
  main()

"""Deterministic C20 dual-path source/build gate; never authorizes actuation."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import subprocess

from .native_preflight import elf_machine, qualify
from .r25_model_assets import MODEL_COMPONENTS

START = '519a981b72fc0ba1bf0a029904628990086b9f37'
C19 = Path('/home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124')
C19_SHA = 'a32dcc0a6e62a4e2a15d9ac4425424e598313c98'
SHADOW = Path('openpilot/starpilot/longitudinal/c20_shadow.py')
SMOKE = Path('openpilot/starpilot/longitudinal/c20_shadow_smoke.py')
ALLOWED = {
  str(SHADOW),
  str(SMOKE),
  'tools/c20_accord11g_long_shadow/r25_gate.py',
  'tools/c20_accord11g_long_shadow/r25_package.py',
  'tools/c20_accord11g_long_shadow/r25_model_assets.py',
  'tools/c20_accord11g_long_shadow/docs/R20_R25_COMBINED_REPORT.md',
  'tools/c20_accord11g_long_shadow/docs/R25_INSTALLATION_RECIPE.md',
  'tools/c20_accord11g_long_shadow/docs/R25_OFFLINE_CANDIDATE_MANIFEST.json',
  'tools/ci/tests/test_r25.py',
  'tools/c20_accord11g_long_shadow/tests/test_campaign.py',
  'tools/c20_accord11g_long_shadow/tests/test_r14.py',
  'tools/c20_accord11g_long_shadow/tests/test_r15_r19.py',
  'prebuilt', 'prebuilt.json',
}
FORBIDDEN = {'PubMaster', 'pub_sock', 'send', 'sendall', 'transmit', 'can_send', 'Panda',
             'CarController', 'carcontroller', 'carControl', 'set_safety_mode', 'setSafetyMode',
             'Params', 'put', 'put_bool'}
FORBIDDEN_DYNAMIC = {'__import__', 'import_module', 'eval', 'exec', 'compile'}


def _git(repo: Path, *args: str) -> str:
  # Preserve Git porcelain's leading status column; strip only line endings.
  return subprocess.check_output(['git', '--no-optional-locks', '-C', str(repo), *args], text=True, timeout=15).rstrip('\r\n')


def command_path_audit(path: Path) -> list[str]:
  try:
    tree = ast.parse(path.read_text())
  except (OSError, SyntaxError, UnicodeError) as exc:
    return [f'shadow source invalid: {type(exc).__name__}']
  findings = []
  for node in ast.walk(tree):
    if isinstance(node, ast.Name) and node.id in FORBIDDEN:
      findings.append('forbidden name '+node.id)
    if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN:
      findings.append('forbidden attribute '+node.attr)
    if isinstance(node, ast.Call):
      name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
      if name in FORBIDDEN_DYNAMIC:
        findings.append('forbidden dynamic call '+name)
    if isinstance(node, ast.Import):
      for alias in node.names:
        if alias.name.startswith(('panda', 'opendbc.safety', 'openpilot.selfdrive.car')):
          findings.append('forbidden import '+alias.name)
    if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(('panda', 'opendbc.safety', 'openpilot.selfdrive.car')):
      findings.append('forbidden import '+node.module)
    if isinstance(node, ast.ImportFrom):
      for alias in node.names:
        if alias.name in FORBIDDEN or (alias.asname and alias.asname in FORBIDDEN):
          findings.append('forbidden name '+alias.name)
  return sorted(set(findings))


def _artifact_path(repo: Path, name: str) -> bool:
  path = Path(name)
  return (name.startswith('openpilot/') and '..' not in path.parts and
          not name.startswith(('openpilot/selfdrive/car/', 'openpilot/system/manager/')) and
          (path.suffix in ('.so', '.pkl', '.bin', '.thneed', '.dlc') or
           name in {str(component) for component in MODEL_COMPONENTS} or
           elf_machine(repo / path) == 'aarch64'))


def evaluate(repo: Path) -> dict:
  repo = repo.resolve()
  reasons = []
  try:
    head = _git(repo, 'rev-parse', 'HEAD')
    if _git(repo, 'merge-base', START, 'HEAD') != START:
      reasons.append('starting baseline is not the exact ancestor')
    working = _git(repo, 'status', '--porcelain', '--untracked-files=all').splitlines()
    dirty = bool(working)
    changed = set(_git(repo, 'diff', '--name-only', START).splitlines()) | {row[3:] for row in working}
    outside = {name for name in changed - ALLOWED if not _artifact_path(repo, name)}
    if outside:
      reasons.append('out-of-scope changed paths: '+', '.join(sorted(outside)))
    if _git(C19, 'rev-parse', 'HEAD') != C19_SHA or _git(C19, 'status', '--porcelain', '--untracked-files=all'):
      reasons.append('frozen C19 mismatch or dirty')
  except (OSError, subprocess.SubprocessError):
    head, dirty = '', True
    reasons.append('git provenance unavailable')
  findings = sorted(set(command_path_audit(repo / SHADOW) + command_path_audit(repo / SMOKE)))
  if findings:
    reasons.extend(findings)
  try:
    native = qualify(repo)
  except (OSError, ValueError, ImportError) as exc:
    native = {'status': 'BLOCKED', 'reasons': [type(exc).__name__], 'executed_solver': False}
  try:
    from tools.ci.check_prebuilt_receipt import check_receipt
    receipt = check_receipt(repo, head) == head
  except (OSError, ValueError, RuntimeError, ImportError, subprocess.SubprocessError):
    receipt = False
  # A historical log or x86 receipt cannot make any current acceptance gate pass.
  source_ok = not reasons and not dirty
  return {
    'schema_version': 1, 'goal': 'C20 R25 Dual-Path Longitudinal Integration & Installation Candidate',
    'starting_commit': START, 'head': head, 'git': 'PENDING_COMMIT' if dirty else 'CLEAN',
    'source_audit': 'PASS' if not findings else 'FAIL', 'reasons': reasons,
    'PATH_A_INSTALL_SOFTWARE': 'BLOCKED_PRODUCT_BUILD_AND_INSTALLER',
    'PATH_B1_SHADOW_SOFTWARE': 'SOURCE_READY_NATIVE_RUNTIME_UNVERIFIED' if source_ok else 'PENDING_COMMIT_OR_SOURCE_REVIEW',
    'PATH_B2_ACTIVE_LONGITUDINAL': 'NO_GO',
    'ARM64_BUILD': 'UNVERIFIED' if native['status'] == 'READY_FOR_ISOLATED_EXECUTION' else 'BLOCKED',
    'ON_DEVICE_ACCEPTANCE': 'NOT_RUN', 'PHYSICAL_SAFETY': 'UNVERIFIED',
    'product_native_preflight': native, 'exact_prebuilt_receipt': receipt,
    'full_planner_execution': 'NOT_EXECUTED', 'current_product_mpc_execution': 'NOT_EXECUTED',
    'r19_x86_native_mpc': 'HISTORICAL_SYNTHETIC_RECEIPT_ONLY',
    'installable': False, 'actuation': 'NONE',
  }


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--repo', type=Path, default=Path.cwd())
  args = parser.parse_args()
  print(json.dumps(evaluate(args.repo), sort_keys=True, indent=2))

"""Read-only software-only C20 R15-R19 gate. No safety or road authorization."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from .native_python_build import C19, verify as verify_build
from .python_mpc import verify_receipt
from .software_faults import EXTERNAL as FAULT_RECEIPT, suite as fault_suite
from .platform_receipt import BASELINE
from .release_gate import source_audit
from .campaign_gate import privacy_scan

RESEARCH = Path(__file__).resolve().parents[2]
START = '7a10fb902449999054eaa4566f870656573e23b1'
BRANCH = 'c20-r15-r19-full-software-qual-20261128'


def _git(repo: Path, *args: str) -> str:
  return subprocess.check_output(['git', '-C', str(repo), *args], text=True, timeout=10).rstrip('\n')


def _scope() -> tuple[bool, list[str]]:
  reasons = []
  if _git(RESEARCH, 'branch', '--show-current') != BRANCH:
    reasons.append('research branch mismatch')
  if subprocess.run(['git', '-C', str(RESEARCH), 'merge-base', '--is-ancestor', START, 'HEAD'],
                    capture_output=True, timeout=10, check=False).returncode != 0:
    reasons.append('research starting commit is not an ancestor of HEAD')
  changed = _git(RESEARCH, 'status', '--porcelain', '--untracked-files=all').splitlines()
  if changed:
    reasons.append('research source tree is not clean')
  for row in changed:
    path = row[3:]
    if not path.startswith('tools/c20_accord11g_long_shadow/'):
      reasons.append('out-of-scope edit: '+path)
  if _git(C19, 'rev-parse', 'HEAD') != BASELINE or _git(C19, 'status', '--porcelain', '--untracked-files=all'):
    reasons.append('frozen C19 revision or cleanliness mismatch')
  return not reasons, reasons


def evaluate() -> dict:
  reasons = []
  scope_ok, scope_reasons = _scope()
  reasons.extend(scope_reasons)
  audit = source_audit(RESEARCH)
  if audit['status'] != 'PASS':
    reasons.extend('source audit: '+finding for finding in audit['findings'])
  privacy = privacy_scan(RESEARCH)
  if privacy['status'] != 'PASS':
    reasons.append('research privacy scan rejected')
  try:
    native = verify_build()
  except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
    native = {'status': 'REJECTED', 'reasons': [str(exc)]}
  if native['status'] != 'VERIFIED_LOCAL_BUILD':
    reasons.append('native Python solver build receipt rejected')
  try:
    mpc = verify_receipt()
  except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as exc:
    mpc = {'status': 'REJECTED', 'reasons': [str(exc)]}
  if mpc['status'] != 'VERIFIED_LOCAL_EXECUTION_RECEIPT':
    reasons.append('C19 Python MPC execution receipt rejected')
  try:
    expected_faults = fault_suite()
    faults = json.loads(FAULT_RECEIPT.read_text())
    fault_ok = faults == expected_faults and faults.get('status') == 'PASS_SYNTHETIC_FAULT_DETECTION'
  except (OSError, ValueError, KeyError, TypeError) as exc:
    faults, fault_ok = {'status': 'REJECTED', 'reason': str(exc)}, False
  if not fault_ok:
    reasons.append('software fault audit rejected')
  status = ('R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW' if not reasons
            else 'R19_BLOCKED_SOFTWARE_EVIDENCE')
  return {
    'schema_version': 1, 'status': status, 'reasons': reasons,
    'stages': {
      'R15': 'C19_PYTHON_MPC_NATIVE_X86_VERIFIED' if mpc['status'] == 'VERIFIED_LOCAL_EXECUTION_RECEIPT' else 'BLOCKED',
      'R14_PRIOR': 'NATIVE_GENERATED_C_EXAMPLE',
      'R16': 'SYNTHETIC_C19_PYTHON_MPC_SCENARIOS_VERIFIED' if mpc['status'] == 'VERIFIED_LOCAL_EXECUTION_RECEIPT' else 'NATIVE_PYTHON_MPC_NOT_RUN',
      'R17': 'PASS_SYNTHETIC_FAULT_DETECTION' if fault_ok else 'BLOCKED',
      'R18': 'PENDING_INDEPENDENT_REVIEW',
      'R19': status,
    },
    'scope_verified': scope_ok and audit['status'] == 'PASS' and privacy['status'] == 'PASS',
    'privacy_scan': privacy['status'],
    'native_build_receipt_sha256': native.get('receipt_sha256'),
    'python_mpc_receipt_sha256': mpc.get('receipt_sha256'),
    'fault_case_count': faults.get('case_count') if fault_ok else None,
    'full_c19_longitudinal_planner': 'FULL_C19_LONGITUDINAL_PLANNER_NOT_RUN',
    'authenticated_vehicle_replay': 'AUTHENTICATED_VEHICLE_REPLAY_NOT_RUN',
    'hardware_gates': {'classification': 'EXCLUDED_BY_USER_FOR_SOFTWARE_CAMPAIGN', 'verification': 'UNVERIFIED'},
    'independent_review': 'PENDING', 'active_alpha_long': 'NO_GO', 'road_use': 'NO_GO',
    'safety_authorization': 'NONE', 'actuation': 'NONE',
    'packaging': 'HOST_OPERATOR_AFTER_COMMIT_CLEAN_TREE_AND_REVIEW_REMEDIATION',
  }


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.parse_args()
  print(json.dumps(evaluate(), indent=2, sort_keys=True))


if __name__ == '__main__':
  main()

"""Pure offline R17 fault substitutions over sanitized synthetic temporal evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from .telemetry_gate import audit
from .python_mpc import scenario_definitions, _validate_cycle

ROOT = Path(__file__).parent
CAPTURE = ROOT/'fixtures/r10_r12_synthetic_capture.json'
MANIFEST = ROOT/'fixtures/r10_r12_synthetic_manifest.json'
EXTERNAL = Path('/home/jdkd/C20_RESEARCH_EVIDENCE_R15_R19_20261128/software_faults_receipt.json')


def _encode(data: dict) -> bytes:
  return (json.dumps(data, sort_keys=True, separators=(',', ':'))+'\n').encode()


def _run(manifest: dict, capture: dict, *, match_digest: bool = True) -> dict:
  raw = _encode(capture)
  manifest = copy.deepcopy(manifest)
  if match_digest:
    manifest['capture_sha256'] = hashlib.sha256(raw).hexdigest()
  return audit(_encode(manifest), raw)


def _shift_cycle(cycle: dict, amount: int) -> dict:
  row = copy.deepcopy(cycle)
  row['cycle_t_ns'] += amount
  row['radar_md_mono_time_ns'] += amount
  for service in row['services'].values():
    service['source_t_ns'] += amount
    service['receipt_t_ns'] += amount
  for lead in row['model_leads']:
    lead['source_t_ns'] += amount
    lead['receipt_t_ns'] += amount
  for frame in row['model_lead_history']:
    frame['source_t_ns'] += amount
    frame['receipt_t_ns'] += amount
  return row


def _three_cycles(capture: dict) -> dict:
  base = copy.deepcopy(capture)
  third = _shift_cycle(base['cycles'][1], 50_000_000)
  third['model_lead_history'] = [copy.deepcopy(base['cycles'][1]['model_lead_history'][-1]), third['model_lead_history'][-1]]
  base['cycles'].append(third)
  return base


def _case(capture: dict, mutate) -> dict:
  item = copy.deepcopy(capture)
  mutate(item)
  return item


def solver_status_gate(statuses: object) -> str:
  if type(statuses) is not list or not statuses or any(type(x) is not int or x < 0 for x in statuses):
    return 'FAIL_CLOSED_INVALID_SOLVER_STATUS'
  return 'SOLVER_STATUS_ZERO_SYNTHETIC' if all(x == 0 for x in statuses) else 'FAIL_CLOSED_SOLVER_FAILURE'


def suite() -> dict:
  manifest = json.loads(MANIFEST.read_text())
  capture = _three_cycles(json.loads(CAPTURE.read_text()))
  variants = {
    'baseline': capture,
    'stale_model': _case(capture, lambda c: c['cycles'][1]['services']['modelV2'].update(source_t_ns=700_000_000)),
    'stale_radar': _case(capture, lambda c: c['cycles'][1]['services']['radarState'].update(source_t_ns=700_000_000)),
    'clock_skew': _case(capture, lambda c: c['cycles'][1].update(clock_disagreement=True)),
    'unexpected_reset': _case(capture, lambda c: c['cycles'][1].update(reset_boundary=True)),
    'lead_loss': _case(capture, lambda c: c['cycles'][1].update(lead_present=False)),
    'driver_override': _case(capture, lambda c: c['cycles'][1].update(gas_pressed=True)),
    'input_time_reversal': _case(capture, lambda c: c['cycles'][1].update(cycle_t_ns=990_000_000)),
  }
  expected = {
    'stale_model': 'SENSOR_STALE', 'stale_radar': 'SENSOR_STALE',
    'clock_skew': 'CLOCK_DISAGREEMENT', 'unexpected_reset': 'UNEXPECTED_RESET',
    'lead_loss': 'LEAD_LOSS', 'driver_override': 'DRIVER_OVERRIDE',
    'input_time_reversal': 'NONMONOTONIC_CYCLE',
  }
  cases = {}
  for name, variant in variants.items():
    report = _run(manifest, variant)
    cases[name] = {'quality_state': report['quality_state'], 'audit_state': report['audit_state'],
                   'faults': report['faults'], 'fault_events': report['fault_events'],
                   'expected_fault_detected': name == 'baseline' or expected[name] in report['faults'],
                   'locked_after_recovery_cycle': name != 'baseline' and report['fault_events'][-1]['audit_state'] == 'FAULT_LOCKED'}
  corrupt = _run(manifest, capture, match_digest=False)
  cases['corrupted_evidence'] = {'quality_state': corrupt['quality_state'], 'audit_state': corrupt['audit_state'],
                                 'faults': corrupt['faults'], 'expected_fault_detected': 'CAPTURE_DIGEST_MISMATCH' in corrupt['faults']}
  malformed = copy.deepcopy(capture)
  malformed['cycles'][1]['model_lead_history'] = malformed['cycles'][1]['model_lead_history'] * 3
  try:
    _run(manifest, malformed)
    malformed_rejected = False
  except (ValueError, TypeError, KeyError):
    malformed_rejected = True
  for row in scenario_definitions()['steady_speed']:
    _validate_cycle(row)
  for invalid in ({'v': float('nan'), 'a': 0., 'lead': None}, {'v': 20., 'a': 0., 'lead': None, 'cap': float('inf')}):
    try:
      _validate_cycle(invalid)
      malformed_rejected = False
    except ValueError:
      pass
  cases['solver_failure'] = {'injected_statuses': [0, 4], 'gate': solver_status_gate([0, 4]),
                             'expected_fault_detected': solver_status_gate([0, 4]) == 'FAIL_CLOSED_SOLVER_FAILURE'}
  cases['malformed_inputs'] = {'rejected': malformed_rejected, 'expected_fault_detected': malformed_rejected}
  passed = (cases['baseline']['quality_state'] == 'PASS_SYNTHETIC_ONLY' and
            all(case['expected_fault_detected'] for case in cases.values()) and
            all(cases[name]['locked_after_recovery_cycle'] for name in expected))
  return {'schema_version': 1, 'classification': 'R17_SYNTHETIC_SOFTWARE_FAULT_AUDIT',
          'status': 'PASS_SYNTHETIC_FAULT_DETECTION' if passed else 'FAIL_CLOSED',
          'actuation': 'NONE', 'input_sha256': hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
          'case_count': len(cases), 'cases': cases, 'native_solver_fault_injection': 'STATUS_GATE_ONLY_NO_SOLVER_MUTATION',
          'authenticated_vehicle_replay': 'NOT_RUN'}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--write-external', action='store_true')
  args = parser.parse_args()
  result = suite()
  if args.write_external:
    if EXTERNAL.is_symlink() or EXTERNAL.parent.is_symlink():
      raise ValueError('linked external fault receipt path')
    EXTERNAL.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
  print(json.dumps({'status': result['status'], 'cases': {k: v['faults'] if 'faults' in v else v for k, v in result['cases'].items()}}, indent=2, sort_keys=True))


if __name__ == '__main__':
  main()

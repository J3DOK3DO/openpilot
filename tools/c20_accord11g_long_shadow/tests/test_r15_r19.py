"""Focused negative substitutions for the software-only native MPC campaign."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.c20_accord11g_long_shadow import bundle, native_python_build, python_mpc, r19_campaign_gate, software_faults


class SyntheticInputTests(unittest.TestCase):
  def test_valid_scenarios_and_nonfinite_substitutions(self):
    cases = python_mpc.scenario_definitions()
    self.assertEqual(set(cases), {'steady_speed', 'following', 'lead_cut_in_loss', 'accel_cap', 'braking_stop_go', 'lead_recovery'})
    for rows in cases.values():
      for row in rows:
        python_mpc._validate_cycle(row)
    for bad in ({'v': float('nan'), 'a': 0.0, 'lead': None},
                {'v': 20.0, 'a': 0.0, 'lead': {'distance': -1.0, 'speed': 0.0}},
                {'v': 20.0, 'a': 0.0, 'lead': None, 'cap': float('inf')},
                {'v': 20.0, 'a': 0.0, 'lead': None, 'unrecognized': 1}):
      with self.assertRaises(ValueError):
        python_mpc._validate_cycle(bad)

  def test_solver_failure_or_invalid_status_fails_closed(self):
    self.assertEqual(software_faults.solver_status_gate([0, 0]), 'SOLVER_STATUS_ZERO_SYNTHETIC')
    for value in ([0, 4], [], [0, True], [0, -1], ['0']):
      self.assertNotEqual(software_faults.solver_status_gate(value), 'SOLVER_STATUS_ZERO_SYNTHETIC')

  def test_temporal_fault_suite_locks_through_recovery(self):
    result = software_faults.suite()
    self.assertEqual(result['status'], 'PASS_SYNTHETIC_FAULT_DETECTION')
    self.assertEqual(result['cases']['baseline']['faults'], [])
    for name in ('stale_model', 'stale_radar', 'clock_skew', 'unexpected_reset',
                 'lead_loss', 'driver_override', 'input_time_reversal'):
      self.assertTrue(result['cases'][name]['expected_fault_detected'])
      self.assertTrue(result['cases'][name]['locked_after_recovery_cycle'])
    self.assertIn('CAPTURE_DIGEST_MISMATCH', result['cases']['corrupted_evidence']['faults'])


class ReceiptAndGateTests(unittest.TestCase):
  def test_native_output_path_and_archive_privacy_reject_substitutions(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      (root/'actual').mkdir()
      (root/'native').symlink_to(root/'actual', target_is_directory=True)
      with patch.object(native_python_build, 'EVIDENCE', root):
        with self.assertRaises(ValueError):
          native_python_build.paths(root/'native')
    for name, content in (('solver.so', b'ELF'), ('source.py', b'"vin":"1HGCM82633A' + b'004352"'),
                          ('source.py', b'"latitude":' + b'25.1'),
                          ('source.py', b'"route_id":"aaaaaaaa--' + b'bbbbbbbbbb"')):
      with self.assertRaises(ValueError):
        bundle._check_public_entry(name, content)

  def test_native_execution_receipt_rejects_status_and_digest_substitutions(self):
    source = python_mpc.OUTPUT
    if not source.is_file():
      self.skipTest('external native execution receipt absent')
    original = json.loads(source.read_text())
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory)/'receipt.json'
      with patch.object(python_mpc, 'OUTPUT', path):
        path.write_text(json.dumps(original))
        self.assertEqual(python_mpc.verify_receipt()['status'], 'VERIFIED_LOCAL_EXECUTION_RECEIPT')
        changed = copy.deepcopy(original)
        changed['scenarios']['following']['samples'][0]['solver_status'] = 4
        path.write_text(json.dumps(changed))
        self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        changed = copy.deepcopy(original)
        changed['scenario_inputs_sha256'] = '0'*64
        path.write_text(json.dumps(changed))
        self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        path.write_text(json.dumps(original))
        self.assertEqual(python_mpc.verify_receipt('0'*64)['status'], 'REJECTED')

  def test_gate_remains_no_go_on_success_and_tamper(self):
    if not python_mpc.OUTPUT.is_file() or not software_faults.EXTERNAL.is_file():
      self.skipTest('external software evidence absent')
    good = r19_campaign_gate.evaluate()
    self.assertEqual(good['status'], 'R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW')
    self.assertEqual(good['road_use'], 'NO_GO')
    self.assertEqual(good['hardware_gates']['verification'], 'UNVERIFIED')
    with patch.object(r19_campaign_gate, 'FAULT_RECEIPT', Path('/missing/c20/faults.json')):
      bad = r19_campaign_gate.evaluate()
    self.assertEqual(bad['status'], 'R19_BLOCKED_SOFTWARE_EVIDENCE')
    self.assertEqual(bad['road_use'], 'NO_GO')


if __name__ == '__main__':
  unittest.main()

"""Focused negative substitutions for the software-only native MPC campaign."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

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
  def test_other_explicit_reruns_clear_prior_external_receipts(self):
    with tempfile.TemporaryDirectory() as directory:
      evidence = Path(directory)
      native = evidence/'native'
      native.mkdir()
      build_receipt = native/'python_build_receipt.json'
      build_receipt.write_text('{"status":"old"}')
      with patch.object(native_python_build, 'EVIDENCE', evidence), \
           patch.object(native_python_build, '_git', return_value='wrong revision'):
        with self.assertRaises(ValueError):
          native_python_build.build(native)
        self.assertFalse(build_receipt.exists())
        self.assertEqual(native_python_build.verify(native)['status'], 'REJECTED')
      faults_receipt = evidence/'software_faults_receipt.json'
      faults_receipt.write_text('{"status":"old"}')
      with patch.object(software_faults, 'EXTERNAL', faults_receipt), \
           patch.object(software_faults, 'suite', side_effect=ValueError('simulated suite failure')), \
           patch.object(sys, 'argv', ['software_faults', '--write-external']):
        with self.assertRaises(ValueError):
          software_faults.main()
      self.assertFalse(faults_receipt.exists())

  def test_failed_rerun_invalidates_prior_verified_mpc_receipt_and_blocks_gate(self):
    source = python_mpc.OUTPUT
    if not source.is_file() or not software_faults.EXTERNAL.is_file():
      self.skipTest('external software receipts absent')
    original = source.read_text()
    self.assertEqual(python_mpc.verify_receipt()['status'], 'VERIFIED_LOCAL_EXECUTION_RECEIPT')
    self.assertEqual(native_python_build.verify()['status'], 'VERIFIED_LOCAL_BUILD')
    self.assertEqual(r19_campaign_gate._git(native_python_build.C19, 'rev-parse', 'HEAD'),
                     r19_campaign_gate.BASELINE)
    with tempfile.TemporaryDirectory() as directory:
      evidence = Path(directory)
      (evidence/'native').symlink_to(python_mpc.EVIDENCE/'native', target_is_directory=True)
      output = evidence/'python_mpc_receipt.json'
      with patch.object(python_mpc, 'EVIDENCE', evidence), patch.object(python_mpc, 'OUTPUT', output), \
           patch.object(python_mpc, 'verify', side_effect=lambda *a, **k: native_python_build.verify()), \
           patch.object(r19_campaign_gate, '_scope', return_value=(True, [])):
        for failure in ('subprocess', 'timeout', 'injected_solve', 'preflight'):
          output.write_text(original)
          self.assertEqual(python_mpc.verify_receipt()['status'], 'VERIFIED_LOCAL_EXECUTION_RECEIPT')
          self.assertEqual(r19_campaign_gate.evaluate()['status'],
                           'R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW')
          if failure == 'preflight':
            native_result = {'status': 'REJECTED', 'reasons': ['simulated preflight failure']}
            with patch.object(python_mpc, 'verify', return_value=native_result):
              with self.assertRaises(ValueError):
                python_mpc.run()
          elif failure == 'timeout':
            with patch.object(python_mpc, '_native_subprocess', side_effect=subprocess.TimeoutExpired('native', 30)):
              with self.assertRaises(subprocess.TimeoutExpired):
                python_mpc.run()
          else:
            result = (Mock(returncode=1, stderr='simulated native failure', stdout='') if failure == 'subprocess'
                      else Mock(returncode=0, stderr='', stdout=json.dumps({'classification': 'TEST_ONLY_INJECTED_SOLVER_FAILURE'})))
            with patch.object(python_mpc, '_native_subprocess', return_value=result):
              with self.assertRaises(RuntimeError):
                python_mpc.run()
          self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
          self.assertEqual(json.loads(output.read_text()), {'status': 'INVALIDATED_FOR_RERUN'})
          blocked = r19_campaign_gate.evaluate()
          self.assertEqual(blocked['status'], 'R19_BLOCKED_SOFTWARE_EVIDENCE')
          self.assertEqual(blocked['road_use'], 'NO_GO')
          self.assertEqual(blocked['active_alpha_long'], 'NO_GO')
          self.assertIn('C19 Python MPC execution receipt rejected', blocked['reasons'])
        successful = json.loads(original)
        with patch.object(python_mpc, '_native_subprocess', return_value=Mock(
             returncode=0, stderr='', stdout=json.dumps(successful))):
          python_mpc.run()
        self.assertEqual(python_mpc.verify_receipt()['status'], 'VERIFIED_LOCAL_EXECUTION_RECEIPT')
        samples = [sample for scenario in json.loads(output.read_text())['scenarios'].values()
                   for sample in scenario['samples']]
        self.assertEqual(len(samples), 24)
        self.assertTrue(all(sample['solve_calls'] == 1 and sample['native_solve_status'] ==
                            sample['solver_status'] == 0 for sample in samples))
        self.assertEqual(r19_campaign_gate.evaluate()['status'],
                         'R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW')
        target = evidence/'linked_target.json'
        target.write_text(original)
        output.unlink()
        output.symlink_to(target)
        with self.assertRaises(ValueError):
          python_mpc.run()
        self.assertEqual(target.read_text(), original)
        self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        output.unlink()
        os.link(target, output)
        with self.assertRaises(ValueError):
          python_mpc.run()
        self.assertEqual(target.read_text(), original)
        self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')

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
        for value in ([], None, 'receipt', {}, {'scenarios': []}):
          path.write_text(json.dumps(value))
          self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        for value in ('{', '{"scenarios": NaN}', ' ' * 2_000_001):
          path.write_text(value)
          self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        for field in ('scenario_inputs_sha256', 'scenarios', 'schema_version'):
          changed = copy.deepcopy(original)
          del changed[field]
          path.write_text(json.dumps(changed))
          self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        for field in ('native_wrapper_sha256',):
          changed = copy.deepcopy(original)
          changed['imports'][field] = '0'*64
          path.write_text(json.dumps(changed))
          self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
        for mutation in ('missing_samples', 'wrong_cycles', 'hidden_reset', 'fake_call_count'):
          changed = copy.deepcopy(original)
          scenario = changed['scenarios']['following']
          if mutation == 'missing_samples':
            del scenario['samples']
          elif mutation == 'wrong_cycles':
            scenario['cycles'] = []
          elif mutation == 'hidden_reset':
            scenario['samples'][0]['native_solve_status'] = 4
            scenario['samples'][0]['solver_status'] = 0
          else:
            scenario['samples'][0]['solve_calls'] = 0
          changed['scenario_output_sha256'] = hashlib.sha256(json.dumps(changed['scenarios'], sort_keys=True,
              separators=(',', ':')).encode()).hexdigest()
          path.write_text(json.dumps(changed))
          self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED', mutation)
        path.write_text(json.dumps(original))
        self.assertEqual(python_mpc.verify_receipt('0'*64)['status'], 'REJECTED')

  def test_test_only_failure_survives_c19_reset_without_writing_receipt(self):
    if not python_mpc.OUTPUT.is_file():
      self.skipTest('external native execution receipt absent')
    before = python_mpc.OUTPUT.read_bytes()
    code = ("from tools.c20_accord11g_long_shadow import python_mpc as p; "
            "r=p.execute(p.EVIDENCE/'native', _test_fault_status=4); "
            "print(json.dumps(r))")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env['LD_LIBRARY_PATH'] = str(python_mpc.CACHE/'lib') + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    result = subprocess.run([sys.executable, '-B', '-c', 'import json; '+code], env=env,
                            capture_output=True, text=True, timeout=30, check=True)
    injected = json.loads(result.stdout)
    samples = [sample for scenario in injected['scenarios'].values() for sample in scenario['samples']]
    self.assertEqual(injected['classification'], 'TEST_ONLY_INJECTED_SOLVER_FAILURE')
    self.assertEqual(len(samples), 24)
    self.assertTrue(all(sample['native_solve_status'] == 0 and sample['solver_status'] == 4
                        and sample['solve_calls'] == 1 for sample in samples))
    with tempfile.TemporaryDirectory() as directory:
      output = Path(directory)/'injected.json'
      output.write_text(json.dumps(injected))
      with patch.object(python_mpc, 'OUTPUT', output):
        self.assertEqual(python_mpc.verify_receipt()['status'], 'REJECTED')
    self.assertEqual(python_mpc.OUTPUT.read_bytes(), before)

  def test_gate_remains_no_go_on_success_and_tamper(self):
    if not python_mpc.OUTPUT.is_file() or not software_faults.EXTERNAL.is_file():
      self.skipTest('external software evidence absent')
    actual_git = r19_campaign_gate._git
    def committed_git(repo, *args):
      if repo == r19_campaign_gate.RESEARCH and args == ('status', '--porcelain', '--untracked-files=all'):
        return ''  # Simulate the host's post-commit clean tree while exercising real HEAD ancestry.
      return actual_git(repo, *args)
    self.assertEqual(subprocess.run(['git', '-C', str(r19_campaign_gate.RESEARCH), 'merge-base',
                      '--is-ancestor', '4793b44feb814ec32c785468d8abfdba7a4e1bc1', 'HEAD'],
                      check=False).returncode, 0)
    with patch.object(r19_campaign_gate, '_git', side_effect=committed_git):
      good = r19_campaign_gate.evaluate()
    self.assertEqual(good['status'], 'R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW')
    self.assertEqual(good['road_use'], 'NO_GO')
    self.assertEqual(good['active_alpha_long'], 'NO_GO')
    self.assertEqual(good['hardware_gates']['verification'], 'UNVERIFIED')
    with patch.object(r19_campaign_gate, '_git', side_effect=committed_git):
      with patch.object(r19_campaign_gate, 'FAULT_RECEIPT', Path('/missing/c20/faults.json')):
        bad = r19_campaign_gate.evaluate()
      self.assertEqual(bad['status'], 'R19_BLOCKED_SOFTWARE_EVIDENCE')
      self.assertEqual(bad['road_use'], 'NO_GO')
      with tempfile.TemporaryDirectory() as directory:
        evidence = Path(directory)
        output = evidence/'python_mpc_receipt.json'
        with patch.object(python_mpc, 'OUTPUT', output):
          for content in ('[]', '{', None):
            if content is None:
              output.unlink()
            else:
              output.write_text(content)
            blocked = r19_campaign_gate.evaluate()
            self.assertEqual(blocked['status'], 'R19_BLOCKED_SOFTWARE_EVIDENCE')
            self.assertEqual(blocked['road_use'], 'NO_GO')
            self.assertEqual(blocked['active_alpha_long'], 'NO_GO')


if __name__ == '__main__':
  unittest.main()

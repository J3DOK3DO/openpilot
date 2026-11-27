from __future__ import annotations

from dataclasses import replace
import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.c20_accord11g_long_shadow.historical_attribution import summarize
from tools.c20_accord11g_long_shadow.native_gap import analyze, message_readiness, PROVENANCE, SERVICES
from tools.c20_accord11g_long_shadow.rawlog_census import EXPECTED, ROOT, SUMMARY, census, _sha256
from tools.c20_accord11g_long_shadow.shadow_advisory import ShadowConfig, ShadowCycle, serialize_observation

HISTORY = Path('/home/jdkd/AI_Workspace/projects/accord11g-starpilot/c2-low-speed-causal-20260914_202004')


class CensusTests(unittest.TestCase):
  def test_actual_four_pinned_segments_and_sanitized_counts(self):
    if not all((ROOT / f'0000009b--9f046e6157--{s}' / 'rlog.zst').is_file() for s in EXPECTED):
      self.skipTest('historical inputs unavailable')
    result = census(summary=json.loads(SUMMARY.read_text()))
    self.assertEqual(result['status'], 'PASS')
    self.assertEqual(result['current_vehicle_authenticated_routes'], 0)
    self.assertEqual(sum(s['services']['modelV2']['count'] for s in result['segments']), 4800)
    self.assertEqual(message_readiness(result)['receipt_timestamps'], 'NOT_RECORDED_BY_RLOG')

  def test_integrity_faults_and_unparsed_state(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      path = root / '0000009b--9f046e6157--5' / 'rlog.zst'
      path.parent.mkdir()
      path.write_bytes(subprocess.check_output(['zstd', '-q', '-c'], input=b'harmless test bytes'))
      expected = {5: _sha256(path)}
      result = census(root, expected)
      self.assertEqual(result['segments'][0]['event_parse'], 'UNPARSED')
      with self.assertRaisesRegex(ValueError, 'unsupported'):
        census(root, expected, decoder='unknown')
      with self.assertRaisesRegex(ValueError, 'SHA-256'):
        census(root, {5: '0' * 64})
      with self.assertRaisesRegex(ValueError, 'summary'):
        census(root, expected, summary={'method': 'unknown', 'segments': {'5': {}}})
      path.write_bytes(path.read_bytes()[:-1] + b'X')
      with self.assertRaisesRegex(ValueError, 'frame integrity'):
        census(root, {5: _sha256(path)})
      path.unlink()
      with self.assertRaisesRegex(ValueError, 'missing'):
        census(root, expected)


class ReadinessFaultTests(unittest.TestCase):
  def inventory(self):
    t = 300_000_000
    cycle = {'t_ns': t, 'drive_id': 'one', 'drive_reset_boundary': False,
             'source_t_ns': {s: t - 10 for s in SERVICES[:-2]},
             'receipt_t_ns': {s: t - 5 for s in SERVICES[:-2]},
             'driver_override': {'gas_pressed': False, 'brake_pressed': False},
             'lead_history': [{'source_t_ns': t - 10, 'receipt_t_ns': t - 5}],
             'model_trajectories': [1]}
    cycle.update({s: {'field': 1} for s in SERVICES})
    return {'provenance': {k: 'present' for k in PROVENANCE}, 'cycles': [cycle]}

  def check(self, data):
    with tempfile.TemporaryDirectory() as temp:
      path = Path(temp) / 'cycle.json'
      path.write_text(json.dumps(data))
      return analyze(path, expected_vehicle='present')

  def test_stale_lead_override_identity_and_reset_faults(self):
    base = self.inventory()
    self.assertEqual(self.check(base)['status'], 'SCHEMA_PRESENT_EXECUTION_UNVERIFIED')
    data = self.inventory(); data['cycles'][0]['lead_history'][0]['source_t_ns'] = 1
    self.assertIn('valid_lead_history_clocks', self.check(data)['missing_cycle_fields'])
    data = self.inventory(); del data['cycles'][0]['driver_override']['brake_pressed']
    self.assertIn('driver_override', self.check(data)['missing_cycle_fields'])
    data = self.inventory(); data['provenance']['vehicle'] = 'different car'
    self.assertIn('vehicle_identity_mismatch', self.check(data)['missing_provenance'])
    data = self.inventory(); data['cycles'].append(dict(data['cycles'][0], t_ns=1))
    with self.assertRaisesRegex(ValueError, 'nonmonotonic'):
      self.check(data)
    data = self.inventory(); data['cycles'].append(dict(data['cycles'][0], t_ns=1, drive_reset_boundary=True))
    self.assertIn('valid_drive_reset_boundary', self.check(data)['missing_cycle_fields'])


class AttributionTests(unittest.TestCase):
  def test_three_source_aligned_summaries(self):
    for event, rows in (('LS001', 1433), ('LS003', 690), ('LS004', 1122)):
      path = HISTORY / f'{event}_FULL_RATE.csv'
      if not path.is_file(): self.skipTest('historical CSV unavailable')
      result = summarize(path)
      self.assertEqual(result['qualifying_rows'], rows)
      self.assertEqual(result['future_source_rows'], 0)
      self.assertGreaterEqual(result['source_hold_age_ms']['carState']['distribution']['max'], 0)
      self.assertFalse(result['executed_solver'])

  def test_missing_provenance_and_cross_segment_fail(self):
    source = HISTORY / 'LS004_FULL_RATE.csv'
    if not source.is_file(): self.skipTest('historical CSV unavailable')
    with source.open(newline='') as stream:
      reader = csv.DictReader(stream); fields = reader.fieldnames; rows = list(reader)
    with tempfile.TemporaryDirectory() as temp:
      path = Path(temp) / 'fault.csv'
      for key, value in (('carState_logMonoTime', ''), ('segment', '105')):
        altered = [dict(row) for row in rows]
        altered[0][key] = value
        with path.open('w', newline='') as stream:
          writer = csv.DictWriter(stream, fields); writer.writeheader(); writer.writerows(altered)
        with self.assertRaises(ValueError): summarize(path)


class ShadowContractTests(unittest.TestCase):
  def test_canonical_inert_bytes_and_faults(self):
    sample = ShadowCycle('historical-test', 0, True, 300_000_000, 250_000_000,
                         260_000_000, -0.5, 'a' * 64)
    enabled = ShadowConfig(True)
    self.assertEqual(json.loads(serialize_observation(sample))['status'], 'DISABLED')
    output = serialize_observation(sample, config=enabled)
    self.assertIsInstance(output, bytes)
    self.assertEqual(output, serialize_observation(sample, config=enabled))
    self.assertEqual(json.loads(output)['status'], 'HISTORICAL_UNVERIFIED')
    self.assertNotIn('command', json.loads(output))
    faults = [replace(sample, source_t_ns=1), replace(sample, source_t_ns=300_000_001),
              replace(sample, receipt_t_ns=300_000_001), replace(sample, source_sha256='bad'),
              replace(sample, reset_boundary=False), replace(sample, provenance='CURRENT_VERIFIED')]
    for fault in faults:
      self.assertEqual(json.loads(serialize_observation(fault, config=enabled))['status'], 'FAILED_INPUT')
    next_cycle = replace(sample, cycle_index=1, reset_boundary=False, t_ns=301_000_000)
    self.assertEqual(json.loads(serialize_observation(next_cycle, sample, enabled))['status'], 'HISTORICAL_UNVERIFIED')
    self.assertEqual(json.loads(serialize_observation(replace(next_cycle, drive_id='other'), sample, enabled))['status'], 'FAILED_INPUT')


if __name__ == '__main__': unittest.main()

from __future__ import annotations

from dataclasses import replace
from copy import deepcopy
import csv
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.c20_accord11g_long_shadow.historical_attribution import summarize
from tools.c20_accord11g_long_shadow.native_gap import analyze, message_readiness, PROVENANCE, SERVICES
from tools.c20_accord11g_long_shadow.rawlog_census import EXPECTED, ROOT, SUMMARY, census, segment_path, _sha256
from tools.c20_accord11g_long_shadow.shadow_advisory import ShadowConfig, ShadowCycle, serialize_observation

HISTORY = ROOT.parents[4] if ROOT.is_absolute() else Path('__R9_HISTORY_UNAVAILABLE__')


class CensusTests(unittest.TestCase):
  def test_actual_four_pinned_segments_and_sanitized_counts(self):
    try:
      available = all(segment_path(ROOT, s).is_file() for s in EXPECTED)
    except ValueError:
      available = False
    if not available:
      self.skipTest('historical inputs unavailable')
    result = census(summary=json.loads(SUMMARY.read_text()))
    self.assertEqual(result['status'], 'PASS')
    self.assertEqual(result['current_vehicle_authenticated_routes'], 0)
    self.assertEqual(sum(s['services']['modelV2']['count'] for s in result['segments']), 4800)
    readiness = message_readiness(result)
    self.assertEqual(readiness['receipt_timestamps'], 'NOT_RECORDED_BY_RLOG')
    self.assertTrue(all(readiness['historical_schema_messages_available_each_segment'].values()))
    self.assertEqual(readiness['status'], 'BLOCKED_RECEIPT_AND_EXACT_SOURCE_PROVENANCE')

  def test_integrity_faults_and_unparsed_state(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      path = root / 'synthetic--5' / 'rlog.zst'
      path.parent.mkdir()
      path.write_bytes(subprocess.check_output(['zstd', '-q', '-c'], input=b'harmless test bytes'))
      expected = {5: _sha256(path)}
      result = census(root, expected)
      self.assertEqual(result['segments'][0]['event_parse'], 'UNPARSED')
      readiness = message_readiness(result)
      self.assertEqual(readiness['status'], 'BLOCKED_RECEIPT_AND_EXACT_SOURCE_PROVENANCE')
      self.assertTrue(all(not value for value in readiness['historical_schema_messages_available_each_segment'].values()))
      self.assertFalse(readiness['current_vehicle_authenticated'])
      self.assertFalse(readiness['executed_solver'])
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

  def test_decoded_counts_and_malformed_counts_fail_closed(self):
    required = ('carState', 'radarState', 'modelV2', 'controlsState', 'selfdriveState', 'carControl', 'carParams')
    segment = {'event_parse': 'DECODED_HISTORICAL_SCHEMA',
               'services': {name: {'state': 'DECODED_HISTORICAL_SCHEMA', 'count': 1} for name in required}}
    base = {'status': 'PASS', 'segments': [deepcopy(segment), deepcopy(segment)]}
    ready = message_readiness(base)
    self.assertTrue(all(ready['historical_schema_messages_available_each_segment'].values()))
    self.assertEqual(ready['status'], 'BLOCKED_RECEIPT_AND_EXACT_SOURCE_PROVENANCE')
    self.assertFalse(ready['current_vehicle_authenticated'])
    self.assertFalse(ready['executed_solver'])
    for value in (None, 0, -1, True, '1', 1.0):
      report = deepcopy(base)
      report['segments'][1]['services']['carState']['count'] = value
      self.assertFalse(message_readiness(report)['historical_schema_messages_available_each_segment']['carState'])
    for mutation in ('missing_service', 'missing_count', 'unparsed', 'empty_segments'):
      report = deepcopy(base)
      if mutation == 'missing_service': del report['segments'][1]['services']['carState']
      if mutation == 'missing_count': del report['segments'][1]['services']['carState']['count']
      if mutation == 'unparsed': report['segments'][1]['event_parse'] = 'UNPARSED'
      if mutation == 'empty_segments': report['segments'] = []
      self.assertFalse(message_readiness(report)['historical_schema_messages_available_each_segment']['carState'])


class ReadinessFaultTests(unittest.TestCase):
  def inventory(self):
    t = 300_000_000
    cycle = {'t_ns': t, 'drive_id': 'one', 'drive_reset_boundary': True,
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
    data = self.inventory(); data['cycles'].append(dict(data['cycles'][0], t_ns=1, drive_reset_boundary=False))
    with self.assertRaisesRegex(ValueError, 'nonmonotonic'):
      self.check(data)
    data = self.inventory(); data['cycles'].append(dict(data['cycles'][0], t_ns=1, drive_reset_boundary=True))
    with self.assertRaisesRegex(ValueError, 'nonmonotonic'):
      self.check(data)

  def test_first_cycle_and_cross_drive_reset_contract(self):
    base = self.inventory()
    self.assertEqual(self.check(base)['status'], 'SCHEMA_PRESENT_EXECUTION_UNVERIFIED')
    self.assertFalse(self.check(base)['executed_solver'])
    for value in (False, None, 'true'):
      data = deepcopy(base)
      if value is None: del data['cycles'][0]['drive_reset_boundary']
      else: data['cycles'][0]['drive_reset_boundary'] = value
      report = self.check(data)
      self.assertEqual(report['status'], 'FAIL_MISSING_REQUIRED_INPUTS')
      self.assertIn('valid_drive_reset_boundary', report['missing_cycle_fields'])
    same = deepcopy(base['cycles'][0]); same['t_ns'] += 1; same['drive_reset_boundary'] = False
    data = deepcopy(base); data['cycles'].append(same)
    self.assertEqual(self.check(data)['status'], 'SCHEMA_PRESENT_EXECUTION_UNVERIFIED')
    for value in (True, None):
      data = deepcopy(base); data['cycles'].append(deepcopy(same))
      if value is None: del data['cycles'][1]['drive_reset_boundary']
      else: data['cycles'][1]['drive_reset_boundary'] = value
      self.assertIn('valid_drive_reset_boundary', self.check(data)['missing_cycle_fields'])
    for t in (base['cycles'][0]['t_ns'], base['cycles'][0]['t_ns'] - 1):
      data = deepcopy(base); data['cycles'].append(dict(same, t_ns=t))
      with self.assertRaisesRegex(ValueError, 'nonmonotonic'):
        self.check(data)
    new_drive = deepcopy(base['cycles'][0]); new_drive['drive_id'] = 'two'
    new_drive['t_ns'] = 100_000_000
    new_drive['source_t_ns'] = {s: new_drive['t_ns'] - 10 for s in SERVICES[:-2]}
    new_drive['receipt_t_ns'] = {s: new_drive['t_ns'] - 5 for s in SERVICES[:-2]}
    new_drive['lead_history'] = [{'source_t_ns': new_drive['t_ns'] - 10,
                                  'receipt_t_ns': new_drive['t_ns'] - 5}]
    data = deepcopy(base); data['cycles'].append(new_drive)
    self.assertEqual(self.check(data)['status'], 'SCHEMA_PRESENT_EXECUTION_UNVERIFIED')
    for value in (False, None):
      data = deepcopy(base); data['cycles'].append(deepcopy(new_drive))
      if value is None: del data['cycles'][1]['drive_reset_boundary']
      else: data['cycles'][1]['drive_reset_boundary'] = value
      self.assertIn('valid_drive_reset_boundary', self.check(data)['missing_cycle_fields'])
    data = deepcopy(base); data['cycles'].append(deepcopy(new_drive))
    data['cycles'][1]['receipt_t_ns']['carState'] = base['cycles'][0]['t_ns']
    self.assertIn('valid_carState_receipt_t_ns', self.check(data)['missing_cycle_fields'])


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

  def test_malformed_measured_acceleration_emits_canonical_failure_only(self):
    sample = ShadowCycle('historical-test', 0, True, 300_000_000, 250_000_000,
                         260_000_000, -0.5, 'a' * 64)
    expected = b'{"advisory_only":true,"status":"FAILED_INPUT"}'
    for value in (10**1000, 'bad', None, [], {}, True, float('nan'), float('inf'), float('-inf')):
      output = serialize_observation(replace(sample, measured_aego_mps2=value), config=ShadowConfig(True))
      self.assertEqual(output, expected)
      self.assertNotIn(b'command', output)
      self.assertNotIn(b'measured_aego', output)
      self.assertNotIn(b'autonomous_braking', output)


if __name__ == '__main__': unittest.main()

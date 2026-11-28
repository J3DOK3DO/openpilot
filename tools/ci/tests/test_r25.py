"""Synthetic isolation tests only; no assertion here claims native execution."""
import hashlib
import json
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import numpy as np

from openpilot.starpilot.longitudinal.c20_shadow import Shadow, admit
from openpilot.starpilot.longitudinal.c20_shadow_smoke import run_synthetic_smoke
from tools.c20_accord11g_long_shadow.r25_gate import command_path_audit, evaluate
from tools.c20_accord11g_long_shadow.r25_model_assets import MODEL_COMPONENTS, verify_models, verify_one
from tools.c20_accord11g_long_shadow.r25_package import candidate
from tools.c20_accord11g_long_shadow.python_mpc import verify_receipt


NOW = 1_000_000_000
FLOOR = 800_000_000
SERVICES = ('carState', 'radarState', 'modelV2', 'controlsState', 'deviceState')


def frame():
  lead = NS(present=True, dRel=35.0, vLead=17.0, aLeadK=0.0, aLeadTau=1.5, modelProb=0.8, radar=True)
  absent = NS(present=False)
  data = {
    'carParams': NS(carFingerprint='ACCORD_11G', openpilotLongitudinalControl=False),
    'carState': NS(canValid=True, canTimeout=False, accFaulted=False, cruiseState=NS(enabled=True),
                   gasPressed=False, brakePressed=False, stockAeb=False, stockFcw=False, vEgo=20.0, aEgo=0.0),
    'radarState': NS(mdMonoTime=950_000_000, leadOne=lead, leadTwo=absent,
                     radarErrors=NS(to_dict=lambda: {})),
    'modelV2': NS(velocity=NS(x=[20.0])),
    'controlsState': NS(forceDecel=False),
    'deviceState': NS(started=True, startedMonoTime=700_000_000),
  }
  names = (*SERVICES, 'carParams')
  class SM:
    valid = dict.fromkeys(names, True)
    alive = dict.fromkeys(names, True)
    logMonoTime = dict.fromkeys(names, 950_000_000)
    recv_time = dict.fromkeys(names, .975)
    def __getitem__(self, key):
      return data[key]
  return SM(), data


class SyntheticSolver:
  def __init__(self, status=0):
    self.status = status
  def solve(self):
    return self.status


class SyntheticMpc:
  next_status = 0
  def __init__(self):
    self.solver = SyntheticSolver(self.next_status)
    self.x_sol = np.zeros((13, 3))
    self.v_solution = np.zeros(13)
    self.a_solution = np.zeros(13)
    self.j_solution = np.zeros(12)
  def set_cur_state(self, v, a):
    self.v_solution[0] = v
  def update(self, radar):
    self.solver.solve()
    self.a_solution[1] = -0.125


class R25SyntheticIsolation(unittest.TestCase):
  def test_admitted_snapshot_and_no_input_leak(self):
    sm, data = frame()
    snapshot = admit(sm, NOW, FLOOR, 'ACCORD_11G')
    self.assertIsNotNone(snapshot)
    data['radarState'].leadOne.dRel = 2.0
    self.assertEqual(snapshot.radar.leadOne.dRel, 35.0)

  def test_missing_stale_and_racing_inputs(self):
    for mutate in (
      lambda sm, d: sm.valid.__setitem__('modelV2', False),
      lambda sm, d: sm.logMonoTime.__setitem__('radarState', 700_000_000),
      lambda sm, d: sm.recv_time.__setitem__('carState', .90),
      lambda sm, d: setattr(d['radarState'], 'mdMonoTime', 949_000_000),
      lambda sm, d: setattr(d['carParams'], 'carFingerprint', 'OTHER'),
      lambda sm, d: setattr(d['carParams'], 'openpilotLongitudinalControl', True),
    ):
      with self.subTest(mutate=mutate):
        sm, data = frame()
        mutate(sm, data)
        self.assertIsNone(admit(sm, NOW, FLOOR, 'ACCORD_11G'))

  def test_slow_device_state_freshness_is_not_fast_stream_skew(self):
    # deviceState publishes at 2 Hz; its last frame can be much older than
    # the 20 Hz model/radar frames while remaining a valid diagnostic input.
    now_ns, floor_ns, fast_ns = 3_000_000_000, 1_000_000_000, 2_960_000_000
    sm, data = frame()
    data['deviceState'].startedMonoTime = 500_000_000
    for name in ('carState', 'radarState', 'modelV2', 'controlsState'):
      sm.logMonoTime[name] = fast_ns
      sm.recv_time[name] = 2.98
    data['radarState'].mdMonoTime = fast_ns
    sm.logMonoTime['deviceState'] = 2_100_000_000
    sm.recv_time['deviceState'] = 2.12
    self.assertIsNotNone(admit(sm, now_ns, floor_ns, 'ACCORD_11G'))
    sm.logMonoTime['deviceState'] = 1_500_000_000
    sm.recv_time['deviceState'] = 1.52
    self.assertIsNone(admit(sm, now_ns, floor_ns, 'ACCORD_11G'))
    sm.logMonoTime['deviceState'] = 2_100_000_000
    sm.recv_time['deviceState'] = 2.12
    sm.logMonoTime['controlsState'] = fast_ns - 100_000_000
    self.assertIsNone(admit(sm, now_ns, floor_ns, 'ACCORD_11G'))

  def test_driver_aeb_bad_clock_lead_loss_and_restart(self):
    for field in ('gasPressed', 'brakePressed', 'stockAeb', 'stockFcw', 'accFaulted'):
      sm, data = frame()
      setattr(data['carState'], field, True)
      self.assertIsNone(admit(sm, NOW, FLOOR, 'ACCORD_11G'))
    sm, data = frame()
    data['radarState'].leadOne.present = False
    self.assertIsNone(admit(sm, NOW, FLOOR, 'ACCORD_11G'))
    sm, data = frame()
    data['carState'].cruiseState.enabled = False
    self.assertIsNone(admit(sm, NOW, FLOOR, 'ACCORD_11G'))
    sm, data = frame()
    data['radarState'].radarErrors = NS(to_dict=lambda: {'fault': True})
    self.assertIsNone(admit(sm, NOW, FLOOR, 'ACCORD_11G'))
    sm, data = frame()
    self.assertIsNone(admit(sm, NOW, NOW + 1, 'ACCORD_11G'))
    self.assertIsNone(admit(sm, NOW - 100_000_000, FLOOR, 'ACCORD_11G'))

  def test_synthetic_solver_isolation_and_status(self):
    name = 'openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc'
    fake = types.ModuleType(name)
    fake.LongitudinalMpc = SyntheticMpc
    with patch.dict(sys.modules, {name: fake}):
      sm, _ = frame()
      shadow = Shadow('ACCORD_11G', FLOOR)
      first = shadow.step(sm, NOW)
      self.assertEqual(first['execution'], 'PRODUCT_NATIVE_MPC_ONLY')
      self.assertEqual(set(first), {'status', 'execution', 'cycle', 'first_accel_mps2'})
      sm.valid['radarState'] = False
      self.assertEqual(shadow.step(sm, NOW)['execution'], 'NONE')
      self.assertIsNone(shadow.mpc)
      sm, _ = frame()
      SyntheticMpc.next_status = 7
      try:
        self.assertEqual(shadow.step(sm, NOW)['status'], 'NATIVE_UNAVAILABLE_OR_FAILED')
        self.assertIsNone(shadow.mpc)
      finally:
        SyntheticMpc.next_status = 0

  def test_bounded_synthetic_native_smoke_never_uses_vehicle(self):
    name = 'openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc'
    fake = types.ModuleType(name)
    fake.LongitudinalMpc = SyntheticMpc
    with patch.dict(sys.modules, {name: fake}):
      result = run_synthetic_smoke(2)
      self.assertEqual(result['classification'], 'SYNTHETIC_LOCAL_NATIVE_MPC_ONLY')
      self.assertEqual(result['status'], 'LOCAL_NUMERICAL_EXECUTION')
      self.assertEqual(result['solve_calls'], 2)
      self.assertEqual(result['native_solve_statuses'], [0, 0])
      self.assertEqual(result['actuation'], 'NONE')
      self.assertEqual(result['vehicle_evidence'], 'NONE')
      SyntheticMpc.next_status = 7
      try:
        self.assertEqual(run_synthetic_smoke(2)['status'], 'NATIVE_UNAVAILABLE_OR_FAILED')
      finally:
        SyntheticMpc.next_status = 0
    with self.assertRaises(ValueError):
      run_synthetic_smoke(0)
    with self.assertRaises(ValueError):
      run_synthetic_smoke(5)

  def test_real_chunked_model_integrity_and_synthetic_tamper(self):
    # Existing published compiled models are verified on disk; this is NOT a
    # QCOM inference test or evidence of a current build.
    repo = Path(__file__).resolve().parents[3]
    self.assertEqual(len(MODEL_COMPONENTS), 7)
    self.assertEqual(verify_models(repo), [])
    import tempfile
    with tempfile.TemporaryDirectory() as temporary:
      sample = Path(temporary) / 'openpilot/selfdrive/modeld/models'
      sample.mkdir(parents=True)
      data = b'offline fake model fixture'
      digest = hashlib.sha256(data).hexdigest()
      name = 'fixture.pkl'
      (sample / f'{name}.chunkmanifest').write_text('1')
      (sample / f'{name}.chunksha256').write_text(json.dumps({
        'bytes': len(data), 'sha256': digest,
        'parts': [{'bytes': len(data), 'sha256': digest}],
      }))
      part = sample / f'{name}.chunk01of01'
      part.write_bytes(data)
      self.assertEqual(verify_one(Path(temporary), name, 1, digest, len(data)), [])
      part.write_bytes(b'X' + data[1:])
      self.assertTrue(verify_one(Path(temporary), name, 1, digest, len(data)))
      part.unlink()
      self.assertTrue(verify_one(Path(temporary), name, 1, digest, len(data)))

  def test_static_command_path_and_package_block(self):
    repo = Path(__file__).resolve().parents[3]
    self.assertEqual(command_path_audit(repo / 'openpilot/starpilot/longitudinal/c20_shadow.py'), [])
    self.assertEqual(command_path_audit(repo / 'openpilot/starpilot/longitudinal/c20_shadow_smoke.py'), [])
    self.assertEqual(candidate(repo)['status'], 'BLOCKED')

  def test_static_command_path_rejects_publication(self):
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'bad.py'
      path.write_text('from openpilot.cereal.messaging import PubMaster\npub.send("carControl", None)\n')
      findings = command_path_audit(path)
      self.assertIn('forbidden name PubMaster', findings)
      self.assertIn('forbidden attribute send', findings)

  def test_static_command_path_rejects_dynamic_imports(self):
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / 'bad_dynamic.py'
      path.write_text('import importlib\n'
                      'def deep_import():\n'
                      '  return importlib.import_module("openpilot.selfdrive.car")\n'
                      '__import__("panda")\n'
                      'eval("42")\n')
      findings = command_path_audit(path)
      self.assertIn('forbidden dynamic call import_module', findings)
      self.assertIn('forbidden dynamic call __import__', findings)
      self.assertIn('forbidden dynamic call eval', findings)

  def test_gate_preserves_first_porcelain_filename(self):
    repo = Path(__file__).resolve().parents[3]
    gate = evaluate(repo)
    self.assertEqual(gate['source_audit'], 'PASS')
    self.assertFalse(any('out-of-scope changed paths' in reason for reason in gate['reasons']))
    self.assertEqual(gate['PATH_B2_ACTIVE_LONGITUDINAL'], 'NO_GO')
    self.assertFalse(gate['installable'])

  def test_r19_genuine_x86_receipt_remains_historical(self):
    self.assertEqual(verify_receipt(expected_sha256='bf69aedd22f4f143e6c6997e3ab64e84870f36315802c4321bdd6f2aadd0c561')['status'],
                     'VERIFIED_LOCAL_EXECUTION_RECEIPT')


if __name__ == '__main__':
  unittest.main()

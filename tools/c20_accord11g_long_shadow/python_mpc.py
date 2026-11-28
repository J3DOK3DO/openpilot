"""Offline synthetic execution of the unmodified C19 Python LongitudinalMpc.

The CLI requires an explicit prebuilt x86 solver. Import never builds or loads it.
The only stubs replace import dependencies outside the numerical MPC; numeric
constants are extracted verbatim from pinned C19 Python source assignments.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from types import SimpleNamespace

from .native_python_build import C19, CACHE, EVIDENCE, digest, verify
from .platform_receipt import BASELINE

MPC = C19/'openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/long_mpc.py'
OUTPUT = EVIDENCE/'python_mpc_receipt.json'
CASADI = CACHE.parents[1]/'casadi'


def _literal(path: Path, name: str):
  tree = ast.parse(path.read_text())
  for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
      return ast.literal_eval(node.value)
  raise ValueError(f'missing source constant {name}: {path}')


def _stub(name: str, records: list[str], **attrs):
  module = types.ModuleType(name)
  module.__dict__.update(attrs)
  sys.modules[name] = module
  records.append(name)


def _load_c19(native: Path) -> tuple[type, dict]:
  # Preserve the frozen checkout even when invoked outside the normal launcher.
  sys.dont_write_bytecode = True
  if any(name == 'openpilot' or name.startswith('openpilot.') or
         name == 'opendbc' or name.startswith('opendbc.') for name in sys.modules):
    raise ValueError('preloaded product namespace prevents isolated C19 import')
  import numpy as np
  sys.path.insert(0, str(C19))
  sys.path.insert(1, str(CACHE.parents[1]))
  records: list[str] = []
  class Personality:
    relaxed, standard, aggressive = 0, 1, 2
  class PlanSource:
    cruise, lead0, lead1 = 0, 1, 2
  _stub('openpilot.cereal', records, log=SimpleNamespace(LongitudinalPersonality=Personality,
         LongitudinalPlan=SimpleNamespace(LongitudinalPlanSource=PlanSource)))
  _stub('opendbc', records, __path__=[])
  _stub('opendbc.car', records, __path__=[])
  opendbc = C19/'opendbc_repo/opendbc/car'
  interfaces = opendbc/'interfaces.py'
  numeric = {
    'ACCEL_MIN': _literal(interfaces, 'ACCEL_MIN'),
    'ACCEL_MAX': _literal(interfaces, 'ACCEL_MAX'),
    'TAKEOFF_ACCEL_MAX': _literal(opendbc/'__init__.py', 'ACCEL_MAX_TAKEOFF'),
    'DT_MDL': _literal(C19/'openpilot/common/realtime.py', 'DT_MDL'),
    '_LEAD_ACCEL_TAU': _literal(C19/'openpilot/selfdrive/controls/radard.py', '_LEAD_ACCEL_TAU'),
    'RADAR_TO_CAMERA': _literal(C19/'openpilot/selfdrive/controls/radard.py', 'RADAR_TO_CAMERA'),
  }
  _stub('opendbc.car.interfaces', records, ACCEL_MIN=numeric['ACCEL_MIN'], ACCEL_MAX=numeric['ACCEL_MAX'])
  _stub('openpilot.starpilot.longitudinal.lead_takeoff_preferences', records, MAX_ACCEL=numeric['TAKEOFF_ACCEL_MAX'])
  _stub('openpilot.common.realtime', records, DT_MDL=numeric['DT_MDL'])
  _stub('openpilot.common.swaglog', records, cloudlog=SimpleNamespace(warning=lambda message: None))
  _stub('openpilot.selfdrive.controls.radard', records, _LEAD_ACCEL_TAU=numeric['_LEAD_ACCEL_TAU'], RADAR_TO_CAMERA=numeric['RADAR_TO_CAMERA'])
  import casadi  # Cached real CasADi; no numerical stub.
  generated = C19/'openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/c_generated_code'
  name = 'openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.c_generated_code.acados_ocp_solver_pyx'
  extension = next(native.glob('acados_ocp_solver_pyx*.so'))
  spec = importlib.util.spec_from_file_location(name, extension)
  if spec is None or spec.loader is None:
    raise ValueError('native wrapper unavailable')
  module = importlib.util.module_from_spec(spec)
  sys.modules[name] = module
  spec.loader.exec_module(module)
  from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc
  if Path(long_mpc.__file__).resolve() != MPC.resolve() or Path(module.__file__).resolve() != extension.resolve():
    raise ValueError('C19 MPC source or native wrapper provenance mismatch')
  from openpilot.selfdrive.modeld import constants
  if Path(constants.__file__).resolve() != (C19/'openpilot/selfdrive/modeld/constants.py').resolve():
    raise ValueError('model constants provenance mismatch')
  return long_mpc.LongitudinalMpc, {
    'classification': 'STUBBED_NONNUMERICAL_IMPORTS', 'stubbed_modules': records,
    'numeric_constants_from_c19_source': numeric,
    'numeric_source_sha256': {str(p.relative_to(C19)): digest(p) for p in
      (interfaces, opendbc/'__init__.py', C19/'openpilot/common/realtime.py',
       C19/'openpilot/selfdrive/controls/radard.py', constants.__file__ and Path(constants.__file__))},
    'c19_long_mpc_sha256': digest(MPC), 'c19_long_mpc_path': str(MPC),
    'native_wrapper_sha256': digest(extension), 'casadi_path': str(Path(casadi.__file__).resolve()),
  }


def scenario_definitions() -> dict[str, list[dict]]:
  # Values are synthetic inputs to C19 update(); each scenario starts a fresh solver.
  free = {'v': 20.0, 'a': 0.0, 'lead': None}
  follow = {'v': 20.0, 'a': 0.0, 'lead': {'distance': 35.0, 'speed': 17.0}}
  near = {'v': 20.0, 'a': 0.0, 'lead': {'distance': 18.0, 'speed': 14.0}}
  stop = {'v': 4.0, 'a': 0.0, 'lead': {'distance': 12.0, 'speed': 0.0}}
  return {
    'steady_speed': [dict(free) for _ in range(4)],
    'following': [dict(follow) for _ in range(4)],
    'lead_cut_in_loss': [dict(free), dict(near), dict(near), dict(free)],
    'accel_cap': [dict(free, cap=0.5) for _ in range(4)],
    'braking_stop_go': [dict(stop), dict(stop), {'v': 0.5, 'a': 0.0, 'lead': {'distance': 7.0, 'speed': 0.0}},
                        {'v': 0.5, 'a': 0.0, 'lead': {'distance': 12.0, 'speed': 2.0}}],
    'lead_recovery': [dict(follow), dict(free), dict(free), dict(follow)],
  }


def _validate_cycle(row: dict) -> None:
  if type(row) is not dict or not {'v', 'a', 'lead'} <= row.keys() or set(row) - {'v', 'a', 'lead', 'cap', 'stop_line_m'}:
    raise ValueError('synthetic cycle schema invalid')
  for field, low, high in (('v', 0, 60), ('a', -5, 4)):
    x = row[field]
    if type(x) not in (int, float) or not math.isfinite(x) or not low <= x <= high:
      raise ValueError('synthetic '+field+' invalid')
  lead = row['lead']
  if lead is not None and (type(lead) is not dict or set(lead) != {'distance', 'speed'} or
      any(type(lead[k]) not in (int, float) or not math.isfinite(lead[k]) for k in lead) or
      not 0 <= lead['distance'] <= 300 or not 0 <= lead['speed'] <= 60):
    raise ValueError('synthetic lead invalid')
  if 'cap' in row and (type(row['cap']) not in (int, float) or not math.isfinite(row['cap']) or not 0 <= row['cap'] <= 3.5):
    raise ValueError('accel cap invalid')
  if 'stop_line_m' in row and (type(row['stop_line_m']) not in (int, float) or not math.isfinite(row['stop_line_m']) or not 0 <= row['stop_line_m'] <= 500):
    raise ValueError('stop line invalid')


def _lead(value: dict | None):
  return SimpleNamespace(present=value is not None, dRel=value['distance'] if value else 50.0,
    vLead=value['speed'] if value else 0.0, aLeadK=0.0, aLeadTau=1.5, modelProb=0.0, radar=True)


class ObservedSolver:
  """Delegate every operation to the real Cython solver; retain solve returns across reset."""
  def __init__(self, native, fault_status: int | None = None):
    self.native = native
    self.fault_status = fault_status
    self.native_statuses: list[int] = []
    self.returned_statuses: list[int] = []

  def __getattr__(self, name):
    return getattr(self.native, name)

  def solve(self):
    status = self.native.solve()
    if type(status) is not int:
      raise ValueError('native solver returned a noninteger status')
    self.native_statuses.append(status)
    returned = self.fault_status if self.fault_status is not None else status
    self.returned_statuses.append(returned)
    return returned


def execute(native: Path, *, _test_fault_status: int | None = None) -> dict:
  if _test_fault_status is not None and (type(_test_fault_status) is not int or _test_fault_status == 0):
    raise ValueError('test fault status must be nonzero integer')
  build = verify(native)
  if build['status'] != 'VERIFIED_LOCAL_BUILD':
    raise ValueError('native build receipt rejected: '+repr(build['reasons']))
  cls, imports = _load_c19(native)
  import numpy as np
  scenarios = {}
  definitions = scenario_definitions()
  for name, rows in definitions.items():
    mpc = cls()
    observed = ObservedSolver(mpc.solver, _test_fault_status)
    mpc.solver = observed
    samples = []
    for row in rows:
      _validate_cycle(row)
      mpc.set_cur_state(row['v'], row['a'])
      radar = SimpleNamespace(leadOne=_lead(row['lead']), leadTwo=_lead(None))
      before = len(observed.native_statuses)
      mpc.update(radar, acceleration_max=row.get('cap'), stop_line_m=row.get('stop_line_m'))
      if len(observed.native_statuses) != before + 1 or len(observed.returned_statuses) != before + 1:
        raise ValueError('expected exactly one genuine native solve per cycle')
      native_status = observed.native_statuses[-1]
      returned_status = observed.returned_statuses[-1]
      if returned_status != 0 and mpc.solution_status != 0:
        raise ValueError('C19 solver failure reset behavior changed')
      arrays = (mpc.x_sol, mpc.v_solution, mpc.a_solution, mpc.j_solution, mpc.params)
      if any(not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError('nonfinite native MPC trajectory')
      samples.append({'solver_status': returned_status, 'native_solve_status': native_status,
                      'solve_calls': len(observed.native_statuses) - before, 'source': int(mpc.source),
                      'v_first_5_mps': np.round(mpc.v_solution[:5], 8).tolist(),
                      'a_first_5_mps2': np.round(mpc.a_solution[:5], 8).tolist(),
                      'jerk_first_5_mps3': np.round(mpc.j_solution[:5], 8).tolist(),
                      'obstacle_m_first': round(float(mpc.params[0, 2]), 8),
                      'accel_ceiling_mps2': round(float(mpc.params[0, 1]), 8)})
    scenarios[name] = {'cycles': len(rows), 'samples': samples,
       'statuses': [s['solver_status'] for s in samples],
       'max_abs_accel_first_5_mps2': round(max(abs(x) for s in samples for x in s['a_first_5_mps2']), 8)}
  scenario_bytes = json.dumps(scenarios, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
  clean_solves = all(all(sample['solver_status'] == sample['native_solve_status'] == 0
                         for sample in scenario['samples']) for scenario in scenarios.values())
  classification = ('TEST_ONLY_INJECTED_SOLVER_FAILURE' if _test_fault_status is not None else
                    'C19_PYTHON_MPC_NATIVE_X86_VERIFIED' if clean_solves else 'C19_PYTHON_MPC_SOLVER_FAILURE')
  return {'schema_version': 2, 'classification': classification,
          'source_commit': BASELINE, 'input_classification': 'DETERMINISTIC_SYNTHETIC',
          'execution_class': 'C19_LONGITUDINAL_MPC_UPDATE_SOLVE',
          'planner_execution': 'FULL_C19_LONGITUDINAL_PLANNER_NOT_RUN',
          'authenticated_vehicle_replay': 'AUTHENTICATED_VEHICLE_REPLAY_NOT_RUN',
          'actuation': 'NONE', 'modelV2_trajectory': 'NOT_SUPPLIED',
          'native_build_receipt_sha256': build['receipt_sha256'], 'imports': imports,
          'scenario_inputs_sha256': hashlib.sha256(json.dumps(definitions, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
          'scenario_output_sha256': hashlib.sha256(scenario_bytes).hexdigest(), 'scenarios': scenarios}


def run() -> dict:
  native = EVIDENCE/'native'
  if OUTPUT.parent != EVIDENCE or any(p.is_symlink() for p in (EVIDENCE, *EVIDENCE.parents)):
    raise ValueError('linked external MPC receipt path')
  if OUTPUT.is_symlink() or (OUTPUT.exists() and
      (not OUTPUT.is_file() or os.stat(OUTPUT, follow_symlinks=False).st_nlink != 1)):
    raise ValueError('linked or unsafe external MPC receipt path')
  # Publish the rejected state before verification or a native subprocess can fail.
  _publish({'status': 'INVALIDATED_FOR_RERUN'})
  preliminary = verify(native)
  if preliminary['status'] != 'VERIFIED_LOCAL_BUILD':
    raise ValueError('native build verification rejected')
  env = dict(os.environ)
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  env['LD_LIBRARY_PATH'] = str(CACHE/'lib') + (':' + env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
  result = _native_subprocess(env)
  if result.returncode:
    raise RuntimeError('native Python MPC subprocess failed: '+result.stderr[-3000:])
  receipt = json.loads(result.stdout)
  if receipt.get('classification') != 'C19_PYTHON_MPC_NATIVE_X86_VERIFIED':
    raise RuntimeError('native Python MPC solve failed; verified receipt was not written')
  _publish(receipt, verify_before_replace=True)
  return receipt


def _native_subprocess(env: dict[str, str]) -> subprocess.CompletedProcess:
  return subprocess.run([sys.executable, '-m', __package__+'.python_mpc', '_execute'],
                        cwd=Path(__file__).resolve().parents[2], env=env,
                        capture_output=True, text=True, timeout=30, check=False)


def _publish(receipt: dict, *, verify_before_replace: bool = False) -> None:
  data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()
  if len(data) > 2_000_000:
    raise ValueError('MPC receipt exceeds size limit')
  fd, temporary = tempfile.mkstemp(prefix='.python_mpc_receipt.', suffix='.tmp', dir=EVIDENCE)
  try:
    with os.fdopen(fd, 'wb') as stream:
      stream.write(data)
      stream.flush()
      os.fsync(stream.fileno())
    if verify_before_replace and verify_receipt(_receipt_path=Path(temporary))['status'] != 'VERIFIED_LOCAL_EXECUTION_RECEIPT':
      raise RuntimeError('native Python MPC receipt failed local verification')
    os.replace(temporary, OUTPUT)
  finally:
    if os.path.exists(temporary):
      os.unlink(temporary)


def verify_receipt(expected_sha256: str | None = None, *, _receipt_path: Path | None = None) -> dict:
  receipt_file = OUTPUT if _receipt_path is None else _receipt_path
  if receipt_file.is_symlink() or any(p.is_symlink() for p in (receipt_file.parent, *receipt_file.parent.parents)):
    return {'status': 'REJECTED', 'reasons': ['linked MPC receipt']}
  if receipt_file.exists() and (not receipt_file.is_file() or
      os.stat(receipt_file, follow_symlinks=False).st_nlink != 1):
    return {'status': 'REJECTED', 'reasons': ['unsafe MPC receipt path']}
  try:
    with receipt_file.open('rb') as stream:
      data = stream.read(2_000_001)
    if len(data) > 2_000_000:
      return {'status': 'REJECTED', 'reasons': ['MPC receipt exceeds size limit']}
    receipt = json.loads(data)
  except (OSError, UnicodeError, ValueError, TypeError) as exc:
    return {'status': 'REJECTED', 'reasons': ['MPC receipt unreadable or malformed: '+type(exc).__name__]}
  if type(receipt) is not dict:
    return {'status': 'REJECTED', 'reasons': ['MPC receipt is not an object']}
  if receipt == {'status': 'INVALIDATED_FOR_RERUN'}:
    return {'status': 'REJECTED', 'reasons': ['MPC receipt invalidated for rerun']}
  reasons = []
  required = {'schema_version', 'classification', 'source_commit', 'input_classification',
              'execution_class', 'planner_execution', 'authenticated_vehicle_replay',
              'actuation', 'modelV2_trajectory', 'native_build_receipt_sha256', 'imports',
              'scenario_inputs_sha256', 'scenario_output_sha256', 'scenarios'}
  if set(receipt) != required or receipt.get('schema_version') != 2:
    reasons.append('MPC receipt schema mismatch')
  if expected_sha256 is not None and digest(receipt_file) != expected_sha256:
    reasons.append('receipt digest mismatch')
  if verify()['status'] != 'VERIFIED_LOCAL_BUILD' or receipt.get('native_build_receipt_sha256') != verify()['receipt_sha256']:
    reasons.append('native build rejected')
  imports = receipt.get('imports') if type(receipt.get('imports')) is dict else {}
  if receipt.get('source_commit') != BASELINE or imports.get('c19_long_mpc_sha256') != digest(MPC) or imports.get('c19_long_mpc_path') != str(MPC):
    reasons.append('C19 MPC source mismatch')
  opendbc = C19/'opendbc_repo/opendbc/car'
  numeric_paths = (opendbc/'interfaces.py', opendbc/'__init__.py', C19/'openpilot/common/realtime.py',
                   C19/'openpilot/selfdrive/controls/radard.py', C19/'openpilot/selfdrive/modeld/constants.py')
  expected_numeric = {'ACCEL_MIN': _literal(numeric_paths[0], 'ACCEL_MIN'),
                      'ACCEL_MAX': _literal(numeric_paths[0], 'ACCEL_MAX'),
                      'TAKEOFF_ACCEL_MAX': _literal(numeric_paths[1], 'ACCEL_MAX_TAKEOFF'),
                      'DT_MDL': _literal(numeric_paths[2], 'DT_MDL'),
                      '_LEAD_ACCEL_TAU': _literal(numeric_paths[3], '_LEAD_ACCEL_TAU'),
                      'RADAR_TO_CAMERA': _literal(numeric_paths[3], 'RADAR_TO_CAMERA')}
  expected_stubs = ['openpilot.cereal', 'opendbc', 'opendbc.car', 'opendbc.car.interfaces',
                    'openpilot.starpilot.longitudinal.lead_takeoff_preferences',
                    'openpilot.common.realtime', 'openpilot.common.swaglog', 'openpilot.selfdrive.controls.radard']
  extension = next((EVIDENCE/'native').glob('acados_ocp_solver_pyx*.so'), None)
  if (imports.get('classification') != 'STUBBED_NONNUMERICAL_IMPORTS' or imports.get('stubbed_modules') != expected_stubs
      or imports.get('numeric_constants_from_c19_source') != expected_numeric
      or imports.get('numeric_source_sha256') != {str(p.relative_to(C19)): digest(p) for p in numeric_paths}
      or extension is None or imports.get('native_wrapper_sha256') != digest(extension)
      or imports.get('casadi_path') != str(CASADI/'__init__.py')):
    reasons.append('import boundary, numeric constants or wrapper mismatch')
  if receipt.get('scenario_inputs_sha256') != hashlib.sha256(json.dumps(scenario_definitions(), sort_keys=True, separators=(',', ':')).encode()).hexdigest():
    reasons.append('scenario input mismatch')
  scenarios = receipt.get('scenarios')
  if type(scenarios) is not dict or set(scenarios) != set(scenario_definitions()):
    reasons.append('scenario set mismatch')
  else:
    try:
      raw = json.dumps(scenarios, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
      if hashlib.sha256(raw).hexdigest() != receipt.get('scenario_output_sha256'):
        reasons.append('scenario output digest mismatch')
    except (TypeError, ValueError):
      reasons.append('scenario values invalid')
    for name, scenario in scenarios.items():
      expected_cycles = len(scenario_definitions()[name])
      if (type(scenario) is not dict or type(scenario.get('cycles')) is not int or
          scenario['cycles'] != expected_cycles or type(scenario.get('samples')) is not list or
          len(scenario['samples']) != expected_cycles or type(scenario.get('statuses')) is not list or
          len(scenario['statuses']) != expected_cycles):
        reasons.append('scenario cycles or samples mismatch: '+name)
        continue
      for index, sample in enumerate(scenario['samples']):
        if (type(sample) is not dict or type(sample.get('solver_status')) is not int or
            type(sample.get('native_solve_status')) is not int or sample['solver_status'] != 0 or
            sample['native_solve_status'] != 0 or type(sample.get('solve_calls')) is not int or
            sample['solve_calls'] != 1 or scenario['statuses'][index] != sample['solver_status']):
          reasons.append('solver status or native call mismatch: '+name)
          break
  if (receipt.get('classification') != 'C19_PYTHON_MPC_NATIVE_X86_VERIFIED' or receipt.get('actuation') != 'NONE'
      or receipt.get('planner_execution') != 'FULL_C19_LONGITUDINAL_PLANNER_NOT_RUN'
      or receipt.get('authenticated_vehicle_replay') != 'AUTHENTICATED_VEHICLE_REPLAY_NOT_RUN'
      or receipt.get('input_classification') != 'DETERMINISTIC_SYNTHETIC'
      or receipt.get('modelV2_trajectory') != 'NOT_SUPPLIED'):
    reasons.append('classification mismatch')
  return {'status': 'VERIFIED_LOCAL_EXECUTION_RECEIPT' if not reasons else 'REJECTED',
          'reasons': reasons, 'receipt_sha256': digest(receipt_file)}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('operation', choices=('run', '_execute', 'verify'))
  parser.add_argument('--expected-sha256')
  args = parser.parse_args()
  result = execute(EVIDENCE/'native') if args.operation == '_execute' else run() if args.operation == 'run' else verify_receipt(args.expected_sha256)
  print(json.dumps(result, sort_keys=True, allow_nan=False) if args.operation == '_execute' else json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
  main()

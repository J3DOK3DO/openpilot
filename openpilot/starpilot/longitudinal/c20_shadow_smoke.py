"""Parked-only, synthetic native MPC smoke test; no vehicle messages or actuation.

Requires explicit command-line opt-in and a complete product Python/native runtime.
The numerical scenario is invented. Success is local runtime evidence only, never
vehicle qualification, production command authorization or authenticated replay.
"""
from __future__ import annotations

import argparse
import json
import math
from types import SimpleNamespace

from .c20_shadow import _ObservedSolver

MAX_CYCLES = 4


def _radar():
  lead = SimpleNamespace(present=True, dRel=35.0, vLead=17.0,
                         aLeadK=0.0, aLeadTau=1.5, modelProb=0.0, radar=True)
  absent = SimpleNamespace(present=False, dRel=50.0, vLead=0.0,
                           aLeadK=0.0, aLeadTau=1.5, modelProb=0.0, radar=False)
  return SimpleNamespace(leadOne=lead, leadTwo=absent)


def run_synthetic_smoke(cycles: int = 2) -> dict:
  if type(cycles) is not int or not 1 <= cycles <= MAX_CYCLES:
    raise ValueError('invalid bounded smoke cycle count')
  classification = 'SYNTHETIC_LOCAL_NATIVE_MPC_ONLY'
  try:
    import numpy as np
    from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import LongitudinalMpc
    mpc = LongitudinalMpc()
    observed = _ObservedSolver(mpc.solver)
    mpc.solver = observed
    radar = _radar()
    accelerations = []
    for _ in range(cycles):
      prior = len(observed.statuses)
      mpc.set_cur_state(20.0, 0.0)
      mpc.update(radar)
      if len(observed.statuses) != prior + 1 or type(observed.statuses[-1]) is not int or observed.statuses[-1] != 0:
        raise ValueError('native solver failed or was not called exactly once')
      if not all(np.all(np.isfinite(part)) for part in
                 (mpc.x_sol, mpc.v_solution, mpc.a_solution, mpc.j_solution)):
        raise ValueError('nonfinite native solution')
      accel = float(mpc.a_solution[1])
      if not math.isfinite(accel):
        raise ValueError('nonfinite first acceleration')
      accelerations.append(round(accel, 6))
    return {'classification': classification, 'status': 'LOCAL_NUMERICAL_EXECUTION',
            'cycles': cycles, 'solve_calls': len(observed.statuses),
            'native_solve_statuses': observed.statuses, 'first_accel_mps2': accelerations,
            'actuation': 'NONE', 'vehicle_evidence': 'NONE'}
  except Exception:
    return {'classification': classification, 'status': 'NATIVE_UNAVAILABLE_OR_FAILED',
            'cycles': 0, 'solve_calls': 0, 'actuation': 'NONE', 'vehicle_evidence': 'NONE'}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--synthetic-native-smoke', action='store_true', help='explicit offline smoke opt-in')
  parser.add_argument('--cycles', type=int, default=2)
  args = parser.parse_args()
  if not args.synthetic_native_smoke or not 1 <= args.cycles <= MAX_CYCLES:
    parser.error('--synthetic-native-smoke and 1..4 cycles required')
  result = run_synthetic_smoke(args.cycles)
  print(json.dumps(result, sort_keys=True))
  if result['status'] != 'LOCAL_NUMERICAL_EXECUTION':
    raise SystemExit(2)


if __name__ == '__main__':
  main()

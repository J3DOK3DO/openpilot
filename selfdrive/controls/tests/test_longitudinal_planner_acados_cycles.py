"""Stateful smoke coverage for the native longitudinal MPC solver.

The inputs deliberately change between calls, but they are not a vehicle model
and this test does not attempt to close the loop around planner outputs.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from opendbc.car.honda.interface import CarInterface as HondaCarInterface
from opendbc.car.honda.values import CAR as HONDA_CAR
from opendbc.car.hyundai.interface import CarInterface as HyundaiCarInterface
from opendbc.car.hyundai.values import CAR as HYUNDAI_CAR
from opendbc.car.toyota.interface import CarInterface as ToyotaCarInterface
from opendbc.car.toyota.values import CAR as TOYOTA_CAR
from openpilot.selfdrive.controls.lib import longitudinal_planner as planner_module
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import LongitudinalMpc
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.controls.tests.test_longitudinal_planner import make_lead, make_sm, make_toggles


VEHICLES = (
  pytest.param(HondaCarInterface, HONDA_CAR.HONDA_CIVIC, id="honda-civic"),
  pytest.param(HondaCarInterface, HONDA_CAR.HONDA_ACCORD_11G, id="honda-accord-11g"),
  pytest.param(ToyotaCarInterface, TOYOTA_CAR.TOYOTA_RAV4_TSS2, id="toyota-rav4-tss2"),
  pytest.param(HyundaiCarInterface, HYUNDAI_CAR.HYUNDAI_SONATA, id="hyundai-sonata"),
)

# Slows to a stopped lead, then presents a departing lead while explicit stop
# contexts are active, and finally clears the stop context. There are exactly
# 25 inputs so each parametrized case exercises 25 successive planner cycles.
LEAD_SPEEDS = (
  12.0, 11.0, 10.0, 9.0, 8.0,
  6.0, 4.0, 2.0, 1.0, 0.0,
  0.0, 0.0, 0.0, 0.0, 0.0,
  0.8, 1.2, 2.0, 3.0, 4.0,
  5.0, 7.0, 9.0, 11.0, 13.0,
)
STOP_FLAGS = ("forcingStop", "redLight", "stopSignConfirmed")


@pytest.mark.parametrize("car_interface,fingerprint", VEHICLES)
def test_25_successive_updates_use_real_acados_and_prioritize_stop_context(
  monkeypatch, car_interface, fingerprint,
):
  cp = car_interface.get_non_essential_params(fingerprint)
  planner = LongitudinalPlanner(cp, init_v=12.0)

  assert type(planner.mpc) is LongitudinalMpc
  assert type(planner.mpc.solver).__name__ == "AcadosOcpSolverCython"
  assert type(planner.mpc.solver).__module__ == "acados_template.acados_ocp_solver_pyx"

  # Planner latches use monotonic time. Advance it by the configured planner
  # period without sleeping or coupling this smoke test to host performance.
  clock = SimpleNamespace(now=100.0)
  monkeypatch.setattr(planner_module, "time", SimpleNamespace(monotonic=lambda: clock.now))

  stop_context_targets = []
  cleared_stop_target = None
  for cycle, lead_speed in enumerate(LEAD_SPEEDS):
    standstill = 10 <= cycle <= 19
    v_ego = 0.0 if standstill else 12.0
    departing = cycle >= 15
    lead = make_lead(
      status=True,
      d_rel=6.5 if standstill else 25.0,
      v_lead=lead_speed,
      a_lead=0.3 if departing else -0.2,
      radar=True,
      model_prob=1.0,
    )
    sm = make_sm(
      v_ego,
      desired_accel=1.0,
      min_accel=-3.5,
      experimental_mode=False,
      tracking_lead=True,
      lead_one=lead,
    )
    sm["carState"].standstill = standstill
    sm["carState"].brakePressed = False
    sm["carState"].gasPressed = False
    sm["starpilotPlan"].stopSignConfirmed = False

    stop_context = 12 <= cycle <= 18
    if stop_context:
      stop_flag = STOP_FLAGS[(cycle - 12) % len(STOP_FLAGS)]
      setattr(sm["starpilotPlan"], stop_flag, True)
      if stop_flag == "forcingStop":
        sm["starpilotPlan"].forcingStopLength = 6.0

    planner.update(sm, make_toggles(radar_takeoffs=True))

    assert planner.mpc.solution_status == 0, f"acados failed on cycle {cycle}"
    assert planner.mpc.crash_cnt == 0, f"MPC crash counter advanced on cycle {cycle}"
    for value in (planner.a_desired, planner.output_a_target):
      assert np.isfinite(value), f"non-finite acceleration on cycle {cycle}"
      assert -3.5 - 1e-6 <= value <= 2.0 + 1e-6
    assert np.all(np.isfinite(planner.mpc.a_solution))
    assert np.all(planner.mpc.a_solution >= -3.5 - 1e-6)
    assert np.all(planner.mpc.a_solution <= 2.0 + 1e-6)

    if stop_context and departing:
      stop_context_targets.append(planner.output_a_target)
    elif cycle == 19:
      cleared_stop_target = planner.output_a_target

    clock.now += planner.dt

  # A moving, accelerating lead and +1 m/s^2 model request must not launch the
  # stationary ego while any source-backed stop flag remains asserted.
  assert len(stop_context_targets) == 4
  assert max(stop_context_targets) <= 0.0
  # A released source stop does not grant an immediate takeoff. This first
  # post-clear cycle still has an MPC braking request, so preserve the braking
  # target until fresh, compatible departure evidence accumulates.
  assert cleared_stop_target is not None and np.isfinite(cleared_stop_target)
  assert cleared_stop_target <= 0.0

"""Campaign B adversarial longitudinal arbitration checks.

These tests use a fixed-output MPC only to expose planner arbitration. They do
not model vehicle dynamics, CAN timing, or qualify the native solver/vehicle.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from cereal import log
from opendbc.car.honda.carcontroller import get_honda_bosch_wind_brake_mps2, update_accord_bosch_braking
from opendbc.car.honda.hondacan import create_acc_commands
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib import longitudinal_planner as planner_module
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.controls.tests.test_longitudinal_planner import make_lead, make_sm, make_toggles


class FixedMpc:
  """Replace only the solver output; all downstream planner code remains real."""

  raw_accel = 0.0
  leads_are_near_duplicates = staticmethod(long_mpc.LongitudinalMpc.leads_are_near_duplicates)

  def __init__(self, *args, **kwargs):
    n = len(long_mpc.T_IDXS)
    self.mode, self.source, self.crash_cnt, self.solve_time = "acc", "lead0", 0, 0.0
    self.lead_xv_0, self.lead_xv_1 = np.zeros((n, 2)), np.zeros((n, 2))
    self.a_solution = np.zeros(n)
    self.v_solution = np.zeros(n)
    self.j_solution = np.zeros(n - 1)
    self.v0 = 0.0

  def set_weights(self, *args, **kwargs):
    pass

  def set_accel_limits(self, lo, hi):
    pass

  def set_cur_state(self, v, a):
    self.v0 = float(v)

  def update(self, radarstate, v_cruise, *args, **kwargs):
    t = np.asarray(long_mpc.T_IDXS)
    self.a_solution = np.full(len(t), self.raw_accel)
    self.v_solution = self.v0 + self.raw_accel * t
    self.j_solution = np.zeros(len(t) - 1)
    self.source = "lead0"


@pytest.fixture
def fixed_mpc(monkeypatch):
  monkeypatch.setattr(planner_module, "LongitudinalMpc", FixedMpc)
  return FixedMpc


def run_scene(fingerprint, v_ego, lead, *, raw_accel, model_accel, flags=None,
              toggles=None, edit=None):
  FixedMpc.raw_accel = raw_accel
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(fingerprint), init_v=v_ego)
  sm = make_sm(
    v_ego,
    desired_accel=model_accel,
    min_accel=-3.5,
    experimental_mode=False,
    tracking_lead=True,
    lead_one=lead,
  )
  sm["starpilotPlan"].stopSignConfirmed = False
  for field, value in (flags or {}).items():
    setattr(sm["starpilotPlan"], field, value)
  if edit is not None:
    edit(sm)
  planner.update(sm, toggles or make_toggles())
  return planner


SOURCE_STOP_FLAGS = {
  "forcingStop": {"forcingStop": True, "forcingStopLength": 80.0},
  "redLight": {"redLight": True},
  "stopSignConfirmed": {"stopSignConfirmed": True},
}


@pytest.mark.parametrize("fingerprint", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD_11G))
@pytest.mark.parametrize("flags", SOURCE_STOP_FLAGS.values(), ids=SOURCE_STOP_FLAGS.keys())
def test_source_stop_context_blocks_standstill_lead_departure_raise(fixed_mpc, fingerprint, flags):
  """Before remediation, -1.0 became +0.05 (red/force) or +0.35 (stop sign)."""

  def at_standstill(sm):
    sm["carState"].standstill = True
    sm["carState"].brakePressed = False

  planner = run_scene(
    fingerprint,
    0.0,
    make_lead(status=True, d_rel=6.5, v_lead=0.8, a_lead=0.3, radar=True, model_prob=1.0),
    raw_accel=-1.0,
    model_accel=0.2,
    flags=flags,
    toggles=make_toggles(radar_takeoffs=True),
    edit=at_standstill,
  )

  assert planner.output_a_target <= -1.0
  assert planner.output_should_stop


def test_stop_sign_context_blocks_lane_change_merge_floor(fixed_mpc):
  """Before remediation, the merge floor changed a raw -1.0 target to +0.55."""
  toggles = make_toggles()
  toggles.lane_change_close_gap = True
  toggles.minimum_lane_change_speed = 0.0

  def during_merge(sm):
    sm["modelV2"].meta.laneChangeState = log.LaneChangeState.preLaneChange
    sm["modelV2"].meta.laneChangeDirection = log.LaneChangeDirection.left
    sm["carState"].leftBlindspot = False
    sm["carState"].rightBlindspot = False
    sm["carState"].brakePressed = False

  planner = run_scene(
    CAR.HONDA_CIVIC,
    25.0,
    make_lead(status=True, d_rel=60.0, v_lead=24.0, radar=True, model_prob=1.0),
    raw_accel=-1.0,
    model_accel=-1.0,
    flags=SOURCE_STOP_FLAGS["stopSignConfirmed"],
    toggles=toggles,
    edit=during_merge,
  )

  assert planner.output_a_target <= -1.0


def test_source_stop_context_bypasses_far_follow_slew(fixed_mpc):
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(CAR.HONDA_ACCORD), init_v=24.0)
  planner.lead_one = make_lead(status=True, d_rel=58.0, v_lead=20.0, radar=True, model_prob=1.0)
  planner.lead_two = make_lead(status=False)
  planner.far_follow_output_slew_active = True

  target = planner.get_vehicle_far_follow_slew_target(
    24.0,
    prev_target=0.4,
    target=-1.0,
    output_should_stop=False,
    panic_bypass=False,
    stop_context=True,
  )

  assert target == pytest.approx(-1.0)
  assert not planner.far_follow_output_slew_active


def test_should_stop_departure_does_not_raise_raw_mpc_without_replay(fixed_mpc):
  """Executable no-go gate for the Dom-native shouldStop/departure ambiguity."""

  def at_standstill(sm):
    sm["carState"].standstill = True
    sm["carState"].brakePressed = False

  planner = run_scene(
    CAR.HONDA_CIVIC,
    0.0,
    make_lead(status=True, d_rel=6.5, v_lead=0.8, a_lead=0.3, radar=True, model_prob=1.0),
    raw_accel=-1.0,
    model_accel=0.2,
    toggles=make_toggles(radar_takeoffs=True),
    edit=at_standstill,
  )

  assert planner.output_a_target <= -1.0
  assert planner.output_should_stop


@pytest.mark.parametrize("v_ego", (20.0, 25.0, 31.0))
def test_accord_minus_point_three_coast_cap_maps_to_brake_request(v_ego):
  """R-F08 evidence: the nominal coast cap is light braking, not throttle-only."""
  requested_accel = -0.30
  min_gas_accel = 0.0
  gas_force = requested_accel + get_honda_bosch_wind_brake_mps2(v_ego)
  braking, _ = update_accord_bosch_braking(
    False,
    0,
    gas_force,
    min_gas_accel,
    requested_accel,
    stopping=False,
    long_active=True,
  )

  class FakePacker:
    @staticmethod
    def make_can_msg(name, bus, values):
      return name, bus, values

  commands = create_acc_commands(
    FakePacker(),
    SimpleNamespace(pt=1),
    enabled=True,
    active=True,
    accel=requested_accel,
    gas=0.0,
    stopping_counter=0,
    CP=SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G),
    gas_force=gas_force,
    braking=braking,
  )
  acc_control = next(values for name, _, values in commands if name == "ACC_CONTROL")

  assert gas_force < min_gas_accel
  assert braking
  assert acc_control["BRAKE_REQUEST"] == 1
  assert acc_control["BRAKE_LIGHTS"] == 1


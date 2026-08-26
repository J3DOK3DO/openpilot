from types import SimpleNamespace
import sys

import numpy as np
import pytest

from cereal import car, log
from opendbc.car.interfaces import ACCEL_MAX, ACCEL_MIN
from opendbc.car.honda.values import CAR as HONDA_CAR
from opendbc.car.toyota.values import CAR as TOYOTA_CAR
from openpilot.common.constants import CV
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.controls.lib.drive_helpers import CONTROL_N
from openpilot.selfdrive.controls.lib.mvl_accord_longitudinal import (
  apply_global_accel_limit,
  create_long_control,
  create_longitudinal_planner,
  is_mvl_accord,
)
from openpilot.selfdrive.controls.lib.mvl_accord_longcontrol import (
  LongCtrlState,
  MVLAccordLongControl,
  mvl_long_control_state_trans,
)
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.mvl_accord_long_mpc import (
  A_CHANGE_COST,
  COST_E_DIM,
  DANGER_ZONE_COST,
  J_EGO_COST,
  LIMIT_COST,
  LongitudinalPlanSource,
  MVLAccordLongitudinalMpc,
  N,
  T_IDXS,
  X_EGO_OBSTACLE_COST,
  get_T_FOLLOW,
)
from openpilot.selfdrive.controls.lib.mvl_accord_longitudinal_planner import (
  A_CRUISE_MAX_BP,
  A_CRUISE_MAX_VALS,
  ALLOW_THROTTLE_THRESHOLD,
  MVLAccordLongitudinalPlanner,
  get_max_accel,
  limit_accel_in_turns,
  mvl_get_accel_from_plan,
)
from openpilot.selfdrive.modeld.constants import ModelConstants


def make_control_cp():
  CP = car.CarParams.new_message()
  CP.carFingerprint = HONDA_CAR.HONDA_ACCORD_11G
  CP.stopAccel = -2.0
  CP.longitudinalTuning.kpBP = [0.0]
  CP.longitudinalTuning.kpV = [0.0]
  CP.longitudinalTuning.kiBP = [0.0]
  CP.longitudinalTuning.kiV = [0.0]
  return CP


def make_car_state(v_ego=10.0, a_ego=0.0, *, brake_pressed=False, standstill=False):
  CS = car.CarState.new_message()
  CS.vEgo = v_ego
  CS.aEgo = a_ego
  CS.brakePressed = brake_pressed
  CS.cruiseState.standstill = standstill
  return CS


@pytest.mark.parametrize(
  "active,state,should_stop,brake_pressed,standstill,expected",
  [
    (False, LongCtrlState.pid, False, False, False, LongCtrlState.off),
    (True, LongCtrlState.off, False, False, False, LongCtrlState.pid),
    (True, LongCtrlState.off, True, False, False, LongCtrlState.stopping),
    (True, LongCtrlState.off, False, True, False, LongCtrlState.stopping),
    (True, LongCtrlState.off, False, False, True, LongCtrlState.stopping),
    (True, LongCtrlState.stopping, False, False, False, LongCtrlState.pid),
    (True, LongCtrlState.pid, True, False, False, LongCtrlState.stopping),
  ],
)
def test_validated_long_control_state_machine(active, state, should_stop, brake_pressed, standstill, expected):
  CP = make_control_cp()
  assert mvl_long_control_state_trans(CP, active, state, should_stop, brake_pressed, standstill) == expected
  assert expected != LongCtrlState.starting


def test_long_control_pid_brake_gas_crossover_and_shared_policy_isolation():
  controller = MVLAccordLongControl(make_control_cp())
  CS = make_car_state()

  output = controller.update(True, CS, 0.8, False, [-3.5, 2.0], object(), traffic_mode_enabled=True,
                             profile_max_accel=0.1, has_lead=True)
  assert controller.long_control_state == LongCtrlState.pid
  assert output == pytest.approx(0.8)

  output = controller.update(True, CS, -0.6, False, [-3.5, 2.0], object(), traffic_mode_enabled=True,
                             profile_max_accel=0.1, has_lead=True)
  assert output == pytest.approx(-0.6)


def test_long_control_stopping_ramp_hold_release_and_off():
  controller = MVLAccordLongControl(make_control_cp())
  CS = make_car_state(v_ego=0.1)
  controller.last_output_accel = 0.4

  assert controller.update(True, CS, -1.0, True, [-3.5, 2.0]) == pytest.approx(-DT_CTRL)
  assert controller.long_control_state == LongCtrlState.stopping

  for _ in range(400):
    controller.update(True, CS, -1.0, True, [-3.5, 2.0])
  assert controller.last_output_accel == pytest.approx(controller.CP.stopAccel)

  assert controller.update(True, CS, 0.3, False, [-3.5, 2.0]) == pytest.approx(0.3)
  assert controller.long_control_state == LongCtrlState.pid
  assert controller.update(False, CS, 0.3, False, [-3.5, 2.0]) == pytest.approx(0.0)
  assert controller.long_control_state == LongCtrlState.off


class FakeSolver:
  def __init__(self, status=0):
    self.status = status
    self.reset_count = 0
    self.costs = {}
    self.values = {}
    self.constraints = {}
    self.x = np.zeros((N + 1, 3))
    self.u = np.zeros((N, 1))

  def reset(self):
    self.reset_count += 1

  def cost_set(self, stage, field, value):
    self.costs[(stage, field)] = np.array(value, copy=True)

  def set(self, stage, field, value):
    self.values[(stage, field)] = np.array(value, copy=True)
    if field == "x":
      self.x[stage] = value

  def constraints_set(self, stage, field, value):
    self.constraints[(stage, field)] = np.array(value, copy=True)

  def solve(self):
    return self.status

  def get_stats(self, field):
    assert field == "time_tot"
    return np.array([0.001])

  def get(self, stage, field):
    return self.x[stage] if field == "x" else self.u[stage]


def make_lead(status=False, d_rel=200.0, v_lead=0.0, a_lead=0.0, model_prob=0.0):
  return SimpleNamespace(
    status=status,
    present=status,
    dRel=d_rel,
    vLead=v_lead,
    aLeadK=a_lead,
    aLeadTau=1.5,
    modelProb=model_prob,
  )


def test_mpc_validated_costs_and_personality_weights():
  solver = FakeSolver()
  mpc = MVLAccordLongitudinalMpc(solver=solver)

  expected = np.diag([X_EGO_OBSTACLE_COST, 0.0, 0.0, 0.0, A_CHANGE_COST, J_EGO_COST])
  assert solver.costs[(0, "W")] == pytest.approx(expected)
  assert solver.costs[(N, "W")].shape == (COST_E_DIM, COST_E_DIM)
  assert solver.costs[(0, "Zl")] == pytest.approx([LIMIT_COST, LIMIT_COST, LIMIT_COST, DANGER_ZONE_COST])

  mpc.set_weights(personality=log.LongitudinalPersonality.aggressive)
  expected_aggressive = np.diag([X_EGO_OBSTACLE_COST, 0.0, 0.0, 0.0, A_CHANGE_COST * 0.5, J_EGO_COST * 0.5])
  assert solver.costs[(0, "W")] == pytest.approx(expected_aggressive)

  mpc.set_weights(prev_accel_constraint=False)
  assert solver.costs[(0, "W")][4, 4] == pytest.approx(0.0)


def test_mpc_lead_processing_source_selection_and_parameters():
  solver = FakeSolver()
  mpc = MVLAccordLongitudinalMpc(solver=solver)
  mpc.set_cur_state(20.0, 0.0)

  no_lead_state = SimpleNamespace(leadOne=make_lead(), leadTwo=make_lead())
  mpc.update(no_lead_state, 25.0)
  assert mpc.source == LongitudinalPlanSource.cruise
  assert mpc.params[:, 0] == pytest.approx(ACCEL_MIN)
  assert mpc.params[:, 1] == pytest.approx(ACCEL_MAX)
  assert mpc.params[:, 4] == pytest.approx(get_T_FOLLOW())

  lead0_state = SimpleNamespace(
    leadOne=make_lead(True, 20.0, 10.0, -0.5, 1.0),
    leadTwo=make_lead(),
  )
  mpc.update(lead0_state, 30.0)
  assert mpc.source == LongitudinalPlanSource.lead0

  lead1_state = SimpleNamespace(
    leadOne=make_lead(True, 50.0, 18.0, 0.0, 1.0),
    leadTwo=make_lead(True, 15.0, 8.0, -1.0, 1.0),
  )
  mpc.update(lead1_state, 30.0)
  assert mpc.source == LongitudinalPlanSource.lead1


def test_mpc_solver_failure_resets_state():
  solver = FakeSolver(status=1)
  mpc = MVLAccordLongitudinalMpc(solver=solver)
  initial_resets = solver.reset_count
  mpc.set_cur_state(10.0, 0.0)
  mpc.run()
  assert solver.reset_count == initial_resets + 1
  assert mpc.solution_status == 0
  assert mpc.v_solution == pytest.approx(np.zeros(N + 1))


def test_mpc_real_generated_solver_smoke():
  mpc = MVLAccordLongitudinalMpc()
  mpc.set_cur_state(20.0, 0.0)
  no_lead_state = SimpleNamespace(leadOne=make_lead(), leadTwo=make_lead())
  mpc.update(no_lead_state, 25.0)

  assert mpc.solution_status == 0
  assert mpc.source == LongitudinalPlanSource.cruise
  assert np.all(np.isfinite(mpc.v_solution))
  assert np.all(np.isfinite(mpc.a_solution))
  assert np.all(np.isfinite(mpc.j_solution))

  lead_state = SimpleNamespace(
    leadOne=make_lead(True, 24.0, 8.0, -1.0, 1.0),
    leadTwo=make_lead(),
  )
  mpc.update(lead_state, 30.0)
  assert mpc.solution_status == 0
  assert mpc.source == LongitudinalPlanSource.lead0
  assert mpc.a_solution[1] < 0.0


class FakeMpc:
  def __init__(self, planned_accel=0.0):
    self.planned_accel = planned_accel
    self.source = LongitudinalPlanSource.cruise
    self.crash_cnt = 0
    self.solve_time = 0.001
    self.v_solution = np.zeros(N + 1)
    self.a_solution = np.zeros(N + 1)
    self.j_solution = np.zeros(N)
    self.v_ego = 0.0
    self.a_ego = 0.0
    self.last_v_cruise = None
    self.last_prev_accel_constraint = None

  def set_weights(self, prev_accel_constraint, personality):
    self.last_prev_accel_constraint = prev_accel_constraint

  def set_cur_state(self, v, a):
    self.v_ego = v
    self.a_ego = a

  def update(self, radar_state, v_cruise, personality):
    del radar_state, personality
    self.last_v_cruise = v_cruise
    self.v_solution = self.v_ego + self.planned_accel * T_IDXS
    self.a_solution[:] = self.planned_accel
    self.j_solution[:] = 0.0


class FakeSM(dict):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.logMonoTime = {"modelV2": 0}

  def all_checks(self, service_list=None):
    del service_list
    return True


def make_planner_cp():
  CP = car.CarParams.new_message()
  CP.carFingerprint = HONDA_CAR.HONDA_ACCORD_11G
  CP.openpilotLongitudinalControl = True
  CP.longitudinalActuatorDelay = 0.05
  CP.steerRatio = 16.7
  CP.wheelbase = 2.83
  return CP


def make_sm(v_ego=10.0, *, v_cruise_kph=90.0, starpilot_v_cruise=25.0, planned_accel=0.0,
            throttle_prob=1.0, steering_angle=0.0, standstill=False, experimental=False,
            e2e_accel=0.0, e2e_stop=False, force_decel=False):
  del planned_accel
  return FakeSM({
    "carControl": SimpleNamespace(orientationNED=[0.0, 0.0, 0.0]),
    "carState": SimpleNamespace(
      vEgo=v_ego,
      vCruise=v_cruise_kph,
      aEgo=0.0,
      standstill=standstill,
      steeringAngleDeg=steering_angle,
    ),
    "controlsState": SimpleNamespace(longControlState=LongCtrlState.pid, forceDecel=force_decel),
    "selfdriveState": SimpleNamespace(
      enabled=True,
      personality=log.LongitudinalPersonality.standard,
      experimentalMode=experimental,
    ),
    "liveParameters": SimpleNamespace(angleOffsetDeg=0.0),
    "modelV2": SimpleNamespace(
      meta=SimpleNamespace(disengagePredictions=SimpleNamespace(gasPressProbs=[0.0, throttle_prob])),
      action=SimpleNamespace(desiredAcceleration=e2e_accel, shouldStop=e2e_stop),
    ),
    "starpilotPlan": SimpleNamespace(vCruise=starpilot_v_cruise),
    "radarState": SimpleNamespace(leadOne=make_lead(), leadTwo=make_lead()),
  })


def test_planner_acceleration_envelope_and_turn_limit():
  for speed, expected in zip(A_CRUISE_MAX_BP, A_CRUISE_MAX_VALS, strict=True):
    assert get_max_accel(speed) == pytest.approx(expected)

  CP = make_planner_cp()
  straight = limit_accel_in_turns(25.0, 0.0, [ACCEL_MIN, 1.2], CP)
  turning = limit_accel_in_turns(25.0, 20.0, [ACCEL_MIN, 1.2], CP)
  assert straight == pytest.approx([ACCEL_MIN, 1.2])
  assert turning[1] < straight[1]


def test_planner_stable_low_delay_interpolation():
  t_idxs = np.asarray(ModelConstants.T_IDXS[:CONTROL_N])
  speeds = 10.0 + t_idxs ** 2
  accels = np.zeros_like(t_idxs)
  target, should_stop = mvl_get_accel_from_plan(speeds, accels, t_idxs, action_t=0.10)
  stable_v_target = speeds[0] + (0.10 / 0.30) * (np.interp(0.30, t_idxs, speeds) - speeds[0])
  expected = 2.0 * (stable_v_target - speeds[0]) / 0.10 - accels[0]
  direct_target = 2.0 * (np.interp(0.10, t_idxs, speeds) - speeds[0]) / 0.10 - accels[0]
  assert target == pytest.approx(expected)
  assert target != pytest.approx(direct_target)
  assert not should_stop


@pytest.mark.parametrize(
  "v_ego,probability,expected",
  [
    (2.5, 0.0, True),
    (2.51, ALLOW_THROTTLE_THRESHOLD, False),
    (5.0, ALLOW_THROTTLE_THRESHOLD + 0.01, True),
  ],
)
def test_planner_throttle_probability_gate(v_ego, probability, expected):
  mpc = FakeMpc()
  planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=v_ego, mpc=mpc)
  planner.update(make_sm(v_ego, throttle_prob=probability), object())
  assert planner.allow_throttle is expected


def test_planner_target_arbitration_only_allows_starpilot_reduction():
  stock_target = 90.0 * CV.KPH_TO_MS

  high_mpc = FakeMpc()
  high_planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=10.0, mpc=high_mpc)
  high_planner.update(make_sm(starpilot_v_cruise=stock_target + 10.0), object())
  assert high_mpc.last_v_cruise == pytest.approx(stock_target)

  low_mpc = FakeMpc()
  low_planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=10.0, mpc=low_mpc)
  low_planner.update(make_sm(starpilot_v_cruise=20.0), object())
  assert low_mpc.last_v_cruise == pytest.approx(20.0)

  force_mpc = FakeMpc()
  force_planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=10.0, mpc=force_mpc)
  force_planner.update(make_sm(force_decel=True), object())
  assert force_mpc.last_v_cruise == pytest.approx(0.0)


def test_planner_e2e_can_only_reduce_mpc_accel_and_stop_is_conservative():
  increasing_mpc = FakeMpc(planned_accel=0.5)
  planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=10.0, mpc=increasing_mpc)
  planner.update(make_sm(experimental=True, e2e_accel=1.0), object())
  assert planner.output_a_target == pytest.approx(0.5)
  assert planner.mpc.source == LongitudinalPlanSource.cruise

  reducing_mpc = FakeMpc(planned_accel=0.5)
  planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=10.0, mpc=reducing_mpc)
  planner.update(make_sm(experimental=True, e2e_accel=-0.2, e2e_stop=True), object())
  assert planner.output_a_target == pytest.approx(-0.2)
  assert planner.output_should_stop
  assert planner.mpc.source == LongitudinalPlanSource.e2e


class FakePubMaster:
  def __init__(self):
    self.message = None

  def send(self, service, message):
    assert service == "longitudinalPlan"
    self.message = message


def test_planner_publish_allow_brake_and_allow_throttle():
  mpc = FakeMpc()
  planner = MVLAccordLongitudinalPlanner(make_planner_cp(), init_v=5.0, mpc=mpc)
  sm = make_sm(5.0, throttle_prob=0.0)
  planner.update(sm, object())
  pm = FakePubMaster()
  planner.publish(sm, pm)
  assert pm.message.longitudinalPlan.allowBrake
  assert not pm.message.longitudinalPlan.allowThrottle


@pytest.mark.parametrize(
  "fingerprint,expected",
  [
    (HONDA_CAR.HONDA_ACCORD_11G, True),
    (HONDA_CAR.HONDA_CRV_6G, False),
    (HONDA_CAR.HONDA_CIVIC_2022, False),
    (HONDA_CAR.HONDA_CIVIC, False),
    (TOYOTA_CAR.TOYOTA_RAV4, False),
  ],
)
def test_exact_accord_route_scope(fingerprint, expected):
  assert is_mvl_accord(SimpleNamespace(carFingerprint=fingerprint)) is expected


def test_control_factory_and_global_accel_policy_are_exact_accord_only():
  accord_cp = make_control_cp()
  civic_cp = make_control_cp()
  civic_cp.carFingerprint = HONDA_CAR.HONDA_CIVIC

  assert isinstance(create_long_control(accord_cp), MVLAccordLongControl)
  assert not isinstance(create_long_control(civic_cp), MVLAccordLongControl)
  assert apply_global_accel_limit(True, 1.0, 0.2) == pytest.approx(1.0)
  assert apply_global_accel_limit(False, 1.0, 0.2) == pytest.approx(0.2)


def test_planner_factory_selects_only_exact_accord(monkeypatch):
  class AccordPlanner:
    def __init__(self, CP):
      self.CP = CP

  class GenericPlanner(AccordPlanner):
    pass

  accord_module = SimpleNamespace(MVLAccordLongitudinalPlanner=AccordPlanner)
  generic_module = SimpleNamespace(LongitudinalPlanner=GenericPlanner)
  monkeypatch.setitem(sys.modules, "openpilot.selfdrive.controls.lib.mvl_accord_longitudinal_planner", accord_module)
  monkeypatch.setitem(sys.modules, "openpilot.selfdrive.controls.lib.longitudinal_planner", generic_module)

  accord = create_longitudinal_planner(SimpleNamespace(carFingerprint=HONDA_CAR.HONDA_ACCORD_11G))
  crv = create_longitudinal_planner(SimpleNamespace(carFingerprint=HONDA_CAR.HONDA_CRV_6G))
  civic = create_longitudinal_planner(SimpleNamespace(carFingerprint=HONDA_CAR.HONDA_CIVIC))
  toyota = create_longitudinal_planner(SimpleNamespace(carFingerprint=TOYOTA_CAR.TOYOTA_RAV4))

  assert type(accord) is AccordPlanner
  assert all(type(planner) is GenericPlanner for planner in (crv, civic, toyota))

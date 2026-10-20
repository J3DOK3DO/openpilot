"""C7 longitudinal lifecycle regressions for the C6-12 close-lead, stop-priority and coast paths.

These tests exercise planner/following state machines directly (no MPC solve). They are
offline source-level evidence only, not driving or Honda replay qualification.
"""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.controls.lib import longitudinal_planner as planner_module
from openpilot.selfdrive.controls.lib.lead_behavior import UNTRACKED_VISION_COAST_HOLD_TIME
from openpilot.selfdrive.controls.lib.longitudinal_planner import (
  CLOSE_LEAD_VISION_CONFIRM_TIME,
  VISION_LEAD_APPROACH_CONFIRM_TIME,
  VISION_LEAD_APPROACH_MIN_DECEL,
  LongitudinalPlanner,
)
from openpilot.selfdrive.controls.lib.longitudinal_vehicle_tunes import is_honda_accord_11g
from openpilot.starpilot.controls.lib.starpilot_following import StarPilotFollowing

PLANNER_SOURCE = Path(planner_module.__file__).read_text(encoding="utf-8")
PLANNER_TREE = ast.parse(PLANNER_SOURCE)


def make_planner(fingerprint=CAR.HONDA_ACCORD_11G):
  """Planner state for the close-lead methods without constructing the acados MPC."""
  CP = CarInterface.get_non_essential_params(fingerprint)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.CP = CP
  planner.dt = DT_MDL
  planner.is_honda_accord_11g = is_honda_accord_11g(CP)
  planner.close_lead_brake_hold_remaining = [0.0, 0.0]
  planner.close_lead_brake_hold_provenance = [None, None]
  planner.close_lead_brake_confirm_t = [0.0, 0.0]
  planner.close_lead_brake_confirm_provenance = [None, None]
  return planner


def vision_lead(**overrides):
  values = dict(status=True, radar=False, radarTrackId=-1, dRel=30.0, vLead=8.5, aLeadK=-0.6,
                yRel=0.0, modelProb=0.99)
  values.update(overrides)
  return SimpleNamespace(**values)


V_EGO = 10.0
ACCEL_MIN = -3.5


def _nonurgent(planner, lead, raw_mpc_accel=0.2):
  context = planner.get_close_lead_brake_context(lead, V_EGO)
  return context is not None and context[0] >= 0.2 and planner.nonurgent_vision_close_lead_brake(lead, V_EGO, context, raw_mpc_accel)


def test_fixture_lead_is_a_nonurgent_vision_brake_demand():
  planner = make_planner()
  assert _nonurgent(planner, vision_lead())


def test_nonurgent_vision_demand_waits_for_confirmation_window():
  planner = make_planner()
  lead = vision_lead()
  frames = int(round(CLOSE_LEAD_VISION_CONFIRM_TIME / DT_MDL))
  caps = [planner.update_close_lead_brake_cap(lead, 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2) for _ in range(frames)]
  assert caps[:-1] == [None] * (frames - 1)
  assert caps[-1] is not None and caps[-1] < 0.0
  assert planner.close_lead_brake_confirm_t[0] == 0.0


@pytest.mark.parametrize("stop_context", (True,))
def test_stop_context_bypasses_nonurgent_confirmation(stop_context):
  """C7 FIX-5: a red light / forced stop / stop sign / should-stop never delays close-lead braking."""
  planner = make_planner()
  cap = planner.update_close_lead_brake_cap(vision_lead(), 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2,
                                            stop_context=stop_context)
  assert cap is not None and cap < 0.0
  assert planner.close_lead_brake_confirm_t[0] == 0.0


URGENT_MUTATIONS = {
  "radar_lead": dict(radar=True, radarTrackId=7),
  "model_prob_below_0.95": dict(modelProb=0.949),
  "headway_below_2.0s": dict(dRel=19.9),
  "closing_speed_above_2.0": dict(vLead=V_EGO - 2.05, aLeadK=-0.2),
  "required_decel_at_least_1.2": dict(dRel=21.0, vLead=V_EGO - 1.95, aLeadK=-2.4),
}


@pytest.mark.parametrize("name", sorted(URGENT_MUTATIONS))
def test_urgent_boundary_crossing_during_partial_confirmation_brakes_immediately(name):
  """Codex coverage gap: cross each urgent boundary with confirmation partially accumulated."""
  planner = make_planner()
  assert planner.update_close_lead_brake_cap(vision_lead(), 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2) is None
  assert planner.close_lead_brake_confirm_t[0] > 0.0

  urgent = vision_lead(**URGENT_MUTATIONS[name])
  assert not _nonurgent(planner, urgent)
  cap = planner.update_close_lead_brake_cap(urgent, 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2)
  assert cap is not None and cap < 0.0
  assert planner.close_lead_brake_confirm_t[0] == 0.0
  assert planner.close_lead_brake_confirm_provenance[0] is None


def test_mpc_already_braking_bypasses_confirmation():
  planner = make_planner()
  assert planner.update_close_lead_brake_cap(vision_lead(), 0, V_EGO, ACCEL_MIN, raw_mpc_accel=-0.01) is not None


def test_ttc_below_9s_bypasses_confirmation():
  planner = make_planner()
  # Only the TTC boundary is urgent: closing <= 2.0, headway >= 2.0 s, demand in [0.2, 1.2).
  lead = vision_lead(dRel=20.5, vLead=V_EGO - 1.98, aLeadK=-0.3)
  context = planner.get_close_lead_brake_context(lead, V_EGO)
  assert context is not None and 0.2 <= context[0] < 1.2 and context[2] <= 2.0
  assert context[1] < 9.0
  assert planner.update_close_lead_brake_cap(lead, 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2) is not None


def test_hold_is_bounded_and_cleared_by_lead_replacement():
  planner = make_planner()
  lead = vision_lead()
  planner.update_close_lead_brake_cap(lead, 0, V_EGO, ACCEL_MIN, stop_context=True)
  assert planner.close_lead_brake_hold_remaining[0] == pytest.approx(VISION_LEAD_APPROACH_CONFIRM_TIME)

  # Same lead, demand eases below the 0.2 m/s^2 cap threshold: the hold keeps a bounded brake.
  easing = vision_lead(vLead=V_EGO - 1.2, aLeadK=0.0)
  context = planner.get_close_lead_brake_context(easing, V_EGO)
  assert context is not None and context[0] < 0.2
  held = planner.update_close_lead_brake_cap(easing, 0, V_EGO, ACCEL_MIN)
  assert held == pytest.approx(-max(context[0], VISION_LEAD_APPROACH_MIN_DECEL))

  # A different object (large geometry jump) must not inherit the hold.
  replaced = vision_lead(dRel=39.0, vLead=V_EGO - 1.6, aLeadK=0.0)
  assert planner.get_close_lead_brake_context(replaced, V_EGO) is not None
  assert planner.update_close_lead_brake_cap(replaced, 0, V_EGO, ACCEL_MIN) is None
  assert planner.close_lead_brake_hold_remaining[0] == 0.0

  # Hold duration is finite.
  planner.update_close_lead_brake_cap(lead, 1, V_EGO, ACCEL_MIN, stop_context=True)
  frames = 0
  while planner.update_close_lead_brake_cap(easing, 1, V_EGO, ACCEL_MIN) is not None:
    frames += 1
    assert frames <= int(round(VISION_LEAD_APPROACH_CONFIRM_TIME / DT_MDL)) + 1
  assert planner.close_lead_brake_hold_remaining[1] == 0.0


def test_non_accord_close_lead_cap_is_immediate_and_stateless():
  planner = make_planner(CAR.HONDA_CIVIC)
  assert not planner.is_honda_accord_11g
  cap = planner.update_close_lead_brake_cap(vision_lead(), 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2)
  assert cap == pytest.approx(planner.get_close_lead_brake_cap(vision_lead(), V_EGO, ACCEL_MIN))
  assert planner.close_lead_brake_confirm_t == [0.0, 0.0]
  assert planner.close_lead_brake_hold_remaining == [0.0, 0.0]


def test_clear_close_lead_brake_state_wipes_both_slots():
  planner = make_planner()
  for index in range(2):
    planner.update_close_lead_brake_cap(vision_lead(), index, V_EGO, ACCEL_MIN, stop_context=True)
  planner.update_close_lead_brake_cap(vision_lead(dRel=31.0), 0, V_EGO, ACCEL_MIN, raw_mpc_accel=0.2)
  planner.clear_close_lead_brake_state()
  assert planner.close_lead_brake_hold_remaining == [0.0, 0.0]
  assert planner.close_lead_brake_hold_provenance == [None, None]
  assert planner.close_lead_brake_confirm_t == [0.0, 0.0]
  assert planner.close_lead_brake_confirm_provenance == [None, None]


# --- Source-wiring contracts (update() needs the MPC; Windows runtime cannot solve it) ---

def _update_function():
  for node in ast.walk(PLANNER_TREE):
    if isinstance(node, ast.FunctionDef) and node.name == "update":
      for arg in node.args.args:
        if arg.arg == "starpilot_toggles":
          return node
  raise AssertionError("LongitudinalPlanner.update not found")


def _assigned_expression(name):
  matches = [node.value for node in ast.walk(PLANNER_TREE)
             if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)]
  assert len(matches) == 1, name
  return compile(ast.Expression(matches[0]), "longitudinal_planner.py", "eval")


def _evaluate(expression, stop=False, low_speed=False, close=False, force=False, red=False, sign=False):
  fields = SimpleNamespace(forcingStop=force, redLight=red, stopSignConfirmed=sign)
  return bool(eval(expression, {"getattr": getattr, "bool": bool}, {
    "sm": {"starpilotPlan": fields}, "output_should_stop": stop,
    "vision_low_speed_stop_active": low_speed, "close_lead_caps": [1] if close else [],
  }))


@pytest.mark.parametrize(("field", "expected"), (("stop", True), ("low_speed", True), ("close", True),
                                               ("force", False), ("red", False), ("sign", False)))
def test_follow_policy_block_list_is_doms(field, expected):
  """Review F-01/F-02: Dom's block list is unchanged; stop flags do not disable the follow policy."""
  expression = _assigned_expression("follow_policy_blocked")
  assert _evaluate(expression, **{field: True}) is expected
  assert not _evaluate(expression)


@pytest.mark.parametrize(("field", "expected"), (("stop", False), ("low_speed", False), ("close", False),
                                               ("force", True), ("red", True), ("sign", True)))
def test_stop_context_truth_table(field, expected):
  expression = _assigned_expression("stop_context")
  assert _evaluate(expression, **{field: True}) is expected


@pytest.mark.parametrize("field", ("stop", "force", "red", "sign"))
def test_close_lead_stop_context_truth_table(field):
  expression = _assigned_expression("close_lead_stop_context")
  assert _evaluate(expression, **{field: True})
  assert not _evaluate(expression)


def test_follow_policy_wiring_and_vision_brake_cap_gate():
  calls = [node for node in ast.walk(PLANNER_TREE)
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "apply_follow_policy"]
  assert calls and all(any(k.arg == "blocked" and isinstance(k.value, ast.Name) and k.value.id == "follow_policy_blocked"
                           for k in call.keywords) for call in calls)
  assert "follow_target = min(follow_result.target, output_a_target) if stop_context else follow_result.target" in PLANNER_SOURCE
  assert "if comfort_follow_lead is not None and not panic_bypass and not stop_priority_veto:" in PLANNER_SOURCE


def test_update_passes_stop_context_and_resets_close_lead_state():
  update = _update_function()
  cap_calls = [node for node in ast.walk(update) if isinstance(node, ast.Call) and
               isinstance(node.func, ast.Attribute) and node.func.attr == "update_close_lead_brake_cap"]
  assert cap_calls
  assert all(any(k.arg == "stop_context" and isinstance(k.value, ast.Name) and k.value.id == "close_lead_stop_context"
                 for k in call.keywords) for call in cap_calls)

  reset_blocks = [node for node in ast.walk(update) if isinstance(node, ast.If) and
                  isinstance(node.test, ast.Name) and node.test.id == "reset_state"]
  assert any(any(isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and
                 isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == "clear_close_lead_brake_state"
                 for stmt in block.body) for block in reset_blocks)


# --- Coast -> follow handoff (C7 FIX-4) ---

class SubMasterLike(dict):
  def __init__(self, data):
    super().__init__(data)
    self.seen = {key: True for key in data}
    self.alive = {key: True for key in data}
    self.valid = {key: True for key in data}


def make_following(lead):
  planner_stub = SimpleNamespace(lead_one=lead, tracking_lead=False, lead_path_y=0.0,
                                 starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0))
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45
  return following, planner_stub


def highway_vision_lead():
  return SimpleNamespace(status=True, radar=False, dRel=105.318, vLead=27.911, vLeadK=27.911,
                         modelProb=0.957, yRel=-0.648, aLeadK=0.0)


def _confirm_coast(following, sm):
  for _ in range(10):
    if following.update_untracked_vision_coast(True, 31.007, sm):
      return
  raise AssertionError("coast never confirmed")


def test_coast_to_follow_handoff_has_no_one_frame_throttle_release():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  sm = SubMasterLike({"carParams": accord, "carState": SimpleNamespace(leftBlinker=False, rightBlinker=False)})
  following, _ = make_following(highway_vision_lead())
  _confirm_coast(following, sm)
  hold = following.untracked_vision_coast_hold_remaining
  assert hold == pytest.approx(UNTRACKED_VISION_COAST_HOLD_TIME)

  closing_speed = 31.007 - 27.911
  disabled_frames = 0
  remaining = hold
  for _ in range(40):
    disabled = following.update_coast_follow_handoff(remaining, True, closing_speed, accord)
    remaining = following.untracked_vision_coast_hold_remaining
    if not disabled:
      break
    disabled_frames += 1
  # Throttle stays withheld through the first tracked frames and releases within the hold.
  assert disabled_frames >= 1
  assert disabled_frames <= int(round(UNTRACKED_VISION_COAST_HOLD_TIME / DT_MDL))
  assert following.untracked_vision_coast_hold_remaining == 0.0


@pytest.mark.parametrize("case", ("opening_lead", "long_control_off", "non_accord", "no_prior_hold"))
def test_coast_to_follow_handoff_releases_immediately_when_not_applicable(case):
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  civic = CarInterface.get_non_essential_params(CAR.HONDA_CIVIC)
  following, _ = make_following(highway_vision_lead())
  args = dict(handoff_hold_remaining=0.5, long_control_active=True, closing_speed=3.0, car_params=accord)
  if case == "opening_lead":
    args["closing_speed"] = 0.0
  elif case == "long_control_off":
    args["long_control_active"] = False
  elif case == "non_accord":
    args["car_params"] = civic
  else:
    args["handoff_hold_remaining"] = 0.0
  assert not following.update_coast_follow_handoff(**args)
  assert following.untracked_vision_coast_hold_remaining == 0.0


# --- update()-level behaviour with a fixed-output solver (C7 fixes for independent review F-01/F-02/F-06/F-09) ---
# FixedMpc replaces only the acados solve with a constant acceleration; every line after
# mpc.update() is the real planner. Results are arbitration deltas for a fixed raw target,
# not on-road magnitudes.

import numpy as np  # noqa: E402

from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib import long_mpc  # noqa: E402
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import desired_follow_distance  # noqa: E402
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState  # noqa: E402
from openpilot.selfdrive.controls.tests import test_longitudinal_planner as tlp  # noqa: E402


class FixedMpc:
  raw_accel = 0.0
  leads_are_near_duplicates = staticmethod(long_mpc.LongitudinalMpc.leads_are_near_duplicates)

  def __init__(self, *args, **kwargs):
    n = len(long_mpc.T_IDXS)
    self.mode, self.source, self.crash_cnt, self.solve_time = 'acc', 'lead0', 0, 0.0
    self.lead_xv_0, self.lead_xv_1 = np.zeros((n, 2)), np.zeros((n, 2))
    self.a_solution, self.v_solution, self.j_solution = np.zeros(n), np.zeros(n), np.zeros(n - 1)
    self.v0, self.captured_v_cruise = 0.0, None

  def set_weights(self, *args, **kwargs):
    pass

  def set_accel_limits(self, lo, hi):
    pass

  def set_cur_state(self, v, a):
    self.v0 = float(v)

  def update(self, radarstate, v_cruise, *args, **kwargs):
    self.captured_v_cruise = float(v_cruise)
    t = np.asarray(long_mpc.T_IDXS)
    self.a_solution = np.full(len(t), self.raw_accel)
    self.v_solution = self.v0 + self.raw_accel * t
    self.j_solution = np.zeros(len(t) - 1)
    self.source = 'lead0'


@pytest.fixture
def fixed_mpc(monkeypatch):
  monkeypatch.setattr(planner_module, "LongitudinalMpc", FixedMpc)
  return FixedMpc


STOP_FLAGS = {"none": {}, "redLight": {"redLight": True}, "forcingStop": {"forcingStop": True, "forcingStopLength": 80.0},
              "stopSignConfirmed": {"stopSignConfirmed": True}}


def _run(fingerprint, v_ego, lead, model_accel, flags, frames=3, toggles=None, sm_edit=None):
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(fingerprint), init_v=v_ego)
  outputs = []
  for _ in range(frames):
    sm = tlp.make_sm(v_ego, desired_accel=model_accel, min_accel=-3.5, experimental_mode=False, tracking_lead=True, lead_one=lead)
    sm["starpilotPlan"].stopSignConfirmed = False
    for key, value in flags.items():
      setattr(sm["starpilotPlan"], key, value)
    if sm_edit:
      sm_edit(sm)
    planner.update(sm, toggles or tlp.make_toggles())
    outputs.append(float(planner.output_a_target))
  return outputs, planner


@pytest.mark.parametrize("fingerprint", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD_11G))
@pytest.mark.parametrize("flag", sorted(STOP_FLAGS))
def test_stop_context_keeps_dom_model_brake_floor(fixed_mpc, fingerprint, flag):
  """Review F-01: a stop context must not remove the tracked-vision model brake floor."""
  fixed_mpc.raw_accel = 0.0
  lead = tlp.make_lead(status=True, d_rel=float(desired_follow_distance(15.0, 13.2, 1.45)) + 0.5, v_lead=13.2, model_prob=0.99)
  baseline, _ = _run(fingerprint, 15.0, lead, -1.0, {})
  outputs, _ = _run(fingerprint, 15.0, lead, -1.0, STOP_FLAGS[flag])
  assert baseline[0] < -0.3
  assert all(out <= base + 1e-9 for out, base in zip(outputs, baseline, strict=True))


@pytest.mark.parametrize("fingerprint", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD_11G))
@pytest.mark.parametrize("flag", sorted(STOP_FLAGS))
def test_stop_context_keeps_follow_catchup_cap(fixed_mpc, fingerprint, flag):
  """Review F-02: a stop context must not remove the catch-up cap / transition limiter."""
  fixed_mpc.raw_accel = 1.0
  lead = tlp.make_lead(status=True, d_rel=float(desired_follow_distance(15.0, 15.0, 1.45)) + 2.0, v_lead=15.0, model_prob=0.99)
  baseline, _ = _run(fingerprint, 15.0, lead, 0.0, {})
  outputs, _ = _run(fingerprint, 15.0, lead, 0.0, STOP_FLAGS[flag])
  assert baseline[0] < 0.5
  assert all(out <= base + 1e-9 for out, base in zip(outputs, baseline, strict=True))


@pytest.mark.parametrize("flag", ("redLight", "forcingStop", "stopSignConfirmed"))
def test_stop_context_follow_policy_never_raises_the_raw_target(fixed_mpc, flag):
  """In a stop context the comfort follow policy may only lower the raw target (matched-follow floor case)."""
  fixed_mpc.raw_accel = -1.0
  v_ego, v_lead = 25.0, 24.0
  lead = tlp.make_lead(status=True, d_rel=v_ego * 1.45, v_lead=v_lead, radar=True, model_prob=1.0)
  outputs, _ = _run(CAR.HONDA_CIVIC, v_ego, lead, -1.0, STOP_FLAGS[flag])
  assert all(out <= -1.0 + 1e-9 for out in outputs)


def test_reset_state_leaves_no_close_lead_state_after_update(fixed_mpc):
  """Review F-06: state accumulated by the every-cycle close-lead stage does not survive a disengaged cycle."""
  fixed_mpc.raw_accel = 0.2

  def disengaged(sm):
    sm["controlsState"].longControlState = LongCtrlState.off
    sm["selfdriveState"].enabled = False

  _, planner = _run(CAR.HONDA_ACCORD_11G, V_EGO, vision_lead(), 0.0, {}, frames=4, sm_edit=disengaged)
  assert planner.close_lead_brake_confirm_t == [0.0, 0.0]
  assert planner.close_lead_brake_hold_remaining == [0.0, 0.0]


@pytest.mark.parametrize(("offset", "expected_kph"), ((0, 72.0), (10, 82.0)))
def test_accord_c1_ceiling_honours_set_speed_offset(fixed_mpc, offset, expected_kph):
  """Review F-09: the C1 reduction-only ceiling includes the user's explicit SetSpeedOffset."""
  toggles = tlp.make_toggles()
  toggles.set_speed_offset = offset

  def cruise(sm):
    sm["carState"].vCruise = 72.0
    sm["starpilotPlan"].vCruise = 40.0  # policy target above the PCM ceiling

  _, planner = _run(CAR.HONDA_ACCORD_11G, 20.0, tlp.make_lead(status=False), 0.0, {}, frames=1, toggles=toggles, sm_edit=cruise)
  assert planner.mpc.captured_v_cruise == pytest.approx(expected_kph * 0.2777777778, rel=1e-6)

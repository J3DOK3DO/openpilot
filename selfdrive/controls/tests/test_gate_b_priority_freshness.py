"""Gate B negative controls for planner stop priority and input freshness.

These tests exercise planner arbitration with synthetic messages and a fixed
MPC. They do not model vehicle dynamics, CAN timing, or closed-loop behavior.
"""
import pytest

from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib import longitudinal_planner as planner_module
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.controls.tests.test_campaign_b_longitudinal_remediation import fixed_mpc, run_scene
from openpilot.selfdrive.controls.tests.test_longitudinal_planner import make_lead, make_sm, make_toggles


class SubMasterFixture(dict):
  """Dictionary payloads plus the production SubMaster health metadata."""

  def __init__(self, data, *, now, alive=True, valid=True, age=0.0, health=None):
    super().__init__(data)
    services = ("carState", "starpilotCarState")
    self.alive = {service: alive for service in services}
    self.valid = {service: valid for service in services}
    self.logMonoTime = {service: int((now - age) * 1e9) for service in services}
    for service, metadata in (health or {}).items():
      self.alive[service] = metadata.get("alive", self.alive[service])
      self.valid[service] = metadata.get("valid", self.valid[service])
      if "age" in metadata:
        self.logMonoTime[service] = int((now - metadata["age"]) * 1e9)


def manual_resume_sm(now, *, source="starpilotCarState", alive=True, valid=True, age=0.0):
  sm = make_sm(0.0, desired_accel=-1.0, min_accel=-3.5, experimental_mode=False)
  sm["carState"].standstill = True
  sm["carState"].gasPressed = source == "carState"
  sm["starpilotCarState"].accelPressed = source == "starpilotCarState"
  sm["modelV2"].action.shouldStop = True
  sm["starpilotPlan"].forcingStop = True
  return SubMasterFixture(sm, now=now, alive=alive, valid=valid, age=age)


@pytest.mark.parametrize("source", ("carState", "starpilotCarState"))
@pytest.mark.parametrize(
  ("alive", "valid", "age"),
  (
    (False, True, 0.0),
    (True, False, 0.0),
    (True, True, 2.0),
    (True, True, -2.0),
  ),
  ids=("dead", "invalid", "stale", "future-clock"),
)
def test_manual_resume_rejects_unhealthy_or_unbounded_source(monkeypatch, source, alive, valid, age):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0

  assert not planner._update_manual_stop_resume_override(
    manual_resume_sm(now, source=source, alive=alive, valid=valid, age=age),
  )
  assert planner.manual_stop_resume_override_until == 0.0


@pytest.mark.parametrize("source", ("carState", "starpilotCarState"))
def test_manual_resume_accepts_fresh_live_valid_source(monkeypatch, source):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0

  assert planner._update_manual_stop_resume_override(manual_resume_sm(now, source=source, age=0.1))


@pytest.mark.parametrize(
  "age",
  (
    -planner_module.MANUAL_STOP_RESUME_SOURCE_FUTURE_TOLERANCE,
    planner_module.MANUAL_STOP_RESUME_SOURCE_MAX_AGE,
  ),
  ids=("future-boundary", "stale-boundary"),
)
def test_manual_resume_accepts_inclusive_freshness_boundaries(monkeypatch, age):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0

  assert planner._update_manual_stop_resume_override(manual_resume_sm(now, age=age))


@pytest.mark.parametrize(
  "age",
  (
    -planner_module.MANUAL_STOP_RESUME_SOURCE_FUTURE_TOLERANCE - 1e-6,
    planner_module.MANUAL_STOP_RESUME_SOURCE_MAX_AGE + 1e-6,
  ),
  ids=("beyond-future-boundary", "beyond-stale-boundary"),
)
def test_manual_resume_rejects_outside_freshness_boundaries(monkeypatch, age):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0

  assert not planner._update_manual_stop_resume_override(manual_resume_sm(now, age=age))


@pytest.mark.parametrize("bad_timestamp", (0, float("nan"), float("inf")), ids=("zero", "nan", "infinite"))
def test_manual_resume_rejects_nonpositive_or_nonfinite_timestamp(monkeypatch, bad_timestamp):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0
  sm = manual_resume_sm(now)
  sm.logMonoTime["starpilotCarState"] = bad_timestamp

  assert not planner._update_manual_stop_resume_override(sm)


def test_manual_resume_rejects_partial_health_metadata(monkeypatch):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0
  sm = manual_resume_sm(now)
  del sm.valid["starpilotCarState"]

  assert not planner._update_manual_stop_resume_override(sm)


@pytest.mark.parametrize("pressed_source", ("carState", "starpilotCarState"))
def test_manual_resume_uses_pressed_source_metadata_not_fresh_alternate(monkeypatch, pressed_source):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  planner = LongitudinalPlanner.__new__(LongitudinalPlanner)
  planner.manual_stop_resume_override_until = 0.0
  alternate = "starpilotCarState" if pressed_source == "carState" else "carState"
  sm = manual_resume_sm(now, source=pressed_source)
  sm.logMonoTime[pressed_source] = int((now - 2.0) * 1e9)
  sm.logMonoTime[alternate] = int(now * 1e9)

  assert not planner._update_manual_stop_resume_override(sm)


def run_manual_resume_scene(now, *, stop_flag, source):
  planner = LongitudinalPlanner(
    CarInterface.get_non_essential_params(CAR.HONDA_CIVIC), init_v=0.0,
  )
  sm = make_sm(0.0, desired_accel=-1.0, min_accel=-3.5, experimental_mode=False)
  sm["carState"].standstill = True
  sm["carState"].gasPressed = source == "carState"
  sm["carState"].brakePressed = False
  sm["starpilotCarState"].accelPressed = source == "starpilotCarState"
  sm["modelV2"].action.shouldStop = True
  sm["starpilotPlan"].stopSignConfirmed = False
  setattr(sm["starpilotPlan"], stop_flag, True)
  planner.update(SubMasterFixture(sm, now=now, age=0.0), make_toggles())
  return planner


@pytest.mark.parametrize("flag", ("redLight", "stopSignConfirmed"))
def test_traffic_control_stop_defeats_current_fresh_pedal(monkeypatch, fixed_mpc, flag):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  fixed_mpc.raw_accel = -1.0
  planner = run_manual_resume_scene(now, stop_flag=flag, source="starpilotCarState")

  assert planner.output_should_stop
  assert planner.output_a_target <= -0.95


@pytest.mark.parametrize("source", ("carState", "starpilotCarState"))
def test_forced_stop_allows_current_fresh_physical_pedal(monkeypatch, fixed_mpc, source):
  now = 100.0
  monkeypatch.setattr(planner_module.time, "monotonic", lambda: now)
  fixed_mpc.raw_accel = -1.0
  planner = run_manual_resume_scene(now, stop_flag="forcingStop", source=source)

  assert not planner.output_should_stop
  assert planner.output_a_target >= planner_module.MANUAL_STOP_RESUME_OVERRIDE_MIN_ACCEL


@pytest.mark.parametrize("model_should_stop", (False, True), ids=("model-go", "model-stop"))
def test_unconfirmed_departure_does_not_raise_negative_mpc_candidate(fixed_mpc, model_should_stop):
  """One lead frame is not enough to replace a braking MPC candidate with takeoff."""

  def at_standstill(sm):
    sm["carState"].standstill = True
    sm["carState"].brakePressed = False
    sm["modelV2"].action.shouldStop = model_should_stop

  planner = run_scene(
    CAR.HONDA_CIVIC,
    0.0,
    make_lead(status=True, d_rel=6.5, v_lead=0.8, a_lead=0.3, radar=True, model_prob=1.0),
    raw_accel=-1.0,
    model_accel=0.2,
    toggles=make_toggles(radar_takeoffs=True),
    edit=at_standstill,
  )

  assert planner.output_should_stop
  assert planner.output_a_target <= -0.95


@pytest.mark.parametrize("fingerprint", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD_11G))
def test_persistent_model_stop_with_negative_mpc_blocks_repeated_departure(fixed_mpc, fingerprint):
  """Safety regression: accumulating lead evidence cannot cancel a strong MPC stop."""
  fixed_mpc.raw_accel = -1.0
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(fingerprint), init_v=0.0)
  for tick in range(12):
    lead = make_lead(status=True, d_rel=6.5 + 0.25*tick,
                     v_lead=0.8 + 0.1*tick, a_lead=0.3, radar=True, model_prob=1.0)
    sm = make_sm(0.0, desired_accel=0.2, min_accel=-3.5, experimental_mode=False,
                 tracking_lead=True, lead_one=lead)
    sm["carState"].standstill = True
    sm["carState"].brakePressed = False
    sm["modelV2"].action.shouldStop = True
    sm["starpilotPlan"].stopSignConfirmed = False
    planner.update(sm, make_toggles(radar_takeoffs=True))
    assert planner.output_should_stop, (fingerprint, tick)
    assert planner.output_a_target <= -0.2, (fingerprint, tick, planner.output_a_target)


@pytest.mark.parametrize("fingerprint", (CAR.HONDA_CIVIC, CAR.HONDA_ACCORD_11G))
@pytest.mark.parametrize("late_path", ("radar_settle", "armed_departure_hold"))
def test_final_priority_blocks_late_positive_floor(monkeypatch, fixed_mpc, fingerprint, late_path):
  """Pre-arm one late positive override; strong model/MPC stop must survive."""
  fixed_mpc.raw_accel = -1.0
  lead = make_lead(status=True, d_rel=6.5, v_lead=0.8, a_lead=0.3, radar=True, model_prob=1.0)
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(fingerprint), init_v=0.0)
  if late_path == "radar_settle":
    monkeypatch.setattr(planner_module, "allow_radar_standstill_gap_settle", lambda cp: True)
    monkeypatch.setattr(LongitudinalPlanner, "update_radar_standstill_gap_settle",
                        lambda self, *args, **kwargs: True)
  else:
    monkeypatch.setattr(LongitudinalPlanner, "get_safe_depart_release_hold_lead",
                        lambda self, *args, **kwargs: lead)
    planner.lead_depart_release_hold_remaining = 1.0
  sm = make_sm(0.0, desired_accel=0.2, min_accel=-3.5, experimental_mode=False,
               tracking_lead=True, lead_one=lead)
  sm["carState"].standstill = True
  sm["carState"].brakePressed = False
  sm["modelV2"].action.shouldStop = True
  sm["starpilotPlan"].stopSignConfirmed = False
  planner.update(sm, make_toggles(radar_takeoffs=True))
  assert planner.output_should_stop
  assert planner.output_a_target <= -0.2


def test_reset_clears_departure_release_and_radar_settle_latches(fixed_mpc):
  """Reset cannot preserve a release hold that could reactivate on re-engagement."""
  fixed_mpc.raw_accel = -0.5
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(CAR.HONDA_CIVIC), init_v=0.0)
  planner.lead_depart_release_candidate_elapsed = 0.15
  planner.lead_depart_release_pending = True
  planner.lead_depart_release_hold_remaining = 1.0
  planner.radar_standstill_gap_settle_elapsed = 0.5
  planner.radar_standstill_gap_settle_active = True
  planner.manual_stop_resume_override_until = 999.0
  sm = make_sm(0.0, desired_accel=0.0, min_accel=-3.5, experimental_mode=False)
  sm["carState"].vCruise = planner_module.V_CRUISE_UNSET
  sm["carState"].standstill = True
  sm["carState"].gasPressed = False
  planner.update(sm, make_toggles())
  assert planner.lead_depart_release_candidate_elapsed == 0.0
  assert not planner.lead_depart_release_pending
  assert planner.lead_depart_release_hold_remaining == 0.0
  assert planner.radar_standstill_gap_settle_elapsed == 0.0
  assert not planner.radar_standstill_gap_settle_active
  assert planner.manual_stop_resume_override_until == 0.0


def test_reset_with_qualifying_moving_lead_cannot_rearm_departure(monkeypatch, fixed_mpc):
  """A lead signal during reset must not repopulate any previously cleared release latch."""
  fixed_mpc.raw_accel = 0.2
  lead = make_lead(status=True, d_rel=6.5, v_lead=0.8, a_lead=0.3, radar=True, model_prob=1.0)
  planner = LongitudinalPlanner(CarInterface.get_non_essential_params(CAR.HONDA_CIVIC), init_v=0.0)
  planner.lead_depart_release_candidate_elapsed = 0.15
  planner.lead_depart_release_pending = True
  planner.lead_depart_release_hold_remaining = 1.0
  planner.lead_depart_accel_hold_until = 99999.0
  planner.lead_depart_accel_hold_floor = 0.35
  planner.post_departure_follow_settle_until = 99999.0
  planner.radar_standstill_gap_settle_elapsed = 0.5
  planner.radar_standstill_gap_settle_active = True
  monkeypatch.setattr(LongitudinalPlanner, "get_safe_depart_release_hold_lead",
                      lambda self, *args, **kwargs: lead)
  sm = make_sm(0.0, desired_accel=0.4, min_accel=-3.5, experimental_mode=False,
               tracking_lead=True, lead_one=lead)
  sm["carState"].vCruise = planner_module.V_CRUISE_UNSET
  sm["carState"].standstill = True
  sm["modelV2"].action.shouldStop = False
  planner.update(sm, make_toggles(radar_takeoffs=True))
  assert planner.lead_depart_release_candidate_elapsed == 0.0
  assert not planner.lead_depart_release_pending
  assert planner.lead_depart_release_hold_remaining == 0.0
  assert planner.radar_standstill_gap_settle_elapsed == 0.0
  assert not planner.radar_standstill_gap_settle_active
  assert planner.lead_depart_accel_hold_floor is None
  assert planner.lead_depart_accel_hold_until == 0.0
  assert planner.post_departure_follow_settle_until == 0.0
  # No previously armed departure state may turn reset into a synthetic
  # acceleration boost above the MPC's own bounded positive request.
  assert planner.output_a_target <= fixed_mpc.raw_accel + 1e-6

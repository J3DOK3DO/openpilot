from types import SimpleNamespace

import pytest

from cereal import log
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib.lead_behavior import get_tracked_lead_catchup_bias
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import STOP_DISTANCE, desired_follow_distance
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.controls.lib.longitudinal_vehicle_tunes import (
  get_tracked_lead_catchup_bias_cap,
  get_tracked_lead_catchup_bias_gain,
  get_tracked_lead_catchup_cruise_error_full,
  get_tracked_lead_catchup_fade_margins,
  get_tracked_lead_catchup_headway_margins,
  get_tracked_lead_catchup_speed_range,
  is_honda_accord_11g,
)
from openpilot.starpilot.controls.lib.starpilot_following import StarPilotFollowing


class SubMasterLike:
  """Match the real messaging.SubMaster access contract: __getitem__, no dict.get()."""

  def __init__(self, data, *, seen=None, alive=None, valid=None):
    self.data = data
    # These are the health maps exposed by messaging.SubMaster. Keeping them on
    # the test double lets fail-closed callers distinguish an unavailable service
    # from a healthy message with all fields false.
    self.seen = seen if seen is not None else {name: True for name in data}
    self.alive = alive if alive is not None else {name: True for name in data}
    self.valid = valid if valid is not None else {name: True for name in data}

  def __getitem__(self, key):
    return self.data[key]


def make_lead(*, d_rel, v_lead, a_lead=0.0, model_prob=1.0, radar=False, radar_track_id=-1, y_rel=0.0):
  lead = log.RadarState.LeadData.new_message()
  lead.status = True
  lead.dRel = d_rel
  lead.vLead = v_lead
  lead.vLeadK = v_lead
  lead.vRel = 0.0
  lead.aLeadK = a_lead
  lead.modelProb = model_prob
  lead.radar = radar
  lead.radarTrackId = radar_track_id
  lead.yRel = y_rel
  return lead


def test_c6_oct1_creep_depart_does_not_accelerate_into_slower_lead():
  """Oct 1 seg101: ego ~1.50 m/s was still closing on a ~0.79 m/s lead."""
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=1.496)
  lead = make_lead(d_rel=7.18, v_lead=0.789, a_lead=0.20)
  nudge_gap = STOP_DISTANCE - 0.5

  assert is_honda_accord_11g(accord)
  assert not planner.is_basic_lead_depart_ready(lead, 1.496, nudge_gap)
  assert not planner.is_slow_creep_lead_depart(lead, 1.496, nudge_gap)


def test_c6_depart_pullaway_guard_preserves_real_standstill_departure():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=0.0)
  lead = make_lead(d_rel=7.18, v_lead=0.789, a_lead=0.20)
  nudge_gap = STOP_DISTANCE - 0.5

  assert planner.is_basic_lead_depart_ready(lead, 0.0, nudge_gap)
  assert planner.is_slow_creep_lead_depart(lead, 0.0, nudge_gap)


def test_c6_depart_pullaway_guard_is_accord11g_scoped():
  civic = CarInterface.get_non_essential_params(CAR.HONDA_CIVIC)
  planner = LongitudinalPlanner(civic, init_v=1.496)
  lead = make_lead(d_rel=7.18, v_lead=0.789, a_lead=0.20)

  assert not is_honda_accord_11g(civic)
  assert planner.is_basic_lead_depart_ready(lead, 1.496, STOP_DISTANCE - 0.5)


def test_c6_oct1_close_lead_brake_cap_survives_aleadk_threshold_dip():
  """Oct 1 seg70 ~17:16:34: required decel 0.245 -> 0.180 -> 0.137 -> 0.165 -> 0.252."""
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)

  frames = [
    (5.059412, 12.320465, 4.405433, -0.315703),
    (5.042295, 12.238079, 4.409201, -0.224487),
    (5.029919, 12.296898, 4.367542, -0.161190),
    (5.039449, 12.334166, 4.382744, -0.201123),
    (5.037205, 12.176617, 4.371906, -0.323634),
  ]
  caps = []
  demands = []
  for v_ego, d_rel, v_lead, a_lead in frames:
    lead = make_lead(d_rel=d_rel, v_lead=v_lead, a_lead=a_lead)
    demands.append(planner.get_close_lead_brake_demand(lead, v_ego))
    caps.append(planner.update_close_lead_brake_cap(lead, 0, v_ego, -1.0))

  assert demands == pytest.approx([0.245174, 0.179710, 0.137110, 0.164706, 0.251963], abs=2e-3)
  assert all(cap is not None and cap < 0.0 for cap in caps)
  assert caps[2] <= -0.15


def test_c6_close_lead_brake_hold_does_not_create_new_braking_without_entry():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.04)
  lead = make_lead(d_rel=12.238079, v_lead=4.409201, a_lead=-0.224487)

  assert planner.get_close_lead_brake_demand(lead, 5.042295) == pytest.approx(0.179710, abs=2e-3)
  assert planner.update_close_lead_brake_cap(lead, 0, 5.042295, -1.0) is None


def test_c6_close_lead_brake_hold_releases_after_short_transient():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  entry = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703)
  mild = make_lead(d_rel=12.3, v_lead=4.50, a_lead=-0.02)

  assert planner.update_close_lead_brake_cap(entry, 0, 5.059412, -1.0) is not None

  held = [planner.update_close_lead_brake_cap(mild, 0, 5.0, -1.0) for _ in range(6)]
  assert any(cap is not None for cap in held[:5])
  assert held[-1] is None


def test_c6_close_lead_brake_hold_does_not_transfer_to_materially_replaced_same_slot_lead():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703, radar=True, radar_track_id=101)
  replacement = make_lead(d_rel=20.0, v_lead=4.0, a_lead=-0.10, model_prob=0.91, radar=False)

  assert planner.get_close_lead_brake_demand(braking_lead, 5.059412) >= 0.20
  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None

  replacement_demand = planner.get_close_lead_brake_demand(replacement, 5.059412)
  assert replacement_demand is not None
  assert 0.0 < replacement_demand < 0.20
  assert planner.update_close_lead_brake_cap(replacement, 0, 5.059412, -1.0) is None


def test_c6_close_lead_brake_hold_does_not_transfer_to_different_radar_track():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703, radar=True, radar_track_id=101)
  replacement = make_lead(d_rel=20.0, v_lead=4.0, a_lead=-0.10, radar=True, radar_track_id=202)

  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None

  replacement_demand = planner.get_close_lead_brake_demand(replacement, 5.059412)
  assert replacement_demand is not None
  assert 0.0 < replacement_demand < 0.20
  assert planner.update_close_lead_brake_cap(replacement, 0, 5.059412, -1.0) is None


def test_c6_close_lead_replacement_preserves_stronger_current_braking_immediately():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  prior_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703, radar=True, radar_track_id=101)
  stronger_replacement = make_lead(d_rel=8.0, v_lead=2.5, a_lead=-0.80, radar=True, radar_track_id=202)

  assert planner.update_close_lead_brake_cap(prior_lead, 0, 5.059412, -3.0) is not None
  replacement_demand = planner.get_close_lead_brake_demand(stronger_replacement, 5.059412)
  assert replacement_demand is not None
  assert replacement_demand >= 0.20
  cap = planner.update_close_lead_brake_cap(stronger_replacement, 0, 5.059412, -3.0)
  assert cap == pytest.approx(max(-3.0, -replacement_demand))
  assert planner.close_lead_brake_hold_remaining[0] == pytest.approx(0.25)
  assert planner.close_lead_brake_hold_provenance[0]["radar_track_id"] == 202


def test_c6_close_lead_brake_hold_invalid_radar_id_uses_material_geometry_fallback():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703, radar=True)
  replacement = make_lead(d_rel=21.0, v_lead=4.0, a_lead=-0.10, radar=True)

  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None
  replacement_demand = planner.get_close_lead_brake_demand(replacement, 5.059412)
  assert replacement_demand is not None
  assert 0.0 < replacement_demand < 0.20
  assert planner.update_close_lead_brake_cap(replacement, 0, 5.059412, -1.0) is None


def test_c6_close_lead_brake_hold_does_not_transfer_to_materially_replaced_vision_lead():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703)
  replacement = make_lead(d_rel=21.0, v_lead=3.50, a_lead=-0.10)

  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None
  replacement_demand = planner.get_close_lead_brake_demand(replacement, 5.0)
  assert replacement_demand is not None
  assert 0.0 < replacement_demand < 0.20
  assert planner.update_close_lead_brake_cap(replacement, 0, 5.0, -1.0) is None


def test_c6_close_lead_brake_hold_keeps_ordinary_vision_lead_frame_motion():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703)
  mild = make_lead(d_rel=12.3, v_lead=4.50, a_lead=-0.02, y_rel=0.1)

  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None
  assert planner.get_close_lead_brake_demand(mild, 5.0) < 0.20
  assert planner.update_close_lead_brake_cap(mild, 0, 5.0, -1.0) is not None


def test_c6_close_lead_brake_hold_idless_provenance_stays_anchored_at_entry():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703, y_rel=0.0)

  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None

  # Each sample moves less than the 2.5 m replacement bound from its predecessor,
  # but the final sample has moved materially from the lead that opened the hold.
  for y_rel in (1.3, 2.6):
    mild = make_lead(d_rel=12.3, v_lead=4.50, a_lead=-0.02, y_rel=y_rel)
    assert 0.0 < planner.get_close_lead_brake_demand(mild, 5.0) < 0.20
    cap = planner.update_close_lead_brake_cap(mild, 0, 5.0, -1.0)

  assert cap is None
  assert planner.close_lead_brake_hold_remaining[0] == 0.0
  assert planner.close_lead_brake_hold_provenance[0] is None


def test_c6_close_lead_brake_hold_idless_nonfinite_provenance_fails_closed():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703, y_rel=0.0)
  mild = make_lead(d_rel=12.3, v_lead=4.50, a_lead=-0.02, y_rel=float("nan"))

  assert planner.update_close_lead_brake_cap(braking_lead, 0, 5.059412, -1.0) is not None
  assert 0.0 < planner.get_close_lead_brake_demand(mild, 5.0) < 0.20
  assert planner.update_close_lead_brake_cap(mild, 0, 5.0, -1.0) is None
  assert planner.close_lead_brake_hold_remaining[0] == 0.0
  assert planner.close_lead_brake_hold_provenance[0] is None


def test_c6_lead_control_disable_clear_routine_resets_both_slots_and_provenance():
  """The update() lead-control-disable branch delegates this reset to this routine."""
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner = LongitudinalPlanner(accord, init_v=5.06)
  braking_lead = make_lead(d_rel=12.320465, v_lead=4.405433, a_lead=-0.315703)

  for lead_index in range(2):
    assert planner.update_close_lead_brake_cap(braking_lead, lead_index, 5.059412, -1.0) is not None
    assert planner.close_lead_brake_hold_provenance[lead_index] is not None
    planner.clear_close_lead_brake_hold(lead_index)

  assert planner.close_lead_brake_hold_remaining == [0.0, 0.0]
  assert planner.close_lead_brake_hold_provenance == [None, None]


def test_c6_accord_untracked_highway_coast_enters_holds_and_releases():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.957, y_rel=-0.648),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45
  sm = SubMasterLike({
    "carParams": accord,
    "carState": SimpleNamespace(leftBlinker=False, rightBlinker=False),
  })

  for _ in range(5):
    assert not following.update_untracked_vision_coast(True, 31.007, sm)
  assert following.update_untracked_vision_coast(True, 31.007, sm)
  assert following.untracked_vision_coast_hold_remaining > 0.0

  # Keep a credible closing lead but move outside the raw <=6 s coast-entry window;
  # the short hold should prevent a one-frame throttle re-entry.
  planner_stub.lead_one.dRel = 110.0
  planner_stub.lead_one.vLead = 29.5
  planner_stub.lead_one.vLeadK = 29.5
  assert following.update_untracked_vision_coast(True, 31.007, sm)

  # Confidence loss is an immediate release condition, not something the hold masks.
  planner_stub.lead_one.modelProb = 0.50
  assert not following.update_untracked_vision_coast(True, 31.007, sm)
  assert following.untracked_vision_coast_hold_remaining == 0.0


def test_c6_accord_untracked_highway_coast_missing_carstate_fails_closed():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.957, y_rel=-0.648),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45
  healthy_sm = SubMasterLike({
    "carParams": accord,
    "carState": SimpleNamespace(leftBlinker=False, rightBlinker=False),
  })

  for _ in range(6):
    following.update_untracked_vision_coast(True, 31.007, healthy_sm)
  assert following.untracked_vision_coast_hold_remaining > 0.0

  assert not following.update_untracked_vision_coast(True, 31.007, SubMasterLike({"carParams": accord}))
  assert following.untracked_vision_coast_confirm_t == 0.0
  assert following.untracked_vision_coast_hold_remaining == 0.0


@pytest.mark.parametrize(("health", "value"), [("seen", False), ("alive", False), ("valid", False)])
def test_c6_accord_untracked_highway_coast_unhealthy_carstate_fails_closed(health, value):
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.957, y_rel=-0.648),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45
  health_maps = {
    "seen": {"carParams": True, "carState": True},
    "alive": {"carParams": True, "carState": True},
    "valid": {"carParams": True, "carState": True},
  }
  health_maps[health]["carState"] = value
  sm = SubMasterLike({
    "carParams": accord,
    "carState": SimpleNamespace(leftBlinker=False, rightBlinker=False),
  }, seen=health_maps["seen"], alive=health_maps["alive"], valid=health_maps["valid"])

  following.untracked_vision_coast_confirm_t = 0.10
  following.untracked_vision_coast_hold_remaining = 0.20
  assert not following.update_untracked_vision_coast(True, 31.007, sm)
  assert following.untracked_vision_coast_confirm_t == 0.0
  assert following.untracked_vision_coast_hold_remaining == 0.0


def test_c6_accord_untracked_highway_coast_mapless_valid_carstate_remains_compatible():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.957, y_rel=-0.648),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45
  sm = {
    "carParams": accord,
    "carState": SimpleNamespace(leftBlinker=False, rightBlinker=False),
  }

  for _ in range(6):
    following.update_untracked_vision_coast(True, 31.007, sm)

  assert following.untracked_vision_coast_hold_remaining > 0.0
  assert following.update_untracked_vision_coast(True, 31.007, sm)


@pytest.mark.parametrize("bad_car_state", [
  None,
  SimpleNamespace(),
  SimpleNamespace(leftBlinker=False),
  SimpleNamespace(rightBlinker=False),
])
def test_c6_accord_untracked_highway_coast_mapless_unreadable_blinkers_fail_closed(bad_car_state):
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.957, y_rel=-0.648),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45

  healthy_sm = {
    "carParams": accord,
    "carState": SimpleNamespace(leftBlinker=False, rightBlinker=False),
  }
  for _ in range(6):
    following.update_untracked_vision_coast(True, 31.007, healthy_sm)
  assert following.untracked_vision_coast_hold_remaining > 0.0

  assert not following.update_untracked_vision_coast(
    True, 31.007, {"carParams": accord, "carState": bad_car_state},
  )
  assert following.untracked_vision_coast_confirm_t == 0.0
  assert following.untracked_vision_coast_hold_remaining == 0.0


@pytest.mark.parametrize("blinker", ["leftBlinker", "rightBlinker"])
def test_c6_accord_untracked_highway_coast_cancels_immediately_on_physical_blinker(blinker):
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.957, y_rel=-0.648),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45
  car_state = SimpleNamespace(leftBlinker=False, rightBlinker=False)
  sm = SubMasterLike({
    "carParams": accord,
    "carState": car_state,
    "modelV2": SimpleNamespace(meta=SimpleNamespace(laneChangeState=log.LaneChangeState.off)),
  })

  for _ in range(6):
    following.update_untracked_vision_coast(True, 31.007, sm)
  assert following.untracked_vision_coast_confirm_t > 0.0
  assert following.untracked_vision_coast_hold_remaining > 0.0

  setattr(car_state, blinker, True)
  assert not following.update_untracked_vision_coast(True, 31.007, sm)
  assert following.untracked_vision_coast_confirm_t == 0.0
  assert following.untracked_vision_coast_hold_remaining == 0.0


def test_c6_untracked_highway_coast_is_accord11g_scoped():
  civic = CarInterface.get_non_essential_params(CAR.HONDA_CIVIC)
  planner_stub = SimpleNamespace(
    lead_one=make_lead(d_rel=105.318, v_lead=27.911, model_prob=0.99, y_rel=0.0),
    tracking_lead=False,
    lead_path_y=0.0,
    starpilot_weather=SimpleNamespace(weather_id=0, increase_following_distance=0.0),
  )
  following = StarPilotFollowing(planner_stub)
  following.t_follow = 1.45

  assert not following.update_untracked_vision_coast(True, 31.007, {"carParams": civic})


def test_c6_accord11g_tracked_catchup_tune_is_lower_speed_and_vision_compatible():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  civic = CarInterface.get_non_essential_params(CAR.HONDA_CIVIC)

  assert get_tracked_lead_catchup_headway_margins(accord) == pytest.approx((0.15, 0.45))
  assert get_tracked_lead_catchup_bias_gain(accord) == pytest.approx(0.75)
  assert get_tracked_lead_catchup_speed_range(accord) == pytest.approx((4.5, 10.0))
  assert get_tracked_lead_catchup_fade_margins(accord) == pytest.approx((0.75, 1.75))
  assert get_tracked_lead_catchup_cruise_error_full(accord) == pytest.approx(0.75)
  # Keep the generic bounded cap so the MPC does not enter the CR-V radar-only path.
  assert get_tracked_lead_catchup_bias_cap(accord) is None
  assert get_tracked_lead_catchup_speed_range(civic) is None


def test_c6_accord11g_catchup_respects_personality_headway_and_stopgo_boundary():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  margins = get_tracked_lead_catchup_headway_margins(accord)
  speed_range = get_tracked_lead_catchup_speed_range(accord)
  fade_margins = get_tracked_lead_catchup_fade_margins(accord)
  gain = get_tracked_lead_catchup_bias_gain(accord)
  cruise_error_full = get_tracked_lead_catchup_cruise_error_full(accord)

  v_ego = 8.0
  v_lead = 8.0
  d_rel = 22.0
  v_cruise = 10.0
  aggressive_gap = desired_follow_distance(v_ego, v_lead, 1.20)
  relaxed_gap = desired_follow_distance(v_ego, v_lead, 1.80)

  aggressive_bias = get_tracked_lead_catchup_bias(
    v_ego, d_rel, aggressive_gap, 0.0, v_cruise=v_cruise, y_rel=0.0,
    min_headway_margin=margins[0], full_headway_margin=margins[1],
    bias_gain=gain, speed_range=speed_range, fade_margins=fade_margins,
    cruise_error_full=cruise_error_full,
  )
  relaxed_bias = get_tracked_lead_catchup_bias(
    v_ego, d_rel, relaxed_gap, 0.0, v_cruise=v_cruise, y_rel=0.0,
    min_headway_margin=margins[0], full_headway_margin=margins[1],
    bias_gain=gain, speed_range=speed_range, fade_margins=fade_margins,
    cruise_error_full=cruise_error_full,
  )

  assert aggressive_bias > 0.0
  assert aggressive_bias > relaxed_bias

  below_stopgo_bias = get_tracked_lead_catchup_bias(
    4.0, 18.0, desired_follow_distance(4.0, 4.0, 1.20), 0.0,
    v_cruise=6.0, y_rel=0.0,
    min_headway_margin=margins[0], full_headway_margin=margins[1],
    bias_gain=gain, speed_range=speed_range, fade_margins=fade_margins,
    cruise_error_full=cruise_error_full,
  )
  assert below_stopgo_bias == 0.0


def test_c6_accord11g_catchup_fades_for_closing_or_offset_lead():
  accord = CarInterface.get_non_essential_params(CAR.HONDA_ACCORD_11G)
  kwargs = {
    "min_headway_margin": get_tracked_lead_catchup_headway_margins(accord)[0],
    "full_headway_margin": get_tracked_lead_catchup_headway_margins(accord)[1],
    "bias_gain": get_tracked_lead_catchup_bias_gain(accord),
    "speed_range": get_tracked_lead_catchup_speed_range(accord),
    "fade_margins": get_tracked_lead_catchup_fade_margins(accord),
    "cruise_error_full": get_tracked_lead_catchup_cruise_error_full(accord),
  }
  desired_gap = desired_follow_distance(8.0, 8.0, 1.20)

  centered = get_tracked_lead_catchup_bias(
    8.0, 22.0, desired_gap, 0.0, v_cruise=10.0, y_rel=0.0, **kwargs,
  )
  offset = get_tracked_lead_catchup_bias(
    8.0, 22.0, desired_gap, 0.0, v_cruise=10.0, y_rel=1.8, **kwargs,
  )
  closing = get_tracked_lead_catchup_bias(
    8.0, 22.0, desired_gap, 3.0, v_cruise=10.0, y_rel=0.0, **kwargs,
  )

  assert centered > 0.0
  assert offset == 0.0
  assert closing < centered

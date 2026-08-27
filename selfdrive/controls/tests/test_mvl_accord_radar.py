from dataclasses import dataclass
import math
from types import SimpleNamespace

import pytest

from cereal import car, log
from opendbc.car import Bus
from opendbc.car.honda.interface import CarInterface as HondaCarInterface
from opendbc.car.honda.radar_interface import BOSCH_A_DBC_NAME, RadarInterface as HondaRadarInterface
from opendbc.car.honda.values import CAR as HONDA_CAR, DBC, HONDA_BOSCH_A, HONDA_BOSCH_A_RADAR_VERIFIED
from opendbc.car.toyota.values import CAR as TOYOTA_CAR
from openpilot.common.filter_simple import FirstOrderFilter
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.controls.lib.mvl_accord_radar import (
  MVL_ACCORD_LEAD_ACCEL_TAU,
  MVL_ACCORD_MODEL_LEAD_PROBABILITY,
  RADAR_TO_CAMERA,
  is_mvl_accord_radar,
  mvl_get_lead,
  mvl_match_vision_to_track,
  update_mvl_accord_accel_tau,
)
from openpilot.selfdrive.controls import radard as radard_module
from openpilot.selfdrive.controls.radard import (
  HONDA_BOSCH_A_RADAR_TS,
  KalmanParams,
  RadarD,
  Track,
  is_bosch_a_radar_car,
)


@dataclass(frozen=True)
class TrackSpec:
  identifier: int
  d_rel: float
  y_rel: float
  v_rel: float
  a_lead: float = 0.0
  a_tau: float = MVL_ACCORD_LEAD_ACCEL_TAU
  cnt: int = 5


@dataclass(frozen=True)
class LeadSpec:
  d_rel: float
  y_rel: float
  v_lead: float
  a_lead: float = 0.0
  probability: float = 0.9
  x_std: float = 1.5
  y_std: float = 0.3
  v_std: float = 1.0


@dataclass(frozen=True)
class RadarScenario:
  name: str
  v_ego: float
  ready: bool
  lead_one: LeadSpec
  lead_two: LeadSpec
  tracks: tuple[TrackSpec, ...]


class FakeTrack:
  def __init__(self, spec: TrackSpec):
    self.identifier = spec.identifier
    self.dRel = spec.d_rel
    self.yRel = spec.y_rel
    self.vRel = spec.v_rel
    self.vLead = 0.0
    self.vLeadK = 0.0
    self.aLeadK = spec.a_lead
    self.aLeadTau = SimpleNamespace(x=spec.a_tau)
    self.cnt = spec.cnt
    self.leadTrackID = 0

  def get_RadarState(self, model_prob: float = 0.0):
    return {
      "dRel": float(self.dRel),
      "yRel": float(self.yRel),
      "vRel": float(self.vRel),
      "vLead": float(self.vLead),
      "vLeadK": float(self.vLeadK),
      "aLeadK": float(self.aLeadK),
      "aLeadTau": float(self.aLeadTau.x),
      "status": True,
      "fcw": model_prob > 0.9,
      "modelProb": model_prob,
      "radar": True,
      "radarTrackId": self.identifier,
    }

  def potential_low_speed_lead(self, v_ego: float):
    return abs(self.yRel) < 1.0 and v_ego < 4.0 and 0.75 < self.dRel < 25.0


def make_lead(spec: LeadSpec):
  return SimpleNamespace(
    x=[spec.d_rel + RADAR_TO_CAMERA],
    y=[-spec.y_rel],
    v=[spec.v_lead],
    a=[spec.a_lead],
    xStd=[spec.x_std],
    yStd=[spec.y_std],
    vStd=[spec.v_std],
    prob=spec.probability,
  )


def make_tracks(specs: tuple[TrackSpec, ...]):
  return {spec.identifier: FakeTrack(spec) for spec in specs}


def reference_laplacian_pdf(x: float, mu: float, scale: float):
  return math.exp(-abs(x - mu) / max(scale, 1e-4))


def reference_match(v_ego: float, lead, tracks):
  if not tracks:
    return None
  offset_vision_dist = lead.x[0] - 1.52

  def probability(track):
    return (
      reference_laplacian_pdf(track.dRel, offset_vision_dist, lead.xStd[0])
      * reference_laplacian_pdf(track.yRel, -lead.y[0], lead.yStd[0])
      * reference_laplacian_pdf(track.vRel + v_ego, lead.v[0], lead.vStd[0])
    )

  track = max(tracks.values(), key=probability)
  dist_sane = abs(track.dRel - offset_vision_dist) < max(offset_vision_dist * 0.25, 5.0)
  vel_sane = abs(track.vRel + v_ego - lead.v[0]) < 10.0 or v_ego + track.vRel > 3.0
  return track if dist_sane and vel_sane else None


def reference_vision_state(lead, v_ego: float, model_v_ego: float, lead_prob: float):
  lead_v_rel_pred = lead.v[0] - model_v_ego
  return {
    "dRel": float(lead.x[0] - 1.52),
    "yRel": float(-lead.y[0]),
    "vRel": float(lead_v_rel_pred),
    "vLead": float(v_ego + lead_v_rel_pred),
    "vLeadK": float(v_ego + lead_v_rel_pred),
    "aLeadK": float(lead.a[0]),
    "aLeadTau": 0.3,
    "fcw": False,
    "modelProb": float(lead_prob),
    "status": True,
    "radar": False,
    "radarTrackId": -1,
  }


def reference_get_lead(v_ego: float, ready: bool, tracks, lead, model_v_ego: float,
                       lead_prob: float, low_speed_override: bool = True):
  track = reference_match(v_ego, lead, tracks) if tracks and ready and lead_prob > 0.5 else None
  lead_dict = {"status": False}
  if track is not None:
    lead_dict = track.get_RadarState(lead_prob)
  elif ready and lead_prob > 0.5:
    lead_dict = reference_vision_state(lead, v_ego, model_v_ego, lead_prob)

  if low_speed_override:
    candidates = [track for track in tracks.values() if track.potential_low_speed_lead(v_ego)]
    if candidates:
      closest = min(candidates, key=lambda candidate: candidate.dRel)
      if not lead_dict["status"] or closest.dRel < lead_dict["dRel"]:
        lead_dict = closest.get_RadarState()

  for radar_track in tracks.values():
    radar_track.leadTrackID = lead_dict.get("radarTrackId", -1)
  return lead_dict


DEFAULT_SECOND_LEAD = LeadSpec(70.0, 0.0, 15.0, probability=0.1)

RADAR_SCENARIOS = (
  RadarScenario("one clear moving lead", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 30.0, 0.0, 0.0),)),
  RadarScenario("two moving leads", 10.0, True, LeadSpec(20.0, 0.0, 9.0), LeadSpec(45.0, 0.1, 12.0),
                (TrackSpec(1, 20.0, 0.0, -1.0), TrackSpec(2, 45.0, 0.1, 2.0))),
  RadarScenario("crossing adjacent object", 12.0, True, LeadSpec(32.0, 0.0, 11.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 32.0, 0.0, -1.0), TrackSpec(2, 15.0, 3.0, -5.0))),
  RadarScenario("stationary lead", 10.0, True, LeadSpec(20.0, 0.0, 0.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 20.0, 0.0, -10.0),)),
  RadarScenario("low speed stopped lead", 2.0, True, LeadSpec(30.0, 0.0, 2.0, probability=0.1), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 8.0, 0.0, -2.0),)),
  RadarScenario("ego approaching stationary lead", 3.5, True, LeadSpec(12.0, 0.0, 0.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 12.0, 0.0, -3.5),)),
  RadarScenario("lead pulling away", 10.0, True, LeadSpec(35.0, 0.0, 12.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 35.0, 0.0, 2.0, 0.8, 0.7),)),
  RadarScenario("model lead without radar match", 10.0, True, LeadSpec(25.0, 0.0, 9.0, 0.2), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 80.0, 3.0, -8.0),)),
  RadarScenario("radar track without model lead", 10.0, False, LeadSpec(25.0, 0.0, 9.0, probability=0.1), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 25.0, 0.0, -1.0),)),
  RadarScenario("weak model probability", 10.0, True, LeadSpec(25.0, 0.0, 9.0, probability=0.5), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 25.0, 0.0, -1.0),)),
  RadarScenario("strong model probability", 10.0, True, LeadSpec(25.0, 0.0, 9.0, 0.4, probability=0.5001), DEFAULT_SECOND_LEAD, ()),
  RadarScenario("range mismatch near threshold", 10.0, True, LeadSpec(20.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 24.999, 0.0, 0.0),)),
  RadarScenario("velocity mismatch near threshold", 2.0, True, LeadSpec(20.0, 0.0, 12.499), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 20.0, 0.0, 0.5),)),
  RadarScenario("duplicate candidate tracks", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(10, 30.0, 0.0, 0.0), TrackSpec(11, 30.0, 0.0, 0.0))),
  RadarScenario("stale track absent", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD, ()),
  RadarScenario("disappearing lead", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD, ()),
  RadarScenario("reappearing same lead", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(7, 30.0, 0.0, 0.0),)),
  RadarScenario("new track id at similar position", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(8, 30.1, 0.0, 0.0),)),
  RadarScenario("lead one lead two swap pressure", 10.0, True, LeadSpec(21.0, 0.0, 9.0), LeadSpec(39.0, 0.0, 11.0),
                (TrackSpec(1, 21.0, 0.0, -1.0), TrackSpec(2, 39.0, 0.0, 1.0))),
  RadarScenario("low speed override candidate", 2.0, True, LeadSpec(40.0, 0.0, 2.0, probability=0.1), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 10.0, 0.2, -2.0),)),
  RadarScenario("low speed override rejection", 2.0, True, LeadSpec(40.0, 0.0, 2.0, probability=0.1), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 10.0, 1.01, -2.0),)),
  RadarScenario("acceleration decay", 10.0, True, LeadSpec(25.0, 0.0, 8.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 25.0, 0.0, -2.0, -1.2, 0.42),)),
  RadarScenario("lead acceleration reset", 10.0, True, LeadSpec(25.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(99, 25.0, 0.0, 0.0, 0.0, 1.5, 0),)),
  RadarScenario("no radar points", 10.0, True, LeadSpec(25.0, 0.0, 9.0), DEFAULT_SECOND_LEAD, ()),
  RadarScenario("multiple plausible radar points", 10.0, True, LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD,
                (TrackSpec(1, 29.0, 0.1, 0.0), TrackSpec(2, 30.2, 0.0, 0.1), TrackSpec(3, 33.0, -0.2, -1.0))),
)


def assert_lead_equal(actual, expected):
  assert actual.keys() == expected.keys()
  for key in actual:
    if isinstance(actual[key], float):
      assert actual[key] == pytest.approx(expected[key])
    else:
      assert actual[key] == expected[key]


@pytest.mark.parametrize("scenario", RADAR_SCENARIOS, ids=lambda scenario: scenario.name)
def test_validated_accord06_differential(scenario: RadarScenario):
  actual_tracks = make_tracks(scenario.tracks)
  expected_tracks = make_tracks(scenario.tracks)
  lead_one = make_lead(scenario.lead_one)
  lead_two = make_lead(scenario.lead_two)

  actual_one = mvl_get_lead(scenario.v_ego, scenario.ready, actual_tracks, lead_one, scenario.v_ego,
                            scenario.lead_one.probability, low_speed_override=True)
  actual_two = mvl_get_lead(scenario.v_ego, scenario.ready, actual_tracks, lead_two, scenario.v_ego,
                            scenario.lead_two.probability, low_speed_override=False)
  expected_one = reference_get_lead(scenario.v_ego, scenario.ready, expected_tracks, lead_one, scenario.v_ego,
                                    scenario.lead_one.probability, low_speed_override=True)
  expected_two = reference_get_lead(scenario.v_ego, scenario.ready, expected_tracks, lead_two, scenario.v_ego,
                                    scenario.lead_two.probability, low_speed_override=False)

  assert_lead_equal(actual_one, expected_one)
  assert_lead_equal(actual_two, expected_two)


def test_low_speed_override_is_lead_one_only():
  tracks = make_tracks((TrackSpec(4, 9.0, 0.0, -2.0),))
  weak_lead = make_lead(LeadSpec(40.0, 0.0, 2.0, probability=0.1))
  lead_one = mvl_get_lead(2.0, True, tracks, weak_lead, 2.0, 0.1, low_speed_override=True)
  lead_two = mvl_get_lead(2.0, True, tracks, weak_lead, 2.0, 0.1, low_speed_override=False)
  assert lead_one["radarTrackId"] == 4
  assert not lead_two["status"]


def test_two_model_leads_select_independent_tracks():
  tracks = make_tracks((TrackSpec(1, 20.0, 0.0, -1.0), TrackSpec(2, 45.0, 0.0, 2.0)))
  lead_one = mvl_get_lead(10.0, True, tracks, make_lead(LeadSpec(20.0, 0.0, 9.0)), 10.0, 0.9, True)
  lead_two = mvl_get_lead(10.0, True, tracks, make_lead(LeadSpec(45.0, 0.0, 12.0)), 10.0, 0.9, False)
  assert lead_one["radarTrackId"] == 1
  assert lead_two["radarTrackId"] == 2


def test_match_thresholds_are_strict_and_validated():
  lead = make_lead(LeadSpec(20.0, 0.0, 2.0))
  inside = make_tracks((TrackSpec(1, 24.999, 0.0, -8.0),))
  boundary = make_tracks((TrackSpec(1, 25.0, 0.0, -8.0),))
  assert mvl_match_vision_to_track(10.0, lead, inside) is inside[1]
  assert mvl_match_vision_to_track(10.0, lead, boundary) is None
  assert MVL_ACCORD_MODEL_LEAD_PROBABILITY == 0.5


def test_mvl_track_acceleration_tau_and_new_track_reset():
  params = KalmanParams(0.05)
  accord_track = Track(1, 10.0, params, mvl_accord_mode=True)
  generic_track = Track(1, 10.0, params)

  assert accord_track.aLeadTau.x == pytest.approx(1.5)
  assert generic_track.aLeadTau.x == pytest.approx(0.6)

  accord_track.aLeadTau.x = 0.2
  update_mvl_accord_accel_tau(accord_track.aLeadTau, 0.49)
  assert accord_track.aLeadTau.x == pytest.approx(1.5)

  update_mvl_accord_accel_tau(accord_track.aLeadTau, 0.5)
  assert accord_track.aLeadTau.x < 1.5

  replacement = Track(1, 10.0, params, mvl_accord_mode=True)
  replacement.update(20.0, 0.0, 0.0, 10.0, True)
  assert replacement.aLeadK == pytest.approx(0.0)
  assert replacement.aLeadTau.x == pytest.approx(1.5)


@pytest.mark.parametrize(
  "fingerprint,expected",
  [
    (HONDA_CAR.HONDA_ACCORD_11G, True),
    (HONDA_CAR.HONDA_CRV_6G, False),
    (HONDA_CAR.HONDA_CIVIC_BOSCH, False),
    (HONDA_CAR.HONDA_CIVIC_2022, False),
    (TOYOTA_CAR.TOYOTA_RAV4, False),
  ],
)
def test_exact_accord_radar_route(fingerprint, expected):
  assert is_mvl_accord_radar(SimpleNamespace(carFingerprint=fingerprint)) is expected


def test_accord_route_is_disjoint_from_bosch_a():
  accord = SimpleNamespace(
    brand="honda",
    carFingerprint=HONDA_CAR.HONDA_ACCORD_11G,
    radarUnavailable=True,
  )
  civic_bosch = SimpleNamespace(
    brand="honda",
    carFingerprint=HONDA_CAR.HONDA_CIVIC_BOSCH,
    radarUnavailable=False,
  )

  assert is_mvl_accord_radar(accord)
  assert not is_bosch_a_radar_car(accord)
  assert not is_mvl_accord_radar(civic_bosch)
  assert is_bosch_a_radar_car(civic_bosch)

  accord_radard = RadarD(radar_ts=0.05, mvl_accord_mode=True)
  bosch_a_radard = RadarD(radar_ts=0.05, honda_bosch_a_radar=True)
  generic_radard = RadarD(radar_ts=0.05)
  assert accord_radard.mvl_accord_mode and not accord_radard.honda_bosch_a_radar
  assert bosch_a_radard.honda_bosch_a_radar and not bosch_a_radard.mvl_accord_mode
  assert bosch_a_radard.kalman_params.A[0][1] == pytest.approx(HONDA_BOSCH_A_RADAR_TS)
  assert not generic_radard.mvl_accord_mode and not generic_radard.honda_bosch_a_radar


def test_current_honda_radar_configuration_remains_native():
  accord_cp = HondaCarInterface.get_non_essential_params(HONDA_CAR.HONDA_ACCORD_11G)
  assert DBC[HONDA_CAR.HONDA_ACCORD_11G][Bus.radar] == "honda_common_canfd_generated"
  assert accord_cp.radarUnavailable
  assert HondaRadarInterface(accord_cp).rcp is None

  bosch_a_dbc_cars = {
    fingerprint for fingerprint, dbc_map in DBC.items()
    if dbc_map.get(Bus.radar) == BOSCH_A_DBC_NAME
  }
  assert bosch_a_dbc_cars == set(HONDA_BOSCH_A)
  assert HONDA_CAR.HONDA_ACCORD_11G not in bosch_a_dbc_cars
  assert HONDA_BOSCH_A_RADAR_VERIFIED <= HONDA_BOSCH_A


def test_accord_probability_filter_and_kalman_timing_remain_20hz():
  radard = RadarD(radar_ts=0.05, mvl_accord_mode=True)
  assert radard.kalman_params.A[0][1] == pytest.approx(0.05)
  assert radard.lead_prob_filters[0].dt == pytest.approx(0.05)


def test_radard_update_executes_isolated_accord_route(monkeypatch):
  toggles = SimpleNamespace(adjacent_lead_tracking=False, human_lane_changes=False)
  monkeypatch.setattr(radard_module, "get_starpilot_toggles", lambda sm=None: toggles)

  model = log.ModelDataV2.new_message()
  model.velocity.x = [10.0]
  model.init("leadsV3", 2)
  for lead, spec in zip(model.leadsV3, (LeadSpec(30.0, 0.0, 10.0), DEFAULT_SECOND_LEAD), strict=True):
    lead.x = [spec.d_rel + RADAR_TO_CAMERA]
    lead.y = [-spec.y_rel]
    lead.v = [spec.v_lead]
    lead.a = [spec.a_lead]
    lead.xStd = [spec.x_std]
    lead.yStd = [spec.y_std]
    lead.vStd = [spec.v_std]
    lead.prob = spec.probability

  radar_data = car.RadarData.new_message()
  radar_data.init("points", 1)
  radar_data.points[0].trackId = 42
  radar_data.points[0].dRel = 30.0
  radar_data.points[0].yRel = 0.0
  radar_data.points[0].vRel = 0.0
  radar_data.points[0].measured = True

  class FakeSubMaster:
    seen = {"modelV2": True}
    recv_frame = {"carState": 1, "liveTracks": 1}
    logMonoTime = {"modelV2": 1, "carState": 1}

    def __init__(self):
      self.data = {
        "modelV2": model.as_reader(),
        "carState": SimpleNamespace(vEgo=10.0, standstill=False),
      }

    def __getitem__(self, service):
      return self.data[service]

    @staticmethod
    def all_checks():
      return True

  radard = RadarD(radar_ts=0.05, mvl_accord_mode=True)
  radard.update(FakeSubMaster(), radar_data)
  assert radard.radar_state.leadOne.status
  assert radard.radar_state.leadOne.radarTrackId == 42
  assert radard.radar_state.leadOne.radar
  assert radard.tracks[42].mvl_accord_mode


def test_acceleration_tau_filter_decay_and_recovery():
  filt = FirstOrderFilter(MVL_ACCORD_LEAD_ACCEL_TAU, 0.45, DT_MDL)
  update_mvl_accord_accel_tau(filt, 1.0)
  decayed = filt.x
  update_mvl_accord_accel_tau(filt, 0.0)
  assert 0.0 < decayed < MVL_ACCORD_LEAD_ACCEL_TAU
  assert filt.x == pytest.approx(MVL_ACCORD_LEAD_ACCEL_TAU)


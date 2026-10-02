import pytest

from cereal import log
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import STOP_DISTANCE
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.controls.lib.longitudinal_vehicle_tunes import is_honda_accord_11g


def make_lead(*, d_rel, v_lead, a_lead=0.0, model_prob=1.0, radar=False, y_rel=0.0):
  lead = log.RadarState.LeadData.new_message()
  lead.status = True
  lead.dRel = d_rel
  lead.vLead = v_lead
  lead.vLeadK = v_lead
  lead.vRel = 0.0
  lead.aLeadK = a_lead
  lead.modelProb = model_prob
  lead.radar = radar
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

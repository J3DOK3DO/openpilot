import pytest

from openpilot.selfdrive.modeld.modeld import (
  accord11g_low_speed_lat_stabilizer_tau,
  get_car_lateral_smooth_seconds,
  get_lateral_smooth_seconds,
  should_stabilize_accord11g_low_speed_curvature,
  stabilize_accord11g_low_speed_curvature,
)


@pytest.mark.parametrize(("v_ego", "expected"), [
  (0.0, 0.4),
  (2.0, 0.4),
  (5.0, 0.2),
  (8.0, 0.0),
  (30.0, 0.0),
])
def test_lateral_smoothing_tapers_with_speed(v_ego, expected):
  assert get_lateral_smooth_seconds(v_ego, 0.4) == pytest.approx(expected)


@pytest.mark.parametrize("v_ego", [0.0, 5.0, 30.0])
def test_default_lateral_smoothing_is_disabled(v_ego):
  assert get_lateral_smooth_seconds(v_ego) == 0.0


@pytest.mark.parametrize("v_ego", [0.0, 5.0, 30.0])
def test_non_rivian_cars_keep_configured_starpilot_smoothing(v_ego):
  assert get_car_lateral_smooth_seconds("toyota", v_ego, 0.4) == 0.4


@pytest.mark.parametrize(("v_ego", "expected"), [
  (0.0, 0.4),
  (2.0, 0.4),
  (5.0, 0.2),
  (8.0, 0.0),
  (30.0, 0.0),
])
def test_subaru_uses_low_speed_configured_smoothing(v_ego, expected):
  assert get_car_lateral_smooth_seconds("subaru", v_ego, 0.4) == pytest.approx(expected)


@pytest.mark.parametrize(("v_ego", "maximum", "expected"), [
  (0.0, 0.4, 0.4),
  (5.0, 0.4, 0.2),
  (30.0, 0.4, 0.0),
  (0.0, 0.0, 0.0),
])
def test_rivian_uses_configured_smoothing(v_ego, maximum, expected):
  assert get_car_lateral_smooth_seconds("rivian", v_ego, maximum) == pytest.approx(expected)


@pytest.mark.parametrize(("v_ego", "expected"), [
  (0.0, 0.15),
  (4.0, 0.15),
  (7.0, 0.075),
  (10.0, 0.0),
  (20.0, 0.0),
])
def test_accord11g_low_speed_stabilizer_tau(v_ego, expected):
  assert accord11g_low_speed_lat_stabilizer_tau(v_ego) == pytest.approx(expected)


def test_accord11g_low_speed_stabilizer_bypasses_real_curve_or_disabled_context():
  assert stabilize_accord11g_low_speed_curvature(0.004, 0.0002, 3.0, True) == pytest.approx(0.004)
  assert stabilize_accord11g_low_speed_curvature(-0.0008, 0.0008, 3.0, False) == pytest.approx(-0.0008)
  assert stabilize_accord11g_low_speed_curvature(-0.0008, 0.0008, 12.0, True) == pytest.approx(-0.0008)


def _sign_flips(values, threshold=0.00035):
  previous = 0
  flips = 0
  for value in values:
    sign = 1 if value > threshold else -1 if value < -threshold else 0
    if sign:
      if previous and sign != previous:
        flips += 1
      previous = sign
  return flips


def test_accord11g_c6_oct1_seg32_pingpong_replay_reduces_sign_reversals():
  # Oct 1 route 000000cb--adeb582aef seg32, strongest C5-D ping-pong
  # window (~8-13 km/h). These are the recorded modelActionCurvature samples.
  road = [
    (2.213085, 0.000287592), (2.266988, 0.000440450), (2.430024, 0.000634701),
    (2.433647, 0.000146949), (2.429543, -0.000354504), (2.527862, -0.001405525),
    (2.648210, -0.001522960), (2.752282, -0.001382154), (2.847137, -0.000546234),
    (2.946123, -0.000098262), (3.032699, 0.000335404), (3.118709, 0.000359983),
    (3.204751, 0.000091786), (3.295130, -0.000492499), (3.376087, -0.001060580),
    (3.436447, -0.001387405), (3.442858, -0.001496377), (3.400854, -0.000935796),
    (3.403718, -0.000522982), (3.461638, 0.000110145), (3.450036, 0.000390970),
    (3.385496, 0.000464771), (3.375043, 0.000295702), (3.358813, -0.000297150),
    (3.342357, -0.001020323), (3.330564, -0.001787569), (3.316691, -0.001970968),
    (3.305838, -0.001619138), (3.292786, -0.000838697), (3.278529, -0.000148443),
    (3.263940, 0.000209805), (3.253693, 0.000410058), (3.292045, 0.000838618),
    (3.335603, 0.001107145), (3.406668, 0.001056454), (3.352998, 0.000624976),
    (3.385938, -0.000116059), (3.445464, -0.000439571), (3.499193, -0.000238567),
    (3.539886, 0.000013930), (3.581754, 0.000358542), (3.620120, 0.000722058),
    (3.662159, 0.000829547),
  ]

  filtered = []
  previous = road[0][1]
  for v_ego, curvature in road:
    previous = stabilize_accord11g_low_speed_curvature(curvature, previous, v_ego, True)
    filtered.append(previous)

  assert _sign_flips([curvature for _, curvature in road]) == 8
  assert _sign_flips(filtered) <= 2
  assert max(abs(value) for value in filtered) < max(abs(curvature) for _, curvature in road)


@pytest.mark.parametrize(("fingerprint", "lat_active", "steering_pressed", "left_blinker", "right_blinker", "lane_change_active", "expected"), [
  ("HONDA_ACCORD_11G", True, False, False, False, False, True),
  ("HONDA_CIVIC", True, False, False, False, False, False),
  ("HONDA_ACCORD_11G", False, False, False, False, False, False),
  ("HONDA_ACCORD_11G", True, True, False, False, False, False),
  ("HONDA_ACCORD_11G", True, False, True, False, False, False),
  ("HONDA_ACCORD_11G", True, False, False, True, False, False),
  ("HONDA_ACCORD_11G", True, False, False, False, True, False),
])
def test_accord11g_low_speed_stabilizer_runtime_scope(
  fingerprint, lat_active, steering_pressed, left_blinker, right_blinker, lane_change_active, expected,
):
  assert should_stabilize_accord11g_low_speed_curvature(
    fingerprint, lat_active, steering_pressed, left_blinker, right_blinker, lane_change_active,
  ) is expected

from dataclasses import dataclass
import sys
import types
from types import SimpleNamespace

from cereal import car, log, messaging
import numpy as np
import pytest

from opendbc.car.honda.values import CAR as HONDA_CAR
from opendbc.car.toyota.values import CAR as TOYOTA_CAR
from openpilot.selfdrive.controls.lib.drive_helpers import clip_curvature
from openpilot.selfdrive.controls.lib.lane_centering import LaneCenteringController
from openpilot.selfdrive.controls.lib.mvl_accord_lateral import (
  MVL_ACCORD_TWITCH_GUARD_DURATION,
  apply_mvl_accord_takeoff_guard,
  limit_mvl_accord_curvature_to_plan,
  scale_mvl_action_curvature,
  update_mvl_accord_twitch_guard,
)
from openpilot.selfdrive.controls.lib.mvl_accord_longitudinal import is_mvl_accord
from openpilot.selfdrive.locationd import lagd
from openpilot.selfdrive.locationd.lagd import (
  BLOCK_NUM_NEEDED,
  LateralLagEstimator,
  MAX_LAG,
  MVL_ACCORD_MIN_LAG,
  MVL_ACCORD_MIN_VEGO,
  retrieve_initial_lag,
)


def _path(curvature: float = 0.0, reach: float = 20.0, points: int = 41):
  xs = np.linspace(0.0, reach, points)
  ys = 0.5 * curvature * xs ** 2
  return SimpleNamespace(x=xs, y=ys, yStd=np.full_like(xs, 0.1))


def _model(curvature: float = 0.0, reach: float = 20.0, lane_change: int = 0,
           left: float = -1.8, right: float = 1.8, lane_prob: float = 0.9,
           lane_std: float = 0.1, path_std: float = 0.1):
  position = _path(curvature, reach)
  position.yStd = np.full_like(position.x, path_std)
  lane_x = np.linspace(0.0, max(reach, 50.0), 52)

  def lane(y):
    return SimpleNamespace(x=lane_x.copy(), y=np.full_like(lane_x, y), yStd=np.full_like(lane_x, 0.1))

  return SimpleNamespace(
    position=position,
    laneLines=[lane(0.0), lane(left), lane(right), lane(0.0)],
    laneLineProbs=[0.0, lane_prob, lane_prob, 0.0],
    laneLineStds=[0.0, lane_std, lane_std, 0.0],
    meta=SimpleNamespace(laneChangeState=lane_change),
  )


def _guard(model, curvature: float, v_ego: float, remaining: float = MVL_ACCORD_TWITCH_GUARD_DURATION,
           blinker: bool = False, turn_hold: bool = False, lane_change: bool = False,
           lat_active: bool = True):
  return apply_mvl_accord_takeoff_guard(model, curvature, v_ego, remaining, blinker, turn_hold, lane_change, lat_active)


@pytest.mark.parametrize(
  ("v_ego", "expected"),
  [(0.0, 0.12), (0.5, 0.12), (1.0, 0.12), (2.0, 0.03), (3.0, 0.12 / 9.0),
   (4.0, 0.0075), (10.0, 0.0012), (30.0, 0.12 / 900.0)],
)
def test_v15_v16_action_scaling_is_applied_exactly_once(v_ego, expected):
  assert scale_mvl_action_curvature(0.12, v_ego) == pytest.approx(expected)


@pytest.mark.parametrize("generation", ["v15", "v16"])
def test_model_action_api_uses_validated_accord_scaling(monkeypatch, generation):
  fake_commonmodel = types.ModuleType("openpilot.selfdrive.modeld.models.commonmodel_pyx")
  fake_commonmodel.DrivingModelFrame = object
  fake_commonmodel.CLContext = object
  monkeypatch.setitem(sys.modules, fake_commonmodel.__name__, fake_commonmodel)
  from openpilot.selfdrive.modeld import modeld

  previous = log.ModelDataV2.Action.new_message()
  previous.desiredCurvature = 0.05
  previous.desiredAcceleration = 0.0
  action = modeld.get_action_from_model(
    {"action": np.array([[0.12, 0.0]], dtype=np.float32)}, previous,
    lat_action_t=0.2, long_action_t=0.5, v_ego=2.0, mlsim=True,
    is_v9=False, is_v14=False, is_v15=generation == "v15",
    starpilot_toggles=SimpleNamespace(vEgoStopping=0.3),
    lat_smooth_seconds=0.0, long_smooth_seconds=0.0,
    mvl_accord_mode=True, is_v16=generation == "v16",
  )
  assert action.desiredCurvature == pytest.approx(0.03)


def test_model_action_holds_previous_curvature_at_zero_speed(monkeypatch):
  fake_commonmodel = types.ModuleType("openpilot.selfdrive.modeld.models.commonmodel_pyx")
  fake_commonmodel.DrivingModelFrame = object
  fake_commonmodel.CLContext = object
  monkeypatch.setitem(sys.modules, fake_commonmodel.__name__, fake_commonmodel)
  from openpilot.selfdrive.modeld import modeld

  previous = log.ModelDataV2.Action.new_message()
  previous.desiredCurvature = 0.017
  action = modeld.get_action_from_model(
    {"action": np.array([[0.12, 0.0]], dtype=np.float32)}, previous,
    0.2, 0.5, 0.0, True, False, False, False, SimpleNamespace(vEgoStopping=0.3),
    lat_smooth_seconds=0.0, long_smooth_seconds=0.0, mvl_accord_mode=True, is_v16=True,
  )
  assert action.desiredCurvature == pytest.approx(previous.desiredCurvature)


def test_takeoff_guard_straight_launch_rejects_action_spike():
  assert _guard(_model(0.0), 0.05, 1.0) == pytest.approx(0.002)


def test_takeoff_guard_preserves_slight_and_sharp_real_curves():
  assert _guard(_model(0.01), 0.015, 1.0) == pytest.approx(0.015)
  assert _guard(_model(0.08), 0.08, 1.0) == pytest.approx(0.08)


@pytest.mark.parametrize("bypass", ["blinker", "turn_hold", "lane_change"])
def test_takeoff_guard_stands_down_for_maneuver_intent(bypass):
  kwargs = {"blinker": False, "turn_hold": False, "lane_change": False}
  kwargs[bypass] = True
  assert _guard(_model(0.0), 0.05, 1.0, **kwargs) == pytest.approx(0.05)


def test_takeoff_guard_stands_down_while_lateral_control_is_inactive():
  assert _guard(_model(0.0), 0.05, 1.0, lat_active=False) == pytest.approx(0.05)


def test_takeoff_guard_fades_out_and_ends():
  assert _guard(_model(0.0), 0.05, 3.5) == pytest.approx(0.026)
  assert _guard(_model(0.0), 0.05, 4.0) == pytest.approx(0.05)
  assert _guard(_model(0.0), 0.05, 1.0, remaining=0.0) == pytest.approx(0.05)


def test_takeoff_guard_rejects_invalid_or_short_plan_as_a_clamp_source():
  short = _model(0.0, reach=8.0)
  invalid = _model(0.0)
  invalid.position.y[4] = np.nan
  missing = SimpleNamespace(position=SimpleNamespace(x=[], y=[]))
  assert _guard(short, 0.05, 1.0) == pytest.approx(0.05)
  assert _guard(invalid, 0.05, 1.0) == pytest.approx(0.05)
  assert _guard(missing, 0.05, 1.0) == pytest.approx(0.05)


def test_takeoff_guard_preserves_action_direction_when_limiting():
  assert limit_mvl_accord_curvature_to_plan(_model(0.01), -0.08, 1.0) < 0.0
  assert abs(limit_mvl_accord_curvature_to_plan(_model(0.01), -0.08, 1.0)) < 0.08


def test_takeoff_guard_timer_rearms_only_at_a_stop():
  remaining = update_mvl_accord_twitch_guard(0.0, 0.0, True)
  assert remaining == pytest.approx(MVL_ACCORD_TWITCH_GUARD_DURATION)
  for _ in range(150):
    remaining = update_mvl_accord_twitch_guard(remaining, 1.0, False)
  assert remaining == pytest.approx(0.0)
  assert update_mvl_accord_twitch_guard(remaining, 1.0, False) == 0.0
  assert update_mvl_accord_twitch_guard(remaining, 0.0, True) == pytest.approx(MVL_ACCORD_TWITCH_GUARD_DURATION)


def _lane_center_output(model, raw: float = 0.01, offset: float = 0.0, authority: float = 0.0,
                        enabled: bool = True, active: bool = True, valid: bool = True,
                        speed: float = 20.0, pause: bool = False, signal: bool = False):
  controller = LaneCenteringController()
  output = raw
  for _ in range(300):
    output = controller.update(raw, model, speed, enabled, offset, authority, active, valid, pause, signal)
  return output


def test_lane_centering_remains_after_accord_raw_curvature():
  right = _lane_center_output(_model(left=-1.5, right=2.1))
  left = _lane_center_output(_model(left=-2.1, right=1.5))
  assert right > 0.01
  assert left < 0.01


def test_lane_centering_zero_weak_disabled_and_low_speed_cases():
  raw = 0.01
  assert _lane_center_output(_model(), raw) == pytest.approx(raw)
  assert _lane_center_output(_model(left=-1.5, right=2.1, lane_prob=0.2), raw) == pytest.approx(raw)
  assert _lane_center_output(_model(left=-1.5, right=2.1), raw, enabled=False) == pytest.approx(raw)
  assert _lane_center_output(_model(left=-1.5, right=2.1), raw, speed=2.0) == pytest.approx(raw)


def test_lane_centering_signal_and_lane_change_gates_remain_native():
  raw = 0.01
  assert _lane_center_output(_model(left=-1.5, right=2.1), raw, pause=True, signal=True) == pytest.approx(raw)
  assert _lane_center_output(_model(left=-1.5, right=2.1, lane_change=1), raw) == pytest.approx(raw)


def _cp(fingerprint=HONDA_CAR.HONDA_ACCORD_11G, delay=0.3):
  return car.CarParams(carFingerprint=fingerprint, steerActuatorDelay=delay)


def _estimator(fingerprint=HONDA_CAR.HONDA_ACCORD_11G):
  estimator = LateralLagEstimator(_cp(fingerprint), 0.05)
  estimator.starpilot_toggles = SimpleNamespace(use_custom_steerActuatorDelay=False, steerActuatorDelay=0.0)
  return estimator


def test_accord_delay_initialization_and_learning_scope():
  estimator = _estimator()
  assert estimator.mvl_accord_mode
  assert estimator.initial_lag == pytest.approx(0.5)
  assert estimator.min_vego == pytest.approx(MVL_ACCORD_MIN_VEGO)
  msg = estimator.get_msg(True)
  assert msg.liveDelay.status == "unestimated"
  assert msg.liveDelay.lateralDelay == pytest.approx(0.5)
  assert msg.liveDelay.lateralDelayEstimate == pytest.approx(0.5)


@pytest.mark.parametrize(("learned", "expected"), [(0.10, 0.15), (0.15, 0.15), (0.30, 0.30), (0.65, 0.65), (0.80, 0.65)])
def test_accord_published_delay_is_bounded(learned, expected):
  estimator = _estimator()
  estimator.block_avg.values[:] = learned
  estimator.block_avg.valid_blocks = BLOCK_NUM_NEEDED
  msg = estimator.get_msg(True)
  assert msg.liveDelay.status == "estimated"
  assert msg.liveDelay.lateralDelay == pytest.approx(expected)


def test_accord_ignores_custom_delay_override_and_falls_back_when_invalid():
  estimator = _estimator()
  estimator.starpilot_toggles = SimpleNamespace(use_custom_steerActuatorDelay=True, steerActuatorDelay=0.01)
  assert estimator.get_msg(True).liveDelay.lateralDelay == pytest.approx(0.5)
  estimator.block_avg.values[:BLOCK_NUM_NEEDED, 0] = np.linspace(0.15, 0.65, BLOCK_NUM_NEEDED)
  estimator.block_avg.valid_blocks = BLOCK_NUM_NEEDED
  msg = estimator.get_msg(True)
  assert msg.liveDelay.status == "invalid"
  assert msg.liveDelay.lateralDelay == pytest.approx(0.5)


def test_generic_delay_behavior_is_unchanged():
  estimator = _estimator(HONDA_CAR.HONDA_CRV_6G)
  estimator.starpilot_toggles = SimpleNamespace(use_custom_steerActuatorDelay=True, steerActuatorDelay=0.27)
  assert not estimator.mvl_accord_mode
  assert estimator.min_vego == pytest.approx(lagd.MIN_VEGO)
  assert estimator.get_msg(True).liveDelay.lateralDelay == pytest.approx(0.27)


class FakeParams:
  def __init__(self, data):
    self.data = data
    self.removed = []

  def get(self, key):
    return self.data.get(key)

  def remove(self, key):
    self.removed.append(key)
    self.data.pop(key, None)


@pytest.mark.parametrize(("cached", "accepted"), [(0.15, True), (0.30, True), (0.65, True), (0.149, False), (0.651, False)])
def test_accord_delay_cache_range_guard(cached, accepted):
  cp = _cp()
  event = messaging.new_message("liveDelay")
  event.liveDelay.status = "estimated"
  event.liveDelay.lateralDelayEstimate = cached
  event.liveDelay.validBlocks = 3
  params = FakeParams({"LiveDelay": event.to_bytes(), "CarParamsPrevRoute": cp.to_bytes()})
  result = retrieve_initial_lag(params, cp)
  if accepted:
    assert result == pytest.approx((cached, 3))
    assert not params.removed
  else:
    assert result is None
    assert params.removed == ["LiveDelay"]


def test_accord_delay_search_excludes_below_minimum_peak():
  dt = 0.05
  signal = np.sin(np.arange(400) * 0.17) + 0.3 * np.sin(np.arange(400) * 0.037)
  actual = np.roll(signal, 1)
  mask = np.ones(signal.size, dtype=bool)
  delay, _, _ = LateralLagEstimator.actuator_delay(signal, actual, mask, dt, MAX_LAG, MVL_ACCORD_MIN_LAG)
  assert MVL_ACCORD_MIN_LAG <= delay <= MAX_LAG


@dataclass(frozen=True)
class DifferentialScenario:
  name: str
  raw: float
  v_ego: float
  path_curvature: float = 0.0
  previous: float = 0.0
  lane_correction: float = 0.0
  remaining: float = 0.0
  blinker: bool = False
  lane_change: bool = False
  expected_safety_improvement: bool = False


DIFFERENTIAL_SCENARIOS = (
  DifferentialScenario("straight lane zero curvature", 0.0, 15.0),
  DifferentialScenario("constant gentle curve", 0.003, 15.0, 0.003),
  DifferentialScenario("constant stronger curve", 0.01, 15.0, 0.01),
  DifferentialScenario("curvature ramp left", -0.008, 12.0, -0.008, -0.004),
  DifferentialScenario("curvature ramp right", 0.008, 12.0, 0.008, 0.004),
  DifferentialScenario("sinusoidal curvature", -0.006, 20.0, -0.006, 0.006),
  DifferentialScenario("low speed straight launch", 0.0, 1.0, remaining=1.5),
  DifferentialScenario("low speed noisy action launch", 0.05, 1.0, remaining=1.5, expected_safety_improvement=True),
  DifferentialScenario("low speed genuine turn", 0.08, 1.0, 0.08, remaining=1.5),
  DifferentialScenario("lane center correction left", 0.005, 15.0, lane_correction=-0.001),
  DifferentialScenario("lane center correction right", 0.005, 15.0, lane_correction=0.001),
  DifferentialScenario("lane centering disabled", 0.005, 15.0),
  DifferentialScenario("blinker active", 0.05, 1.0, remaining=1.5, blinker=True),
  DifferentialScenario("lane change", 0.05, 1.0, remaining=1.5, lane_change=True),
  DifferentialScenario("turn hold bypass", 0.04, 2.0, 0.04, remaining=1.5, blinker=True),
  DifferentialScenario("delay 0.15", 0.004, 10.0),
  DifferentialScenario("delay 0.30", 0.004, 10.0),
  DifferentialScenario("delay 0.65", 0.004, 10.0),
  DifferentialScenario("attempted delay below bound", 0.004, 10.0),
  DifferentialScenario("attempted delay above bound", 0.004, 10.0),
  DifferentialScenario("startup before valid learned delay", 0.004, 10.0),
  DifferentialScenario("model v15 action", 0.03, 2.0, 0.03),
  DifferentialScenario("model v16 action", 0.03, 2.0, 0.03),
  DifferentialScenario("large raw action at low speed", 0.12, 2.0, 0.12, remaining=1.5),
  DifferentialScenario("straight path noisy action", 0.08, 1.0, remaining=1.5, expected_safety_improvement=True),
  DifferentialScenario("matching high path and action", 0.08, 1.0, 0.08, remaining=1.5),
  DifferentialScenario("invalid path safety handling", 0.04, 1.0, remaining=0.0),
  DifferentialScenario("highway speed curve", 0.003, 30.0, 0.003),
  DifferentialScenario("stop then launch", 0.05, 1.0, 0.05, remaining=1.5),
  DifferentialScenario("repeated stop launch straight", 0.05, 1.0, remaining=1.5, expected_safety_improvement=True),
)


@pytest.mark.parametrize("scenario", DIFFERENTIAL_SCENARIOS, ids=lambda scenario: scenario.name)
def test_validated_accord07_differential(scenario):
  model = _model(scenario.path_curvature, lane_change=int(scenario.lane_change))
  guarded = _guard(model, scenario.raw, scenario.v_ego, scenario.remaining,
                   blinker=scenario.blinker, lane_change=scenario.lane_change)
  historical, _ = clip_curvature(scenario.v_ego, scenario.previous,
                                 scenario.raw + scenario.lane_correction, 0.0, 1.0)
  actual, _ = clip_curvature(scenario.v_ego, scenario.previous,
                             guarded + scenario.lane_correction, 0.0, 1.0)
  if scenario.expected_safety_improvement:
    assert abs(actual) < abs(historical)
  else:
    assert actual == pytest.approx(historical)


@pytest.mark.parametrize(
  "fingerprint",
  [HONDA_CAR.HONDA_CRV_6G, HONDA_CAR.HONDA_CIVIC_BOSCH,
   HONDA_CAR.HONDA_CIVIC_2022, HONDA_CAR.HONDA_ODYSSEY, TOYOTA_CAR.TOYOTA_RAV4],
)
def test_non_accord_platforms_do_not_select_accord_lateral_route(fingerprint):
  assert not is_mvl_accord(SimpleNamespace(carFingerprint=fingerprint))


def test_exact_accord_selects_lateral_route():
  assert is_mvl_accord(SimpleNamespace(carFingerprint=HONDA_CAR.HONDA_ACCORD_11G))

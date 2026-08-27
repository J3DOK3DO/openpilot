"""Validated Accord 11G lateral model helpers isolated from generic StarPilot policy."""

import math

from openpilot.common.realtime import DT_CTRL


MVL_ACCORD_TWITCH_GUARD_MAX_SPEED = 4.0
MVL_ACCORD_TWITCH_GUARD_FADE_SPEED = 3.0
MVL_ACCORD_TWITCH_GUARD_DURATION = 1.5
MVL_ACCORD_TWITCH_GUARD_PLAN_RATIO = 4.0
MVL_ACCORD_TWITCH_GUARD_FLOOR = 0.002
MVL_ACCORD_TWITCH_GUARD_STRAIGHT_LO = 0.005
MVL_ACCORD_TWITCH_GUARD_STRAIGHT_HI = 0.014
MVL_ACCORD_TWITCH_GUARD_MIN_REACH = 12.0
MVL_ACCORD_TWITCH_GUARD_LOOKAHEAD = 7.0


def scale_mvl_action_curvature(raw_action: float, v_ego: float) -> float:
  """Scale v15/v16 lateral acceleration action into curvature exactly once."""
  return float(raw_action) / max(1.0, float(v_ego)) ** 2


def update_mvl_accord_twitch_guard(remaining: float, v_ego: float, standstill: bool) -> float:
  if not (math.isfinite(remaining) and math.isfinite(v_ego)):
    return 0.0
  if standstill or abs(v_ego) <= 0.3:
    return MVL_ACCORD_TWITCH_GUARD_DURATION
  return max(remaining - DT_CTRL, 0.0)


def _plan_positions(model_v2):
  try:
    xs = tuple(float(x) for x in model_v2.position.x)
    ys = tuple(float(y) for y in model_v2.position.y)
  except (AttributeError, TypeError, ValueError, OverflowError):
    return None
  if len(xs) != len(ys) or not xs or not all(math.isfinite(x) and math.isfinite(y) for x, y in zip(xs, ys, strict=True)):
    return None
  return xs, ys


def _plan_circle_curvature(xs, ys, lookahead: float) -> float:
  px, py = 0.0, 0.0
  for x, y in zip(xs, ys, strict=True):
    px, py = x, y
    if math.hypot(x, y) >= lookahead:
      break
  denom = px * px + py * py
  return 0.0 if denom < 1e-6 else 2.0 * py / denom


def limit_mvl_accord_curvature_to_plan(model_v2, curvature: float, v_ego: float) -> float:
  """Reject only an implausible pull-away action spike against a valid straighter path."""
  if not (math.isfinite(curvature) and math.isfinite(v_ego)):
    return curvature
  if v_ego >= MVL_ACCORD_TWITCH_GUARD_MAX_SPEED or curvature == 0.0:
    return curvature

  positions = _plan_positions(model_v2)
  if positions is None:
    return curvature
  xs, ys = positions
  reach = xs[-1]
  if not math.isfinite(reach) or reach < MVL_ACCORD_TWITCH_GUARD_MIN_REACH:
    return curvature

  plan = abs(_plan_circle_curvature(xs, ys, MVL_ACCORD_TWITCH_GUARD_LOOKAHEAD))
  straightness = ((plan - MVL_ACCORD_TWITCH_GUARD_STRAIGHT_LO) /
                  (MVL_ACCORD_TWITCH_GUARD_STRAIGHT_HI - MVL_ACCORD_TWITCH_GUARD_STRAIGHT_LO))
  limit = max(MVL_ACCORD_TWITCH_GUARD_PLAN_RATIO * plan * min(max(straightness, 0.0), 1.0),
              MVL_ACCORD_TWITCH_GUARD_FLOOR)
  if abs(curvature) <= limit:
    return curvature

  fade = ((MVL_ACCORD_TWITCH_GUARD_MAX_SPEED - v_ego) /
          (MVL_ACCORD_TWITCH_GUARD_MAX_SPEED - MVL_ACCORD_TWITCH_GUARD_FADE_SPEED))
  fade = min(max(fade, 0.0), 1.0)
  return curvature + (math.copysign(limit, curvature) - curvature) * fade


def apply_mvl_accord_takeoff_guard(model_v2, curvature: float, v_ego: float, remaining: float,
                                   blinker_active: bool, turn_hold_active: bool,
                                   lane_change_active: bool, lat_active: bool = True) -> float:
  if not lat_active or remaining <= 0.0 or blinker_active or turn_hold_active or lane_change_active:
    return curvature
  return limit_mvl_accord_curvature_to_plan(model_v2, curvature, v_ego)

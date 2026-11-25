"""Bounded numerical references; values are descriptive acceleration in m/s².

These functions are not C6/MVL/C19 solver or controller ports. They deliberately
have no state outside an explicitly supplied LeadMemory instance.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


def clip(value: float, lower: float, upper: float) -> float:
  return min(upper, max(lower, value))


@dataclass(frozen=True)
class LeadMemory:
  track_id: str | None = None
  last_ns: int | None = None
  hold_until_ns: int = 0


@dataclass(frozen=True)
class ReferenceResult:
  accel: float
  brake_hold: bool
  lead_transition: bool
  standstill: bool
  driver_override: bool
  lead_fresh: bool
  reason: str
  memory: LeadMemory


@dataclass(frozen=True)
class ResponseFactors:
  gas: float = 1.0
  wind: float = 1.0


def lead_is_fresh(row: dict) -> bool:
  lead = row.get("lead")
  return bool(lead and lead.get("valid") is True and
              type(lead.get("t_ns")) is int and
              0 <= row["t_ns"] - lead["t_ns"] <= 200_000_000)


def c6_track_window(v_ego: float, distance: float, lead_speed: float, *, radar: bool,
                    model_length: float = 192.0, stop_distance: float = 6.0) -> bool:
  """C6 should_track_lead window with explicit finite bounds; no track continuity."""
  if not all(math.isfinite(x) for x in (v_ego, distance, lead_speed, model_length, stop_distance)):
    return False
  if not 0 <= v_ego <= 80 or not 0 <= lead_speed <= 80 or not 0 <= distance <= 300:
    return False
  buffer = max(clip(stop_distance, 0, 20), 4.0)
  model_limit = clip(model_length, 0, 250) + buffer
  if radar:
    return distance < model_limit
  closing = max(0.0, v_ego - lead_speed)
  gap = 1.75 + min(0.2 * closing, 2.5)
  return distance < min(model_limit, max(25.0, v_ego * gap + buffer))


def close_lead_decel(v_ego: float, distance: float, lead_speed: float, follow_s: float = 1.8) -> float:
  """Kinematic close-lead reference, not C6's calibrated MPC intervention."""
  closing = max(0.0, v_ego - lead_speed)
  desired = max(5.0, follow_s * max(v_ego, 0.0))
  available = max(1.0, distance - desired)
  return clip(closing * closing / (2.0 * available), 0.0, 4.0)


def mvl_coast_reference(pitch_rad: float) -> float:
  """Exact scalar expression in MVL planner get_coast_accel; bounded input."""
  if not math.isfinite(pitch_rad) or abs(pitch_rad) > 0.4:
    raise ValueError("pitch outside declared research range")
  return -5.65 * math.sin(pitch_rad) - 0.3


def mvl_wind_reference(speed_mps: float) -> float:
  """Paired MVL Honda controller wind table; not an Accord calibration."""
  if not math.isfinite(speed_mps) or not 0 <= speed_mps <= 80:
    raise ValueError("speed outside declared research range")
  x = (0.0, 13.4, 22.4, 31.3, 40.2)
  y = (0.0, 0.049, 0.136, 0.267, 0.441)
  if speed_mps >= x[-1]:
    return y[-1]
  for i in range(1, len(x)):
    if speed_mps <= x[i]:
      return y[i-1] + (y[i]-y[i-1]) * (speed_mps-x[i-1]) / (x[i]-x[i-1])
  raise AssertionError("unreachable")


def response_reference(speed_mps: float, pitch_rad: float, observed_accel: float,
                       gas_proxy: float | None) -> dict:
  """Illustrative response residual; gas_proxy is dimensionless, never CAN gas.

  The controller's gasfactor/windfactor adaptation cannot be reconstructed from
  these signals. The residual has no vehicle calibration or actuator meaning.
  """
  if not math.isfinite(observed_accel) or not -12 <= observed_accel <= 8:
    raise ValueError("acceleration outside declared research range")
  if gas_proxy is not None and (not math.isfinite(gas_proxy) or not 0 <= gas_proxy <= 1):
    raise ValueError("gas proxy outside [0,1]")
  coast = mvl_coast_reference(pitch_rad)
  wind = mvl_wind_reference(speed_mps)
  return {"coast_mps2": coast, "wind_mps2": wind,
          "grade_component_mps2": -5.65 * math.sin(pitch_rad),
          "gas_proxy": gas_proxy,
          "observed_minus_coast_mps2": observed_accel - coast,
          "model_equivalence": False}


def mvl_factor_reference(desired_accel: float, observed_accel: float, speed_mps: float,
                         pitch_rad: float, factors: ResponseFactors, *, min_gas_mps2: float,
                         active: bool, driver_override: bool) -> ResponseFactors:
  """Bounded counterfactual of paired MVL Bosch gas/wind learning terms.

  The original requires controller state, lookup breakpoints, PID mode and
  saturation history. Those are absent here, so this is a comparison only.
  No gas request or controller value is returned.
  """
  if not all(math.isfinite(x) for x in (desired_accel, observed_accel, min_gas_mps2,
                                       factors.gas, factors.wind)):
    raise ValueError("nonfinite response input")
  if not (-12 <= desired_accel <= 8 and -12 <= observed_accel <= 8 and
          -4 <= min_gas_mps2 <= 4 and 0.01 <= factors.gas <= 3 and 0.1 <= factors.wind <= 3):
    raise ValueError("response input outside bounds")
  wind = mvl_wind_reference(speed_mps)
  grade = math.sin(pitch_rad) * 9.81 if abs(pitch_rad) <= 0.4 else float("nan")
  if not math.isfinite(grade):
    raise ValueError("pitch outside bounds")
  if not active or driver_override:
    return factors
  error = desired_accel - observed_accel
  force = desired_accel + wind * factors.wind + grade
  gas_factor = factors.gas
  wind_factor = factors.wind
  if error != 0 and force > min_gas_mps2:
    gas_factor = clip(gas_factor + error / 50.0 * (force - min_gas_mps2), 0.01, 3.0)
  if error != 0 and speed_mps > 0:
    adjustment = 1.0 + wind / 1000.0
    wind_factor = clip(wind_factor * (adjustment if error > 0 else 1.0 / adjustment), 0.1, 3.0)
  return ResponseFactors(gas_factor, wind_factor)


def step(row: dict, strategy: str, memory: LeadMemory = LeadMemory()) -> ReferenceResult:
  """Compare bounded behavioral references against the same observed row.

  Raw observed braking, stock AEB, and driver braking are never relaxed by a
  reference calculation. This is only an analysis guard, not a safety claim.
  """
  if strategy not in ("c19_behavioral", "c6_behavioral"):
    raise ValueError("unknown reference strategy")
  t = row["t_ns"]
  lead = row.get("lead") if lead_is_fresh(row) else None
  fresh = lead is not None
  track_id = lead["track_id"] if lead else None
  transition = memory.track_id != track_id and (memory.track_id is not None or track_id is not None)
  if transition or not fresh:
    memory = LeadMemory()
  standstill = row["v_ego"] < 0.25
  driver_override = row["gas_pressed"] or row["brake_pressed"]
  accel = clip((row["v_cruise"] - row["v_ego"]) * 0.4, -2.0, 1.2)
  reason = "cruise_reference"
  hold = False
  if fresh:
    v, d, vl = row["v_ego"], lead["distance"], lead["speed"]
    tracked = c6_track_window(v, d, vl, radar=lead["radar"])
    if tracked:
      follow = 1.8 if strategy == "c6_behavioral" else 2.0
      deficit = max(0.0, (follow * v + 5.0 - d) / max(v, 1.0))
      demand = close_lead_decel(v, d, vl, follow)
      accel = min(accel, -clip(0.45 * deficit + demand, 0.0, 4.0))
      reason = "tracked_lead_reference"
      if strategy == "c6_behavioral" and v < 1.0 and vl < 0.5 and d < 8.0:
        # Hold is tied to the present track ID; replacement resets memory.
        hold = True
        memory = LeadMemory(track_id, t, t + 300_000_000)
        accel = min(accel, -0.5)
        reason = "stopped_lead_reference"
    elif lead["radar"]:
      reason = "lead_outside_tracking_window"
  elif row.get("lead") is not None:
    reason = "stale_lead_ignored"
  if row["stock_aeb"]:
    accel = min(accel, row["raw_accel"], -2.0)
    reason = "stock_aeb_observed"
  elif row["brake_pressed"]:
    accel = min(accel, row["raw_accel"])
    reason = "driver_brake_observed"
  else:
    accel = min(accel, row["raw_accel"]) if row["raw_accel"] < -0.2 else accel
    if row["gas_pressed"]:
      reason = "driver_gas_override"
  if not hold:
    memory = LeadMemory(track_id, t if fresh else None, 0)
  return ReferenceResult(clip(accel, -12.0, 2.0), hold, transition, standstill,
                         driver_override, fresh, reason, memory)

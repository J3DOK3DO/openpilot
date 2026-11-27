"""Pure offline telemetry formatter. It has no process, transport, or control hook."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math


@dataclass(frozen=True)
class ShadowConfig:
  enabled: bool = False


@dataclass(frozen=True)
class HistoricalSample:
  t_ns: int
  measured_aego_mps2: float
  decoded_can_accel_mps2: float
  source_sha256: str


def observe(sample: HistoricalSample, config: ShadowConfig = ShadowConfig()) -> dict:
  """Return immutable-source observations only; no acceleration proposal is computed."""
  if not config.enabled:
    return {"status": "DISABLED", "advisory_only": True}
  if not isinstance(sample.t_ns, int) or sample.t_ns <= 0:
    return {"status": "FAILED_INPUT", "advisory_only": True}
  if (not all(math.isfinite(x) for x in (sample.measured_aego_mps2, sample.decoded_can_accel_mps2))
      or len(sample.source_sha256) != 64 or any(c not in "0123456789abcdef" for c in sample.source_sha256)):
    return {"status": "FAILED_INPUT", "advisory_only": True}
  return {"status": "HISTORICAL_UNVERIFIED", "advisory_only": True,
          "autonomous_braking": False, "t_ns": sample.t_ns,
          "measured_aego_mps2": sample.measured_aego_mps2,
          "decoded_historical_can_accel_mps2": sample.decoded_can_accel_mps2,
          "source_sha256": sample.source_sha256}


@dataclass(frozen=True)
class ShadowCycle:
  drive_id: str
  cycle_index: int
  reset_boundary: bool
  t_ns: int
  source_t_ns: int
  receipt_t_ns: int
  measured_aego_mps2: float
  source_sha256: str
  provenance: str = 'HISTORICAL_UNVERIFIED'


def serialize_observation(cycle: ShadowCycle, previous: ShadowCycle | None = None,
                          config: ShadowConfig = ShadowConfig(), max_age_ns: int = 200_000_000) -> bytes:
  """Canonical immutable bytes for an inert observation. Failures contain no signal."""
  def emit(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')

  if not config.enabled:
    return emit({'status': 'DISABLED', 'advisory_only': True})
  measured = None
  if type(cycle.measured_aego_mps2) in (int, float):
    try:
      measured = float(cycle.measured_aego_mps2)
    except (OverflowError, TypeError, ValueError):
      pass
  valid = (isinstance(cycle.drive_id, str) and bool(cycle.drive_id) and len(cycle.drive_id) <= 128
           and type(cycle.cycle_index) is int and cycle.cycle_index >= 0
           and type(cycle.reset_boundary) is bool
           and all(type(v) is int for v in (cycle.t_ns, cycle.source_t_ns, cycle.receipt_t_ns, max_age_ns))
           and 0 < cycle.source_t_ns <= cycle.receipt_t_ns <= cycle.t_ns
           and 0 <= cycle.t_ns - cycle.source_t_ns <= max_age_ns <= 1_000_000_000
           and measured is not None and math.isfinite(measured)
           and isinstance(cycle.source_sha256, str) and len(cycle.source_sha256) == 64
           and all(char in '0123456789abcdef' for char in cycle.source_sha256)
           and cycle.provenance in ('SIMULATED', 'HISTORICAL_UNVERIFIED'))
  if previous is None:
    valid = valid and cycle.reset_boundary and cycle.cycle_index == 0
  elif cycle.drive_id == previous.drive_id:
    valid = valid and not cycle.reset_boundary and cycle.cycle_index == previous.cycle_index + 1 and cycle.t_ns > previous.t_ns
  else:
    valid = valid and cycle.reset_boundary and cycle.cycle_index == 0
  if not valid:
    return emit({'status': 'FAILED_INPUT', 'advisory_only': True})
  return emit({'status': cycle.provenance, 'advisory_only': True, 'autonomous_braking': False,
               'drive_id': cycle.drive_id, 'cycle_index': cycle.cycle_index,
               'reset_boundary': cycle.reset_boundary, 't_ns': cycle.t_ns,
               'source_t_ns': cycle.source_t_ns, 'receipt_t_ns': cycle.receipt_t_ns,
               'max_age_ns': max_age_ns, 'measured_aego_mps2': measured,
               'source_sha256': cycle.source_sha256})

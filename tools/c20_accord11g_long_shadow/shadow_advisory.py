"""Pure offline telemetry formatter. It has no process, transport, or control hook."""
from __future__ import annotations

from dataclasses import dataclass
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

"""CLI for deterministic, read-only JSON telemetry comparisons.

No imports from car, CAN, controller, device, launcher, or native solver modules.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

try:
  from .admission import Status, admit, load_json_bytes, validate_rows
  from .policies import LeadMemory, response_reference, step
except ImportError:  # direct script invocation
  from admission import Status, admit, load_json_bytes, validate_rows
  from policies import LeadMemory, response_reference, step


def compare(rows: list[dict], *, mode: str = "SIMULATED", admission_status: str | None = None) -> dict:
  """Public comparison API accepts synthetic mode only.

  Recorded status is computed exclusively by compare_recorded from trace bytes.
  """
  if mode != "SIMULATED" or admission_status not in (None, Status.COMPATIBLE_BUT_UNVERIFIED.value):
    raise ValueError("use compare_recorded for recorded input")
  return _compare(rows, mode="SIMULATED", admission_status=Status.COMPATIBLE_BUT_UNVERIFIED.value)


def compare_recorded(trace_bytes: bytes, manifest: dict, trusted_reference: dict,
                     expected_reference_sha256: str) -> dict:
  admission = admit(manifest, trace_bytes, trusted_reference, expected_reference_sha256)
  if admission.status != Status.VERIFIED_MATCH:
    raise ValueError(f"recording rejected: {admission.status.value}: {'; '.join(admission.reasons)}")
  return _compare(load_json_bytes(trace_bytes), mode="RECORDED_VERIFIED", admission_status=admission.status.value)


def _compare(rows: list[dict], *, mode: str, admission_status: str) -> dict:
  errors = validate_rows(rows)
  if errors:
    raise ValueError("; ".join(errors))
  results = {}
  for strategy in ("c19_behavioral", "c6_behavioral"):
    memory = LeadMemory()
    output = []
    counts: Counter[str] = Counter()
    jerk_values: list[float] = []
    accel_errors: list[float] = []
    headways: list[float] = []
    signal_ages_ms: list[float] = []
    previous = None
    for row in rows:
      result = step(row, strategy, memory)
      memory = result.memory
      counts[result.reason] += 1
      counts["brake_hold"] += result.brake_hold
      counts["lead_transition"] += result.lead_transition
      counts["standstill"] += result.standstill
      counts["driver_override"] += result.driver_override
      counts["fresh_lead"] += result.lead_fresh
      counts["stale_lead"] += row["lead"] is not None and not result.lead_fresh
      counts["fresh_signal_rows"] += 1  # validate_rows already checked every source timestamp
      signal_ages_ms.extend((row["t_ns"] - source_ns) / 1e6 for source_ns in row["signal_t_ns"].values())
      if result.lead_fresh and row["v_ego"] >= 0.5:
        headways.append(row["lead"]["distance"] / row["v_ego"])
      accel_errors.append(result.accel - row["raw_accel"])
      if previous is not None:
        jerk_values.append((result.accel - previous[1]) / ((row["t_ns"] - previous[0]) / 1e9))
      previous = row["t_ns"], result.accel
      output.append({"t_ns": row["t_ns"], "accel_reference_mps2": round(result.accel, 6),
                     "brake_hold": result.brake_hold, "reason": result.reason,
                     "response": response_reference(row["v_ego"], row["pitch"], row["a_ego"], None)})
    n = len(rows)
    results[strategy] = {
      "classification": "behavioral reference, not native C19/C6 solver or control replay",
      "samples": n,
      "mean_headway_s": round(sum(headways) / len(headways), 6) if headways else None,
      "min_headway_s": round(min(headways), 6) if headways else None,
      "mean_abs_accel_demand_error_mps2": round(sum(abs(x) for x in accel_errors) / n, 6),
      "max_abs_jerk_mps3": round(max(map(abs, jerk_values)), 6) if jerk_values else None,
      "max_signal_age_ms": round(max(signal_ages_ms), 6),
      "counts": dict(sorted(counts.items())),
      "rows": output,
    }
  return {"mode": mode, "admission_status": admission_status,
          "claim": "descriptive telemetry only; no vehicle improvement or braking validation",
          "strategies": results}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("trace", type=Path, help="local JSON time-series")
  parser.add_argument("--synthetic", action="store_true", help="explicitly synthetic input")
  parser.add_argument("--manifest", type=Path, help="recording manifest")
  parser.add_argument("--trusted-reference", type=Path, help="independently authenticated identity record")
  parser.add_argument("--reference-sha256", help="expected canonical SHA-256 obtained independently")
  args = parser.parse_args()
  trace_bytes = args.trace.read_bytes()
  if args.synthetic:
    if args.manifest or args.trusted_reference or args.reference_sha256:
      parser.error("synthetic mode cannot use recording provenance")
    result = compare(load_json_bytes(trace_bytes))
  else:
    if not args.manifest or not args.trusted_reference or not args.reference_sha256:
      parser.error("recorded replay requires manifest, authenticated reference and independently obtained reference hash")
    manifest = load_json_bytes(args.manifest.read_bytes())
    reference = load_json_bytes(args.trusted_reference.read_bytes())
    try:
      result = compare_recorded(trace_bytes, manifest, reference, args.reference_sha256)
    except ValueError as exc:
      parser.error(str(exc))
  print(json.dumps(result, indent=2, sort_keys=True,
                   allow_nan=False))


if __name__ == "__main__":
  main()

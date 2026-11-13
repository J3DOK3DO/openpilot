"""Read-only CAN2 triage view of the existing full-snapshot offline summary."""
import argparse
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "c2_timeline_summary.json"
COUNTERS = ("totalRxCnt", "totalErrorCnt", "totalRxLostCnt", "busOffCnt", "canCoreResetCnt")


def summarize(source):
  data = json.loads(Path(source).read_text())
  limit = data["limit_per_second"]
  result = []
  for route in data["routes"]:
    deltas = route["observed_counter_delta_sum"]
    result.append({
      "route": route["route_index"],
      "decoded_segments": route["decoded_segments"],
      "peak_irq0": route["peak_irq0"],
      "above_limit": route["peak_irq0"] > limit,
      "high_rate_samples": route["high_rate_panda_samples"],
      "first_active_fault_ns": route["first_active_fault_ns"],
      "first_mismatch_ns": route["first_controls_mismatch_ns"],
      "observed_counter_delta_sum": {key: deltas[key] for key in COUNTERS},
    })
  return {"limit_per_second": limit, "routes": result,
          "caveat": "Counter sums are observed epoch deltas; IRQ includes RX and errors. No cause or wall-clock time inferred."}


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--summary", type=Path, default=DEFAULT)
  args = parser.parse_args()
  print(json.dumps(summarize(args.summary), indent=2))

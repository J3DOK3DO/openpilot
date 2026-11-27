"""Deterministic adversarial synthetic cases for the offline behavioral comparator."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .admission import load_json_bytes, validate_rows
from .policies import ResponseFactors, mvl_factor_reference
from .replay import compare

FIXTURE = Path(__file__).parent / "fixtures/synthetic_trace.json"


def cases() -> dict[str, list[dict]]:
  base = load_json_bytes(FIXTURE.read_bytes())
  result = {"baseline": base}
  def variant(name, changes):
    rows = copy.deepcopy(base)
    for index, fields in changes.items():
      for key, value in fields.items():
        if key.startswith("lead."):
          if rows[index]["lead"] is None:
            rows[index]["lead"] = copy.deepcopy(base[1]["lead"])
            rows[index]["lead"]["t_ns"] = rows[index]["t_ns"]
          rows[index]["lead"][key[5:]] = value
        else:
          rows[index][key] = value
    result[name] = rows
  variant("static_closing", {1: {"lead.distance": 25.0, "lead.speed": 0.0}, 2: {"lead.distance": 18.0, "lead.speed": 0.0}})
  variant("cut_in", {2: {"lead.track_id": "cut-in", "lead.distance": 8.0, "lead.speed": 10.0}})
  variant("phantom", {1: {"lead.radar": False, "lead.confidence": 0.01, "lead.distance": 200.0}})
  variant("override_aeb", {2: {"gas_pressed": True}, 3: {"stock_aeb": True, "raw_accel": -6.0}})
  variant("radar_loss", {2: {"lead": None}, 3: {"lead": None}})
  variant("grade", {1: {"pitch": 0.08}, 2: {"pitch": -0.08}})
  variant("stop_go", {1: {"v_ego": 0.1, "lead.distance": 5.0, "lead.speed": 0.0},
                      2: {"v_ego": 0.1, "lead.distance": 5.0, "lead.speed": 0.0},
                      3: {"v_ego": 0.5, "lead.distance": 9.0, "lead.speed": 2.0}})
  return result


def suite() -> dict:
  output = {}
  for name, rows in cases().items():
    replay = compare(rows)
    factors = ResponseFactors()
    for row, output_row in zip(rows, replay["strategies"]["c19_behavioral"]["rows"], strict=True):
      factors = mvl_factor_reference(output_row["accel_reference_mps2"], row["a_ego"], row["v_ego"],
                                     row["pitch"], factors, min_gas_mps2=0.0, active=True,
                                     driver_override=row["gas_pressed"] or row["brake_pressed"])
    output[name] = {"samples": len(rows),
                    "c6": {key: value for key, value in replay["strategies"]["c6_behavioral"].items() if key != "rows"},
                    "c19": {key: value for key, value in replay["strategies"]["c19_behavioral"].items() if key != "rows"},
                    "deltas": replay["identical_input_deltas"],
                    "mvl_counterfactual_factors": {"gas": round(factors.gas, 6), "wind": round(factors.wind, 6),
                                                   "vehicle_calibration": False}}
  stale = cases()["baseline"]
  stale[1]["lead"]["t_ns"] = 1
  return {"mode": "SIMULATED", "vehicle_response_verified": False, "cases": output,
          "rejected_inputs": {"stale_lead": list(validate_rows(stale))}}


if __name__ == "__main__":
  print(json.dumps(suite(), indent=2, sort_keys=True))

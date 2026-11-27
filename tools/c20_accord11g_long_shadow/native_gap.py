"""Machine-checkable same-cycle input inventory; never invokes the C19 solver."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SERVICES = ("carState", "radarState", "modelV2", "controlsState",
            "vehicleParameters", "carControl", "selfdriveState", "CP", "planner_state")
PROVENANCE = ("route_id", "trace_sha256", "software_sha", "dbc_sha",
              "carFingerprint", "vehicle", "ecu_firmware", "independent_custody_reference")
EXTRAS = ("source_t_ns", "receipt_t_ns", "drive_reset_boundary", "model_trajectories", "lead_history")


def analyze(path: Path) -> dict:
  if path.suffix == ".csv":
    with path.open(newline="", encoding="utf-8") as stream:
      fields = csv.DictReader(stream).fieldnames or []
    # Scalar extracts do not constitute complete serialized messages.
    return {"status": "FAIL_MISSING_REQUIRED_INPUTS", "format": "scalar_csv",
            "present_scalar_columns": sorted(fields), "missing_services": list(SERVICES),
            "missing_provenance": list(PROVENANCE), "missing_cycle_fields": list(EXTRAS),
            "executed_solver": False}
  if path.suffix != ".json":
    raise ValueError("only CSV or JSON input inventories are accepted")
  data = json.loads(path.read_text())
  if not isinstance(data, dict) or not isinstance(data.get("cycles"), list) or not data["cycles"]:
    raise ValueError("JSON must contain nonempty cycles")
  metadata = data.get("provenance", {})
  if not isinstance(metadata, dict):
    raise ValueError("provenance must be an object")
  missing_provenance = [key for key in PROVENANCE if not metadata.get(key)]
  missing_services = set()
  missing_cycle = set()
  last_t = None
  for index, cycle in enumerate(data["cycles"]):
    if not isinstance(cycle, dict):
      raise ValueError(f"cycle {index} must be an object")
    t = cycle.get("t_ns")
    if type(t) is not int or t <= 0 or last_t is not None and t <= last_t:
      raise ValueError(f"cycle {index} has nonmonotonic or duplicate t_ns")
    last_t = t
    missing_services.update(key for key in SERVICES if not isinstance(cycle.get(key), dict) or not cycle[key])
    missing_cycle.update(key for key in EXTRAS if not cycle.get(key))
    for service in SERVICES[:-2]:
      stamp = cycle.get("source_t_ns", {}).get(service) if isinstance(cycle.get("source_t_ns"), dict) else None
      if type(stamp) is not int or stamp <= 0 or stamp > t:
        missing_cycle.add(f"valid_{service}_source_t_ns")
  missing = bool(missing_services or missing_cycle or missing_provenance)
  return {"status": "FAIL_MISSING_REQUIRED_INPUTS" if missing else "SCHEMA_PRESENT_EXECUTION_UNVERIFIED",
          "format": "cycle_json", "cycles": len(data["cycles"]),
          "missing_services": sorted(missing_services), "missing_cycle_fields": sorted(missing_cycle),
          "missing_provenance": missing_provenance, "executed_solver": False}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("artifact", type=Path)
  args = parser.parse_args()
  print(json.dumps(analyze(args.artifact), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

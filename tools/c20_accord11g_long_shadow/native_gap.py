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
EXTRAS = ("source_t_ns", "receipt_t_ns", "drive_reset_boundary", "model_trajectories", "lead_history", "driver_override", "drive_id")
CLOCKED_SERVICES = SERVICES[:-2]


def analyze(path: Path, expected_vehicle: str | None = None) -> dict:
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
  if expected_vehicle is not None and metadata.get('vehicle') != expected_vehicle:
    missing_provenance.append('vehicle_identity_mismatch')
  missing_services = set()
  missing_cycle = set()
  last_t = None
  last_drive = None
  for index, cycle in enumerate(data["cycles"]):
    if not isinstance(cycle, dict):
      raise ValueError(f"cycle {index} must be an object")
    t = cycle.get("t_ns")
    reset = cycle.get("drive_reset_boundary") is True
    drive = cycle.get("drive_id")
    if type(t) is not int or t <= 0 or (last_t is not None and t <= last_t and not reset):
      raise ValueError(f"cycle {index} has nonmonotonic or duplicate t_ns without reset")
    if reset and (index == 0 or not isinstance(drive, str) or not drive or drive == last_drive):
      missing_cycle.add("valid_drive_reset_boundary")
    if not isinstance(drive, str) or not drive or (last_drive is not None and drive != last_drive and not reset):
      missing_cycle.add("drive_id")
    last_t = t
    last_drive = drive
    missing_services.update(key for key in SERVICES if not isinstance(cycle.get(key), dict) or not cycle[key])
    missing_cycle.update(key for key in EXTRAS if key != "drive_reset_boundary" and not cycle.get(key))
    if type(cycle.get("drive_reset_boundary")) is not bool:
      missing_cycle.add("drive_reset_boundary")
    override = cycle.get("driver_override")
    if not isinstance(override, dict) or any(type(override.get(key)) is not bool for key in ("gas_pressed", "brake_pressed")):
      missing_cycle.add("driver_override")
    history = cycle.get("lead_history")
    if not isinstance(history, list) or not history:
      missing_cycle.add("lead_history")
    else:
      for lead in history:
        if not isinstance(lead, dict) or any(type(lead.get(key)) is not int for key in ("source_t_ns", "receipt_t_ns")):
          missing_cycle.add("valid_lead_history_clocks")
          break
        if not 0 < lead["source_t_ns"] <= lead["receipt_t_ns"] <= t or t - lead["source_t_ns"] > 200_000_000:
          missing_cycle.add("valid_lead_history_clocks")
          break
    sources = cycle.get("source_t_ns")
    receipts = cycle.get("receipt_t_ns")
    if not isinstance(sources, dict):
      sources = {}
    if not isinstance(receipts, dict):
      receipts = {}
    for service in CLOCKED_SERVICES + tuple(key for key in SERVICES[-2:] if key in sources):
      source_t = sources.get(service)
      receipt_t = receipts.get(service)
      if type(source_t) is not int or source_t <= 0 or source_t > t:
        missing_cycle.add(f"valid_{service}_source_t_ns")
      if (type(receipt_t) is not int or receipt_t <= 0 or receipt_t > t
          or type(source_t) is not int or receipt_t < source_t):
        missing_cycle.add(f"valid_{service}_receipt_t_ns")
  missing = bool(missing_services or missing_cycle or missing_provenance)
  return {"status": "FAIL_MISSING_REQUIRED_INPUTS" if missing else "SCHEMA_PRESENT_EXECUTION_UNVERIFIED",
          "format": "cycle_json", "cycles": len(data["cycles"]),
          "missing_services": sorted(missing_services), "missing_cycle_fields": sorted(missing_cycle),
          "missing_provenance": missing_provenance, "executed_solver": False}


def message_readiness(census_report: dict) -> dict:
  """Counts indicate schema availability only; rlogs do not record receiver clocks."""
  required = ("carState", "radarState", "modelV2", "controlsState", "selfdriveState", "carControl", "carParams")
  available = {name: all(segment["services"][name]["count"] > 0
                         for segment in census_report["segments"]) for name in required}
  return {"status": "BLOCKED_RECEIPT_AND_EXACT_SOURCE_PROVENANCE",
          "historical_schema_messages_available_each_segment": available,
          "source_timestamps": "MESSAGE_LOG_MONO_TIME_AVAILABLE",
          "receipt_timestamps": "NOT_RECORDED_BY_RLOG",
          "model_lead_history": "NOT_RECONSTRUCTED",
          "drive_reset_boundaries": "NOT_AUTHENTICATED",
          "current_vehicle_authenticated": False, "executed_solver": False}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("artifact", type=Path)
  parser.add_argument("--expected-vehicle")
  args = parser.parse_args()
  print(json.dumps(analyze(args.artifact, args.expected_vehicle), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

"""Streaming, read-only audit of the September Candidate-1 extracted CSVs.

These rows are keyed to decoded CAN publications. They are not C19 MPC input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path

ORIGIN_NS = 31_374_859_675
# Pinned to the read-only September extractor's EVENTS, not CSV-supplied flags.
# LS004 legitimately continues from physical segment 5 into segment 6.
EVENTS = {
  "LS001": (105, "6332.903982011", "6361.700527937"),
  "LS003": (106, "6361.910310646", "6375.783673595"),
  "LS004": (5, "348.372878096", "370.920876374"),
}
# First next-segment CAN publications in the read-only extracted source CSVs.
SEGMENT_SWITCH_NS = {105: 6_393_176_766_727, 5: 393_058_465_682}
EVENT_BOUNDS_NS = {
  event: (ORIGIN_NS + int(Decimal(start) * 1_000_000_000),
          ORIGIN_NS + int(Decimal(end) * 1_000_000_000))
  for event, (_, start, end) in EVENTS.items()
}
NUMERIC = ("carState.vEgo", "carState.aEgo", "longitudinalPlan.aTarget",
           "carControl.actuators.accel", "ACC_CONTROL.ACCEL_COMMAND",
           "GAS_COMMAND", "BRAKE_REQUEST", "planner_to_longcontrol_delta",
           "longcontrol_to_final_can_delta")
SOURCES = ("longitudinalPlan", "carControl", "carState", "radarState", "starpilotPlan")
REQUIRED = {"event_id", "segment", "logMonoTime", "time_s_from_route", "in_qualifying_event",
            "carControl.longControlState", "carState.standstill", *NUMERIC,
            *(s + "_logMonoTime" for s in SOURCES), *(s + "_age_ms" for s in SOURCES)}
NATIVE_REQUIRED = {"carState", "radarState", "modelV2", "controlsState",
                   "vehicleParameters", "carControl", "selfdriveState", "CP",
                   "planner_state", "source_and_receipt_timestamps", "model_trajectories",
                   "lead_history", "drive_reset_boundaries"}


def digest(path: Path) -> str:
  h = hashlib.sha256()
  with path.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
      h.update(chunk)
  return h.hexdigest()


def _number(row: dict, key: str, line: int) -> float:
  try:
    value = float(row[key])
  except (ValueError, TypeError, KeyError):
    raise ValueError(f"line {line}: missing or invalid {key}") from None
  if not math.isfinite(value):
    raise ValueError(f"line {line}: nonfinite {key}")
  return value


def _integer(row: dict, key: str, line: int) -> int:
  raw = row.get(key, "")
  if not raw.isascii() or not raw.isdecimal():
    raise ValueError(f"line {line}: invalid integer {key}")
  return int(raw)


def audit_csv(path: Path) -> dict:
  if not path.is_file() or path.is_symlink():
    raise ValueError("CSV must be a regular, non-symlink file")
  # Hash before and after reading so ordinary in-place mutation fails closed.
  before = (path.stat().st_size, path.stat().st_mtime_ns, digest(path))
  counts = {"all_rows": 0, "event_rows": 0, "negative_boundary_rows": 0,
            "gas_to_brake": 0, "brake_to_gas": 0, "stopping_rows": 0,
            "standstill_brake_rows": 0}
  minima = {key: None for key in ("planner", "longcontrol", "can", "measured_aego", "planner_to_longcontrol", "longcontrol_to_can")}
  map_keys = {"planner": "longitudinalPlan.aTarget", "longcontrol": "carControl.actuators.accel",
              "can": "ACC_CONTROL.ACCEL_COMMAND", "measured_aego": "carState.aEgo",
              "planner_to_longcontrol": "planner_to_longcontrol_delta",
              "longcontrol_to_can": "longcontrol_to_final_can_delta"}
  ages = {s: 0.0 for s in SOURCES}
  previous_t = None
  previous_gas = None
  previous_brake = None
  event_id = None
  first_t = last_t = None
  with path.open(newline="", encoding="utf-8") as stream:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or not REQUIRED <= set(fields):
      raise ValueError(f"missing/duplicate columns: {sorted(REQUIRED - set(fields))}")
    for line, row in enumerate(reader, 2):
      if None in row or any(row.get(k) is None for k in REQUIRED):
        raise ValueError(f"line {line}: malformed CSV row")
      t = _integer(row, "logMonoTime", line)
      if previous_t is not None and t <= previous_t:
        raise ValueError(f"line {line}: nonmonotonic or duplicate CAN tick")
      previous_t = t
      first_t = t if first_t is None else first_t
      last_t = t
      if event_id is None:
        event_id = row["event_id"]
      if row["event_id"] != event_id:
        raise ValueError(f"line {line}: mixed event IDs")
      if event_id not in EVENTS:
        raise ValueError(f"line {line}: unknown event ID")
      segment = _integer(row, "segment", line)
      source_segment = EVENTS[event_id][0]
      first_segment = 5 if source_segment == 5 else 105
      expected_segment = first_segment + (t >= SEGMENT_SWITCH_NS[first_segment])
      if segment != expected_segment:
        raise ValueError(f"line {line}: source segment disagrees with event")
      values = {key: _number(row, key, line) for key in NUMERIC}
      # A filtered near-zero vEgo can dip slightly below zero in this extraction.
      if values["carState.vEgo"] < -0.5 or values["BRAKE_REQUEST"] not in (0, 1):
        raise ValueError(f"line {line}: invalid speed or brake bit")
      if abs(values["planner_to_longcontrol_delta"] - (values["carControl.actuators.accel"] - values["longitudinalPlan.aTarget"])) > 1e-6:
        raise ValueError(f"line {line}: planner delta disagrees with source columns")
      if abs(values["longcontrol_to_final_can_delta"] - (values["ACC_CONTROL.ACCEL_COMMAND"] - values["carControl.actuators.accel"])) > 1e-6:
        raise ValueError(f"line {line}: CAN delta disagrees with source columns")
      time_s = _number(row, "time_s_from_route", line)
      if abs(time_s - (t - ORIGIN_NS) / 1e9) > 1e-5:
        raise ValueError(f"line {line}: route time transform disagrees with clock")
      for source in SOURCES:
        source_t = _integer(row, source + "_logMonoTime", line)
        age = _number(row, source + "_age_ms", line)
        if source_t > t or source_t <= 0 or abs(age - (t - source_t) / 1e6) > 1e-4 or age < 0:
          raise ValueError(f"line {line}: future or inconsistent {source} hold")
        ages[source] = max(ages[source], age)
      if row["in_qualifying_event"] not in ("True", "False") or row["carState.standstill"] not in ("True", "False"):
        raise ValueError(f"line {line}: invalid boolean")
      start_ns, end_ns = EVENT_BOUNDS_NS[event_id]
      in_window = start_ns <= t <= end_ns
      if (row["in_qualifying_event"] == "True") != in_window or (in_window and event_id != "LS004" and segment != source_segment):
        raise ValueError(f"line {line}: event window flag or segment disagrees with clock")
      counts["all_rows"] += 1
      gas = values["GAS_COMMAND"] > -30000
      brake = values["BRAKE_REQUEST"] == 1
      if in_window:
        counts["event_rows"] += 1
        if previous_gas is True and not gas and brake:
          counts["gas_to_brake"] += 1
        if previous_brake is True and gas and not brake:
          counts["brake_to_gas"] += 1
        if row["carControl.longControlState"] == "stopping":
          counts["stopping_rows"] += 1
        if row["carState.standstill"] == "True" and brake:
          counts["standstill_brake_rows"] += 1
        if values["longcontrol_to_final_can_delta"] < -0.02:
          counts["negative_boundary_rows"] += 1
        for label, key in map_keys.items():
          value = values[key]
          old = minima[label]
          if old is None or value < old["value_mps2"]:
            minima[label] = {"value_mps2": value, "t_ns": t, "t_s_from_route": time_s,
                             "planner_mps2": values["longitudinalPlan.aTarget"],
                             "longcontrol_mps2": values["carControl.actuators.accel"],
                             "can_mps2": values["ACC_CONTROL.ACCEL_COMMAND"],
                             "measured_aego_mps2": values["carState.aEgo"]}
      previous_gas, previous_brake = gas, brake
  after = (path.stat().st_size, path.stat().st_mtime_ns, digest(path))
  if before != after or not counts["event_rows"]:
    raise ValueError("CSV changed during read or has no qualifying event rows")
  return {"label": "HISTORICAL_UNVERIFIED_CANDIDATE1_MEASURED_AND_DECODED",
          "file": path.name, "sha256": before[2], "bytes": before[0], "event_id": event_id,
          "first_t_ns": first_t, "last_t_ns": last_t, "clock_origin_ns": ORIGIN_NS,
          "units": {"time": "monotonic ns", "speed": "m/s", "acceleration": "m/s^2", "age": "ms"},
          "counts": counts, "minima": minima, "max_hold_age_ms": ages,
          "native_same_cycle": {"status": "FAIL_MISSING_REQUIRED_INPUTS",
                                "missing": sorted(NATIVE_REQUIRED), "executed_solver": False}}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("csv", type=Path, nargs="+")
  args = parser.parse_args()
  print(json.dumps([audit_csv(p) for p in args.csv], indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

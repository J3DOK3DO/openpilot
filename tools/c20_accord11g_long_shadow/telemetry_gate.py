"""TEST_ONLY / RESEARCH sanitized capture admission and temporal quality audit.

Consumes digests and clocks only. It cannot reconstruct C19 input messages,
authenticate custody, calculate acceleration, or communicate with a vehicle.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from .admission import load_json_bytes
from .platform_receipt import BASELINE

HEX = re.compile(r"[0-9a-f]{64}\Z")
SERVICES = ("carControl", "carState", "controlsState", "vehicleParameters", "radarState", "modelV2", "selfdriveState")
STATES = ("CP", "planner_state", "preferences", "drive_state")
MANIFEST_KEYS = {"schema_version", "label", "vehicle", "fingerprint_sha256", "ecu_firmware_sha256",
                 "source_commit", "dbc_sha256", "model_sha256", "hardware_sha256", "capture_sha256",
                 "custody_reference_sha256", "attestation"}
CAPTURE_KEYS = {"schema_version", "label", "fingerprint_sha256", "ecu_firmware_sha256",
                "source_commit", "dbc_sha256", "model_sha256", "hardware_sha256", "cycles"}
CYCLE_KEYS = {"cycle_t_ns", "drive_token_sha256", "reset_boundary", "services", "model_leads",
              "radar_md_mono_time_ns", "model_lead_history",
              "state_sha256", "gas_pressed", "brake_pressed", "lead_present", "source_integrity",
              "clock_disagreement"}
SAMPLE_KEYS = {"source_t_ns", "receipt_t_ns", "payload_sha256"}
HISTORY_KEYS = SAMPLE_KEYS | {"lead_payload_sha256"}
MAX_HISTORY_AGE_NS = 150_000_000
MAX_MANIFEST = 16 * 1024
MAX_CAPTURE = 2 * 1024 * 1024
MAX_CYCLES = 2000
MAX_AGE_NS = 200_000_000
MAX_GAP_NS = 500_000_000
VEHICLE = "HONDA_ACCORD_11G_HYBRID_TOURING_US_BOSCH_C"


def _digest(value: object) -> bool:
  return type(value) is str and bool(HEX.fullmatch(value))


def _ns(value: object) -> bool:
  return type(value) is int and 0 < value < 10**19


def _keys(value: object, expected: set[str]) -> bool:
  return type(value) is dict and set(value) == expected


def read_bounded(path: Path, maximum: int) -> bytes:
  if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
    raise ValueError("missing, linked or oversized input")
  with path.open("rb") as stream:
    data = stream.read(maximum + 1)
  if len(data) > maximum:
    raise ValueError("oversized input")
  return data


def _percentiles(values: list[int]) -> dict:
  ordered = sorted(values)
  if not ordered:
    return {"count": 0, "min_ns": None, "p50_ns": None, "p90_ns": None, "p99_ns": None, "max_ns": None}
  def p(frac: float) -> int:
    return ordered[max(0, int(frac * len(ordered) + .999999) - 1)]
  return {"count": len(ordered), "min_ns": ordered[0], "p50_ns": p(.5), "p90_ns": p(.9),
          "p99_ns": p(.99), "max_ns": ordered[-1]}


def audit(manifest_raw: bytes, capture_raw: bytes) -> dict:
  if len(manifest_raw) > MAX_MANIFEST or len(capture_raw) > MAX_CAPTURE:
    raise ValueError("oversized input")
  manifest = load_json_bytes(manifest_raw)
  capture = load_json_bytes(capture_raw)
  if not _keys(manifest, MANIFEST_KEYS) or not _keys(capture, CAPTURE_KEYS):
    raise ValueError("schema mismatch")
  if manifest["schema_version"] != 1 or capture["schema_version"] != 1:
    raise ValueError("schema version mismatch")
  if manifest["label"] != "SYNTHETIC" or capture["label"] != "SYNTHETIC":
    # This tool can analyze future captures, but cannot authenticate them.
    if manifest["label"] != "CURRENT_UNVERIFIED" or capture["label"] != "CURRENT_UNVERIFIED":
      raise ValueError("classification invalid")
  for key in ("fingerprint_sha256", "ecu_firmware_sha256", "dbc_sha256", "model_sha256",
              "hardware_sha256", "capture_sha256", "custody_reference_sha256"):
    if not _digest(manifest[key]):
      raise ValueError("manifest digest invalid")
  for key in ("fingerprint_sha256", "ecu_firmware_sha256", "dbc_sha256", "model_sha256", "hardware_sha256"):
    if not _digest(capture[key]):
      raise ValueError("capture identity digest invalid")
  if manifest["vehicle"] != VEHICLE or manifest["source_commit"] != BASELINE or capture["source_commit"] != BASELINE:
    raise ValueError("vehicle or source mismatch")
  if manifest["attestation"] != "UNVERIFIED_SELF_REPORT":
    raise ValueError("unsupported attestation; PKI verification unavailable")
  faults = set()
  if manifest["capture_sha256"] != hashlib.sha256(capture_raw).hexdigest():
    faults.add("CAPTURE_DIGEST_MISMATCH")
  for key in ("fingerprint_sha256", "ecu_firmware_sha256", "dbc_sha256", "model_sha256", "hardware_sha256"):
    if manifest[key] != capture[key]:
      faults.add("SOURCE_IDENTITY_CONFLICT")
  if not isinstance(capture["cycles"], list) or not 0 < len(capture["cycles"]) <= MAX_CYCLES:
    raise ValueError("cycle count invalid")
  state = "FAULT_LOCKED" if faults else "START"
  state_transitions = 0
  ages = {name: [] for name in SERVICES}
  receipts = {name: [] for name in SERVICES}
  gaps = {name: [] for name in SERVICES}
  source_skews = []
  last_source = {}
  last_cycle = None
  last_drive = None
  last_by_service = {}
  last_history = {}
  state_valid_count = 0
  clocks_valid_count = 0
  association_lags = []
  fault_events = []
  for index, cycle in enumerate(capture["cycles"]):
    faults_before = set(faults) if index else set()
    if not _keys(cycle, CYCLE_KEYS):
      raise ValueError("cycle schema mismatch")
    if not _ns(cycle["cycle_t_ns"]) or not _digest(cycle["drive_token_sha256"]) or type(cycle["reset_boundary"]) is not bool:
      raise ValueError("cycle clock or boundary invalid")
    if any(type(cycle[key]) is not bool for key in ("gas_pressed", "brake_pressed", "lead_present", "source_integrity", "clock_disagreement")):
      raise ValueError("cycle flags invalid")
    drive = cycle["drive_token_sha256"]
    now = cycle["cycle_t_ns"]
    if index == 0:
      if not cycle["reset_boundary"]:
        faults.add("RESET_BOUNDARY_MISSING")
    elif drive == last_drive:
      if cycle["reset_boundary"]:
        faults.add("UNEXPECTED_RESET")
      if now <= last_cycle:
        faults.add("NONMONOTONIC_CYCLE")
    else:
      faults.add("ROUTE_MISMATCH")
      if not cycle["reset_boundary"]:
        faults.add("RESET_BOUNDARY_MISSING")
      last_source = {}
      last_by_service = {}
      last_history = {}
    if index > 0 and cycle["reset_boundary"]:
      faults.add("RESET_OBSERVED")
    if not _keys(cycle["state_sha256"], set(STATES)) or any(not _digest(cycle["state_sha256"][key]) for key in STATES):
      faults.add("PLANNER_STATE_MISSING")
    else:
      state_valid_count += 1
    if cycle["gas_pressed"] or cycle["brake_pressed"]:
      faults.add("DRIVER_OVERRIDE")
    if not cycle["lead_present"]:
      faults.add("LEAD_LOSS")
    if not cycle["source_integrity"]:
      faults.add("SOURCE_INTEGRITY_FAILURE")
    if cycle["clock_disagreement"]:
      faults.add("CLOCK_DISAGREEMENT")
    services = cycle["services"]
    if not _keys(services, set(SERVICES)):
      faults.add("SERVICE_MISSING")
      services = {} if type(services) is not dict else services
    cycle_clocks_valid = True
    cycle_sources = []
    for name in SERVICES:
      sample = services.get(name)
      if not _keys(sample, SAMPLE_KEYS) or not _ns(sample["source_t_ns"]) or not _ns(sample["receipt_t_ns"]) or not _digest(sample["payload_sha256"]):
        faults.add("RECEIPT_OR_PAYLOAD_MISSING")
        cycle_clocks_valid = False
        continue
      source = sample["source_t_ns"]
      receipt = sample["receipt_t_ns"]
      cycle_sources.append(source)
      if source > now or receipt > now:
        faults.add("FUTURE_SAMPLE")
        cycle_clocks_valid = False
      if source > receipt:
        faults.add("CLOCK_DISAGREEMENT")
        cycle_clocks_valid = False
      if source <= last_source.get(name, 0) or receipt <= last_by_service.get(name, 0):
        faults.add("NONMONOTONIC_SERVICE")
        cycle_clocks_valid = False
      if 0 <= now - source <= MAX_AGE_NS:
        ages[name].append(now - source)
      else:
        faults.add("SENSOR_STALE")
      if 0 <= receipt - source <= MAX_AGE_NS:
        receipts[name].append(receipt - source)
      else:
        faults.add("RECEIPT_LATENCY")
      if name in last_source:
        gap = source - last_source[name]
        if gap > 0:
          gaps[name].append(gap)
          if gap > MAX_GAP_NS:
            faults.add("SERVICE_GAP")
      last_source[name] = source
      last_by_service[name] = receipt
    if len(cycle_sources) == len(SERVICES):
      skew = max(cycle_sources) - min(cycle_sources)
      source_skews.append(skew)
      if skew > MAX_AGE_NS:
        faults.add("SOURCE_SKEW")
    if cycle_clocks_valid:
      clocks_valid_count += 1
    model = services.get("modelV2")
    radar = services.get("radarState")
    associated = cycle["radar_md_mono_time_ns"]
    if not _ns(associated):
      raise ValueError("radar model association clock invalid")
    if type(radar) is not dict or not _ns(radar.get("source_t_ns")) or associated > radar["source_t_ns"]:
      faults.add("FUTURE_SAMPLE")
    history = cycle["model_lead_history"]
    if not isinstance(history, list) or not 0 < len(history) <= 4:
      raise ValueError("model lead history length invalid")
    current_history = {}
    for frame in history:
      if (not _keys(frame, HISTORY_KEYS) or not _ns(frame["source_t_ns"])
          or not _ns(frame["receipt_t_ns"]) or not _digest(frame["payload_sha256"])
          or type(frame["lead_payload_sha256"]) is not list
          or len(frame["lead_payload_sha256"]) != 2
          or any(not _digest(value) for value in frame["lead_payload_sha256"])):
        raise ValueError("model lead history schema invalid")
      stamp = frame["source_t_ns"]
      if stamp in current_history or (current_history and stamp <= max(current_history)):
        faults.add("MODEL_HISTORY_INVALID")
      if stamp > frame["receipt_t_ns"] or frame["receipt_t_ns"] > now or stamp > now:
        faults.add("FUTURE_SAMPLE")
      if now - stamp > MAX_HISTORY_AGE_NS:
        faults.add("SENSOR_STALE")
      if type(model) is not dict or not _ns(model.get("source_t_ns")) or stamp > model["source_t_ns"]:
        faults.add("FUTURE_SAMPLE")
      if type(model) is dict and stamp == model.get("source_t_ns"):
        if frame["receipt_t_ns"] != model.get("receipt_t_ns") or frame["payload_sha256"] != model.get("payload_sha256"):
          faults.add("MODEL_HISTORY_INVALID")
      elif last_history.get(stamp) != frame:
        faults.add("MODEL_HISTORY_INVALID")
      current_history[stamp] = frame
    if associated not in current_history:
      faults.add("MODEL_LEAD_SOURCE_MISMATCH")
    leads = cycle["model_leads"]
    if not isinstance(leads, list) or len(leads) > 4:
      raise ValueError("model lead list invalid")
    if cycle["lead_present"] and len(leads) < 2:
      faults.add("MODEL_LEAD_DROPPED")
    selected = current_history.get(associated)
    if selected is not None and now >= associated:
      association_lags.append(now - associated)
    for lead_index, lead in enumerate(leads):
      if not _keys(lead, SAMPLE_KEYS) or not _ns(lead["source_t_ns"]) or not _ns(lead["receipt_t_ns"]) or not _digest(lead["payload_sha256"]):
        faults.add("MODEL_LEAD_DROPPED")
        continue
      if lead["source_t_ns"] > lead["receipt_t_ns"] or lead["receipt_t_ns"] > now:
        faults.add("FUTURE_SAMPLE")
      if now - lead["source_t_ns"] > MAX_AGE_NS:
        faults.add("SENSOR_STALE")
      if (selected is None or lead["source_t_ns"] != associated
          or lead["receipt_t_ns"] != selected["receipt_t_ns"]
          or lead_index >= 2 or lead["payload_sha256"] != selected["lead_payload_sha256"][lead_index]):
        faults.add("MODEL_LEAD_SOURCE_MISMATCH")
    last_history = current_history
    last_cycle = now
    last_drive = drive
    next_state = "FAULT_LOCKED" if faults != faults_before or state == "FAULT_LOCKED" else "OBSERVING"
    if next_state != state:
      state_transitions += 1
    state = next_state
    fault_events.append({"cycle_index": index, "new_faults": sorted(faults - faults_before), "audit_state": state})
  return {"schema_version": 1, "classification": "SANITIZED_TEMPORAL_JOIN", "input_label": capture["label"],
          "input_presence": "PRESENT", "type_length_validation": "PASS" if (clocks_valid_count == len(capture["cycles"])
             and state_valid_count == len(capture["cycles"])
             and not faults.intersection({"MODEL_LEAD_DROPPED", "SERVICE_MISSING", "RECEIPT_OR_PAYLOAD_MISSING"})) else "FAIL",
          "semantic_source_equivalence": "UNVERIFIED_SERIALIZED_MESSAGES_ABSENT",
          "provenance": "UNVERIFIED_SELF_REPORT", "custody_authenticated": False,
          "capture_digest_match": "CAPTURE_DIGEST_MISMATCH" not in faults,
          "cycle_count": len(capture["cycles"]), "faults": sorted(faults),
          "audit_state": state, "state_transitions": state_transitions, "fault_events": fault_events,
          "quality_state": "PASS_SYNTHETIC_ONLY" if not faults and capture["label"] == "SYNTHETIC" else "FAIL_CLOSED",
          "gaps_ns": {name: _percentiles(gaps[name]) for name in SERVICES},
          "source_age_ns": {name: _percentiles(ages[name]) for name in SERVICES},
          "receipt_latency_ns": {name: _percentiles(receipts[name]) for name in SERVICES},
          "source_skew_ns": _percentiles(source_skews),
          "model_association_lag_ns": _percentiles(association_lags),
          "native_c19_planner_replay": "NOT_DONE",
          "native_solver_executed": False,
          "release_blockers": ["NATIVE_SOLVER_ABSENT", "CUSTODY_UNVERIFIED", "SERIALIZED_SOURCE_EQUIVALENCE_UNVERIFIED"],
          "active_alpha_long": "NO_GO", "road_deployment": "NO_GO"}


def csv_summary(report: dict) -> str:
  stream = io.StringIO()
  writer = csv.writer(stream, lineterminator="\n")
  writer.writerow(("label", "cycles", "quality_state", "fault", "service", "gap_p90_ns", "source_age_p90_ns"))
  for name in SERVICES:
    for fault in report["faults"] or [""]:
      writer.writerow((report["input_label"], report["cycle_count"], report["quality_state"], fault, name,
                       report["gaps_ns"][name]["p90_ns"], report["source_age_ns"][name]["p90_ns"]))
  return stream.getvalue()


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--manifest", type=Path, required=True)
  parser.add_argument("--capture", type=Path, required=True)
  parser.add_argument("--format", choices=("json", "csv"), default="json")
  args = parser.parse_args()
  try:
    report = audit(read_bounded(args.manifest, MAX_MANIFEST), read_bounded(args.capture, MAX_CAPTURE))
  except (OSError, ValueError, TypeError, KeyError):
    report = {"schema_version": 1, "classification": "TEST_ONLY_RESEARCH", "quality_state": "FAIL_CLOSED",
              "faults": ["INVALID_INPUT"], "active_alpha_long": "NO_GO", "road_deployment": "NO_GO"}
  print(csv_summary(report) if args.format == "csv" and "gaps_ns" in report else json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

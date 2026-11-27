"""Strict, local admission of JSON telemetry and externally corroborated provenance.

An exact match to a supplied reference establishes only consistency with that
reference. The caller remains responsible for authenticating the reference.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import re
from typing import Any


class Status(str, Enum):
  REFERENCE_MATCH_UNVERIFIED = "REFERENCE_MATCH_UNVERIFIED"
  COMPATIBLE_BUT_UNVERIFIED = "COMPATIBLE_BUT_UNVERIFIED"
  MISMATCH = "MISMATCH"
  INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Admission:
  status: Status
  reasons: tuple[str, ...]


EXPECTED_VEHICLE = {"make": "Honda", "model": "Accord", "year": 2024,
                    "powertrain": "Hybrid", "trim": "Touring", "market": "US-spec import"}
UNITS = {"timestamp": "ns", "speed": "m/s", "acceleration": "m/s^2",
         "distance": "m", "pitch": "rad"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_LEAD_AGE_NS = 200_000_000
MAX_SIGNAL_AGE_NS = 200_000_000
MAX_ROW_GAP_NS = 500_000_000
MAX_ROWS = 10_000
MAX_TRACE_BYTES = 64 * 1024 * 1024
SIGNAL_KEYS = ("v_ego", "a_ego", "v_cruise", "raw_accel", "pitch",
               "gas_pressed", "brake_pressed", "stock_aeb")


def _number(value: Any, lo: float, hi: float) -> bool:
  return type(value) in (int, float) and math.isfinite(value) and lo <= value <= hi


def _known(value: Any) -> bool:
  return isinstance(value, str) and bool(value.strip()) and value.upper() not in {"UNKNOWN", "UNVERIFIED", "PLACEHOLDER", "N/A"}


def load_json_bytes(data: bytes) -> Any:
  def unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
      if key in result:
        raise ValueError(f"duplicate JSON key: {key}")
      result[key] = value
    return result
  return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                    parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def reference_digest(reference: Any) -> str:
  """Canonical digest to compare with an independently obtained expected hash."""
  return hashlib.sha256(json.dumps(reference, sort_keys=True, separators=(",", ":"),
                                   allow_nan=False).encode("utf-8")).hexdigest()


def validate_rows(rows: Any, start_ns: int | None = None, end_ns: int | None = None) -> tuple[str, ...]:
  reasons: list[str] = []
  if not isinstance(rows, list) or not rows:
    return ("missing time-series rows",)
  if len(rows) > MAX_ROWS:
    return ("time-series row limit exceeded",)
  previous = None
  for index, row in enumerate(rows):
    if not isinstance(row, dict):
      reasons.append(f"row {index}: expected object")
      continue
    t = row.get("t_ns")
    if type(t) is not int or t < 0 or (previous is not None and t <= previous):
      reasons.append(f"row {index}: nonmonotonic timestamp")
    elif (start_ns is not None and t < start_ns) or (end_ns is not None and t > end_ns):
      reasons.append(f"row {index}: outside declared range")
    elif previous is not None and t - previous > MAX_ROW_GAP_NS:
      reasons.append(f"row {index}: signal gap")
    if type(t) is int:
      previous = t
    for key, lo, hi in (("v_ego", 0, 80), ("a_ego", -12, 8),
                        ("v_cruise", 0, 80), ("raw_accel", -12, 8),
                        ("pitch", -0.4, 0.4)):
      if not _number(row.get(key), lo, hi):
        reasons.append(f"row {index}: missing/invalid {key}")
    for key in ("gas_pressed", "brake_pressed", "stock_aeb"):
      if type(row.get(key)) is not bool:
        reasons.append(f"row {index}: missing/invalid {key}")
    signal_times = row.get("signal_t_ns")
    if not isinstance(signal_times, dict):
      reasons.append(f"row {index}: missing signal timestamps")
    else:
      for key in SIGNAL_KEYS:
        source_time = signal_times.get(key)
        if type(source_time) is not int or type(t) is not int or not 0 <= t - source_time <= MAX_SIGNAL_AGE_NS:
          reasons.append(f"row {index}: stale/future/missing {key} timestamp")
    if "lead" not in row:
      reasons.append(f"row {index}: missing lead signal")
    lead = row.get("lead")
    if lead is not None:
      if not isinstance(lead, dict) or not _known(lead.get("track_id")):
        reasons.append(f"row {index}: invalid lead identity")
        continue
      if type(lead.get("radar")) is not bool or type(lead.get("valid")) is not bool or not lead["valid"]:
        reasons.append(f"row {index}: invalid lead flags")
      if not _number(lead.get("distance"), 0, 300) or not _number(lead.get("speed"), 0, 80):
        reasons.append(f"row {index}: invalid lead kinematics")
      if not _number(lead.get("confidence"), 0, 1):
        reasons.append(f"row {index}: invalid lead confidence")
      lt = lead.get("t_ns")
      if type(lt) is not int or type(t) is not int or not 0 <= t - lt <= MAX_LEAD_AGE_NS:
        reasons.append(f"row {index}: stale/future lead")
  if start_ns is not None and rows and isinstance(rows[0], dict) and rows[0].get("t_ns") != start_ns:
    reasons.append("start timestamp does not match first row")
  if end_ns is not None and rows and isinstance(rows[-1], dict) and rows[-1].get("t_ns") != end_ns:
    reasons.append("end timestamp does not match last row")
  return tuple(reasons)


def admit(manifest: Any, trace_bytes: bytes, trusted_reference: Any = None,
          expected_reference_sha256: str | None = None) -> Admission:
  if len(trace_bytes) > MAX_TRACE_BYTES:
    return Admission(Status.INSUFFICIENT_EVIDENCE, ("trace byte limit exceeded",))
  if not isinstance(manifest, dict):
    return Admission(Status.INSUFFICIENT_EVIDENCE, ("manifest is not an object",))
  mismatch: list[str] = []
  missing: list[str] = []
  if manifest.get("carFingerprint") != "HONDA_ACCORD_11G":
    mismatch.append("carFingerprint is not HONDA_ACCORD_11G")
  if manifest.get("vehicle") != EXPECTED_VEHICLE:
    mismatch.append("vehicle identity differs from 2024 Hybrid Touring US-spec import")
  if manifest.get("source_kind") != "RECORDED":
    missing.append("source_kind must be RECORDED")
  for key in ("route_id", "software_sha", "dbc_sha"):
    value = manifest.get(key)
    if not _known(value) or (key.endswith("sha") and not HEX64.fullmatch(value)):
      missing.append(f"missing/invalid {key}")
  if manifest.get("units") != UNITS:
    missing.append("units mismatch or incomplete")
  fw = manifest.get("ecu_firmware")
  if not isinstance(fw, dict) or not all(_known(fw.get(k)) for k in ("radar", "camera", "brake")):
    missing.append("missing radar/camera/brake ECU firmware identifiers")
  digest = hashlib.sha256(trace_bytes).hexdigest()
  if manifest.get("trace_sha256") != digest:
    mismatch.append("trace SHA-256 does not match bytes")
  start, end = manifest.get("start_ns"), manifest.get("end_ns")
  if type(start) is not int or type(end) is not int or start < 0 or end <= start:
    missing.append("invalid timestamp range")
    start = end = None
  try:
    rows = load_json_bytes(trace_bytes)
  except (ValueError, UnicodeError) as exc:
    return Admission(Status.INSUFFICIENT_EVIDENCE, (f"invalid trace JSON: {exc}",))
  missing.extend(validate_rows(rows, start, end))
  if trusted_reference is not None:
    if not isinstance(trusted_reference, dict):
      missing.append("invalid trusted reference")
    else:
      # Route and artifact binding prevent an unrelated route from inheriting identity.
      for key in ("source_kind", "carFingerprint", "vehicle", "route_id", "software_sha", "dbc_sha",
                  "ecu_firmware", "trace_sha256", "start_ns", "end_ns", "units"):
        if trusted_reference.get(key) != manifest.get(key):
          mismatch.append(f"trusted reference {key} mismatch")
      if trusted_reference.get("authenticated") is not True:
        missing.append("trusted reference authentication absent")
      if not isinstance(expected_reference_sha256, str) or not HEX64.fullmatch(expected_reference_sha256):
        missing.append("independent reference SHA-256 absent")
      elif reference_digest(trusted_reference) != expected_reference_sha256:
        mismatch.append("independent reference SHA-256 mismatch")
  if mismatch:
    return Admission(Status.MISMATCH, tuple(mismatch + missing))
  if missing:
    return Admission(Status.INSUFFICIENT_EVIDENCE, tuple(missing))
  if trusted_reference is None:
    return Admission(Status.COMPATIBLE_BUT_UNVERIFIED, ("no independently authenticated reference",))
  return Admission(Status.REFERENCE_MATCH_UNVERIFIED,
                   ("bytes match caller-supplied reference; independent issuer and vehicle custody remain unverified",))

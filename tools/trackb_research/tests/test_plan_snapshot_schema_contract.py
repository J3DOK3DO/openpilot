"""Bind PlanSnapshot to the current Dom ``LongitudinalPlan`` schema so drift is detected."""
import re
from dataclasses import fields
from pathlib import Path

from tools.trackb_research.plan_controller_sim import PlanSnapshot

ROOT = Path(__file__).resolve().parents[3]
LOG_CAPNP = ROOT / "openpilot" / "cereal" / "log.capnp"

# Schema field (camelCase) -> PlanSnapshot field. modelMonoTime/planLogMonoTime are the plan identifiers.
MAPPED = {
  "modelMonoTime": "model_log_monotonic",
  "hasLead": "has_lead",
  "fcw": "fcw",
  "longitudinalPlanSource": "longitudinal_plan_source",
  "accels": "accels",
  "speeds": "speeds",
  "jerks": "jerks",
  "aTarget": "a_target",
  "shouldStop": "should_stop",
  "allowThrottle": "allow_throttle",
  "allowBrake": "allow_brake",
}
# Schema fields deliberately outside the abstract contract (diagnostic/timing only, no authority semantics).
ACKNOWLEDGED_UNMODELED = {"processingDelay", "accelBoost", "solverExecutionTime"}
# Snapshot fields that come from log envelope or test clock rather than the LongitudinalPlan struct.
ENVELOPE = {"plan_log_monotonic", "published_monotonic"}


def _live_schema_fields() -> set[str]:
  text = LOG_CAPNP.read_text(encoding="utf-8")
  body = text.split("struct LongitudinalPlan @", 1)[1].split("  deprecated :group", 1)[0]
  body = re.sub(r"enum \w+ \{.*?\}", "", body, flags=re.DOTALL)
  return set(re.findall(r"^\s+(\w+)\s*@\d+\s*:", body, re.MULTILINE))


# Pinned schema ordinal and type per mapped field; a type or ordinal change must be re-reviewed here.
MAPPED_TYPES = {
  "modelMonoTime": ("9", "UInt64"), "hasLead": ("7", "Bool"), "fcw": ("8", "Bool"),
  "longitudinalPlanSource": ("15", "LongitudinalPlanSource"), "accels": ("32", "List(Float32)"),
  "speeds": ("33", "List(Float32)"), "jerks": ("34", "List(Float32)"), "aTarget": ("18", "Float32"),
  "shouldStop": ("37", "Bool"), "allowThrottle": ("38", "Bool"), "allowBrake": ("39", "Bool"),
}


def test_mapped_fields_keep_pinned_ordinal_and_type():
  text = LOG_CAPNP.read_text(encoding="utf-8")
  body = text.split("struct LongitudinalPlan @", 1)[1].split("  deprecated :group", 1)[0]
  live = {name: (ordinal, kind) for name, ordinal, kind in re.findall(r"^\s+(\w+)\s*@(\d+)\s*:\s*([\w().]+)\s*;", body, re.MULTILINE)}
  assert {name: live.get(name) for name in MAPPED_TYPES} == MAPPED_TYPES


def test_every_live_schema_field_is_mapped_or_explicitly_acknowledged():
  live = _live_schema_fields()
  assert {"aTarget", "shouldStop", "fcw"} <= live  # guard against a vacuous parse
  assert live == set(MAPPED) | ACKNOWLEDGED_UNMODELED


def test_snapshot_fields_are_exactly_the_mapped_schema_fields_plus_envelope():
  assert {field.name for field in fields(PlanSnapshot)} == set(MAPPED.values()) | ENVELOPE

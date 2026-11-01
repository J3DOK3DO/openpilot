"""Pure, non-actuating Release B qualification gate around the subordinate controller simulation.

Release B (operational Bosch-C longitudinal) may only ever propose anything once every B1-B6 requirement in the
evidence register has passed with independently reviewed evidence of the one kind that requirement accepts, where
every evidence item resolves to caller-supplied artifact bytes whose SHA-256 matches, and identity requirements bind
the measured hash in their evidence to the qualified identity. This module evaluates a caller-supplied register and
artifacts plus synthetic inputs; it never decodes, transmits, forwards, or suppresses CAN/UDS traffic, is never
imported by production code, and its "eligible" proposal is still an abstract test record.

This is an integrity and completeness check, not authentication: fabricated artifacts with matching hashes would
pass it. Authenticity rests on the named independent reviewer. Passing this gate in a test is not vehicle
authorization.
"""
from dataclasses import dataclass
from hashlib import sha256

from tools.trackb_research.ownership_evidence_model import STATE_OBSERVED_STOCK, OwnershipEvidence
from tools.trackb_research.plan_controller_sim import MODE_WITHDRAWN, PlanControllerSimulation, SimulationRecord

# OWNER_DEFERRED records an owner deferral of a physical stage (B5/B6, 2026-11-01): not executed, not passed, not
# waived. OUT_OF_SCOPE is the earlier name of the same record. Like every non-PASS status, both hold.
STATUSES = frozenset(("PASS", "FAIL", "HOLD", "NOT_RUN", "NOT_APPLICABLE", "OUT_OF_SCOPE", "OWNER_DEFERRED"))
# The only evidence kinds each requirement accepts. Physical rows never accept source, host or image evidence.
REQUIRED_KINDS = {
  "B1-OEM-COMMAND-OWNERSHIP": frozenset(("oem_authenticated",)),
  "B1-CMBS-AEB-PRECEDENCE": frozenset(("oem_authenticated",)),
  "B1-CANFD-TOPOLOGY-ARBITRATION": frozenset(("oem_authenticated",)),
  "B1-OWNER-TRANSITION": frozenset(("oem_authenticated",)),
  "B2-SUBORDINATE-CONTROLLER-CONTRACTS": frozenset(("source_test", "source_review")),
  "B3-HOST-RELEASE-DENIAL": frozenset(("host_test",)),
  "B3-TARGET-PANDA-RELEASE-IDENTITY": frozenset(("target_measurement",)),
  "B4-SOURCE-BUILD-COMPATIBILITY": frozenset(("source_test", "host_test", "image_hash")),
  "B4-INSTALLED-DEVICE-IDENTITY": frozenset(("target_measurement",)),
  "B5-ISOLATED-BENCH": frozenset(("bench_record",)),
  "B6-CONTROLLED-VEHICLE": frozenset(("vehicle_record",)),
  "R-INDEPENDENT-REVIEW": frozenset(("source_review",)),
}
REQUIRED_IDS = tuple(REQUIRED_KINDS)
PHYSICAL_IDS = frozenset(i for i in REQUIRED_IDS if i.startswith(("B1-", "B5-", "B6-")) or i in
                         ("B3-TARGET-PANDA-RELEASE-IDENTITY", "B4-INSTALLED-DEVICE-IDENTITY"))
IDENTITY_IDS = {"panda_release_sha256": "B3-TARGET-PANDA-RELEASE-IDENTITY", "agnos_system_sha256": "B4-INSTALLED-DEVICE-IDENTITY"}
_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True, slots=True)
class TargetIdentity:
  """Synthetic, caller-supplied identity of the target being evaluated; not a measurement by this module."""

  panda_release_sha256: str
  agnos_system_sha256: str


@dataclass(frozen=True, slots=True)
class Authorization:
  eligible: bool
  holds: tuple[str, ...]
  qualified_identity: TargetIdentity | None


@dataclass(frozen=True, slots=True)
class GateRecord:
  """Shadow record is always computed for audit; proposal is None unless every gate holds."""

  proposal: SimulationRecord | None
  reason: str
  shadow: SimulationRecord


def assess_register(register: object, artifacts: object) -> Authorization:
  """Fail closed: any malformed, missing, non-PASS, unresolved or wrong-kind requirement is a hold.

  ``artifacts`` maps each evidence ``path`` to the artifact bytes the caller read; this module performs no I/O.
  """
  if type(register) is not dict or type(register.get("requirements")) is not list or type(artifacts) is not dict:
    return Authorization(False, ("register_invalid",), None)
  entries = {}
  for entry in register["requirements"]:
    if type(entry) is not dict or type(entry.get("id")) is not str or entry["id"] in entries:
      return Authorization(False, ("register_invalid",), None)
    entries[entry["id"]] = entry
  holds = tuple(rid for rid in REQUIRED_IDS if not _passed(rid, entries.get(rid), artifacts))
  if holds:
    return Authorization(False, holds, None)
  return Authorization(True, (), TargetIdentity(*(entries[rid]["qualified_identity"] for rid in IDENTITY_IDS.values())))


def _passed(rid: str, entry: object, artifacts: dict) -> bool:
  if type(entry) is not dict or entry.get("status") != "PASS":
    return False
  evidence, reviewer, author = entry.get("evidence"), entry.get("independent_reviewer"), entry.get("author")
  if type(evidence) is not list or not evidence or not _label(reviewer) or not _label(author) or reviewer == author:
    return False
  if not all(_resolved(item, REQUIRED_KINDS[rid], artifacts) for item in evidence):
    return False
  if rid in IDENTITY_IDS.values():
    # The qualified identity must be what the target measurement evidence actually recorded.
    qualified = entry.get("qualified_identity")
    return _sha256(qualified) and all(item.get("measured_sha256") == qualified for item in evidence)
  return True


def _resolved(item: object, kinds: frozenset, artifacts: dict) -> bool:
  if type(item) is not dict or item.get("kind") not in kinds or not _sha256(item.get("sha256")) or not _label(item.get("path")):
    return False
  data = artifacts.get(item["path"])
  return type(data) is bytes and bool(data) and sha256(data).hexdigest() == item["sha256"]


def _sha256(value: object) -> bool:
  return type(value) is str and len(value) == 64 and set(value) <= _HEX


def _label(value: object) -> bool:
  return type(value) is str and bool(value) and value == value.strip()


class SubordinateReleaseBGate:
  """Wraps the Dom-plan-following simulation; Dom remains the only planner and the OEM stack the only actuator owner."""

  def __init__(self, register: object, artifacts: object) -> None:
    self._authorization = assess_register(register, artifacts)
    self._simulation = PlanControllerSimulation()

  @property
  def authorization(self) -> Authorization:
    return self._authorization

  def reset(self) -> None:
    self._simulation.reset()

  def step(self, plan: object, observation: object, policy: object, now_monotonic: object,
           ownership: object, target: object) -> GateRecord:
    shadow = self._simulation.step(plan, observation, policy, now_monotonic)
    reason = self._gate_reason(shadow, ownership, target)
    if reason is not None:
      return GateRecord(None, reason, shadow)
    return GateRecord(shadow, "release_b_gates_passed_abstract_only", shadow)

  def _gate_reason(self, shadow: SimulationRecord, ownership: object, target: object) -> str | None:
    if not self._authorization.eligible:
      return f"release_b_qualification_hold:{self._authorization.holds[0]}"
    if type(target) is not TargetIdentity or target != self._authorization.qualified_identity:
      return "target_identity_mismatch"
    if type(ownership) is not OwnershipEvidence or ownership.state != STATE_OBSERVED_STOCK:
      return "oem_protection_state_not_observed"
    if shadow.mode == MODE_WITHDRAWN:
      return f"shadow_withdrawn:{shadow.reason}"
    return None

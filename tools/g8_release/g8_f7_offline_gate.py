#!/usr/bin/env python3
"""G8 F7 OFFLINE-ONLY gate and bounded startup/recovery model.

This module is deliberately non-deployable. It parses only caller-supplied,
bounded canonical JSON bytes, verifies detached signatures in memory, and
returns advisory analysis. It has no CLI, path, subprocess, network, device,
CAN, Panda, launcher, updater, ``abctl``, or execution interface.

A valid signature proves only that the supplied software key signed a claim.
It is never proof of hardware measurement, protected counters, secure boot,
production key custody, or a real health authority. Every accepted claim and
every success token is explicitly marked SIMULATED.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


SIMULATION_ONLY = "SIMULATED_F7_SOFTWARE_EVIDENCE_NOT_HARDWARE_AUTHORITY"
EVIDENCE_SCHEMA = "c7-g8-f7-simulated-external-evidence/1"
BUNDLE_SCHEMA = "c7-g8-f7-offline-input-bundle/1"
RESULT_SCHEMA = "c7-g8-f7-offline-analysis/1"
SIGNING_DOMAIN = b"c7-g8-f7-simulated-external-evidence/v1\x00"
F6_REFERENCE = "9e4398e54c0cddb42f8f006257c317f4362cc332"
F5_REFERENCE = "a0b5b6ff54e190e36b6374e2a6ec791e32465a08"
MAX_JSON_BYTES = 128 * 1024
MAX_EVIDENCE = 32
MAX_AGE_SECONDS = 3600

_HEX16 = re.compile(r"^[0-9a-f]{16}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]{1,96}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?$")

F6_OPEN_IDS = tuple(f"F6-OPEN-{i:02d}" for i in range(1, 11))
REQUIRED_EVIDENCE_KINDS = (
  "boot_chain", "protected_state", "early_boot", "immutable_runtime",
  "independent_health", "key_lifecycle", "native_abi", "bench_recovery",
  "panda_can", "regression",
)
EXPECTED_F7A = {
  "F7A_inventory": "COMPLETED_PASS_LIMITED_TO_PROBED_EVIDENCE",
  "production_security_feasibility": "UNKNOWN_HOLD",
  "F7B_installation": "NO_GO",
  "device_AGNOS": "19.8.1",
  "reported_boot_slot": "_a",
  "F6_reference_commit": F6_REFERENCE,
  "data_mount": "/dev/sda12 ext4 read-write, approximately 46 GB free",
}

EVIDENCE_ASSERTION_KEYS = {
  "boot_chain": frozenset({"agnos_version", "os_slot", "verity_root_sha256", "boot_chain_measured"}),
  "protected_state": frozenset({"counter", "nonce_history_protected", "rollback_protected"}),
  "early_boot": frozenset({"authority_precedes_mutable_launcher", "boot_success_deferred"}),
  "immutable_runtime": frozenset({"full_runtime_immutable", "data_mount_read_only", "dependency_closure_verified"}),
  "independent_health": frozenset({"boot_nonce", "counter", "heartbeat_fresh", "signer_independent", "tests_passed"}),
  "key_lifecycle": frozenset({"production_custody", "rotation_defined", "revocation_defined"}),
  "native_abi": frozenset({"agnos_version", "aarch64_native_verified", "loader_closure_verified"}),
  "bench_recovery": frozenset({"power_loss_matrix_complete", "storage_fault_matrix_complete", "rollback_verified"}),
  "panda_can": frozenset({"static_source_reviewed", "host_safety_tests_passed", "physical_vehicle_qualified"}),
  "regression": frozenset({"f7_host_suite_passed", "aarch64_suite_passed", "broad_non_honda_failures_resolved"}),
}


class ProtocolError(ValueError):
  """Fail-closed schema, signature, freshness, or state-machine rejection."""


def canonical(value: Any) -> bytes:
  """Return the only accepted JSON encoding; NaN/Infinity are forbidden."""
  try:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")
  except (TypeError, ValueError, UnicodeError) as error:
    raise ProtocolError("value is not canonical JSON") from error


def parse_canonical_json(data: Any, *, maximum: int = MAX_JSON_BYTES) -> Any:
  """Parse bounded canonical ASCII JSON. YAML/pickle/path inputs are absent."""
  if type(data) is not bytes or not 1 <= len(data) <= maximum:
    raise ProtocolError("input must be bounded canonical JSON bytes")
  try:
    value = json.loads(data.decode("ascii"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
  except (UnicodeDecodeError, UnicodeError, ValueError, TypeError) as error:
    raise ProtocolError("input is not strict JSON") from error
  if canonical(value) != data:
    raise ProtocolError("input JSON is not canonical")
  return value


def _strict_dict(value: Any, keys: set[str] | frozenset[str], label: str) -> dict[str, Any]:
  if type(value) is not dict or set(value) != set(keys) or any(type(k) is not str for k in value):
    raise ProtocolError(f"malformed {label}")
  return value


def _token(value: Any, label: str) -> str:
  if type(value) is not str or not _TOKEN.fullmatch(value):
    raise ProtocolError(f"malformed {label}")
  return value


def _integer(value: Any, label: str, low: int = 0, high: int = 2**63 - 1) -> int:
  if type(value) is not int or not low <= value <= high:
    raise ProtocolError(f"malformed {label}")
  return value


def _bool(value: Any, label: str) -> bool:
  if type(value) is not bool:
    raise ProtocolError(f"malformed {label}")
  return value


def _key_id(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()[:16]


def evidence_payload(kind: str, assertions: dict[str, Any], *, issued_at: int,
                     expires_at: int, evidence_id: str, issuer: str = "f7-test-authority") -> dict[str, Any]:
  """Build a strict payload for tests; the result is still only SIMULATED."""
  return {
    "schema": EVIDENCE_SCHEMA, "simulation_marker": SIMULATION_ONLY,
    "evidence_id": evidence_id, "issuer": issuer, "kind": kind,
    "issued_at": issued_at, "expires_at": expires_at,
    "f6_reference_commit": F6_REFERENCE, "assertions": copy.deepcopy(assertions),
  }


def _validate_assertion_types(kind: str, assertions: dict[str, Any]) -> None:
  for key, value in assertions.items():
    if key in {"agnos_version", "os_slot", "verity_root_sha256", "boot_nonce"}:
      if type(value) is not str:
        raise ProtocolError("malformed typed evidence assertion")
    elif key == "counter":
      _integer(value, "protected counter", 1)
    else:
      _bool(value, "boolean evidence assertion")
  if "agnos_version" in assertions and not _VERSION.fullmatch(assertions["agnos_version"]):
    raise ProtocolError("malformed AGNOS version")
  if "os_slot" in assertions and assertions["os_slot"] not in ("_a", "_b"):
    raise ProtocolError("malformed OS slot")
  if "verity_root_sha256" in assertions and not _HEX64.fullmatch(assertions["verity_root_sha256"]):
    raise ProtocolError("malformed verity root")
  if "boot_nonce" in assertions and not _HEX64.fullmatch(assertions["boot_nonce"]):
    raise ProtocolError("malformed boot nonce")


def verify_detached_evidence(payload_bytes: Any, signature_b64: Any, public_key_b64: Any,
                             *, expected_key_id: str, assessment_time: int) -> dict[str, Any]:
  """Verify one detached software signature and strict, fresh payload."""
  payload = parse_canonical_json(payload_bytes)
  keys = {"schema", "simulation_marker", "evidence_id", "issuer", "kind", "issued_at",
          "expires_at", "f6_reference_commit", "assertions"}
  _strict_dict(payload, keys, "evidence payload")
  if payload["schema"] != EVIDENCE_SCHEMA or payload["simulation_marker"] != SIMULATION_ONLY:
    raise ProtocolError("evidence is not explicitly simulated")
  _token(payload["evidence_id"], "evidence id")
  _token(payload["issuer"], "issuer")
  kind = _token(payload["kind"], "evidence kind")
  if kind not in EVIDENCE_ASSERTION_KEYS:
    raise ProtocolError("unknown evidence kind")
  assertions = _strict_dict(payload["assertions"], EVIDENCE_ASSERTION_KEYS[kind], "evidence assertions")
  issued = _integer(payload["issued_at"], "issued time")
  expires = _integer(payload["expires_at"], "expiry time")
  now = _integer(assessment_time, "assessment time")
  if issued > now or expires < now or expires <= issued or now - issued > MAX_AGE_SECONDS:
    raise ProtocolError("stale or future-dated evidence")
  if payload["f6_reference_commit"] != F6_REFERENCE:
    raise ProtocolError("evidence F6 commit mismatch")
  if type(expected_key_id) is not str or not _HEX16.fullmatch(expected_key_id):
    raise ProtocolError("malformed trusted key id")
  try:
    raw_key = base64.b64decode(public_key_b64, validate=True)
    signature = base64.b64decode(signature_b64, validate=True)
  except (TypeError, ValueError) as error:
    raise ProtocolError("malformed detached signature or public key") from error
  if len(raw_key) != 32 or _key_id(raw_key) != expected_key_id:
    raise ProtocolError("untrusted evidence signer")
  try:
    Ed25519PublicKey.from_public_bytes(raw_key).verify(signature, SIGNING_DOMAIN + payload_bytes)
  except (InvalidSignature, ValueError, TypeError) as error:
    raise ProtocolError("detached evidence signature invalid") from error
  _validate_assertion_types(kind, assertions)
  return copy.deepcopy(payload)


@dataclass(frozen=True)
class OfflineGateResult:
  schema: str
  simulation_marker: str
  offline_review: str
  production_trust: str
  production_release: str
  installation_authorized: bool
  device_actions_authorized: bool
  permitted_offline_actions: tuple[str, ...]
  reason_codes: tuple[str, ...]
  accepted_evidence_kinds: tuple[str, ...]

  def __post_init__(self) -> None:
    if (self.schema != RESULT_SCHEMA or self.simulation_marker != SIMULATION_ONLY or
        self.production_trust != "UNKNOWN" or self.production_release != "HOLD" or
        self.installation_authorized or self.device_actions_authorized):
      raise ProtocolError("offline result must never authorize device or production")

  def as_dict(self) -> dict[str, Any]:
    return {
      "schema": self.schema, "simulation_marker": self.simulation_marker,
      "offline_review": self.offline_review, "production_trust": self.production_trust,
      "production_release": self.production_release,
      "installation_authorized": self.installation_authorized,
      "device_actions_authorized": self.device_actions_authorized,
      "permitted_offline_actions": list(self.permitted_offline_actions),
      "reason_codes": list(self.reason_codes),
      "accepted_evidence_kinds": list(self.accepted_evidence_kinds),
    }


def _validate_f7a(f7a: Any) -> list[str]:
  if type(f7a) is not dict:
    return ["F7A_MISSING_OR_MALFORMED"]
  problems = ["F7A_MISMATCH_" + key.upper() for key, expected in EXPECTED_F7A.items()
              if f7a.get(key) != expected or type(f7a.get(key)) is not type(expected)]
  if f7a.get("device_modified") is not False:
    problems.append("F7A_NONMUTATION_MISSING")
  problems.append("OBSERVED_DATA_MOUNT_MUTABLE")
  return problems


def _validate_open_items(open_items: Any) -> list[str]:
  if type(open_items) is not dict or set(open_items) != set(F6_OPEN_IDS):
    return ["F6_OPEN_REGISTER_INCOMPLETE"]
  if any(type(open_items[k]) is not str or open_items[k] not in ("OPEN", "DEFERRED_BLOCKER")
         for k in F6_OPEN_IDS):
    return ["F6_OPEN_ITEM_NOT_RETAINED"]
  return []


def _claim_problem_codes(claims: dict[str, dict[str, Any]]) -> list[str]:
  p: list[str] = []
  boot = claims.get("boot_chain", {}).get("assertions", {})
  state = claims.get("protected_state", {}).get("assertions", {})
  early = claims.get("early_boot", {}).get("assertions", {})
  runtime = claims.get("immutable_runtime", {}).get("assertions", {})
  health = claims.get("independent_health", {}).get("assertions", {})
  required_true = {
    "boot_chain": ("boot_chain_measured",),
    "protected_state": ("nonce_history_protected", "rollback_protected"),
    "early_boot": ("authority_precedes_mutable_launcher", "boot_success_deferred"),
    "immutable_runtime": ("full_runtime_immutable", "data_mount_read_only", "dependency_closure_verified"),
    "independent_health": ("heartbeat_fresh", "signer_independent", "tests_passed"),
    "key_lifecycle": ("production_custody", "rotation_defined", "revocation_defined"),
    "native_abi": ("aarch64_native_verified", "loader_closure_verified"),
    "bench_recovery": ("power_loss_matrix_complete", "storage_fault_matrix_complete", "rollback_verified"),
    "panda_can": ("static_source_reviewed", "host_safety_tests_passed", "physical_vehicle_qualified"),
    "regression": ("f7_host_suite_passed", "aarch64_suite_passed", "broad_non_honda_failures_resolved"),
  }
  for kind, keys in required_true.items():
    values = claims.get(kind, {}).get("assertions", {})
    if any(values.get(key) is not True for key in keys):
      p.append("EVIDENCE_NEGATIVE_" + kind.upper())
  if boot.get("agnos_version") != EXPECTED_F7A["device_AGNOS"]:
    p.append("STALE_OR_MISMATCHED_AGNOS")
  if boot.get("os_slot") != EXPECTED_F7A["reported_boot_slot"]:
    p.append("STALE_OR_MISMATCHED_OS_SLOT")
  if health.get("counter") != state.get("counter"):
    p.append("HEALTH_COUNTER_MISMATCH")
  if not state.get("counter"):
    p.append("PROTECTED_COUNTER_MISSING")
  if early and not early.get("boot_success_deferred"):
    p.append("PREMATURE_BOOT_SUCCESS")
  if runtime and not runtime.get("data_mount_read_only"):
    p.append("MUTABLE_RUNTIME")
  return p


def evaluate_signed_bundle(f7a: Any, open_items: Any, evidence: Any, trusted_keys: Any,
                           *, assessment_time: int) -> OfflineGateResult:
  """Analyze signed synthetic claims. Raw inputs never enter output strings."""
  problems = _validate_f7a(f7a) + _validate_open_items(open_items)
  accepted: dict[str, dict[str, Any]] = {}
  if type(trusted_keys) is not dict or not trusted_keys:
    problems.append("TRUST_STORE_MISSING")
  if type(evidence) is not list or not 1 <= len(evidence) <= MAX_EVIDENCE:
    problems.append("EVIDENCE_SET_MISSING_OR_OVERSIZED")
  else:
    seen_ids: set[str] = set()
    for item in evidence:
      try:
        _strict_dict(item, {"payload", "signature", "key_id"}, "evidence envelope")
        key_id = item["key_id"]
        _token(key_id, "key id")
        public = trusted_keys[key_id] if type(trusted_keys) is dict else None
        claim = verify_detached_evidence(item["payload"], item["signature"], public,
                                         expected_key_id=key_id, assessment_time=assessment_time)
        if claim["evidence_id"] in seen_ids or claim["kind"] in accepted:
          raise ProtocolError("duplicate evidence")
        seen_ids.add(claim["evidence_id"])
        accepted[claim["kind"]] = claim
      except (ProtocolError, KeyError, TypeError):
        problems.append("EVIDENCE_REJECTED")
  if set(REQUIRED_EVIDENCE_KINDS) - set(accepted):
    problems.append("EVIDENCE_KINDS_INCOMPLETE")
  problems.extend(_claim_problem_codes(accepted))
  problems.append("SOFTWARE_SIGNATURE_IS_NOT_HARDWARE_PROOF")
  reason_codes = tuple(sorted(set(problems)))
  technical = {"OBSERVED_DATA_MOUNT_MUTABLE", "SOFTWARE_SIGNATURE_IS_NOT_HARDWARE_PROOF"}
  return OfflineGateResult(
    schema=RESULT_SCHEMA, simulation_marker=SIMULATION_ONLY,
    offline_review="SIMULATED_EVIDENCE_COMPLETE" if set(reason_codes) == technical else "BLOCKED",
    production_trust="UNKNOWN", production_release="HOLD",
    installation_authorized=False, device_actions_authorized=False,
    permitted_offline_actions=("STATIC_SOURCE_REVIEW", "HOST_SIMULATION", "REPORT_GENERATION"),
    reason_codes=reason_codes, accepted_evidence_kinds=tuple(sorted(accepted)),
  )


def analyze_canonical_bundle(bundle_bytes: Any, trusted_keys: Any, *,
                             assessment_time: int) -> OfflineGateResult:
  """Strict external boundary using data bytes only—never caller paths.

  Detached payloads are base64 inside the outer canonical JSON document so the
  exact signed bytes survive transport without an ambiguous JSON re-encoding.
  """
  bundle = parse_canonical_json(bundle_bytes)
  _strict_dict(bundle, {"schema", "simulation_marker", "f7a_gatecard",
                        "f6_open_items", "evidence"}, "input bundle")
  if bundle["schema"] != BUNDLE_SCHEMA or bundle["simulation_marker"] != SIMULATION_ONLY:
    raise ProtocolError("input bundle is not explicitly simulated")
  if type(bundle["evidence"]) is not list:
    raise ProtocolError("malformed evidence set")
  decoded = []
  for item in bundle["evidence"]:
    _strict_dict(item, {"payload_b64", "signature", "key_id"}, "transport envelope")
    try:
      payload = base64.b64decode(item["payload_b64"], validate=True)
    except (TypeError, ValueError) as error:
      raise ProtocolError("malformed signed payload transport") from error
    decoded.append({"payload": payload, "signature": item["signature"], "key_id": item["key_id"]})
  return evaluate_signed_bundle(bundle["f7a_gatecard"], bundle["f6_open_items"], decoded,
                                trusted_keys, assessment_time=assessment_time)


class Phase(str, Enum):
  IDLE = "IDLE"
  STARTED = "STARTED"
  CONSUMED = "CONSUMED"
  HEALTH_VERIFIED = "HEALTH_VERIFIED"
  ABORTED = "ABORTED"


class MockTrial:
  """Bounded volatile host model; no durable/protected state or real abctl call."""

  def __init__(self, *, slot: str, image_digest: str, max_attempts: int = 2):
    if slot not in ("_a", "_b"):
      raise ProtocolError("invalid OS slot")
    if type(image_digest) is not str or not _HEX64.fullmatch(image_digest):
      raise ProtocolError("invalid image digest")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 5:
      raise ProtocolError("invalid attempt bound")
    self.slot, self.image_digest, self.max_attempts = slot, image_digest, max_attempts
    self.attempts = self.protected_counter = 0
    self.phase = Phase.IDLE
    self.seen_nonces: set[str] = set()
    self.nonce: str | None = None
    self.boot_success_simulated = False

  @staticmethod
  def _nonce(nonce: Any) -> None:
    if type(nonce) is not str or not _HEX64.fullmatch(nonce):
      raise ProtocolError("invalid boot nonce")

  def begin(self, *, nonce: str, reported_slot: str, measured_digest: str,
            provenance_authenticated: bool, counter: int | None = None) -> None:
    self._nonce(nonce)
    expected_counter = self.protected_counter + 1
    if self.phase not in (Phase.IDLE, Phase.ABORTED):
      raise ProtocolError("previous trial unresolved")
    if self.attempts >= self.max_attempts:
      raise ProtocolError("retry limit exhausted")
    if nonce in self.seen_nonces:
      raise ProtocolError("nonce replay")
    if counter is not None and (type(counter) is not int or counter != expected_counter):
      raise ProtocolError("protected counter rollback or jump")
    if provenance_authenticated is not True or reported_slot != self.slot or measured_digest != self.image_digest:
      raise ProtocolError("mock boot identity/provenance mismatch")
    self.seen_nonces.add(nonce)
    self.nonce, self.attempts = nonce, self.attempts + 1
    self.protected_counter = expected_counter
    self.boot_success_simulated = False
    self.phase = Phase.STARTED

  def consume(self, *, nonce: str) -> None:
    if self.phase != Phase.STARTED or nonce != self.nonce:
      raise ProtocolError("trial cannot be consumed")
    self.phase = Phase.CONSUMED

  def health(self, *, nonce: str, reported_slot: str, measured_digest: str,
             signer_authenticated: bool, tests_passed: bool, heartbeat_fresh: bool = True,
             counter: int | None = None) -> None:
    if self.phase != Phase.CONSUMED or nonce != self.nonce:
      raise ProtocolError("health before trial consumption or stale nonce")
    if counter is not None and (type(counter) is not int or counter != self.protected_counter):
      raise ProtocolError("stale health counter")
    if signer_authenticated is not True or tests_passed is not True or heartbeat_fresh is not True:
      raise ProtocolError("unauthenticated, unhealthy, or stale heartbeat")
    if reported_slot != self.slot or measured_digest != self.image_digest:
      raise ProtocolError("health bound to incorrect image or slot")
    self.phase = Phase.HEALTH_VERIFIED

  def simulated_success(self, *, nonce: str) -> str:
    if self.phase != Phase.HEALTH_VERIFIED or nonce != self.nonce:
      raise ProtocolError("premature boot-success acknowledgment")
    self.boot_success_simulated = True
    return "SIMULATED_BOOT_SUCCESS_NOT_ABCTL"

  def abort(self) -> None:
    if self.phase not in (Phase.STARTED, Phase.CONSUMED):
      raise ProtocolError("no active trial to abort")
    self.phase, self.boot_success_simulated = Phase.ABORTED, False

  def powercut(self) -> None:
    if self.phase in (Phase.STARTED, Phase.CONSUMED):
      self.abort()

  def storage_fault(self) -> None:
    if self.phase in (Phase.STARTED, Phase.CONSUMED):
      self.abort()

  def restore_state_from_old_copy(self, _state: Mapping[str, Any]) -> None:
    raise ProtocolError("mock storage cannot authenticate restored monotonic state")


def f7a_minimal_observed_gatecard() -> dict[str, Any]:
  """Known observations only; this is not a trusted device attestation."""
  return {**EXPECTED_F7A, "device_modified": False}


def unresolved_f6_items() -> dict[str, str]:
  return {item: "DEFERRED_BLOCKER" for item in F6_OPEN_IDS}

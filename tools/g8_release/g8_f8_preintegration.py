#!/usr/bin/env python3
"""Offline-only G8 F8 pre-integration assessment and manifest guard.

This module has no CLI, path, network, subprocess, device, Panda, CAN, boot,
key-generation, signing, or execution interface.  It consumes only bounded,
canonical JSON bytes and returns advisory data.  In particular, caller input
can never establish a hardware root of trust: such provenance must be checked
by a future platform verifier that is intentionally absent here.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


BUNDLE_SCHEMA = "c7-g8-f8-offline-preintegration/1"
RESULT_SCHEMA = "c7-g8-f8-offline-assessment/1"
MANIFEST_SCHEMA = "c7-g8-f8-runtime-manifest/1"
OFFLINE_MARKER = "F8_HOST_ONLY_NON_DEPLOYABLE"
F7_REFERENCE = "8fe7fb42c320316d74868321247ce0255ec80cb2"
MAX_JSON_BYTES = 128 * 1024
MAX_AGE_SECONDS = 3600
MAX_COMPONENTS = 128

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_.:-]{1,96}$")

EVIDENCE_TYPES = frozenset({
  "OBSERVED_INVENTORY", "SOURCE_DERIVED", "GENERIC_DOCUMENTATION",
  "SOFTWARE_SIGNED_SYNTHETIC",
})
REQUIRED_CONTROLS = (
  "authority_outside_data", "slot_digest_secure_binding", "protected_monotonic_state",
  "nonce_bound_health", "claim_freshness", "delayed_boot_success", "key_lifecycle",
  "immutable_dependency_closure", "no_capability_fallback", "native_agnos_abi",
  "physical_fault_recovery", "panda_can_failsafe", "broad_regression_closure",
)
HARDWARE_CONTROLS = frozenset({
  "slot_digest_secure_binding", "protected_monotonic_state", "nonce_bound_health",
  "delayed_boot_success", "native_agnos_abi", "physical_fault_recovery",
  "panda_can_failsafe",
})
OBSERVED_LIMITS = {
  "agnos_version": "19.8.1",
  "kernel": "4.9.103",
  "architecture": "aarch64",
  "reported_slot": "_a",
  "root_read_only": True,
  "data_read_only": False,
  "root_free_mb": 272,
  "launcher_early_set_success_observed": True,
}


class AssessmentError(ValueError):
  """Strict input, typing, freshness, or contract rejection."""


def canonical(value: Any) -> bytes:
  try:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")
  except (TypeError, ValueError, UnicodeError) as error:
    raise AssessmentError("value is not canonical JSON") from error


def parse_canonical_json(data: Any) -> Any:
  if type(data) is not bytes or not 1 <= len(data) <= MAX_JSON_BYTES:
    raise AssessmentError("input must be bounded canonical JSON bytes")
  try:
    value = json.loads(data.decode("ascii"),
                       parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
                       object_pairs_hook=_unique_object)
  except (UnicodeError, ValueError, TypeError) as error:
    raise AssessmentError("input is not strict unique-key JSON") from error
  if canonical(value) != data:
    raise AssessmentError("input JSON is not canonical")
  return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for key, value in pairs:
    if key in result:
      raise ValueError("duplicate JSON key")
    result[key] = value
  return result


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
  if type(value) is not dict or set(value) != keys or any(type(k) is not str for k in value):
    raise AssessmentError(f"malformed {label}")
  return value


def _token(value: Any, label: str) -> str:
  if type(value) is not str or not _TOKEN.fullmatch(value):
    raise AssessmentError(f"malformed {label}")
  return value


def _integer(value: Any, label: str, low: int = 0, high: int = 2**63 - 1) -> int:
  if type(value) is not int or not low <= value <= high:
    raise AssessmentError(f"malformed {label}")
  return value


def _boolean(value: Any, label: str) -> bool:
  if type(value) is not bool:
    raise AssessmentError(f"malformed {label}")
  return value


def validate_runtime_manifest(value: Any, *, assessment_time: int) -> tuple[str, ...]:
  """Validate a caller-supplied immutable-runtime description, without paths."""
  keys = {"schema", "generated_at", "agnos_version", "kernel", "architecture",
          "interpreter", "loader", "components"}
  manifest = _exact(value, keys, "runtime manifest")
  if manifest["schema"] != MANIFEST_SCHEMA:
    raise AssessmentError("runtime manifest schema mismatch")
  now = _integer(assessment_time, "assessment time")
  generated = _integer(manifest["generated_at"], "manifest generation time")
  if generated > now or now - generated > MAX_AGE_SECONDS:
    raise AssessmentError("runtime manifest is stale or future dated")
  if (manifest["agnos_version"] != "19.8.1" or manifest["kernel"] != "4.9.103" or
      manifest["architecture"] != "aarch64"):
    raise AssessmentError("runtime target mismatch")
  components = manifest["components"]
  if type(components) is not list or not 1 <= len(components) <= MAX_COMPONENTS:
    raise AssessmentError("runtime component set missing or oversized")
  names: set[str] = set()
  roles: set[str] = set()
  for item in components:
    _exact(item, {"name", "role", "sha256", "mount_class", "read_only", "executable"},
           "runtime component")
    name = _token(item["name"], "component name")
    role = _token(item["role"], "component role")
    if name in names:
      raise AssessmentError("duplicate runtime component")
    names.add(name)
    roles.add(role)
    if type(item["sha256"]) is not str or not _HEX64.fullmatch(item["sha256"]):
      raise AssessmentError("malformed runtime digest")
    if item["mount_class"] not in ("VERIFIED_ROOT", "VERIFIED_APP_IMAGE"):
      raise AssessmentError("mutable or unverified runtime mount")
    if _boolean(item["read_only"], "component read-only") is not True:
      raise AssessmentError("writable runtime component")
    _boolean(item["executable"], "component executable")
  interpreter = _token(manifest["interpreter"], "interpreter component")
  loader = _token(manifest["loader"], "loader component")
  if interpreter not in names or loader not in names:
    raise AssessmentError("interpreter or loader absent from closure")
  if not {"application", "interpreter", "loader", "crypto"}.issubset(roles):
    raise AssessmentError("runtime dependency roles incomplete")
  return tuple(sorted(names))


@dataclass(frozen=True)
class AssessmentResult:
  schema: str
  marker: str
  docs_prepared: bool
  offline_preintegration: str
  hardware_qualified: bool
  production_release_go: bool
  installation_authorized: bool
  device_actions_authorized: bool
  accepted_controls: tuple[str, ...]
  reason_codes: tuple[str, ...]

  def __post_init__(self) -> None:
    if (self.schema != RESULT_SCHEMA or self.marker != OFFLINE_MARKER or
        self.hardware_qualified or self.production_release_go or
        self.installation_authorized or self.device_actions_authorized):
      raise AssessmentError("offline result cannot authorize hardware or release")

  def as_dict(self) -> dict[str, Any]:
    return {
      "schema": self.schema, "marker": self.marker,
      "docs_prepared": self.docs_prepared,
      "offline_preintegration": self.offline_preintegration,
      "hardware_qualified": self.hardware_qualified,
      "production_release_go": self.production_release_go,
      "installation_authorized": self.installation_authorized,
      "device_actions_authorized": self.device_actions_authorized,
      "accepted_controls": list(self.accepted_controls),
      "reason_codes": list(self.reason_codes),
    }


def assess_canonical_bundle(data: Any) -> AssessmentResult:
  """Assess documentation and synthetic guards; never certify trusted hardware."""
  bundle = _exact(parse_canonical_json(data), {
    "schema", "marker", "f7_reference", "assessment_time", "observed",
    "contract_evidence", "runtime_manifest",
  }, "assessment bundle")
  if (bundle["schema"] != BUNDLE_SCHEMA or bundle["marker"] != OFFLINE_MARKER or
      bundle["f7_reference"] != F7_REFERENCE):
    raise AssessmentError("bundle identity mismatch")
  now = _integer(bundle["assessment_time"], "assessment time")
  if bundle["observed"] != OBSERVED_LIMITS:
    raise AssessmentError("observed F7A boundary mismatch")
  validate_runtime_manifest(bundle["runtime_manifest"], assessment_time=now)
  evidence = bundle["contract_evidence"]
  if type(evidence) is not list or len(evidence) != len(REQUIRED_CONTROLS):
    raise AssessmentError("contract evidence set incomplete")
  accepted: set[str] = set()
  reasons = {
    "HARDWARE_ROOTED_ATTESTATION_NOT_DEMONSTRATED",
    "PROTECTED_MONOTONIC_STATE_NOT_DEMONSTRATED",
    "QSEE_RPMB_TRUSTED_EARLY_BOOT_NOT_DEMONSTRATED",
    "VERITY_SECURE_MEASURED_APP_NOT_DEMONSTRATED",
    "NATIVE_AGNOS_AND_PHYSICAL_BENCH_NOT_QUALIFIED",
    "PANDA_CAN_AND_BROAD_REGRESSION_HOLD",
  }
  boot_binding: tuple[str, str, int, int, str] | None = None
  for item in evidence:
    _exact(item, {"control", "evidence_type", "claim", "issued_at", "expires_at",
                  "slot", "boot_nonce", "counter", "attempt", "image_digest"},
           "contract evidence")
    control = _token(item["control"], "control")
    if control not in REQUIRED_CONTROLS or control in accepted:
      raise AssessmentError("unknown or duplicate control")
    evidence_type = item["evidence_type"]
    if evidence_type not in EVIDENCE_TYPES:
      raise AssessmentError("unsupported or forged evidence provenance")
    issued = _integer(item["issued_at"], "claim issue time")
    expires = _integer(item["expires_at"], "claim expiry time")
    if issued > now or expires < now or expires <= issued or now - issued > MAX_AGE_SECONDS:
      raise AssessmentError("stale or future-dated contract claim")
    if _boolean(item["claim"], "control claim") is not True:
      raise AssessmentError("negative contract control")
    if item["slot"] != "_a":
      raise AssessmentError("slot binding mismatch")
    if type(item["boot_nonce"]) is not str or not _HEX64.fullmatch(item["boot_nonce"]):
      raise AssessmentError("nonce binding malformed")
    counter = _integer(item["counter"], "boot counter", 1)
    attempt = _integer(item["attempt"], "attempt number", 1, 5)
    if type(item["image_digest"]) is not str or not _HEX64.fullmatch(item["image_digest"]):
      raise AssessmentError("image digest malformed")
    candidate_binding = (item["slot"], item["boot_nonce"], counter, attempt, item["image_digest"])
    if boot_binding is None:
      boot_binding = candidate_binding
    elif candidate_binding != boot_binding:
      raise AssessmentError("boot evidence binding mismatch or rollback")
    if control in HARDWARE_CONTROLS and evidence_type != "SOFTWARE_SIGNED_SYNTHETIC":
      raise AssessmentError("hardware control lacks explicitly synthetic test evidence")
    accepted.add(control)
  complete = accepted == set(REQUIRED_CONTROLS)
  return AssessmentResult(
    schema=RESULT_SCHEMA, marker=OFFLINE_MARKER, docs_prepared=complete,
    offline_preintegration="CONDITIONALLY_PREPARED" if complete else "HOLD",
    hardware_qualified=False, production_release_go=False,
    installation_authorized=False, device_actions_authorized=False,
    accepted_controls=tuple(sorted(accepted)), reason_codes=tuple(sorted(reasons)),
  )

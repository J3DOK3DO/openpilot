#!/usr/bin/env python3
"""G8-F12 RC3 Honda: NON-DEPLOYABLE host-only signed-context verifier.

This is an offline *negative assurance* and protocol specimen.  It has no
signing keys, launch/install/device/network/boot interfaces, storage, or
authority to release a CAN-controlling application.  The caller's public key,
expected measurements and floor are NOT trusted roots on commodity /data.
Passing this function only proves that its supplied test data are consistent.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PLATFORM = "HONDA_ACCORD_11G"
SCHEMA = "G8_F12_RC3_STAGE2BC_SIGNED_CONTEXT_TEST_V1"
TRUST = "SIMULATED_TEST_TRUST_ONLY"
DOMAIN = b"g8-f12-rc3/stage2bc/full-context/test-only/v1\x00"
_MAX_JSON_BYTES = 8192
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z")
_SLOTS = ("OS_A", "OS_B")
_ALLOWED_CONTEXT = frozenset({
  "schema", "trust", "platform", "agnos", "os_slot", "os_boot_nonce",
  "os_boot_sequence", "rootfs_sha256", "comma_identity_sha256",
  "panda_identity_sha256", "source_commit", "manifest_sha256",
  "app_snapshot_sha256", "recovery_snapshot_sha256", "gate_receipt_sha256",
  "attempt_nonce", "attempt_number", "monotonic_epoch", "neutral_can",
  "physical_gate_observed", "operation",
})
_ALLOWED_ENVELOPE = frozenset(("schema", "trust", "key_id", "context", "signature"))


class ContextVerificationError(ValueError):
  pass


def _pairs_strict(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for k, v in pairs:
    if k in result:
      raise ContextVerificationError("duplicate JSON key")
    result[k] = v
  return result


def strict_json_decode(raw: bytes) -> Any:
  if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_JSON_BYTES:
    raise ContextVerificationError("JSON input has unsafe size/type")
  try:
    x = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_strict,
                   parse_constant=lambda _s: (_ for _ in ()).throw(
                     ContextVerificationError("non-finite JSON constant")))
  except (UnicodeError, json.JSONDecodeError, TypeError) as ex:
    raise ContextVerificationError("malformed UTF-8 JSON") from ex
  if _canonical(x) != raw:
    raise ContextVerificationError("signed input not canonical JSON")
  return x


def _canonical(obj: Any) -> bytes:
  try:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                     allow_nan=False).encode("utf-8")
  except (ValueError, TypeError) as ex:
    raise ContextVerificationError("unsupported JSON value") from ex
  if len(raw) > _MAX_JSON_BYTES:
    raise ContextVerificationError("canonical record oversized")
  return raw


def _hex(val: Any, name: str, forty: bool = False) -> None:
  if type(val) is not str or not ((_HEX40 if forty else _HEX64).fullmatch(val)):
    raise ContextVerificationError(f"invalid {name}")


def _context(obj: Any) -> None:
  if type(obj) is not dict or set(obj) != _ALLOWED_CONTEXT:
    raise ContextVerificationError("full launch context schema mismatch")
  if obj["schema"] != SCHEMA or obj["trust"] != TRUST or obj["platform"] != PLATFORM:
    raise ContextVerificationError("wrong schema/trust/platform")
  if (type(obj["agnos"]) is not str or not _TOKEN.fullmatch(obj["agnos"]) or
      obj["os_slot"] not in _SLOTS or type(obj["os_slot"]) is not str):
    raise ContextVerificationError("invalid OS binding")
  if obj["operation"] != "HOST_MODEL_CONTEXT_ONLY":
    raise ContextVerificationError("production-capable operations never allowed")
  for k in (
      "os_boot_nonce", "rootfs_sha256", "comma_identity_sha256",
      "panda_identity_sha256", "manifest_sha256", "app_snapshot_sha256",
      "recovery_snapshot_sha256", "gate_receipt_sha256", "attempt_nonce"):
    _hex(obj[k], k)
  _hex(obj["source_commit"], "source_commit", forty=True)
  for k in ("os_boot_sequence", "attempt_number", "monotonic_epoch"):
    if type(obj[k]) is not int or obj[k] < 1 or obj[k] > 2**63-1:
      raise ContextVerificationError("invalid monotonic counter")
  if obj["neutral_can"] is not True:
    raise ContextVerificationError("neutral-CAN claim absent")
  if type(obj["physical_gate_observed"]) is not bool:
    raise ContextVerificationError("physical gate is not an exact boolean")


@dataclass(frozen=True)
class HostOnlyContextResult:
  context_digest_sha256: str
  source_commit: str
  os_slot: str
  boot_sequence: int
  monotonic_epoch: int
  attempt_number: int
  signature_matched_pinned_test_key: bool = True
  trusted_hardware_root_proven: bool = False
  hardware_antirollback_proven: bool = False
  protected_journal_proven: bool = False
  physical_honda_can_qualified: bool = False
  installation_authorized: bool = False
  boot_slot_change_authorized: bool = False
  panda_can_actuation_authorized: bool = False
  road_use_authorized: bool = False


def verify_signed_test_context(
    envelope_bytes: bytes, *, expected_context: dict[str, Any],
    pinned_test_public_key: bytes, protected_epoch_floor: int) -> HostOnlyContextResult:
  """Strict signed equality check; all trust inputs caller-controlled in this prototype.

  No code path returns installation/launch/boot/Panda/CAN authorization.
  The epoch floor MUST come from a protected monotonic hardware authority in
  future production integration; here it is only mock input.
  """
  if type(protected_epoch_floor) is not int or protected_epoch_floor < 0:
    raise ContextVerificationError("invalid protected epoch floor")
  if type(pinned_test_public_key) is not bytes or len(pinned_test_public_key) != 32:
    raise ContextVerificationError("invalid pinned Ed25519 test public key")
  _context(expected_context)
  envelope = strict_json_decode(envelope_bytes)
  if type(envelope) is not dict or set(envelope) != _ALLOWED_ENVELOPE:
    raise ContextVerificationError("envelope schema mismatch")
  if envelope["schema"] != SCHEMA or envelope["trust"] != TRUST:
    raise ContextVerificationError("envelope test-trust binding mismatch")
  expected_id = hashlib.sha256(pinned_test_public_key).hexdigest()[:16]
  if type(envelope["key_id"]) is not str or envelope["key_id"] != expected_id:
    raise ContextVerificationError("wrong pinned test-signing identity")
  _context(envelope["context"])
  if _canonical(envelope["context"]) != _canonical(expected_context):
    raise ContextVerificationError("signed full launch context does not match expected")
  if envelope["context"]["monotonic_epoch"] <= protected_epoch_floor:
    raise ContextVerificationError("stale or replayed protected epoch")
  signature_text = envelope["signature"]
  if type(signature_text) is not str or len(signature_text) > 100:
    raise ContextVerificationError("signature encoding malformed")
  try:
    signature = base64.b64decode(signature_text, validate=True)
    if len(signature) != 64 or base64.b64encode(signature).decode("ascii") != signature_text:
      raise ContextVerificationError("noncanonical or non-Ed25519 signature")
    Ed25519PublicKey.from_public_bytes(pinned_test_public_key).verify(
      signature, DOMAIN + _canonical(envelope["context"]))
  except (InvalidSignature, ValueError, binascii.Error) as ex:
    raise ContextVerificationError("invalid Ed25519 signed context") from ex
  context = envelope["context"]
  return HostOnlyContextResult(
    context_digest_sha256=hashlib.sha256(_canonical(context)).hexdigest(),
    source_commit=context["source_commit"],
    os_slot=context["os_slot"],
    boot_sequence=context["os_boot_sequence"],
    monotonic_epoch=context["monotonic_epoch"],
    attempt_number=context["attempt_number"],
  )


def integration_constraints() -> dict[str, Any]:
  """Testable Stage 2C OS service boundary; no systemd unit or launcher."""
  return {
    "kind": "DESIGN_ONLY_NO_PROCESS_EXECUTION",
    "honda_only": True,
    "signature_library": "cryptography.Ed25519PublicKey",
    "root_of_trust_provisioned": False,
    "protected_epoch_floor_available": False,
    "os_resident_service_installed": False,
    "immutable_recovery_snapshot_proven": False,
    "device_startup_qualified": False,
    "operation_whitelist": ["HOST_MODEL_CONTEXT_ONLY"],
    "production_install": False, "boot_slot_switch": False,
    "panda_can": False, "road_use": False,
  }

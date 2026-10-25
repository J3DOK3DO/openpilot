#!/usr/bin/env python3
"""Offline, fail-closed RC3 physical-evidence readiness gate.

This program only reads caller-designated host files.  It has no network,
device, process-execution, installation, boot-slot, Panda, or CAN interface.
It never authorizes installation or boot operations.  A structurally complete
synthetic fixture remains a HOLD.  A complete physical evidence set means only
that this offline verifier found the required, independently signed records;
it is not a production or installation approval.

Ed25519 verification below is a small RFC 8032-compatible verification-only
implementation using Python's standard library.  There is deliberately no key
generation or signing function in this module.  The trust-policy digest must
be pinned by the caller outside the evidence manifest.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "G8_F12_RC3_HARDWARE_EVIDENCE_MANIFEST_V1"
TRUST_POLICY_SCHEMA = "G8_F12_RC3_ATTESTER_TRUST_POLICY_V1"
OBSERVATION_SCHEMA = "G8_F12_RC3_SIGNED_OBSERVATION_V1"
GATECARD_SCHEMA = "G8_F12_RC3_HARDWARE_READINESS_GATECARD_V1"
SIGNATURE_DOMAIN = b"g8-f12-rc3/hardware-observation/v1\x00"

FROZEN_COMMIT = "bbb771a2fadf5af96f532e798846ba8171483e50"
FROZEN_TREE = "fcd3142e877a165911a677f9361c6594f3eecf6b"
ENGINEERING_COMMIT = "93cf96efd6b026854464b9aa505f01ad3c45b4a2"
ENGINEERING_TREE = "a9a481ad44848c2708ef7c1bc45b24fcf3fcd48a"
PLATFORM = "HONDA_ACCORD_11G"

MAX_MANIFEST_BYTES = 1 << 20
MAX_POLICY_BYTES = 1 << 20
MAX_ARTIFACT_BYTES = 4 << 20
MAX_TOTAL_ARTIFACT_BYTES = 32 << 20
MAX_EVIDENCE_AGE = timedelta(days=30)
MAX_CLOCK_SKEW = timedelta(minutes=5)

PHYSICAL = "PHYSICAL_DEVICE_EVIDENCE"
SYNTHETIC = "SYNTHETIC_TEST_FIXTURE"
CLASSIFICATIONS = frozenset({PHYSICAL, SYNTHETIC})

REQUIRED_ARTIFACTS: dict[str, tuple[str, tuple[str, ...]]] = {
  "boot_trust_antirollback": (
    "PHYSICAL_DEVICE",
    ("boot_chain_measurement", "antirollback_test"),
  ),
  "os_resident_supervisor": (
    "PHYSICAL_DEVICE",
    ("os_placement_measurement", "isolation_test"),
  ),
  "authenticated_trial_recovery": (
    "PHYSICAL_DEVICE",
    ("authority_authentication_test", "transactional_recovery_test"),
  ),
  "signed_reproducible_package": (
    "REPRODUCIBLE_BUILD_LAB",
    ("signed_package_verification", "reproducible_build_comparison"),
  ),
  "native_arm64_neutral_can": (
    "PHYSICAL_DEVICE_NEUTRAL_CAN",
    ("arm64_startup_log", "model_execution_log", "pandad_neutral_can_log"),
  ),
  "physical_failure_recovery": (
    "PHYSICAL_DEVICE_POWER_FAULT_LAB",
    ("bootloop_matrix", "powercut_matrix", "forced_failure_matrix", "recovery_observation"),
  ),
  "honda11g_panda_can_bench": (
    "HONDA_11G_NON_VEHICLE_BENCH",
    ("fail_silent_test", "watchdog_test", "disengagement_test", "allowlist_test",
     "heartbeat_test", "bench_safety_summary"),
  ),
}

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+:-]{0,127}$")
_MEDIA_TYPES = frozenset({"application/json", "application/octet-stream", "text/csv", "text/plain"})


class EvidenceError(ValueError):
  """The evidence set is unsafe, malformed, stale, unauthenticated, or mismatched."""


def canonical_json(value: Any) -> bytes:
  """One accepted serialization: sorted compact ASCII JSON plus LF."""
  try:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")
  except (TypeError, ValueError, UnicodeEncodeError) as error:
    raise EvidenceError("value is not canonical-JSON encodable") from error


def _duplicate_rejector(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  value: dict[str, Any] = {}
  for key, item in pairs:
    if key in value:
      raise EvidenceError(f"duplicate JSON key: {key}")
    value[key] = item
  return value


def _load_canonical(raw: bytes, label: str) -> dict[str, Any]:
  try:
    value = json.loads(
      raw, object_pairs_hook=_duplicate_rejector,
      parse_constant=lambda token: (_ for _ in ()).throw(
        EvidenceError(f"invalid JSON constant in {label}: {token}")),
    )
  except (UnicodeDecodeError, json.JSONDecodeError) as error:
    raise EvidenceError(f"malformed {label} JSON") from error
  if type(value) is not dict or canonical_json(value) != raw:
    raise EvidenceError(f"{label} must be a canonical JSON object")
  return value


def _strict(value: Any, keys: set[str], label: str) -> dict[str, Any]:
  if type(value) is not dict or set(value) != keys:
    raise EvidenceError(f"malformed {label} schema")
  return value


def _safe_relative(value: Any) -> tuple[str, ...]:
  if (type(value) is not str or not value or len(value) > 512 or value.startswith("/") or
      "\\" in value or "\x00" in value):
    raise EvidenceError("evidence path must be a bounded canonical relative POSIX path")
  parts = tuple(value.split("/"))
  if any(part in ("", ".", "..") or len(part) > 128 for part in parts):
    raise EvidenceError("evidence path contains traversal or noncanonical components")
  return parts


def _safe_root(root: Path) -> Path:
  if not root.is_absolute():
    raise EvidenceError("evidence root must be absolute")
  absolute = Path(os.path.abspath(os.fspath(root)))
  current = Path(absolute.anchor)
  try:
    for part in absolute.parts[1:]:
      current = current / part
      info = os.lstat(current)
      if stat.S_ISLNK(info.st_mode):
        raise EvidenceError("evidence root traversal crosses a symlink")
    if not stat.S_ISDIR(os.lstat(absolute).st_mode):
      raise EvidenceError("evidence root is not a real directory")
  except OSError as error:
    raise EvidenceError("evidence root is unavailable") from error
  return absolute


def _read_relative(root: Path, relative: Any, maximum: int, label: str) -> bytes:
  """Read through openat/O_NOFOLLOW and verify a stable regular-file identity."""
  parts = _safe_relative(relative)
  nofollow = getattr(os, "O_NOFOLLOW", 0)
  directory = getattr(os, "O_DIRECTORY", 0)
  cloexec = getattr(os, "O_CLOEXEC", 0)
  parent_fd: int | None = None
  final_fd: int | None = None
  try:
    parent_fd = os.open(root, os.O_RDONLY | directory | nofollow | cloexec)
    for part in parts[:-1]:
      next_fd = os.open(part, os.O_RDONLY | directory | nofollow | cloexec, dir_fd=parent_fd)
      os.close(parent_fd)
      parent_fd = next_fd
    final_fd = os.open(parts[-1], os.O_RDONLY | os.O_NONBLOCK | nofollow | cloexec,
                       dir_fd=parent_fd)
    before = os.fstat(final_fd)
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink < 1 or before.st_size <= 0 or
        before.st_size > maximum):
      raise EvidenceError(f"{label} is not a bounded linked regular file")
    chunks: list[bytes] = []
    total = 0
    while chunk := os.read(final_fd, min(1 << 20, maximum + 1 - total)):
      chunks.append(chunk)
      total += len(chunk)
      if total > maximum:
        raise EvidenceError(f"{label} exceeds its size bound")
    after = os.fstat(final_fd)
    identity = lambda info: (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
                             info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if total != before.st_size or identity(before) != identity(after):
      raise EvidenceError(f"{label} changed while read")
    return b"".join(chunks)
  except EvidenceError:
    raise
  except OSError as error:
    raise EvidenceError(f"{label} is missing, symlinked, or unreadable") from error
  finally:
    if final_fd is not None:
      os.close(final_fd)
    if parent_fd is not None:
      os.close(parent_fd)


def _descriptor(value: Any, label: str, *, artifact: bool = False) -> dict[str, Any]:
  keys = {"path", "sha256", "size_bytes"}
  if artifact:
    keys |= {"kind", "media_type", "capture_mode"}
  item = _strict(value, keys, label)
  _safe_relative(item["path"])
  if type(item["sha256"]) is not str or not _HEX64.fullmatch(item["sha256"]):
    raise EvidenceError(f"malformed {label} SHA256")
  if type(item["size_bytes"]) is not int or not 1 <= item["size_bytes"] <= MAX_ARTIFACT_BYTES:
    raise EvidenceError(f"malformed {label} size")
  if artifact:
    if type(item["kind"]) is not str or not _TOKEN.fullmatch(item["kind"]):
      raise EvidenceError(f"malformed {label} kind")
    if item["media_type"] not in _MEDIA_TYPES:
      raise EvidenceError(f"unsupported {label} media type")
    if item["capture_mode"] not in {"DIRECT_MEASUREMENT", "INSTRUMENT_LOG", "SIGNED_REPORT",
                                    "SYNTHETIC_GENERATED"}:
      raise EvidenceError(f"unsupported {label} capture mode")
  return item


def _read_descriptor(root: Path, descriptor: dict[str, Any], label: str, maximum: int) -> bytes:
  raw = _read_relative(root, descriptor["path"], maximum, label)
  if len(raw) != descriptor["size_bytes"] or hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
    raise EvidenceError(f"{label} size or SHA256 mismatch")
  return raw


def _utc(value: Any, label: str) -> datetime:
  if type(value) is not str or len(value) != 20:
    raise EvidenceError(f"malformed {label} timestamp")
  try:
    parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
  except ValueError as error:
    raise EvidenceError(f"malformed {label} timestamp") from error
  return parsed


def _fresh(observed: Any, expires: Any, now: datetime, label: str) -> None:
  start = _utc(observed, f"{label} observed_at_utc")
  end = _utc(expires, f"{label} expires_at_utc")
  if start > now + MAX_CLOCK_SKEW or now >= end or now - start > MAX_EVIDENCE_AGE:
    raise EvidenceError(f"{label} is future-dated, stale, or expired")
  if end <= start or end - start > MAX_EVIDENCE_AGE:
    raise EvidenceError(f"{label} freshness window is invalid")


# Verification-only Edwards25519 operations in extended coordinates.
_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _Q - 2, _Q)) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)
_IDENTITY = (0, 1, 1, 0)


def _recover_x(y: int, sign: int) -> int:
  xx = (y * y - 1) * pow(_D * y * y + 1, _Q - 2, _Q) % _Q
  x = pow(xx, (_Q + 3) // 8, _Q)
  if (x * x - xx) % _Q:
    x = x * _I % _Q
  if (x * x - xx) % _Q:
    raise EvidenceError("Ed25519 point is not on the curve")
  if (x & 1) != sign:
    x = _Q - x
  if x == 0 and sign:
    raise EvidenceError("Ed25519 point has a noncanonical sign")
  return x


def _decode_point(encoded: bytes) -> tuple[int, int, int, int]:
  if len(encoded) != 32:
    raise EvidenceError("Ed25519 point has the wrong length")
  integer = int.from_bytes(encoded, "little")
  y = integer & ((1 << 255) - 1)
  if y >= _Q:
    raise EvidenceError("Ed25519 point encoding is noncanonical")
  x = _recover_x(y, integer >> 255)
  return (x, y, 1, x * y % _Q)


def _point_add(first: tuple[int, int, int, int],
               second: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
  x1, y1, z1, t1 = first
  x2, y2, z2, t2 = second
  a = (y1 - x1) * (y2 - x2) % _Q
  b = (y1 + x1) * (y2 + x2) % _Q
  c = 2 * _D * t1 * t2 % _Q
  d = 2 * z1 * z2 % _Q
  e, f, g, h = b - a, d - c, d + c, b + a
  return (e * f % _Q, g * h % _Q, f * g % _Q, e * h % _Q)


def _scalar_mult(point: tuple[int, int, int, int], scalar: int) -> tuple[int, int, int, int]:
  result = _IDENTITY
  addend = point
  while scalar:
    if scalar & 1:
      result = _point_add(result, addend)
    addend = _point_add(addend, addend)
    scalar >>= 1
  return result


def _encode_point(point: tuple[int, int, int, int]) -> bytes:
  x, y, z, _ = point
  inverse = pow(z, _Q - 2, _Q)
  affine_x, affine_y = x * inverse % _Q, y * inverse % _Q
  return (affine_y | ((affine_x & 1) << 255)).to_bytes(32, "little")


_BASE_Y = 4 * pow(5, _Q - 2, _Q) % _Q
_BASE_X = _recover_x(_BASE_Y, 0)
_BASE = (_BASE_X, _BASE_Y, 1, _BASE_X * _BASE_Y % _Q)


def verify_ed25519(public_key: bytes, message: bytes, signature: bytes) -> bool:
  """Strict Ed25519 verification with canonical and prime-subgroup checks."""
  try:
    if len(public_key) != 32 or len(signature) != 64:
      return False
    r_encoded, s_encoded = signature[:32], signature[32:]
    scalar_s = int.from_bytes(s_encoded, "little")
    if scalar_s >= _L:
      return False
    public_point = _decode_point(public_key)
    r_point = _decode_point(r_encoded)
    if (_encode_point(public_point) != public_key or _encode_point(r_point) != r_encoded or
        _encode_point(public_point) == _encode_point(_IDENTITY) or
        _encode_point(r_point) == _encode_point(_IDENTITY) or
        _encode_point(_scalar_mult(public_point, _L)) != _encode_point(_IDENTITY) or
        _encode_point(_scalar_mult(r_point, _L)) != _encode_point(_IDENTITY)):
      return False
    challenge = int.from_bytes(
      hashlib.sha512(r_encoded + public_key + message).digest(), "little") % _L
    return _encode_point(_scalar_mult(_BASE, scalar_s)) == _encode_point(
      _point_add(r_point, _scalar_mult(public_point, challenge)))
  except (EvidenceError, ValueError, OverflowError):
    return False


def _source(value: Any) -> dict[str, Any]:
  source = _strict(value, {
    "frozen_commit", "frozen_tree", "engineering_commit", "engineering_tree",
    "package_manifest_sha256", "readiness_gate_sha256", "supervisor_contract_sha256",
    "launcher_exit_code",
  }, "source binding")
  expected = {
    "frozen_commit": FROZEN_COMMIT,
    "frozen_tree": FROZEN_TREE,
    "engineering_commit": ENGINEERING_COMMIT,
    "engineering_tree": ENGINEERING_TREE,
    "launcher_exit_code": 78,
  }
  if any(source.get(key) != wanted for key, wanted in expected.items()):
    raise EvidenceError("source binding does not match frozen RC3 and engineering HEAD")
  if (type(source["package_manifest_sha256"]) is not str or
      not _HEX64.fullmatch(source["package_manifest_sha256"])):
    raise EvidenceError("malformed signed-package binding")
  try:
    expected_tools = {
      "readiness_gate_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      "supervisor_contract_sha256": hashlib.sha256(
        Path(__file__).with_name("rc3_supervisor_contract.py").read_bytes()).hexdigest(),
    }
  except OSError as error:
    raise EvidenceError("qualification-tool source is unavailable") from error
  if any(source.get(field) != digest for field, digest in expected_tools.items()):
    raise EvidenceError("qualification-tool source binding mismatch")
  return source


def _hardware(value: Any) -> dict[str, Any]:
  hardware = _strict(value, {
    "platform", "comma_device_model", "comma_serial_sha256", "panda_serial_sha256",
    "agnos_version", "bootloader_version",
  }, "hardware binding")
  if hardware["platform"] != PLATFORM:
    raise EvidenceError("wrong vehicle platform or platform case")
  if (type(hardware["comma_device_model"]) is not str or
      not _TOKEN.fullmatch(hardware["comma_device_model"]) or
      type(hardware["agnos_version"]) is not str or not _VERSION.fullmatch(hardware["agnos_version"]) or
      type(hardware["bootloader_version"]) is not str or
      not _VERSION.fullmatch(hardware["bootloader_version"])):
    raise EvidenceError("malformed hardware model or software-version binding")
  for field in ("comma_serial_sha256", "panda_serial_sha256"):
    if type(hardware[field]) is not str or not _HEX64.fullmatch(hardware[field]):
      raise EvidenceError(f"malformed hardware identity: {field}")
  return hardware


def _trust_keys(policy: dict[str, Any], classification: str) -> dict[str, dict[str, Any]]:
  expected_policy_class = (
    "PHYSICAL_LAB_TRUST_POLICY" if classification == PHYSICAL else "SYNTHETIC_TEST_TRUST_POLICY")
  if (policy["schema"] != TRUST_POLICY_SCHEMA or policy["classification"] != expected_policy_class or
      type(policy["policy_id"]) is not str or not _TOKEN.fullmatch(policy["policy_id"]) or
      type(policy["keys"]) is not list or len(policy["keys"]) < 2 or len(policy["keys"]) > 16):
    raise EvidenceError("attester trust policy is malformed or wrong-class")
  expected_purpose = "PHYSICAL_DEVICE_QUALIFICATION" if classification == PHYSICAL else "SYNTHETIC_TEST_ONLY"
  keys: dict[str, dict[str, Any]] = {}
  identities: set[str] = set()
  for entry_value in policy["keys"]:
    entry = _strict(entry_value, {
      "key_id", "identity", "organization", "role", "purpose", "algorithm",
      "public_key_b64", "independent_from_owner", "independent_from_developer",
    }, "attester key")
    for field in ("key_id", "identity", "organization"):
      if type(entry[field]) is not str or not _TOKEN.fullmatch(entry[field]):
        raise EvidenceError(f"malformed attester {field}")
    if (entry["key_id"] in keys or entry["identity"] in identities or
        entry["role"] not in {"LAB_OPERATOR", "INDEPENDENT_REVIEWER"} or
        entry["purpose"] != expected_purpose or entry["algorithm"] != "Ed25519" or
        entry["independent_from_owner"] is not True or
        entry["independent_from_developer"] is not True):
      raise EvidenceError("attester identities are duplicate, non-independent, or wrong-purpose")
    try:
      raw_key = base64.b64decode(entry["public_key_b64"], validate=True)
    except (ValueError, TypeError, binascii.Error) as error:
      raise EvidenceError("malformed attester public key") from error
    if len(raw_key) != 32:
      raise EvidenceError("malformed attester public key length")
    item = dict(entry)
    item["raw_key"] = raw_key
    keys[entry["key_id"]] = item
    identities.add(entry["identity"])
  return keys


def _verify_signature(value: Any, payload: dict[str, Any], keys: dict[str, dict[str, Any]],
                      expected_role: str) -> dict[str, Any]:
  signature = _strict(value, {"algorithm", "key_id", "signature_b64"}, "attestation signature")
  key = keys.get(signature.get("key_id"))
  if signature.get("algorithm") != "Ed25519" or key is None or key["role"] != expected_role:
    raise EvidenceError("attestation signature has the wrong algorithm, key, or role")
  try:
    raw_signature = base64.b64decode(signature["signature_b64"], validate=True)
  except (ValueError, TypeError, binascii.Error) as error:
    raise EvidenceError("malformed attestation signature") from error
  if not verify_ed25519(key["raw_key"], SIGNATURE_DOMAIN + canonical_json(payload), raw_signature):
    raise EvidenceError("attestation signature verification failed")
  return key


def _base_gatecard(now: datetime) -> dict[str, Any]:
  return {
    "schema": GATECARD_SCHEMA,
    "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "qualification_id": None,
    "evidence_classification": "NONE",
    "manifest_sha256": None,
    "trust_policy_sha256": None,
    "trust_policy_caller_pinned": False,
    "owner_authorization_observed": False,
    "owner_risk_acceptance_observed": False,
    "validated_requirements": [],
    "technical_evidence_complete": False,
    "independent_attestations_verified": False,
    "disposition": "HOLD",
    "installation_authorized": False,
    "boot_operations_authorized": False,
    "production_approved": False,
    "road_use_authorized": False,
    "progression": {"sequence": 0, "previous_gatecard_sha256": None, "run_nonce": None},
    "holds": ["NO_VERIFIED_PHYSICAL_EVIDENCE"],
    "validation_errors": [],
  }


def verify_manifest(root: Path, manifest_relative: str, pinned_trust_policy_sha256: str,
                    *, now: datetime) -> dict[str, Any]:
  """Verify one evidence set or raise EvidenceError.  No action is authorized."""
  root = _safe_root(root)
  if type(pinned_trust_policy_sha256) is not str or not _HEX64.fullmatch(pinned_trust_policy_sha256):
    raise EvidenceError("an exact lowercase SHA256 trust-policy pin is required")
  manifest_raw = _read_relative(root, manifest_relative, MAX_MANIFEST_BYTES, "evidence manifest")
  manifest = _load_canonical(manifest_raw, "evidence manifest")
  _strict(manifest, {
    "schema", "classification", "qualification_id", "created_at_utc", "expires_at_utc",
    "source", "hardware", "owner_context", "trust_policy", "progression", "requirements",
  }, "evidence manifest")
  classification = manifest["classification"]
  if manifest["schema"] != MANIFEST_SCHEMA or classification not in CLASSIFICATIONS:
    raise EvidenceError("evidence manifest schema or classification mismatch")
  qualification_id = manifest["qualification_id"]
  if type(qualification_id) is not str or not _TOKEN.fullmatch(qualification_id):
    raise EvidenceError("malformed qualification id")
  _fresh(manifest["created_at_utc"], manifest["expires_at_utc"], now, "manifest")
  source = _source(manifest["source"])
  hardware = _hardware(manifest["hardware"])

  owner = _strict(manifest["owner_context"], {
    "owner_identity", "future_operations_authorized", "risk_accepted", "statement_sha256",
  }, "owner context")
  if (type(owner["owner_identity"]) is not str or not _TOKEN.fullmatch(owner["owner_identity"]) or
      type(owner["future_operations_authorized"]) is not bool or type(owner["risk_accepted"]) is not bool or
      type(owner["statement_sha256"]) is not str or not _HEX64.fullmatch(owner["statement_sha256"])):
    raise EvidenceError("malformed owner context")

  progression = _strict(manifest["progression"], {
    "sequence", "previous_gatecard", "run_nonce",
  }, "progression")
  if (type(progression["sequence"]) is not int or progression["sequence"] < 1 or
      type(progression["run_nonce"]) is not str or not _HEX64.fullmatch(progression["run_nonce"])):
    raise EvidenceError("malformed monotone progression")
  previous_descriptor = progression["previous_gatecard"]
  previous: str | None = None
  if progression["sequence"] == 1:
    if previous_descriptor is not None:
      raise EvidenceError("first progression record cannot name a predecessor")
  else:
    predecessor = _descriptor(previous_descriptor, "previous gatecard")
    previous = predecessor["sha256"]

  policy_descriptor = _descriptor(manifest["trust_policy"], "trust policy")
  if (policy_descriptor["sha256"] != pinned_trust_policy_sha256 or
      policy_descriptor["size_bytes"] > MAX_POLICY_BYTES):
    raise EvidenceError("trust policy does not match the independent caller pin")
  policy_raw = _read_descriptor(root, policy_descriptor, "trust policy", MAX_POLICY_BYTES)
  policy = _load_canonical(policy_raw, "trust policy")
  _strict(policy, {"schema", "classification", "policy_id", "keys"}, "trust policy")
  keys = _trust_keys(policy, classification)

  requirements = manifest["requirements"]
  if type(requirements) is not list or len(requirements) != len(REQUIRED_ARTIFACTS):
    raise EvidenceError("evidence manifest must contain every requirement exactly once")
  seen_requirements: set[str] = set()
  seen_paths: set[str] = {policy_descriptor["path"], manifest_relative}
  if progression["sequence"] > 1:
    predecessor = _descriptor(previous_descriptor, "previous gatecard")
    if predecessor["path"] in seen_paths:
      raise EvidenceError("previous gatecard path is reused")
    predecessor_raw = _read_descriptor(root, predecessor, "previous gatecard", MAX_ARTIFACT_BYTES)
    predecessor_card = _load_canonical(predecessor_raw, "previous gatecard")
    _strict(predecessor_card, set(_base_gatecard(now)), "previous gatecard")
    if (predecessor_card.get("schema") != GATECARD_SCHEMA or
        predecessor_card.get("qualification_id") != qualification_id or
        predecessor_card.get("evidence_classification") != classification or
        predecessor_card.get("installation_authorized") is not False or
        predecessor_card.get("boot_operations_authorized") is not False or
        predecessor_card.get("production_approved") is not False or
        predecessor_card.get("road_use_authorized") is not False or
        type(predecessor_card.get("progression")) is not dict or
        predecessor_card["progression"].get("sequence") != progression["sequence"] - 1 or
        predecessor_card["progression"].get("run_nonce") == progression["run_nonce"] or
        type(predecessor_card.get("validated_requirements")) is not list):
      raise EvidenceError("previous gatecard does not establish a monotone predecessor")
    seen_paths.add(predecessor["path"])
  validated: list[str] = []
  total_bytes = 0
  operator_identities: set[str] = set()
  reviewer_identities: set[str] = set()
  operator_organizations: set[str] = set()
  reviewer_organizations: set[str] = set()

  for envelope_value in requirements:
    envelope = _strict(envelope_value, {"payload", "signatures"}, "requirement envelope")
    payload = _strict(envelope["payload"], {
      "schema", "classification", "qualification_id", "evidence_nonce", "requirement_id",
      "environment", "source_binding", "hardware_binding", "observed_at_utc", "expires_at_utc",
      "result", "artifacts", "operator_key_id", "reviewer_key_id", "progression_binding",
    }, "signed observation")
    requirement_id = payload["requirement_id"]
    if requirement_id not in REQUIRED_ARTIFACTS or requirement_id in seen_requirements:
      raise EvidenceError("unknown or duplicate qualification requirement")
    expected_environment, expected_kinds = REQUIRED_ARTIFACTS[requirement_id]
    expected_result = "OBSERVED_PASS" if classification == PHYSICAL else "SYNTHETIC_PASS"
    if (payload["schema"] != OBSERVATION_SCHEMA or payload["classification"] != classification or
        payload["qualification_id"] != qualification_id or
        payload["evidence_nonce"] != progression["run_nonce"] or
        payload["progression_binding"] != progression or
        payload["environment"] != expected_environment or payload["source_binding"] != source or
        payload["hardware_binding"] != hardware or payload["result"] != expected_result):
      raise EvidenceError(f"{requirement_id} observation binding or result mismatch")
    _fresh(payload["observed_at_utc"], payload["expires_at_utc"], now, requirement_id)
    artifacts = payload["artifacts"]
    if type(artifacts) is not list or len(artifacts) != len(expected_kinds):
      raise EvidenceError(f"{requirement_id} artifact set is incomplete")
    observed_kinds: list[str] = []
    for artifact_value in artifacts:
      artifact = _descriptor(artifact_value, f"{requirement_id} artifact", artifact=True)
      if artifact["path"] in seen_paths:
        raise EvidenceError("an evidence file was replayed or reused")
      if classification == PHYSICAL and artifact["capture_mode"] == "SYNTHETIC_GENERATED":
        raise EvidenceError("physical evidence cannot use synthetic capture mode")
      if classification == SYNTHETIC and artifact["capture_mode"] != "SYNTHETIC_GENERATED":
        raise EvidenceError("synthetic fixtures must be explicitly labeled at every artifact")
      raw = _read_descriptor(root, artifact, f"{requirement_id}/{artifact['kind']}", MAX_ARTIFACT_BYTES)
      total_bytes += len(raw)
      if total_bytes > MAX_TOTAL_ARTIFACT_BYTES:
        raise EvidenceError("aggregate evidence exceeds its size bound")
      seen_paths.add(artifact["path"])
      observed_kinds.append(artifact["kind"])
    if tuple(observed_kinds) != expected_kinds:
      raise EvidenceError(f"{requirement_id} artifact kinds or order mismatch")

    signatures = envelope["signatures"]
    if type(signatures) is not list or len(signatures) != 2:
      raise EvidenceError("each observation requires exactly operator and reviewer signatures")
    operator = _verify_signature(signatures[0], payload, keys, "LAB_OPERATOR")
    reviewer = _verify_signature(signatures[1], payload, keys, "INDEPENDENT_REVIEWER")
    if (payload["operator_key_id"] != operator["key_id"] or
        payload["reviewer_key_id"] != reviewer["key_id"] or
        operator["identity"] == reviewer["identity"] or
        operator["organization"] == reviewer["organization"]):
      raise EvidenceError("operator and reviewer are not separately bound independent identities")
    operator_identities.add(operator["identity"])
    reviewer_identities.add(reviewer["identity"])
    operator_organizations.add(operator["organization"])
    reviewer_organizations.add(reviewer["organization"])
    seen_requirements.add(requirement_id)
    validated.append(requirement_id)

  if seen_requirements != set(REQUIRED_ARTIFACTS):
    raise EvidenceError("one or more irreducible qualification requirements are missing")
  if progression["sequence"] > 1:
    prior_validated = predecessor_card["validated_requirements"]
    if (any(type(item) is not str for item in prior_validated) or
        not set(prior_validated).issubset(set(validated))):
      raise EvidenceError("progression would remove a previously validated requirement")
  if (operator_identities & reviewer_identities or
      operator_organizations & reviewer_organizations):
    raise EvidenceError("operator and reviewer trust domains overlap")

  physical_complete = classification == PHYSICAL
  return {
    "schema": GATECARD_SCHEMA,
    "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "qualification_id": qualification_id,
    "evidence_classification": classification,
    "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
    "trust_policy_sha256": pinned_trust_policy_sha256,
    "trust_policy_caller_pinned": True,
    "owner_authorization_observed": owner["future_operations_authorized"],
    "owner_risk_acceptance_observed": owner["risk_accepted"],
    "validated_requirements": validated,
    "technical_evidence_complete": physical_complete,
    "independent_attestations_verified": True,
    "disposition": (
      "EVIDENCE_COMPLETE_AWAIT_EXTERNAL_RELEASE_DECISION" if physical_complete
      else "HOLD_SYNTHETIC_EVIDENCE_NON_DEPLOYABLE"),
    "installation_authorized": False,
    "boot_operations_authorized": False,
    "production_approved": False,
    "road_use_authorized": False,
    "progression": {
      "sequence": progression["sequence"],
      "previous_gatecard_sha256": previous,
      "run_nonce": progression["run_nonce"],
    },
    "holds": ([
      "EXTERNAL_RELEASE_DECISION_REQUIRED",
      "THIS_GATE_NEVER_AUTHORIZES_INSTALLATION_OR_BOOT_OPERATIONS",
    ] if physical_complete else [
      "SYNTHETIC_EVIDENCE_IS_NOT_PHYSICAL_QUALIFICATION",
      "HARDWARE_DEVICE_AND_BENCH_OBSERVATIONS_REQUIRED",
      "THIS_GATE_NEVER_AUTHORIZES_INSTALLATION_OR_BOOT_OPERATIONS",
    ]),
    "validation_errors": [],
  }


def assess(root: Path, manifest_relative: str | None,
           pinned_trust_policy_sha256: str | None, *,
           now: datetime | None = None) -> dict[str, Any]:
  """Return a machine-readable result; every error maps to HOLD."""
  evaluated_at = now or datetime.now(timezone.utc).replace(microsecond=0)
  if evaluated_at.tzinfo is None or evaluated_at.utcoffset() != timedelta(0):
    raise EvidenceError("assessment time must be timezone-aware UTC")
  result = _base_gatecard(evaluated_at)
  if manifest_relative is None:
    result["validation_errors"] = ["no evidence manifest supplied"]
    return result
  try:
    return verify_manifest(root, manifest_relative, pinned_trust_policy_sha256 or "", now=evaluated_at)
  except EvidenceError as error:
    result["validation_errors"] = [str(error)]
    result["holds"] = ["EVIDENCE_VALIDATION_FAILED", "NO_VERIFIED_PHYSICAL_EVIDENCE"]
    return result


def write_new(path: Path, payload: bytes) -> None:
  path = path if path.is_absolute() else Path.cwd() / path
  path.parent.resolve(strict=True)
  flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
  try:
    descriptor = os.open(path, flags, 0o644)
  except OSError as error:
    raise EvidenceError("refusing to overwrite or follow output path") from error
  try:
    with os.fdopen(descriptor, "wb", closefd=False) as stream:
      stream.write(payload)
      stream.flush()
      os.fsync(stream.fileno())
  finally:
    os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--evidence-root", type=Path, required=True)
  parser.add_argument("--manifest", help="canonical relative path beneath evidence root")
  parser.add_argument("--pinned-trust-policy-sha256")
  parser.add_argument("--output", type=Path, help="create a new gatecard; overwrite is refused")
  arguments = parser.parse_args(argv)
  result = assess(arguments.evidence_root, arguments.manifest,
                  arguments.pinned_trust_policy_sha256)
  payload = canonical_json(result)
  if arguments.output is None:
    sys.stdout.buffer.write(payload)
  else:
    try:
      write_new(arguments.output, payload)
    except EvidenceError as error:
      print(f"RC3 evidence gate output rejected: {error}", file=sys.stderr)
      return 2
  return 0 if result["technical_evidence_complete"] else 78


if __name__ == "__main__":
  raise SystemExit(main())

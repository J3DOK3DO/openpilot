#!/usr/bin/env python3
"""Strict caller-supplied signature verifier for RC3 host simulations only.

This module has no signing function and contains no private or production key.
It accepts only canonical JSON, Ed25519 signatures from a separately supplied
host-simulation keyring, and policies that explicitly deny installation and
device operations.  The caller-supplied keyring is not an independent trust
anchor and conveys no production release authority.  This module never
performs a device, network, boot-slot, or process operation.
"""
from __future__ import annotations

import base64
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

MAX_TRUST_BYTES = 256 * 1024
KEYRING_SCHEMA = "G8_F12_RC3_HOST_SIMULATION_KEYRING_V1"
POLICY_SCHEMA = "G8_F12_RC3_EXTERNAL_TRUST_POLICY_V1"
HEALTH_SCHEMA = "G8_F12_RC3_HOST_HEALTH_RECEIPT_V1"
HOST_SCOPE = "HOST_ONLY_SIMULATION_NOT_INSTALLATION"
POLICY_DOMAIN = b"g8-f12-rc3/host-policy/v1\x00"
HEALTH_DOMAIN = b"g8-f12-rc3/host-health/v1\x00"

_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")


class TrustError(ValueError):
  """Fail-closed trust-policy or signed-receipt rejection."""


def canonical_json(value: Any) -> bytes:
  return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for key, value in pairs:
    if key in result:
      raise TrustError(f"duplicate JSON key: {key}")
    result[key] = value
  return result


def _strict_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
  if type(value) is not dict or set(value) != keys:
    raise TrustError(f"malformed {label}")
  return value


def _external_regular_file(source_root: Path, path: Path, label: str) -> Path:
  source_root = source_root.resolve(strict=True)
  if not path.is_absolute():
    raise TrustError(f"{label} path must be absolute")
  try:
    info = os.lstat(path)
  except OSError as error:
    raise TrustError(f"missing {label}") from error
  if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
    raise TrustError(f"{label} must be a regular non-symlink file")
  resolved = path.resolve(strict=True)
  try:
    if resolved.is_relative_to(source_root):
      raise TrustError(f"{label} must be outside the mutable source/application tree")
  except ValueError as error:
    raise TrustError(f"cannot establish external trust-domain separation for {label}") from error
  return resolved


def load_canonical_external_json(source_root: Path, path: Path, label: str) -> dict[str, Any]:
  resolved = _external_regular_file(source_root, path, label)
  size = resolved.stat().st_size
  if size <= 0 or size > MAX_TRUST_BYTES:
    raise TrustError(f"{label} has invalid size")
  raw = resolved.read_bytes()
  try:
    value = json.loads(raw, object_pairs_hook=_reject_duplicate_pairs,
                       parse_constant=lambda value: (_ for _ in ()).throw(
                         TrustError(f"invalid JSON constant: {value}")))
  except (UnicodeDecodeError, json.JSONDecodeError) as error:
    raise TrustError(f"malformed {label} JSON") from error
  if type(value) is not dict or canonical_json(value) != raw:
    raise TrustError(f"{label} must be canonical JSON")
  return value


class ExternalTrustVerifier:
  """Reload and verify a policy/keyring before each sensitive transition."""

  def __init__(self, source_root: Path, policy_path: Path, keyring_path: Path):
    self.source_root = source_root.resolve(strict=True)
    self.policy_path = Path(policy_path)
    self.keyring_path = Path(keyring_path)

  def _trusted_key(self, key_id: Any) -> Ed25519PublicKey:
    if type(key_id) is not str or not _TOKEN.fullmatch(key_id):
      raise TrustError("malformed signing key id")
    keyring = load_canonical_external_json(self.source_root, self.keyring_path, "external keyring")
    _strict_object(keyring, {"schema", "keys"}, "external keyring")
    if keyring["schema"] != KEYRING_SCHEMA or type(keyring["keys"]) is not list:
      raise TrustError("external keyring schema mismatch")
    matches = []
    seen: set[str] = set()
    for item in keyring["keys"]:
      key = _strict_object(item, {"key_id", "algorithm", "purpose", "public_key_b64"}, "key entry")
      if type(key["key_id"]) is not str or not _TOKEN.fullmatch(key["key_id"]) or key["key_id"] in seen:
        raise TrustError("malformed or duplicate external key id")
      seen.add(key["key_id"])
      if key["algorithm"] != "ed25519" or key["purpose"] != "host-simulation-only":
        raise TrustError("external key has unsupported algorithm or purpose")
      if key["key_id"] == key_id:
        matches.append(key)
    if len(matches) != 1:
      raise TrustError("signed object key is absent from the caller-supplied keyring")
    try:
      raw = base64.b64decode(matches[0]["public_key_b64"], validate=True)
      if len(raw) != 32:
        raise ValueError("wrong public key length")
      return Ed25519PublicKey.from_public_bytes(raw)
    except (TypeError, ValueError) as error:
      raise TrustError("malformed external public key") from error

  def _verify_envelope(self, envelope: dict[str, Any], domain: bytes, payload_key: str) -> dict[str, Any]:
    _strict_object(envelope, {"algorithm", "key_id", payload_key, "signature_b64"}, "signed envelope")
    if envelope["algorithm"] != "ed25519":
      raise TrustError("unsupported signed-envelope algorithm")
    payload = envelope[payload_key]
    if type(payload) is not dict:
      raise TrustError("signed payload must be an object")
    public_key = self._trusted_key(envelope["key_id"])
    try:
      signature = base64.b64decode(envelope["signature_b64"], validate=True)
      if len(signature) != 64:
        raise ValueError("wrong signature length")
      public_key.verify(signature, domain + canonical_json(payload))
    except (TypeError, ValueError, InvalidSignature) as error:
      raise TrustError("external signature verification failed") from error
    return payload

  def verify_policy(self, *, frozen_commit: str, frozen_tree: str,
                    inventory_sha256: str) -> dict[str, Any]:
    envelope = load_canonical_external_json(self.source_root, self.policy_path, "external policy")
    policy = self._verify_envelope(envelope, POLICY_DOMAIN, "policy")
    _strict_object(policy, {
      "schema", "scope", "policy_id", "frozen_commit", "frozen_tree",
      "inventory_sha256", "release_sequence", "max_trial_attempts",
      "installation_authorized", "device_operations_authorized",
    }, "external policy payload")
    if (policy["schema"] != POLICY_SCHEMA or policy["scope"] != HOST_SCOPE or
        policy["frozen_commit"] != frozen_commit or policy["frozen_tree"] != frozen_tree or
        policy["inventory_sha256"] != inventory_sha256):
      raise TrustError("external policy is not pinned to this exact RC3 inventory")
    if type(policy["policy_id"]) is not str or not _TOKEN.fullmatch(policy["policy_id"]):
      raise TrustError("malformed external policy id")
    for name in ("frozen_commit", "frozen_tree", "inventory_sha256"):
      pattern = _HEX40 if name != "inventory_sha256" else _HEX64
      if type(policy[name]) is not str or not pattern.fullmatch(policy[name]):
        raise TrustError(f"malformed policy {name}")
    if (type(policy["release_sequence"]) is not int or policy["release_sequence"] < 1 or
        type(policy["max_trial_attempts"]) is not int or not 1 <= policy["max_trial_attempts"] <= 3):
      raise TrustError("invalid release sequence or trial-attempt bound")
    if policy["installation_authorized"] is not False or policy["device_operations_authorized"] is not False:
      raise TrustError("host-only policy must explicitly deny installation and device operations")
    return policy

  def verify_health(self, health_path: Path, *, inventory_sha256: str,
                    policy_id: str, trial_nonce: str, attempt: int) -> dict[str, Any]:
    envelope = load_canonical_external_json(self.source_root, Path(health_path), "health receipt")
    receipt = self._verify_envelope(envelope, HEALTH_DOMAIN, "receipt")
    _strict_object(receipt, {
      "schema", "scope", "policy_id", "inventory_sha256", "trial_nonce", "attempt",
      "startup_passed", "probation_complete", "boot_success_not_marked_early",
      "device_operations_authorized",
    }, "health receipt payload")
    if (receipt["schema"] != HEALTH_SCHEMA or receipt["scope"] != HOST_SCOPE or
        receipt["policy_id"] != policy_id or receipt["inventory_sha256"] != inventory_sha256 or
        receipt["trial_nonce"] != trial_nonce or receipt["attempt"] != attempt):
      raise TrustError("health receipt is stale or bound to a different trial")
    if (type(trial_nonce) is not str or not _HEX64.fullmatch(trial_nonce) or
        type(attempt) is not int or attempt < 1):
      raise TrustError("malformed trial binding")
    if (receipt["startup_passed"] is not True or receipt["probation_complete"] is not True or
        receipt["boot_success_not_marked_early"] is not True or
        receipt["device_operations_authorized"] is not False):
      raise TrustError("health receipt does not prove the complete host-only probation contract")
    return receipt

#!/usr/bin/env python3
"""NON-DEPLOYABLE F6 secure early-boot boundary protocol reference.

This module is an offline protocol model.  It does not discover a boot slot,
verify dm-verity, execute an application, call ``abctl``, or provide protected
storage.  ``MockEarlyBootAdapter`` stores ordinary files and test keys remain
in the test process; it is deliberately *not* a hardware security boundary.

A production adapter would have to obtain caller identity, boot nonce, OS slot,
monotonic state, policy, and immutable-snapshot provenance from protected early
boot and rollback-resistant hardware.  The application may request a decision,
but none of its writable files are an authorization input.
"""
from __future__ import annotations

import base64
import copy
import errno
import fcntl
import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from typing import Any, Callable, Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from g8_protected_authority import CandidateIdentity, PolicySnapshot, canonical
from g8_readonly_fd_verifier import PinnedRelease, ReadOnlyFdVerifier


SIMULATED_F6_TRUST = "SIMULATED_F6_HOST_TRUST_NOT_HARDWARE"
STATE_SCHEMA = "c7-g8-f6-mock-early-boot-state/1"
BOOT_SCHEMA = "c7-g8-f6-boot-context/1"
POLICY_SCHEMA = "c7-g8-f6-policy/1"
GRANT_SCHEMA = "c7-g8-f6-snapshot-grant/1"
CONSUME_SCHEMA = "c7-g8-f6-consume-receipt/1"
HEALTH_SCHEMA = "c7-g8-f6-health-attestation/1"
HEALTH_RECEIPT_SCHEMA = "c7-g8-f6-health-receipt/1"
BOOT_DOMAIN = b"c7-g8-f6-boot-context/v1\x00"
POLICY_DOMAIN = b"c7-g8-f6-policy/v1\x00"
GRANT_DOMAIN = b"c7-g8-f6-snapshot-grant/v1\x00"
CONSUME_DOMAIN = b"c7-g8-f6-consume-receipt/v1\x00"
HEALTH_DOMAIN = b"c7-g8-f6-health/v1\x00"
HEALTH_RECEIPT_DOMAIN = b"c7-g8-f6-health-receipt/v1\x00"

_HEX16 = re.compile(r"^[0-9a-f]{16}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9._:-]{1,96}$")
_OS_SLOT = re.compile(r"^[ab]$")


class BoundaryError(Exception):
  """Fail-closed protocol, provenance, or qualification error."""


class SimulatedBoundaryPowerLoss(BaseException):
  """Deterministic host-only abrupt-death injection."""


class BoundaryFaults:
  """Host-only fault hooks; these do not model real storage guarantees."""

  def __init__(self, crash_at: str | None = None, oserror_at: dict[str, int] | None = None,
               action_at: dict[str, Callable[[], None]] | None = None):
    self.crash_at = crash_at
    self.oserror_at = dict(oserror_at or {})
    self.action_at = dict(action_at or {})
    self.points_seen: list[str] = []

  def hit(self, point: str) -> None:
    self.points_seen.append(point)
    action = self.action_at.get(point)
    if action is not None:
      action()
    if point in self.oserror_at:
      number = self.oserror_at[point]
      raise OSError(number, os.strerror(number), point)
    if point == self.crash_at:
      raise SimulatedBoundaryPowerLoss(point)


def _key_id(raw: bytes) -> str:
  return hashlib.sha256(raw).hexdigest()[:16]


def public_key_b64(private_key: Ed25519PrivateKey) -> str:
  raw = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  return base64.b64encode(raw).decode()


def _decode_public(value: str, expected_id: str) -> bytes:
  try:
    raw = base64.b64decode(value, validate=True)
  except (TypeError, ValueError) as error:
    raise BoundaryError("malformed public key") from error
  if len(raw) != 32 or _key_id(raw) != expected_id:
    raise BoundaryError("public key identity mismatch")
  return raw


def _sign(private_key: Ed25519PrivateKey, domain: bytes, payload: dict[str, Any]) -> dict[str, Any]:
  raw = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  return {
    "alg": "ed25519",
    "key_id": _key_id(raw),
    "payload": copy.deepcopy(payload),
    "signature": base64.b64encode(private_key.sign(domain + canonical(payload))).decode(),
    "trust": SIMULATED_F6_TRUST,
  }


def verify_envelope(envelope: Any, domain: bytes, public_b64: str,
                    expected_payload: dict[str, Any] | None = None) -> dict[str, Any]:
  """Strictly verify an envelope and return a defensive payload copy."""
  if not isinstance(envelope, dict) or set(envelope) != {
      "alg", "key_id", "payload", "signature", "trust"}:
    raise BoundaryError("malformed signed envelope")
  raw = _decode_public(public_b64, envelope.get("key_id"))
  payload = envelope.get("payload")
  if (envelope.get("alg") != "ed25519" or envelope.get("trust") != SIMULATED_F6_TRUST or
      not isinstance(payload, dict) or (expected_payload is not None and payload != expected_payload)):
    raise BoundaryError("signed envelope fields do not match the protected request")
  try:
    signature = base64.b64decode(envelope["signature"], validate=True)
    Ed25519PublicKey.from_public_bytes(raw).verify(signature, domain + canonical(payload))
  except (InvalidSignature, TypeError, ValueError) as error:
    raise BoundaryError("signed envelope authentication failed") from error
  return copy.deepcopy(payload)


@dataclass(frozen=True)
class CallerIdentity:
  caller_id: str
  executable_sha256: str

  def validate(self) -> None:
    if not isinstance(self.caller_id, str) or not _IDENTIFIER.fullmatch(self.caller_id):
      raise BoundaryError("malformed caller identity")
    if not isinstance(self.executable_sha256, str) or not _HEX64.fullmatch(self.executable_sha256):
      raise BoundaryError("malformed caller measurement")

  @classmethod
  def from_dict(cls, value: Any) -> "CallerIdentity":
    if not isinstance(value, dict) or set(value) != {"caller_id", "executable_sha256"}:
      raise BoundaryError("malformed caller object")
    caller = cls(**value)
    caller.validate()
    return caller


@dataclass(frozen=True)
class SnapshotProvenance:
  """Externally established immutable-media evidence, never locally discovered."""

  os_slot: str
  mount_source: str
  filesystem_type: str
  verity_root_digest: str
  read_only: bool
  verity_verified: bool
  snapshot_fingerprint: str

  @classmethod
  def create(cls, *, os_slot: str, mount_source: str, verity_root_digest: str,
             filesystem_type: str = "dm-verity") -> "SnapshotProvenance":
    claims = {
      "os_slot": os_slot,
      "mount_source": mount_source,
      "filesystem_type": filesystem_type,
      "verity_root_digest": verity_root_digest,
      "read_only": True,
      "verity_verified": True,
    }
    fingerprint = hashlib.sha256(canonical(claims)).hexdigest()
    result = cls(snapshot_fingerprint=fingerprint, **claims)
    result.validate()
    return result

  def validate(self) -> None:
    claims = asdict(self)
    fingerprint = claims.pop("snapshot_fingerprint", None)
    if (not isinstance(self.os_slot, str) or not _OS_SLOT.fullmatch(self.os_slot) or
        not isinstance(self.mount_source, str) or not self.mount_source.startswith("/dev/") or
        self.filesystem_type != "dm-verity" or self.read_only is not True or
        self.verity_verified is not True or not isinstance(self.verity_root_digest, str) or
        not _HEX64.fullmatch(self.verity_root_digest) or not isinstance(fingerprint, str) or
        not _HEX64.fullmatch(fingerprint)):
      raise BoundaryError("snapshot lacks explicit read-only dm-verity provenance")
    if hashlib.sha256(canonical(claims)).hexdigest() != fingerprint:
      raise BoundaryError("snapshot fingerprint does not match provenance claims")

  @classmethod
  def from_dict(cls, value: Any) -> "SnapshotProvenance":
    if not isinstance(value, dict) or set(value) != {
        "os_slot", "mount_source", "filesystem_type", "verity_root_digest",
        "read_only", "verity_verified", "snapshot_fingerprint"}:
      raise BoundaryError("malformed snapshot provenance object")
    snapshot = cls(**value)
    snapshot.validate()
    return snapshot


@dataclass(frozen=True)
class BootContext:
  authority_id: str
  caller: CallerIdentity
  boot_nonce: str
  boot_counter: int
  os_slot: str

  def validate(self) -> None:
    if not isinstance(self.authority_id, str) or not _IDENTIFIER.fullmatch(self.authority_id):
      raise BoundaryError("malformed authority identity")
    self.caller.validate()
    if (not isinstance(self.boot_nonce, str) or not _HEX64.fullmatch(self.boot_nonce) or
        isinstance(self.boot_counter, bool) or not isinstance(self.boot_counter, int) or
        self.boot_counter < 1 or not isinstance(self.os_slot, str) or not _OS_SLOT.fullmatch(self.os_slot)):
      raise BoundaryError("malformed immutable boot context")

  @classmethod
  def from_payload(cls, payload: Any) -> "BootContext":
    if not isinstance(payload, dict) or set(payload) != {
        "schema", "authority_id", "caller", "boot_nonce", "boot_counter", "os_slot"} or \
        payload.get("schema") != BOOT_SCHEMA:
      raise BoundaryError("malformed boot-context payload")
    context = cls(
      payload["authority_id"], CallerIdentity.from_dict(payload["caller"]), payload["boot_nonce"],
      payload["boot_counter"], payload["os_slot"],
    )
    context.validate()
    return context


@dataclass(frozen=True)
class ConsumedAuthorization:
  grant: dict[str, Any]
  consume_receipt: dict[str, Any]
  consume_sequence: int


@dataclass
class QualifiedSnapshot:
  context: BootContext
  candidate: CandidateIdentity
  provenance: SnapshotProvenance
  authorization: ConsumedAuthorization
  pinned_release: PinnedRelease
  immutable_precondition_verified: bool = True
  executed: bool = False

  def close(self) -> None:
    self.pinned_release.close()

  def __enter__(self) -> "QualifiedSnapshot":
    return self

  def __exit__(self, *_exc: object) -> bool:
    self.close()
    return False


class EarlyBootAdapter(Protocol):
  """Production-shaped protocol; implementations must be protected early boot."""

  @property
  def trust_domain_path(self) -> str: ...

  def begin_boot(self, caller: CallerIdentity, boot_nonce: str) -> dict[str, Any]: ...

  def policy_for_boot(self, boot_envelope: dict[str, Any]) -> dict[str, Any]: ...

  def authorize_snapshot(self, boot_envelope: dict[str, Any], candidate: CandidateIdentity,
                         provenance: SnapshotProvenance) -> dict[str, Any]: ...

  def consume_authorization(self, grant: dict[str, Any]) -> ConsumedAuthorization: ...

  def record_health(self, grant: dict[str, Any], health_envelope: dict[str, Any]) -> dict[str, Any]: ...


def _policy_to_dict(policy: PolicySnapshot) -> dict[str, Any]:
  return {
    "generation": policy.generation,
    "epoch": policy.epoch,
    "recovery": asdict(policy.recovery),
    "expected_commit": policy.expected_commit,
    "minimum_release_sequence": policy.minimum_release_sequence,
    "signing_keys": [copy.deepcopy(item) for item in policy.signing_keys],
    "policy_sha256": policy.policy_sha256,
  }


def _policy_from_dict(value: Any) -> PolicySnapshot:
  if not isinstance(value, dict) or set(value) != {
      "generation", "epoch", "recovery", "expected_commit", "minimum_release_sequence",
      "signing_keys", "policy_sha256"}:
    raise BoundaryError("malformed protected policy")
  recovery = CandidateIdentity.from_dict(value["recovery"])
  policy = PolicySnapshot(
    value["generation"], value["epoch"], recovery, value["expected_commit"],
    value["minimum_release_sequence"], tuple(copy.deepcopy(value["signing_keys"])),
    value["policy_sha256"],
  )
  if (isinstance(policy.generation, bool) or not isinstance(policy.generation, int) or policy.generation < 1 or
      isinstance(policy.epoch, bool) or not isinstance(policy.epoch, int) or policy.epoch < 0 or
      not isinstance(policy.expected_commit, str) or not _HEX40.fullmatch(policy.expected_commit) or
      isinstance(policy.minimum_release_sequence, bool) or
      not isinstance(policy.minimum_release_sequence, int) or policy.minimum_release_sequence < 0 or
      not isinstance(policy.policy_sha256, str) or not _HEX64.fullmatch(policy.policy_sha256)):
    raise BoundaryError("malformed protected policy counters")
  if (policy.recovery.source_commit != policy.expected_commit or
      policy.recovery.release_sequence < policy.minimum_release_sequence):
    raise BoundaryError("protected policy is internally inconsistent")
  if not isinstance(value["signing_keys"], list) or not value["signing_keys"]:
    raise BoundaryError("protected signing policy is empty or malformed")
  seen: set[str] = set()
  for item in value["signing_keys"]:
    if (not isinstance(item, dict) or set(item) != {"key_id", "pubkey_b64", "purpose"} or
        item.get("purpose") != "production" or not isinstance(item.get("key_id"), str) or
        not _HEX16.fullmatch(item["key_id"]) or item["key_id"] in seen):
      raise BoundaryError("protected signing policy is malformed")
    _decode_public(item.get("pubkey_b64"), item["key_id"])
    seen.add(item["key_id"])
  if policy.recovery.signing_key_id not in seen:
    raise BoundaryError("protected recovery signing key is not approved")
  return policy


def health_payload(grant: dict[str, Any], boot_measurement: str) -> dict[str, Any]:
  payload = grant.get("payload") if isinstance(grant, dict) else None
  if (not isinstance(payload, dict) or payload.get("schema") != GRANT_SCHEMA or
      not isinstance(boot_measurement, str) or not _HEX64.fullmatch(boot_measurement)):
    raise BoundaryError("cannot form health payload for malformed grant")
  return {
    "schema": HEALTH_SCHEMA,
    "authority_id": payload["authority_id"],
    "grant_id": payload["grant_id"],
    "caller": copy.deepcopy(payload["caller"]),
    "policy_generation": payload["policy_generation"],
    "epoch": payload["epoch"],
    "boot_nonce": payload["boot_nonce"],
    "authorized_os_slot": payload["authorized_os_slot"],
    "snapshot_fingerprint": payload["snapshot"]["snapshot_fingerprint"],
    "candidate": copy.deepcopy(payload["candidate"]),
    "decision": "healthy",
    "boot_measurement": boot_measurement,
  }


class MockEarlyBootAdapter:
  """Ordinary-file host simulation.  This is obviously not hardware-secured."""

  @property
  def trust_domain_path(self) -> str:
    return self.root

  def __init__(self, root: str | os.PathLike[str], authority_private_key: Ed25519PrivateKey,
               *, faults: BoundaryFaults | None = None):
    if not isinstance(authority_private_key, Ed25519PrivateKey):
      raise BoundaryError("mock requires an exact in-process Ed25519 test key")
    self.root = os.path.abspath(os.fspath(root))
    self._state_path = os.path.join(self.root, "mock_f6_state.json")
    self._lock_path = os.path.join(self.root, "mock_f6.lock")
    self._authority_key = authority_private_key
    self.faults = faults or BoundaryFaults()
    state = self._load()
    if state["authority_pubkey_b64"] != public_key_b64(authority_private_key):
      raise BoundaryError("mock authority private key does not match persisted identity")

  @classmethod
  def create(cls, root: str | os.PathLike[str], *, authority_id: str, caller: CallerIdentity,
             authorized_os_slot: str, policy: PolicySnapshot, candidate: CandidateIdentity,
             provenance: SnapshotProvenance, authority_private_key: Ed25519PrivateKey,
             health_pubkey_b64: str, faults: BoundaryFaults | None = None) -> "MockEarlyBootAdapter":
    caller.validate()
    candidate.validate()
    provenance.validate()
    policy_dict = _policy_to_dict(policy)
    _policy_from_dict(policy_dict)
    if (not isinstance(authority_id, str) or not _IDENTIFIER.fullmatch(authority_id) or
        authorized_os_slot != provenance.os_slot or candidate != policy.recovery):
      raise BoundaryError("mock bootstrap policy, OS slot, candidate, or provenance mismatch")
    authority_public = public_key_b64(authority_private_key)
    authority_id_key = _key_id(base64.b64decode(authority_public))
    health_raw = base64.b64decode(health_pubkey_b64, validate=True)
    health_key_id = _key_id(health_raw)
    _decode_public(health_pubkey_b64, health_key_id)
    root_path = os.path.abspath(os.fspath(root))
    if os.path.lexists(root_path):
      if not os.path.isdir(root_path) or os.listdir(root_path):
        raise BoundaryError("mock trust-domain directory must be new and empty")
    else:
      os.makedirs(root_path, mode=0o700)
    state = {
      "schema": STATE_SCHEMA,
      "simulation_warning": SIMULATED_F6_TRUST,
      "revision": 0,
      "authority_id": authority_id,
      "authority_key_id": authority_id_key,
      "authority_pubkey_b64": authority_public,
      "health_key_id": health_key_id,
      "health_pubkey_b64": health_pubkey_b64,
      "caller": asdict(caller),
      "authorized_os_slot": authorized_os_slot,
      "policy": policy_dict,
      "candidate": asdict(candidate),
      "provenance": asdict(provenance),
      "boot_counter": 0,
      "used_boot_nonces": [],
      "active_boot": None,
      "active_grant": None,
      "consume_sequence": 0,
      "health_receipt": None,
    }
    cls._validate_state(state)
    path = os.path.join(root_path, "mock_f6_state.json")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
      os.write(descriptor, canonical(state))
      os.fsync(descriptor)
    finally:
      os.close(descriptor)
    directory = os.open(root_path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
      os.fsync(directory)
    finally:
      os.close(directory)
    return cls(root_path, authority_private_key, faults=faults)

  @staticmethod
  def _validate_state(state: Any) -> None:
    required = {
      "schema", "simulation_warning", "revision", "authority_id", "authority_key_id",
      "authority_pubkey_b64", "health_key_id", "health_pubkey_b64", "caller",
      "authorized_os_slot", "policy", "candidate", "provenance", "boot_counter",
      "used_boot_nonces", "active_boot", "active_grant", "consume_sequence", "health_receipt",
    }
    if not isinstance(state, dict) or set(state) != required or state.get("schema") != STATE_SCHEMA or \
        state.get("simulation_warning") != SIMULATED_F6_TRUST:
      raise BoundaryError("mock early-boot state is malformed")
    if (isinstance(state["revision"], bool) or not isinstance(state["revision"], int) or state["revision"] < 0 or
        isinstance(state["boot_counter"], bool) or not isinstance(state["boot_counter"], int) or
        state["boot_counter"] < 0 or isinstance(state["consume_sequence"], bool) or
        not isinstance(state["consume_sequence"], int) or state["consume_sequence"] < 0):
      raise BoundaryError("mock monotonic counters are malformed")
    if not _IDENTIFIER.fullmatch(state["authority_id"]):
      raise BoundaryError("mock authority identity is malformed")
    _decode_public(state["authority_pubkey_b64"], state["authority_key_id"])
    _decode_public(state["health_pubkey_b64"], state["health_key_id"])
    caller = CallerIdentity.from_dict(state["caller"])
    policy = _policy_from_dict(state["policy"])
    candidate = CandidateIdentity.from_dict(state["candidate"])
    provenance = SnapshotProvenance.from_dict(state["provenance"])
    if (candidate != policy.recovery or state["authorized_os_slot"] != provenance.os_slot or
        not _OS_SLOT.fullmatch(state["authorized_os_slot"])):
      raise BoundaryError("mock protected selection is inconsistent")
    nonces = state["used_boot_nonces"]
    if (not isinstance(nonces, list) or len(nonces) != len(set(nonces)) or
        any(not isinstance(item, str) or not _HEX64.fullmatch(item) for item in nonces)):
      raise BoundaryError("mock boot nonce history is malformed")
    active = state["active_boot"]
    if active is not None:
      context = BootContext.from_payload(active)
      if (context.authority_id != state["authority_id"] or context.caller != caller or
          context.os_slot != state["authorized_os_slot"] or context.boot_nonce not in nonces or
          context.boot_counter != state["boot_counter"]):
        raise BoundaryError("mock active boot is inconsistent")
    grant = state["active_grant"]
    if grant is not None:
      if not isinstance(grant, dict) or set(grant) != {"envelope", "consumed", "consume_sequence"}:
        raise BoundaryError("mock active grant is malformed")
      if not isinstance(grant["consumed"], bool):
        raise BoundaryError("mock grant consume flag is malformed")
      if grant["consumed"] and grant["consume_sequence"] != state["consume_sequence"]:
        raise BoundaryError("mock grant consume sequence is inconsistent")
    receipt = state["health_receipt"]
    if receipt is not None and (grant is None or not grant["consumed"] or not isinstance(receipt, dict)):
      raise BoundaryError("mock health state is inconsistent")

  def _load(self) -> dict[str, Any]:
    try:
      before = os.lstat(self._state_path)
      if not os.path.isfile(self._state_path) or os.path.islink(self._state_path) or before.st_size > (1 << 20):
        raise BoundaryError("mock state is not a bounded regular file")
      descriptor = os.open(self._state_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
      try:
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
          raise BoundaryError("mock state changed while opening")
        raw = os.read(descriptor, (1 << 20) + 1)
      finally:
        os.close(descriptor)
      if len(raw) > (1 << 20):
        raise BoundaryError("mock state is oversized")
      state = json.loads(raw)
      self._validate_state(state)
      return state
    except BoundaryError:
      raise
    except (OSError, TypeError, ValueError) as error:
      raise BoundaryError(f"mock protected state is missing, corrupt, or unreadable: {error!r}") from error

  def _locked(self):
    class Lock:
      def __init__(inner, outer: "MockEarlyBootAdapter"):
        inner.outer = outer
        inner.fd: int | None = None

      def __enter__(inner):
        try:
          inner.fd = os.open(inner.outer._lock_path, os.O_RDWR | os.O_CREAT, 0o600)
          fcntl.flock(inner.fd, fcntl.LOCK_EX)
        except OSError as error:
          if inner.fd is not None:
            os.close(inner.fd)
          raise BoundaryError(f"mock authority lock unavailable: {error!r}") from error
        return inner

      def __exit__(inner, *_exc: object) -> bool:
        if inner.fd is not None:
          os.close(inner.fd)
        return False
    return Lock(self)

  def _commit(self, state: dict[str, Any], operation: str) -> None:
    self._validate_state(state)
    state["revision"] += 1
    self.faults.hit(f"{operation}_precommit")
    self.faults.hit("authority_write")
    descriptor, temporary = tempfile.mkstemp(prefix="mock_f6_state.tmp.", dir=self.root)
    try:
      with os.fdopen(descriptor, "wb") as output:
        output.write(canonical(state))
        output.flush()
        os.fsync(output.fileno())
      self.faults.hit("authority_before_replace")
      os.replace(temporary, self._state_path)
      directory = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
      try:
        os.fsync(directory)
      finally:
        os.close(directory)
      self.faults.hit(f"{operation}_committed")
    except SimulatedBoundaryPowerLoss:
      raise
    except BaseException:
      try:
        os.unlink(temporary)
      except FileNotFoundError:
        pass
      raise

  @staticmethod
  def _boot_payload(state: dict[str, Any], caller: CallerIdentity, nonce: str) -> dict[str, Any]:
    return {
      "schema": BOOT_SCHEMA,
      "authority_id": state["authority_id"],
      "caller": asdict(caller),
      "boot_nonce": nonce,
      "boot_counter": state["boot_counter"],
      "os_slot": state["authorized_os_slot"],
    }

  def _require_active_boot(self, state: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    payload = verify_envelope(envelope, BOOT_DOMAIN, state["authority_pubkey_b64"])
    if payload != state["active_boot"]:
      raise BoundaryError("boot context is stale or not the current protected boot")
    BootContext.from_payload(payload)
    return payload

  def begin_boot(self, caller: CallerIdentity, boot_nonce: str) -> dict[str, Any]:
    caller.validate()
    if not isinstance(boot_nonce, str) or not _HEX64.fullmatch(boot_nonce):
      raise BoundaryError("boot nonce must be a 256-bit lowercase hex value")
    with self._locked():
      state = self._load()
      if asdict(caller) != state["caller"]:
        raise BoundaryError("caller is not the protected early-boot caller")
      if boot_nonce in state["used_boot_nonces"]:
        raise BoundaryError("boot nonce replay detected")
      state["boot_counter"] += 1
      state["used_boot_nonces"].append(boot_nonce)
      payload = self._boot_payload(state, caller, boot_nonce)
      envelope = _sign(self._authority_key, BOOT_DOMAIN, payload)
      state["active_boot"] = payload
      state["active_grant"] = None
      state["health_receipt"] = None
      self._commit(state, "begin_boot")
      return envelope

  def policy_for_boot(self, boot_envelope: dict[str, Any]) -> dict[str, Any]:
    with self._locked():
      state = self._load()
      boot = self._require_active_boot(state, boot_envelope)
      payload = {
        "schema": POLICY_SCHEMA,
        "authority_id": state["authority_id"],
        "caller": copy.deepcopy(state["caller"]),
        "boot_nonce": boot["boot_nonce"],
        "boot_counter": boot["boot_counter"],
        "authorized_os_slot": state["authorized_os_slot"],
        "policy": copy.deepcopy(state["policy"]),
      }
      return _sign(self._authority_key, POLICY_DOMAIN, payload)

  def authorize_snapshot(self, boot_envelope: dict[str, Any], candidate: CandidateIdentity,
                         provenance: SnapshotProvenance) -> dict[str, Any]:
    candidate.validate()
    provenance.validate()
    with self._locked():
      state = self._load()
      boot = self._require_active_boot(state, boot_envelope)
      if state["active_grant"] is not None:
        raise BoundaryError("this boot already has an authorization decision")
      if asdict(candidate) != state["candidate"]:
        raise BoundaryError("candidate differs from protected early-boot policy")
      if asdict(provenance) != state["provenance"]:
        raise BoundaryError("snapshot provenance differs from protected early-boot evidence")
      policy = _policy_from_dict(state["policy"])
      payload = {
        "schema": GRANT_SCHEMA,
        "authority_id": state["authority_id"],
        "grant_id": os.urandom(8).hex(),
        "caller": copy.deepcopy(state["caller"]),
        "policy_generation": policy.generation,
        "epoch": policy.epoch,
        "policy_sha256": policy.policy_sha256,
        "boot_nonce": boot["boot_nonce"],
        "boot_counter": boot["boot_counter"],
        "authorized_os_slot": state["authorized_os_slot"],
        "candidate": asdict(candidate),
        "snapshot": asdict(provenance),
        "decision": "authorize-read-only-qualification",
      }
      envelope = _sign(self._authority_key, GRANT_DOMAIN, payload)
      state["active_grant"] = {"envelope": envelope, "consumed": False, "consume_sequence": None}
      self._commit(state, "authorize")
      return envelope

  def consume_authorization(self, grant: dict[str, Any]) -> ConsumedAuthorization:
    """Persist monotonic consumption before returning; a later failure cannot refund."""
    with self._locked():
      state = self._load()
      payload = verify_envelope(grant, GRANT_DOMAIN, state["authority_pubkey_b64"])
      active = state["active_grant"]
      if active is None or active["envelope"] != grant:
        raise BoundaryError("authorization is stale or is not the protected active grant")
      if active["consumed"]:
        raise BoundaryError("authorization replay detected")
      if state["active_boot"] is None or payload.get("boot_nonce") != state["active_boot"]["boot_nonce"]:
        raise BoundaryError("authorization is not bound to the active boot")
      state["consume_sequence"] += 1
      active["consumed"] = True
      active["consume_sequence"] = state["consume_sequence"]
      receipt_payload = {
        "schema": CONSUME_SCHEMA,
        "authority_id": state["authority_id"],
        "grant_id": payload["grant_id"],
        "boot_nonce": payload["boot_nonce"],
        "authorized_os_slot": payload["authorized_os_slot"],
        "snapshot_fingerprint": payload["snapshot"]["snapshot_fingerprint"],
        "consume_sequence": state["consume_sequence"],
      }
      receipt = _sign(self._authority_key, CONSUME_DOMAIN, receipt_payload)
      self._commit(state, "consume")
      return ConsumedAuthorization(copy.deepcopy(grant), receipt, state["consume_sequence"])

  def record_health(self, grant: dict[str, Any], health_envelope: dict[str, Any]) -> dict[str, Any]:
    with self._locked():
      state = self._load()
      grant_payload = verify_envelope(grant, GRANT_DOMAIN, state["authority_pubkey_b64"])
      active = state["active_grant"]
      if active is None or active["envelope"] != grant or not active["consumed"]:
        raise BoundaryError("health requires the consumed protected grant")
      if state["health_receipt"] is not None:
        raise BoundaryError("health receipt replay detected")
      payload = verify_envelope(health_envelope, HEALTH_DOMAIN, state["health_pubkey_b64"])
      expected = health_payload(grant, payload.get("boot_measurement", ""))
      if payload != expected:
        raise BoundaryError("health attestation is stale or mismatched")
      receipt_payload = {
        "schema": HEALTH_RECEIPT_SCHEMA,
        "authority_id": state["authority_id"],
        "grant_id": grant_payload["grant_id"],
        "caller": copy.deepcopy(grant_payload["caller"]),
        "policy_generation": grant_payload["policy_generation"],
        "epoch": grant_payload["epoch"],
        "boot_nonce": grant_payload["boot_nonce"],
        "authorized_os_slot": grant_payload["authorized_os_slot"],
        "snapshot_fingerprint": grant_payload["snapshot"]["snapshot_fingerprint"],
        "candidate": copy.deepcopy(grant_payload["candidate"]),
        "consume_sequence": active["consume_sequence"],
        "attestation_sha256": hashlib.sha256(canonical(health_envelope)).hexdigest(),
      }
      receipt = _sign(self._authority_key, HEALTH_RECEIPT_DOMAIN, receipt_payload)
      state["health_receipt"] = receipt
      self._commit(state, "health")
      return receipt

  def protected_counters(self) -> tuple[int, int]:
    with self._locked():
      state = self._load()
      return state["boot_counter"], state["consume_sequence"]


class ImmutableSnapshotQualifier:
  """Verify signed preconditions, consume once, then run supplemental F5 checks."""

  def __init__(self, app_root: str | os.PathLike[str], adapter: EarlyBootAdapter,
               caller: CallerIdentity, authority_id: str, authority_pubkey_b64: str,
               *, faults: BoundaryFaults | None = None):
    caller.validate()
    if type(adapter) is not MockEarlyBootAdapter:
      raise BoundaryError("host reference requires the exact obviously-insecure mock adapter")
    self.app_root = os.path.abspath(os.fspath(app_root))
    self.adapter = adapter
    self.caller = caller
    self.authority_id = authority_id
    self.authority_pubkey_b64 = authority_pubkey_b64
    self.faults = faults or BoundaryFaults()
    app = os.path.realpath(self.app_root)
    trust = os.path.realpath(adapter.trust_domain_path)
    try:
      if os.path.commonpath((app, trust)) == app:
        raise BoundaryError("mock authority must be outside the application-writable tree")
    except ValueError as error:
      raise BoundaryError("cannot establish mock trust-domain separation") from error

  def begin_boot(self, boot_nonce: str) -> tuple[BootContext, dict[str, Any]]:
    envelope = self.adapter.begin_boot(self.caller, boot_nonce)
    payload = verify_envelope(envelope, BOOT_DOMAIN, self.authority_pubkey_b64)
    context = BootContext.from_payload(payload)
    if context.authority_id != self.authority_id or context.caller != self.caller:
      raise BoundaryError("boot context authority or caller identity mismatch")
    return context, envelope

  def qualify(self, context: BootContext, boot_envelope: dict[str, Any],
              candidate: CandidateIdentity, provenance: SnapshotProvenance) -> QualifiedSnapshot:
    context.validate()
    provenance.validate()
    actual_boot = BootContext.from_payload(verify_envelope(
      boot_envelope, BOOT_DOMAIN, self.authority_pubkey_b64))
    if actual_boot != context or context.authority_id != self.authority_id or context.caller != self.caller:
      raise BoundaryError("boot context is forged, stale, or mismatched")
    if provenance.os_slot != context.os_slot:
      raise BoundaryError("snapshot is for the wrong authenticated OS slot")

    policy_envelope = self.adapter.policy_for_boot(boot_envelope)
    policy_payload = verify_envelope(policy_envelope, POLICY_DOMAIN, self.authority_pubkey_b64)
    if (set(policy_payload) != {
        "schema", "authority_id", "caller", "boot_nonce", "boot_counter",
        "authorized_os_slot", "policy"} or policy_payload.get("schema") != POLICY_SCHEMA or
        policy_payload.get("authority_id") != self.authority_id or
        policy_payload.get("caller") != asdict(self.caller) or
        policy_payload.get("boot_nonce") != context.boot_nonce or
        policy_payload.get("boot_counter") != context.boot_counter or
        policy_payload.get("authorized_os_slot") != context.os_slot):
      raise BoundaryError("protected policy envelope is stale or mismatched")
    policy = _policy_from_dict(policy_payload["policy"])
    if candidate != policy.recovery:
      raise BoundaryError("candidate is not the authority-selected protected candidate")

    grant = self.adapter.authorize_snapshot(boot_envelope, candidate, provenance)
    grant_payload = verify_envelope(grant, GRANT_DOMAIN, self.authority_pubkey_b64)
    expected_fields = {
      "schema", "authority_id", "grant_id", "caller", "policy_generation", "epoch",
      "policy_sha256", "boot_nonce", "boot_counter", "authorized_os_slot", "candidate",
      "snapshot", "decision",
    }
    if (set(grant_payload) != expected_fields or grant_payload.get("schema") != GRANT_SCHEMA or
        grant_payload.get("authority_id") != self.authority_id or
        grant_payload.get("caller") != asdict(self.caller) or
        grant_payload.get("policy_generation") != policy.generation or
        grant_payload.get("epoch") != policy.epoch or
        grant_payload.get("policy_sha256") != policy.policy_sha256 or
        grant_payload.get("boot_nonce") != context.boot_nonce or
        grant_payload.get("boot_counter") != context.boot_counter or
        grant_payload.get("authorized_os_slot") != context.os_slot or
        grant_payload.get("candidate") != asdict(candidate) or
        grant_payload.get("snapshot") != asdict(provenance) or
        grant_payload.get("decision") != "authorize-read-only-qualification" or
        not isinstance(grant_payload.get("grant_id"), str) or
        not _HEX16.fullmatch(grant_payload["grant_id"])):
      raise BoundaryError("signed grant fields are missing, stale, or mismatched")

    authorization = self.adapter.consume_authorization(grant)
    consume_payload = verify_envelope(
      authorization.consume_receipt, CONSUME_DOMAIN, self.authority_pubkey_b64)
    if (consume_payload.get("grant_id") != grant_payload["grant_id"] or
        consume_payload.get("boot_nonce") != context.boot_nonce or
        consume_payload.get("authorized_os_slot") != context.os_slot or
        consume_payload.get("snapshot_fingerprint") != provenance.snapshot_fingerprint or
        consume_payload.get("consume_sequence") != authorization.consume_sequence):
      raise BoundaryError("consume receipt is stale or mismatched")
    self.faults.hit("after_consume")

    # Supplemental only: external signed dm-verity/RO provenance above is the
    # immutable-media precondition.  F5 detects package inconsistencies but
    # cannot establish or replace immutability.
    pinned = ReadOnlyFdVerifier(self.app_root, policy).pin(candidate)
    try:
      self.faults.hit("after_f5_pin")
      return QualifiedSnapshot(context, candidate, provenance, authorization, pinned)
    except BaseException:
      pinned.close()
      raise


def sign_health(private_key: Ed25519PrivateKey, grant: dict[str, Any],
                boot_measurement: str) -> dict[str, Any]:
  """Test helper representing a separate authenticated health producer."""
  return _sign(private_key, HEALTH_DOMAIN, health_payload(grant, boot_measurement))

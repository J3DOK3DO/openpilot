#!/usr/bin/env python3
"""F4 protected-authority contract and durable host-only mock.

This module is NON-DEPLOYABLE.  ``MockProtectedAuthority`` is a filesystem
model for tests, not a secure element, TPM, RPMB implementation, or claim of
protected storage.  Its directory must be outside the replaceable application
tree.  Production must replace this mock with an early-boot adapter providing
hardware-backed identity/trust, authenticated health, rollback-resistant
transactional monotonic writes, and OS restart/boot-slot binding.

The mock deliberately never stores a private signing key.  Trial intent and
health decisions are authenticated with caller-owned ephemeral Ed25519 test
keys; the mock stores only their public keys.  Its durable counter is the sole
source of retry truth.  Application ``state.json`` is never accepted here.
"""
from __future__ import annotations

import base64
import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from typing import Any, Protocol


AUTHORITY_SCHEMA = "c7-g8-f4-mock-authority/1"
INTENT_SCHEMA = "c7-g8-f4-trial-intent/1"
HEALTH_SCHEMA = "c7-g8-f4-health-attestation/1"
REVOKE_SCHEMA = "c7-g8-f4-revoke/1"
INTENT_DOMAIN = b"c7-g8-f4-simulated-trial-intent/v1\x00"
HEALTH_DOMAIN = b"c7-g8-f4-simulated-health/v1\x00"
REVOKE_DOMAIN = b"c7-g8-f4-simulated-revoke/v1\x00"
SIMULATED_TRUST_LABEL = "SIMULATED_TEST_TRUST"

_SID_RE = re.compile(r"^[0-9]{6}-[0-9a-f]{12}$")
_HEX16_RE = re.compile(r"^[0-9a-f]{16}$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[0-9a-f]{64}$")


class AuthorityError(Exception):
  """Fail-closed authority or protocol error."""


class SimulatedPowerLoss(BaseException):
  """Abrupt process death at a named durability boundary."""


class AuthorityFaults:
  """Host-only deterministic fault hooks; never a storage durability claim."""

  def __init__(self, crash_at: str | None = None, oserror_at: dict[str, int] | None = None):
    self.crash_at = crash_at
    self.oserror_at = dict(oserror_at or {})
    self.points_seen: list[str] = []

  def hit(self, point: str) -> None:
    self.points_seen.append(point)
    if point in self.oserror_at:
      error_number = self.oserror_at[point]
      raise OSError(error_number, os.strerror(error_number), point)
    if point == self.crash_at:
      raise SimulatedPowerLoss(point)


def canonical(value: Any) -> bytes:
  return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _public_key_id(public_key_raw: bytes) -> str:
  return hashlib.sha256(public_key_raw).hexdigest()[:16]


def _decode_public_key(value: str, expected_key_id: str) -> bytes:
  try:
    raw = base64.b64decode(value, validate=True)
  except (ValueError, TypeError) as error:
    raise AuthorityError("malformed authority public key") from error
  if len(raw) != 32 or _public_key_id(raw) != expected_key_id:
    raise AuthorityError("authority public key identity mismatch")
  return raw


def _verify_envelope(envelope: Any, expected_payload: dict[str, Any], public_key_b64: str,
                     key_id: str, domain: bytes) -> None:
  """Verify a strict test-only Ed25519 decision envelope."""
  from cryptography.exceptions import InvalidSignature
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

  if not isinstance(envelope, dict) or set(envelope) != {"alg", "key_id", "payload", "signature", "trust"}:
    raise AuthorityError("malformed authenticated decision envelope")
  if (envelope.get("alg") != "ed25519" or envelope.get("key_id") != key_id or
      envelope.get("trust") != SIMULATED_TRUST_LABEL or envelope.get("payload") != expected_payload):
    raise AuthorityError("authenticated decision does not match protected request")
  try:
    signature = base64.b64decode(envelope["signature"], validate=True)
    public_key = Ed25519PublicKey.from_public_bytes(_decode_public_key(public_key_b64, key_id))
    public_key.verify(signature, domain + canonical(expected_payload))
  except InvalidSignature as error:
    raise AuthorityError("authenticated decision signature mismatch") from error
  except (KeyError, TypeError, ValueError) as error:
    raise AuthorityError("malformed authenticated decision signature") from error


@dataclass(frozen=True)
class CandidateIdentity:
  slot_id: str
  manifest_sha256: str
  source_commit: str
  release_sequence: int
  signing_key_id: str

  def validate(self) -> None:
    if not _SID_RE.fullmatch(self.slot_id):
      raise AuthorityError("malformed candidate slot identity")
    if not _HEX64_RE.fullmatch(self.manifest_sha256):
      raise AuthorityError("malformed candidate manifest identity")
    if not _HEX40_RE.fullmatch(self.source_commit):
      raise AuthorityError("malformed candidate commit identity")
    if (isinstance(self.release_sequence, bool) or not isinstance(self.release_sequence, int) or
        not 0 <= self.release_sequence <= (1 << 63) - 1):
      raise AuthorityError("malformed candidate rollback sequence")
    if not _HEX16_RE.fullmatch(self.signing_key_id):
      raise AuthorityError("malformed candidate signing identity")

  @classmethod
  def from_dict(cls, value: Any) -> "CandidateIdentity":
    if not isinstance(value, dict) or set(value) != {
        "slot_id", "manifest_sha256", "source_commit", "release_sequence", "signing_key_id"}:
      raise AuthorityError("malformed candidate identity object")
    candidate = cls(**value)
    candidate.validate()
    return candidate


@dataclass(frozen=True)
class PolicySnapshot:
  generation: int
  epoch: int
  recovery: CandidateIdentity
  expected_commit: str
  minimum_release_sequence: int
  signing_keys: tuple[dict[str, str], ...]
  policy_sha256: str


@dataclass(frozen=True)
class TrialTicket:
  generation: int
  epoch: int
  candidate: CandidateIdentity
  ticket_id: str
  secret: str

  def validate(self) -> None:
    if (isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 1 or
        isinstance(self.epoch, bool) or not isinstance(self.epoch, int) or self.epoch < 1):
      raise AuthorityError("malformed trial generation or epoch")
    self.candidate.validate()
    if not _HEX16_RE.fullmatch(self.ticket_id) or not _TOKEN_RE.fullmatch(self.secret):
      raise AuthorityError("malformed trial ticket")


@dataclass(frozen=True)
class BootGrant:
  disposition: str
  candidate: CandidateIdentity
  attempts_consumed: int
  attempts_limit: int


@dataclass(frozen=True)
class HealthReceipt:
  generation: int
  epoch: int
  candidate: CandidateIdentity
  ticket_id: str
  attestation_sha256: str


class ProtectedAuthority(Protocol):
  """Adapter surface that a real external authority must implement."""

  @property
  def trust_domain_path(self) -> str: ...

  def policy_snapshot(self) -> PolicySnapshot: ...

  def authorize_trial(self, candidate: CandidateIdentity, max_attempts: int,
                      intent_envelope: dict[str, Any]) -> TrialTicket: ...

  def consume_attempt(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket) -> BootGrant: ...

  def attest_health(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket,
                    attestation_envelope: dict[str, Any]) -> HealthReceipt: ...

  def promote_recovery(self, receipt: HealthReceipt) -> PolicySnapshot: ...

  def cancel_trial(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket) -> PolicySnapshot: ...

  def revoke_trial(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket,
                   reason: str, revocation_envelope: dict[str, Any]) -> PolicySnapshot: ...


def trial_intent_payload(policy: PolicySnapshot, candidate: CandidateIdentity, max_attempts: int) -> dict[str, Any]:
  """Exact payload an offline test authority must authenticate."""
  candidate.validate()
  return {
    "schema": INTENT_SCHEMA,
    "generation": policy.generation,
    "epoch": policy.epoch,
    "policy_sha256": policy.policy_sha256,
    "candidate": asdict(candidate),
    "max_attempts": max_attempts,
  }


def health_payload(ticket: TrialTicket, boot_measurement: str) -> dict[str, Any]:
  """Exact payload an independent simulated health source must authenticate."""
  ticket.validate()
  if not isinstance(boot_measurement, str) or not _HEX64_RE.fullmatch(boot_measurement):
    raise AuthorityError("malformed health measurement")
  return {
    "schema": HEALTH_SCHEMA,
    "generation": ticket.generation,
    "epoch": ticket.epoch,
    "ticket_id": ticket.ticket_id,
    "candidate": asdict(ticket.candidate),
    "decision": "healthy",
    "boot_measurement": boot_measurement,
  }


def revoke_payload(policy: PolicySnapshot, ticket: TrialTicket, reason: str) -> dict[str, Any]:
  ticket.validate()
  if not isinstance(reason, str) or not reason or len(reason) > 256:
    raise AuthorityError("malformed revocation reason")
  return {
    "schema": REVOKE_SCHEMA,
    "generation": policy.generation,
    "epoch": ticket.epoch,
    "ticket_id": ticket.ticket_id,
    "candidate": asdict(ticket.candidate),
    "reason": reason,
  }


class MockProtectedAuthority:
  """Durable external trust-domain model for hostile-app tests only.

  The state file is rollback-resistant only within the stated simulation:
  callers may forge/replay the entire application tree, but do not control this
  separate directory.  Real rollback resistance requires hardware.
  """

  @property
  def trust_domain_path(self) -> str:
    return self.root

  def __init__(self, root: str | os.PathLike[str], *, faults: AuthorityFaults | None = None,
               expected_commit: str | None = None, minimum_release_sequence: int | None = None,
               signing_keys: list[dict[str, str]] | None = None,
               decision_key_id: str | None = None, health_key_id: str | None = None):
    self.root = os.path.abspath(os.fspath(root))
    self.faults = faults or AuthorityFaults()
    self._state_path = os.path.join(self.root, "protected_state.json")
    self._lock_path = os.path.join(self.root, "authority.lock")
    state = self._load()
    supplied = {
      "expected_commit": expected_commit,
      "minimum_release_sequence": minimum_release_sequence,
      "signing_keys": signing_keys,
      "decision_key_id": decision_key_id,
      "health_key_id": health_key_id,
    }
    for name, wanted in supplied.items():
      if wanted is not None and state["policy"].get(name) != wanted:
        raise AuthorityError(f"protected authority bootstrap conflict: {name}")

  @classmethod
  def create(cls, root: str | os.PathLike[str], *, recovery: CandidateIdentity,
             expected_commit: str, minimum_release_sequence: int,
             signing_keys: list[dict[str, str]], decision_pubkey_b64: str,
             health_pubkey_b64: str, faults: AuthorityFaults | None = None) -> "MockProtectedAuthority":
    recovery.validate()
    root_path = os.path.abspath(os.fspath(root))
    if os.path.lexists(root_path):
      if not os.path.isdir(root_path) or os.listdir(root_path):
        raise AuthorityError("mock authority root must be a new empty directory")
    else:
      os.makedirs(root_path, mode=0o700)
    if recovery.source_commit != expected_commit:
      raise AuthorityError("initial recovery commit conflicts with protected policy")
    if recovery.release_sequence < minimum_release_sequence:
      raise AuthorityError("initial recovery is below protected rollback minimum")
    normalized_keys = cls._validate_signing_keys(signing_keys)
    allowed = {item["key_id"] for item in normalized_keys}
    if recovery.signing_key_id not in allowed:
      raise AuthorityError("initial recovery signing key is not protected-policy approved")
    decision_raw = base64.b64decode(decision_pubkey_b64, validate=True)
    health_raw = base64.b64decode(health_pubkey_b64, validate=True)
    decision_key_id = _public_key_id(decision_raw)
    health_key_id = _public_key_id(health_raw)
    _decode_public_key(decision_pubkey_b64, decision_key_id)
    _decode_public_key(health_pubkey_b64, health_key_id)
    state = {
      "schema": AUTHORITY_SCHEMA,
      "revision": 0,
      "policy": {
        "generation": 1,
        "epoch": 0,
        "recovery": asdict(recovery),
        "expected_commit": expected_commit,
        "minimum_release_sequence": minimum_release_sequence,
        "signing_keys": normalized_keys,
        "decision_key_id": decision_key_id,
        "decision_pubkey_b64": decision_pubkey_b64,
        "health_key_id": health_key_id,
        "health_pubkey_b64": health_pubkey_b64,
      },
      "active_trial": None,
      "pending_health": None,
    }
    cls._validate_state(state)
    cls._atomic_initial_write(root_path, state)
    return cls(root_path, faults=faults)

  @staticmethod
  def _validate_signing_keys(signing_keys: Any) -> list[dict[str, str]]:
    if not isinstance(signing_keys, list) or not signing_keys:
      raise AuthorityError("protected signing policy is empty or malformed")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in signing_keys:
      if not isinstance(item, dict) or set(item) != {"key_id", "pubkey_b64", "purpose"}:
        raise AuthorityError("malformed protected signing-key policy")
      if item["purpose"] != "production":
        raise AuthorityError("mock release verifier requires production-purpose semantics")
      key_id = item["key_id"]
      if not isinstance(key_id, str) or not _HEX16_RE.fullmatch(key_id) or key_id in seen:
        raise AuthorityError("malformed or duplicate protected signing-key identity")
      _decode_public_key(item["pubkey_b64"], key_id)
      normalized.append(copy.deepcopy(item))
      seen.add(key_id)
    normalized.sort(key=lambda item: item["key_id"])
    return normalized

  @staticmethod
  def _policy_digest(policy: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(policy)).hexdigest()

  @classmethod
  def _validate_state(cls, state: Any) -> None:
    if not isinstance(state, dict) or set(state) != {
        "schema", "revision", "policy", "active_trial", "pending_health"}:
      raise AuthorityError("protected authority state is malformed")
    if state.get("schema") != AUTHORITY_SCHEMA:
      raise AuthorityError("protected authority schema mismatch")
    revision = state.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
      raise AuthorityError("protected authority revision is malformed")
    policy = state.get("policy")
    if not isinstance(policy, dict) or set(policy) != {
        "generation", "epoch", "recovery", "expected_commit", "minimum_release_sequence", "signing_keys",
        "decision_key_id", "decision_pubkey_b64", "health_key_id", "health_pubkey_b64"}:
      raise AuthorityError("protected authority policy is malformed")
    generation, epoch = policy["generation"], policy["epoch"]
    minimum = policy["minimum_release_sequence"]
    if (isinstance(generation, bool) or not isinstance(generation, int) or generation < 1 or
        isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0 or
        isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0 or
        not isinstance(policy["expected_commit"], str) or not _HEX40_RE.fullmatch(policy["expected_commit"])):
      raise AuthorityError("protected generation/epoch/commit/minimum is malformed")
    recovery = CandidateIdentity.from_dict(policy["recovery"])
    keys = cls._validate_signing_keys(policy["signing_keys"])
    if recovery.source_commit != policy["expected_commit"] or recovery.release_sequence < minimum:
      raise AuthorityError("protected recovery violates commit or rollback policy")
    if recovery.signing_key_id not in {item["key_id"] for item in keys}:
      raise AuthorityError("protected recovery signing key is not approved")
    for prefix in ("decision", "health"):
      key_id = policy[f"{prefix}_key_id"]
      if not isinstance(key_id, str) or not _HEX16_RE.fullmatch(key_id):
        raise AuthorityError(f"protected {prefix} key identity is malformed")
      _decode_public_key(policy[f"{prefix}_pubkey_b64"], key_id)
    active = state["active_trial"]
    if active is not None:
      if not isinstance(active, dict) or set(active) != {
          "generation", "epoch", "candidate", "ticket_id", "ticket_hash", "attempts_limit", "attempts_consumed"}:
        raise AuthorityError("protected active trial is malformed")
      candidate = CandidateIdentity.from_dict(active["candidate"])
      if active["generation"] != generation or active["epoch"] != epoch:
        raise AuthorityError("protected active trial generation is inconsistent")
      if candidate.source_commit != policy["expected_commit"] or candidate.release_sequence < minimum:
        raise AuthorityError("protected active trial violates policy")
      if candidate.signing_key_id not in {item["key_id"] for item in keys}:
        raise AuthorityError("protected active trial signing key is not approved")
      if (not isinstance(active["ticket_id"], str) or not _HEX16_RE.fullmatch(active["ticket_id"]) or
          not isinstance(active["ticket_hash"], str) or not _HEX64_RE.fullmatch(active["ticket_hash"])):
        raise AuthorityError("protected active ticket is malformed")
      limit, consumed = active["attempts_limit"], active["attempts_consumed"]
      if (isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100 or
          isinstance(consumed, bool) or not isinstance(consumed, int) or not 0 <= consumed <= limit):
        raise AuthorityError("protected attempt accounting is malformed")
    pending = state["pending_health"]
    if pending is not None:
      if active is None or not isinstance(pending, dict) or set(pending) != {
          "generation", "epoch", "candidate", "ticket_id", "attestation_sha256"}:
        raise AuthorityError("protected health decision is malformed")
      receipt = HealthReceipt(candidate=CandidateIdentity.from_dict(pending["candidate"]), **{
        key: pending[key] for key in ("generation", "epoch", "ticket_id", "attestation_sha256")})
      if (receipt.generation != active["generation"] or receipt.epoch != active["epoch"] or
          asdict(receipt.candidate) != active["candidate"] or receipt.ticket_id != active["ticket_id"] or
          not _HEX64_RE.fullmatch(receipt.attestation_sha256)):
        raise AuthorityError("protected health decision is inconsistent")

  @staticmethod
  def _atomic_initial_write(root: str, state: dict[str, Any]) -> None:
    path = os.path.join(root, "protected_state.json")
    if os.path.lexists(path):
      raise AuthorityError("mock protected state already exists")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
      os.write(fd, canonical(state))
      os.fsync(fd)
    finally:
      os.close(fd)
    directory_fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
      os.fsync(directory_fd)
    finally:
      os.close(directory_fd)

  def _load(self) -> dict[str, Any]:
    try:
      before = os.lstat(self._state_path)
      if not os.path.isfile(self._state_path) or os.path.islink(self._state_path) or before.st_size > (1 << 20):
        raise AuthorityError("protected authority state is not a bounded regular file")
      fd = os.open(self._state_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
      try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
          raise AuthorityError("protected authority state changed while opening")
        raw = os.read(fd, (1 << 20) + 1)
      finally:
        os.close(fd)
      if len(raw) > (1 << 20):
        raise AuthorityError("protected authority state is oversized")
      state = json.loads(raw)
      self._validate_state(state)
      return state
    except AuthorityError:
      raise
    except (OSError, ValueError, TypeError) as error:
      raise AuthorityError(f"protected authority is missing, corrupt, or unreadable: {error!r}") from error

  def _commit(self, state: dict[str, Any], operation: str) -> None:
    self._validate_state(state)
    state["revision"] += 1
    self.faults.hit(f"{operation}_precommit")
    self.faults.hit("authority_write")
    fd, temporary = tempfile.mkstemp(prefix="protected_state.tmp.", dir=self.root)
    try:
      with os.fdopen(fd, "wb") as output:
        output.write(canonical(state))
        output.flush()
        os.fsync(output.fileno())
      self.faults.hit("authority_before_replace")
      os.replace(temporary, self._state_path)
      directory_fd = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
      try:
        os.fsync(directory_fd)
      finally:
        os.close(directory_fd)
      self.faults.hit(f"{operation}_committed")
    except SimulatedPowerLoss:
      raise
    except BaseException:
      try:
        os.unlink(temporary)
      except FileNotFoundError:
        pass
      raise

  def _locked(self):
    class Lock:
      def __init__(inner, outer: "MockProtectedAuthority"):
        inner.outer = outer
        inner.fd: int | None = None

      def __enter__(inner):
        try:
          inner.fd = os.open(inner.outer._lock_path, os.O_RDWR | os.O_CREAT, 0o600)
          fcntl.flock(inner.fd, fcntl.LOCK_EX)
        except OSError as error:
          if inner.fd is not None:
            os.close(inner.fd)
          raise AuthorityError(f"protected authority lock unavailable: {error!r}") from error
        return inner

      def __exit__(inner, *_exc):
        if inner.fd is not None:
          os.close(inner.fd)
        return False

    return Lock(self)

  @staticmethod
  def _snapshot(state: dict[str, Any]) -> PolicySnapshot:
    policy = state["policy"]
    return PolicySnapshot(
      generation=policy["generation"], epoch=policy["epoch"],
      recovery=CandidateIdentity.from_dict(policy["recovery"]),
      expected_commit=policy["expected_commit"], minimum_release_sequence=policy["minimum_release_sequence"],
      signing_keys=tuple(copy.deepcopy(policy["signing_keys"])),
      policy_sha256=MockProtectedAuthority._policy_digest(policy),
    )

  def policy_snapshot(self) -> PolicySnapshot:
    with self._locked():
      return self._snapshot(self._load())

  @staticmethod
  def _check_candidate(candidate: CandidateIdentity, state: dict[str, Any]) -> None:
    candidate.validate()
    policy = state["policy"]
    if candidate.source_commit != policy["expected_commit"]:
      raise AuthorityError("candidate commit differs from protected policy")
    if candidate.release_sequence < policy["minimum_release_sequence"]:
      raise AuthorityError("candidate violates protected rollback minimum")
    if candidate.signing_key_id not in {item["key_id"] for item in policy["signing_keys"]}:
      raise AuthorityError("candidate signing key differs from protected policy")

  @staticmethod
  def _ticket_hash(ticket: TrialTicket) -> str:
    ticket.validate()
    return hashlib.sha256(canonical({
      "generation": ticket.generation,
      "epoch": ticket.epoch,
      "candidate": asdict(ticket.candidate),
      "ticket_id": ticket.ticket_id,
      "secret": ticket.secret,
    })).hexdigest()

  @classmethod
  def _require_active(cls, state: dict[str, Any], trial: CandidateIdentity, epoch: int,
                      ticket: TrialTicket) -> dict[str, Any]:
    trial.validate()
    ticket.validate()
    active = state["active_trial"]
    if active is None:
      raise AuthorityError("no protected active trial")
    if (epoch != state["policy"]["epoch"] or epoch != ticket.epoch or
        ticket.generation != state["policy"]["generation"] or
        trial != ticket.candidate or asdict(trial) != active["candidate"] or
        active["ticket_id"] != ticket.ticket_id or active["ticket_hash"] != cls._ticket_hash(ticket)):
      raise AuthorityError("trial ticket, generation, epoch, or identity mismatch")
    return active

  def authorize_trial(self, candidate: CandidateIdentity, max_attempts: int,
                      intent_envelope: dict[str, Any]) -> TrialTicket:
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 100:
      raise AuthorityError("trial retry budget must be an integer from 1 through 100")
    with self._locked():
      state = self._load()
      if state["active_trial"] is not None:
        raise AuthorityError("a protected trial is already active")
      self._check_candidate(candidate, state)
      snapshot = self._snapshot(state)
      payload = trial_intent_payload(snapshot, candidate, max_attempts)
      policy = state["policy"]
      _verify_envelope(intent_envelope, payload, policy["decision_pubkey_b64"],
                       policy["decision_key_id"], INTENT_DOMAIN)
      policy["epoch"] += 1
      ticket = TrialTicket(
        generation=policy["generation"], epoch=policy["epoch"], candidate=candidate,
        ticket_id=os.urandom(8).hex(), secret=os.urandom(32).hex(),
      )
      state["active_trial"] = {
        "generation": ticket.generation, "epoch": ticket.epoch, "candidate": asdict(candidate),
        "ticket_id": ticket.ticket_id, "ticket_hash": self._ticket_hash(ticket),
        "attempts_limit": max_attempts, "attempts_consumed": 0,
      }
      state["pending_health"] = None
      self._commit(state, "authorize")
      return ticket

  def consume_attempt(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket) -> BootGrant:
    """Durably consume before returning trial; post-commit crash loses an attempt."""
    with self._locked():
      state = self._load()
      active = self._require_active(state, trial, epoch, ticket)
      if active["attempts_consumed"] >= active["attempts_limit"]:
        return BootGrant("recovery", CandidateIdentity.from_dict(state["policy"]["recovery"]),
                         active["attempts_consumed"], active["attempts_limit"])
      active["attempts_consumed"] += 1
      self._commit(state, "consume")
      return BootGrant("trial", trial, active["attempts_consumed"], active["attempts_limit"])

  def attest_health(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket,
                    attestation_envelope: dict[str, Any]) -> HealthReceipt:
    with self._locked():
      state = self._load()
      active = self._require_active(state, trial, epoch, ticket)
      if active["attempts_consumed"] < 1:
        raise AuthorityError("health cannot confirm a trial that was never granted")
      payload = attestation_envelope.get("payload") if isinstance(attestation_envelope, dict) else None
      if not isinstance(payload, dict) or payload.get("candidate") != asdict(trial):
        raise AuthorityError("health attestation candidate mismatch")
      policy = state["policy"]
      _verify_envelope(attestation_envelope, payload, policy["health_pubkey_b64"],
                       policy["health_key_id"], HEALTH_DOMAIN)
      expected_without_measurement = {
        "schema": HEALTH_SCHEMA, "generation": ticket.generation, "epoch": ticket.epoch,
        "ticket_id": ticket.ticket_id, "candidate": asdict(ticket.candidate), "decision": "healthy",
      }
      if ({key: payload.get(key) for key in expected_without_measurement} != expected_without_measurement or
          not isinstance(payload.get("boot_measurement"), str) or
          not _HEX64_RE.fullmatch(payload["boot_measurement"])):
        raise AuthorityError("health attestation claims are malformed or stale")
      receipt = HealthReceipt(
        ticket.generation, ticket.epoch, trial, ticket.ticket_id,
        hashlib.sha256(canonical(attestation_envelope)).hexdigest(),
      )
      state["pending_health"] = asdict(receipt)
      self._commit(state, "attest")
      return receipt

  def promote_recovery(self, receipt: HealthReceipt) -> PolicySnapshot:
    """Atomically promote only the protected, authenticated health decision."""
    with self._locked():
      state = self._load()
      active = state["active_trial"]
      pending = state["pending_health"]
      if active is None or pending is None or pending != asdict(receipt):
        raise AuthorityError("promotion lacks the protected authenticated health decision")
      if (receipt.generation != state["policy"]["generation"] or receipt.epoch != state["policy"]["epoch"] or
          asdict(receipt.candidate) != active["candidate"] or receipt.ticket_id != active["ticket_id"]):
        raise AuthorityError("promotion receipt is stale or inconsistent")
      policy = state["policy"]
      policy["recovery"] = asdict(receipt.candidate)
      policy["minimum_release_sequence"] = max(
        policy["minimum_release_sequence"], receipt.candidate.release_sequence)
      policy["generation"] += 1
      policy["epoch"] += 1
      state["active_trial"] = None
      state["pending_health"] = None
      self._commit(state, "promote")
      return self._snapshot(state)

  def cancel_trial(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket) -> PolicySnapshot:
    with self._locked():
      state = self._load()
      self._require_active(state, trial, epoch, ticket)
      state["active_trial"] = None
      state["pending_health"] = None
      state["policy"]["epoch"] += 1
      self._commit(state, "cancel")
      return self._snapshot(state)

  def revoke_trial(self, trial: CandidateIdentity, epoch: int, ticket: TrialTicket,
                   reason: str, revocation_envelope: dict[str, Any]) -> PolicySnapshot:
    with self._locked():
      state = self._load()
      self._require_active(state, trial, epoch, ticket)
      payload = revoke_payload(self._snapshot(state), ticket, reason)
      policy = state["policy"]
      _verify_envelope(revocation_envelope, payload, policy["decision_pubkey_b64"],
                       policy["decision_key_id"], REVOKE_DOMAIN)
      state["active_trial"] = None
      state["pending_health"] = None
      policy["epoch"] += 1
      self._commit(state, "revoke")
      return self._snapshot(state)

  def protected_attempts(self) -> tuple[int, int]:
    """Test diagnostics only; never an application authorization input."""
    with self._locked():
      state = self._load()
      active = state["active_trial"]
      if active is None:
        return (0, 0)
      return active["attempts_consumed"], active["attempts_limit"]

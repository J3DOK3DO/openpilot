#!/usr/bin/env python3
"""NON-DEPLOYABLE Stage 2 supervised application-slot integration prototype.

This host-only model has no process, device, network, mount, boot-control,
systemd installation, Panda, or CAN interface.  It never executes a launcher.
Ordinary files under a host temporary directory simulate a crash journal; they
are not rollback-resistant storage.  Production requires a verified OS-rooted
supervisor, vetted cryptography, and hardware-backed monotonic state.

Every decision that can advance a trial is returned by an externally supplied
``AuthenticatedDecisionProvider``.  This module contains no signer and cannot
self-authorize physical readiness, health, or recovery promotion.  Durable
retry truth is delegated to the existing ``ProtectedAuthority`` protocol.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from g8_protected_authority import (
  BootGrant,
  CandidateIdentity,
  HealthReceipt,
  PolicySnapshot,
  ProtectedAuthority,
  TrialTicket,
)


STATE_SCHEMA = "G8_F12_RC3_STAGE2_HOST_JOURNAL_V1"
PROTOTYPE_CLASSIFICATION = "NON_DEPLOYABLE_HOST_ONLY_STAGE2_PROTOTYPE"
PLATFORM = "HONDA_ACCORD_11G"
MAX_ATTEMPTS = 3
MAX_STATE_BYTES = 1 << 20

PRODUCTION_CRYPTO_REQUIREMENT: dict[str, Any] = {
  "status": "UNSATISFIED_EXTERNAL_REQUIREMENT",
  "required_backend": "VETTED_MAINTAINED_PRODUCTION_CRYPTOGRAPHY_DEPENDENCY",
  "custom_ed25519_implementation_allowed": False,
  "existing_readiness_gate_custom_ed25519_is_production_acceptable": False,
  "reason": "qualification tooling must not become a production cryptographic primitive",
}

# Design data only.  It is deliberately not service-unit syntax and contains no
# command, executable pathname, or installation operation.
OS_INTEGRATION_CONTRACT: dict[str, Any] = {
  "classification": "DOCUMENTATION_ONLY_NONINSTALLABLE",
  "unit_emitted": False,
  "start_command_defined": False,
  "verified_rootfs_required": True,
  "rollback_resistant_state_required": "TEE_OR_RPMB_BACKED_MONOTONIC_AUTHORITY",
  "selinux_agnos_19_8_1": "PERMISSIVE_IS_NOT_A_SECURITY_BOUNDARY",
  "application_storage": "SHARED_DATA_REQUIRES_SEPARATE_IMMUTABLE_APP_SLOTS",
  "os_slots_are_application_slots": False,
  "panda_default": "PHYSICALLY_NEUTRALIZED_AND_DEVICE_ACCESS_DENIED",
  "physical_key_custody_assumed": False,
  "production_crypto": PRODUCTION_CRYPTO_REQUIREMENT,
}

_HEX16 = re.compile(r"^[0-9a-f]{16}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")


class Stage2Error(RuntimeError):
  """A strict protocol, state, or external-authority failure."""


class SimulatedPowerInterruption(BaseException):
  """Host-test crash at a named journal/authority boundary."""


class Stage2Faults:
  """Deterministic host-only crash hooks; not a durability claim."""

  def __init__(self, crash_at: str | None = None):
    self.crash_at = crash_at
    self.points_seen: list[str] = []

  def hit(self, point: str) -> None:
    self.points_seen.append(point)
    if point == self.crash_at:
      raise SimulatedPowerInterruption(point)


class OsSlot(str, Enum):
  A = "OS_A"
  B = "OS_B"


class Phase(str, Enum):
  RECOVERY_PINNED = "RECOVERY_PINNED"
  PREAUTHORIZING = "PREAUTHORIZING"
  TRIAL_AUTHORIZED = "TRIAL_AUTHORIZED"
  ATTEMPT_CONSUMED = "ATTEMPT_CONSUMED"
  PROBATION = "PROBATION"
  RETRY_READY = "RETRY_READY"
  HEALTH_ATTESTED = "HEALTH_ATTESTED"
  PROMOTED_MODEL_ONLY = "PROMOTED_MODEL_ONLY"
  ROLLED_BACK = "ROLLED_BACK"
  HOLD = "HOLD"


@dataclass(frozen=True)
class OsBootIdentity:
  """Authenticated OS context, never an application-slot name."""

  slot: OsSlot
  boot_nonce: str
  boot_sequence: int
  rootfs_measurement: str
  agnos_version: str

  def validate(self) -> None:
    if type(self.slot) is not OsSlot:
      raise Stage2Error("OS slot must use the distinct OsSlot type")
    if not _HEX64.fullmatch(self.boot_nonce) or not _HEX64.fullmatch(self.rootfs_measurement):
      raise Stage2Error("OS boot nonce or rootfs measurement is malformed")
    if type(self.boot_sequence) is not int or self.boot_sequence < 1:
      raise Stage2Error("OS boot sequence must be a positive monotonic integer")
    if type(self.agnos_version) is not str or not _TOKEN.fullmatch(self.agnos_version):
      raise Stage2Error("AGNOS version is malformed")


@dataclass(frozen=True)
class DeviceIdentity:
  platform: str
  comma_serial_sha256: str
  panda_serial_sha256: str

  def validate(self) -> None:
    if self.platform != PLATFORM:
      raise Stage2Error("device platform is not the exact Honda-only platform")
    if (not _HEX64.fullmatch(self.comma_serial_sha256) or
        not _HEX64.fullmatch(self.panda_serial_sha256)):
      raise Stage2Error("device identity digest is malformed")


@dataclass(frozen=True)
class SupervisorPolicy:
  max_attempts: int
  expected_source_commit: str
  require_physical_gate: bool = True
  neutral_can_required: bool = True

  def validate(self) -> None:
    if type(self.max_attempts) is not int or not 1 <= self.max_attempts <= MAX_ATTEMPTS:
      raise Stage2Error("Stage 2 retry budget must be an integer from one through three")
    if not _HEX40.fullmatch(self.expected_source_commit):
      raise Stage2Error("Stage 2 expected source commit is malformed")
    if self.require_physical_gate is not True or self.neutral_can_required is not True:
      raise Stage2Error("Stage 2 policy cannot waive physical gating or neutral CAN")


@dataclass(frozen=True)
class RecoveryExpectation:
  candidate: CandidateIdentity
  os_slot: OsSlot
  rootfs_measurement: str
  device: DeviceIdentity


@dataclass(frozen=True)
class RecoveryApproval:
  candidate: CandidateIdentity
  os_slot: OsSlot
  rootfs_measurement: str
  device: DeviceIdentity
  immutable_snapshot_sha256: str
  approval_id: str
  approval_sequence: int
  authenticated: bool

  def validate(self) -> None:
    self.candidate.validate()
    self.device.validate()
    if type(self.os_slot) is not OsSlot or not _HEX64.fullmatch(self.rootfs_measurement):
      raise Stage2Error("recovery approval has an invalid OS binding")
    if not _HEX64.fullmatch(self.immutable_snapshot_sha256):
      raise Stage2Error("recovery approval lacks immutable snapshot identity")
    if not _TOKEN.fullmatch(self.approval_id):
      raise Stage2Error("recovery approval id is malformed")
    if type(self.approval_sequence) is not int or self.approval_sequence < 1:
      raise Stage2Error("recovery approval sequence is invalid")
    if self.authenticated is not True:
      raise Stage2Error("recovery identity is not externally authenticated")


@dataclass(frozen=True)
class GateExpectation:
  candidate: CandidateIdentity
  os_boot: OsBootIdentity
  device: DeviceIdentity
  gate_nonce: str
  gate_sequence: int
  owner_approval_sha256: str
  neutral_can_required: bool


@dataclass(frozen=True)
class PhysicalGateDecision:
  candidate: CandidateIdentity
  os_boot: OsBootIdentity
  device: DeviceIdentity
  gate_nonce: str
  gate_sequence: int
  owner_approval_sha256: str
  evidence_manifest_sha256: str
  disposition: str
  evidence_classification: str
  authenticated: bool
  physical_gate_passed: bool
  neutral_can_confirmed: bool

  def validate(self) -> None:
    self.candidate.validate()
    self.os_boot.validate()
    self.device.validate()
    if not _HEX64.fullmatch(self.gate_nonce) or not _HEX64.fullmatch(self.owner_approval_sha256):
      raise Stage2Error("gate nonce or owner context digest is malformed")
    if not _HEX64.fullmatch(self.evidence_manifest_sha256):
      raise Stage2Error("gate evidence manifest identity is malformed")
    if type(self.gate_sequence) is not int or self.gate_sequence < 1:
      raise Stage2Error("gate sequence is invalid")
    if (self.disposition != "PHYSICAL_GATE_PASSED_FOR_HOST_MODEL_ONLY" or
        self.evidence_classification != "PHYSICAL_DEVICE_EVIDENCE" or
        self.authenticated is not True or self.physical_gate_passed is not True or
        self.neutral_can_confirmed is not True):
      raise Stage2Error("external physical gate did not pass all required claims")


@dataclass(frozen=True)
class HealthExpectation:
  candidate: CandidateIdentity
  os_boot: OsBootIdentity
  device: DeviceIdentity
  gate_nonce: str
  gate_sequence: int
  attempt_nonce: str
  attempts_consumed: int
  owner_approval_sha256: str


@dataclass(frozen=True)
class HealthDecision:
  candidate: CandidateIdentity
  os_boot: OsBootIdentity
  device: DeviceIdentity
  gate_nonce: str
  gate_sequence: int
  attempt_nonce: str
  attempts_consumed: int
  owner_approval_sha256: str
  measurement_sha256: str
  decision: str
  authenticated: bool
  independent_attester: bool

  def validate(self) -> None:
    self.candidate.validate()
    self.os_boot.validate()
    self.device.validate()
    for value in (self.gate_nonce, self.attempt_nonce, self.owner_approval_sha256,
                  self.measurement_sha256):
      if not _HEX64.fullmatch(value):
        raise Stage2Error("health decision contains a malformed digest or nonce")
    if (type(self.gate_sequence) is not int or self.gate_sequence < 1 or
        type(self.attempts_consumed) is not int or self.attempts_consumed < 1):
      raise Stage2Error("health decision counters are malformed")
    if (self.decision != "HEALTHY" or self.authenticated is not True or
        self.independent_attester is not True):
      raise Stage2Error("health is not an authenticated independent healthy decision")


@dataclass(frozen=True)
class PromotionExpectation:
  health: HealthDecision
  receipt: HealthReceipt
  previous_recovery: RecoveryApproval


class AuthenticatedDecisionProvider(Protocol):
  """External verifier/authority boundary.  The controller never implements it."""

  def verify_recovery(self, envelope: dict[str, Any],
                      expected: RecoveryExpectation) -> RecoveryApproval: ...

  def verify_physical_gate(self, envelope: dict[str, Any],
                           expected: GateExpectation) -> PhysicalGateDecision: ...

  def verify_health(self, envelope: dict[str, Any],
                    expected: HealthExpectation) -> HealthDecision: ...

  def verify_promotion(self, envelope: dict[str, Any],
                       expected: PromotionExpectation) -> RecoveryApproval: ...


@dataclass(frozen=True)
class LauncherDecision:
  """Metadata-only decision; no executable name, descriptor, or operation."""

  candidate: CandidateIdentity
  os_boot: OsBootIdentity
  attempt_nonce: str
  attempts_consumed: int
  attempts_limit: int
  physical_gate_passed: bool
  disposition: str = "OBSERVE_TRIAL_WITH_CAN_PHYSICALLY_NEUTRALIZED"
  process_started: bool = False
  installation_authorized: bool = False
  boot_slot_change_authorized: bool = False
  panda_or_can_authorized: bool = False


def _canonical(value: Any) -> bytes:
  try:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")
  except (TypeError, ValueError, UnicodeEncodeError) as error:
    raise Stage2Error("journal value is not canonical-JSON encodable") from error


def _candidate(value: Any) -> CandidateIdentity:
  try:
    return CandidateIdentity.from_dict(value)
  except Exception as error:
    raise Stage2Error("journal candidate identity is malformed") from error


def _ticket(value: Any) -> TrialTicket:
  if type(value) is not dict or set(value) != {
      "generation", "epoch", "candidate", "ticket_id", "secret"}:
    raise Stage2Error("journal trial ticket is malformed")
  ticket = TrialTicket(
    generation=value["generation"], epoch=value["epoch"],
    candidate=_candidate(value["candidate"]), ticket_id=value["ticket_id"], secret=value["secret"])
  try:
    ticket.validate()
  except Exception as error:
    raise Stage2Error("journal trial ticket is malformed") from error
  return ticket


def _os_boot(value: Any) -> OsBootIdentity:
  if type(value) is not dict or set(value) != {
      "slot", "boot_nonce", "boot_sequence", "rootfs_measurement", "agnos_version"}:
    raise Stage2Error("journal OS identity is malformed")
  try:
    identity = OsBootIdentity(slot=OsSlot(value["slot"]), **{
      key: value[key] for key in ("boot_nonce", "boot_sequence", "rootfs_measurement", "agnos_version")})
  except (TypeError, ValueError) as error:
    raise Stage2Error("journal OS identity is malformed") from error
  identity.validate()
  return identity


def _device(value: Any) -> DeviceIdentity:
  if type(value) is not dict or set(value) != {
      "platform", "comma_serial_sha256", "panda_serial_sha256"}:
    raise Stage2Error("journal device identity is malformed")
  identity = DeviceIdentity(**value)
  identity.validate()
  return identity


class Stage2Supervisor:
  """Strict, crash-injectable, non-executing application-slot controller model."""

  _STATE_KEYS = {
    "schema", "classification", "revision", "sequence", "phase", "last_event",
    "os_boot", "device", "recovery", "last_gate_sequence", "trial", "ticket",
    "gate", "start_request_id", "attempts_consumed", "attempts_limit",
    "current_attempt_nonce", "used_attempt_nonces", "health", "health_receipt",
  }

  def __init__(self, *, authority: ProtectedAuthority,
               decisions: AuthenticatedDecisionProvider,
               state_root: str | os.PathLike[str], writable_app_root: str | os.PathLike[str],
               os_boot: OsBootIdentity, device: DeviceIdentity, policy: SupervisorPolicy,
               recovery_envelope: dict[str, Any], faults: Stage2Faults | None = None):
    if authority is None or decisions is None:
      raise Stage2Error("protected authority and external decision provider are mandatory")
    os_boot.validate()
    device.validate()
    policy.validate()
    self.authority = authority
    self.decisions = decisions
    self.os_boot = os_boot
    self.device = device
    self.policy = policy
    self.faults = faults or Stage2Faults()
    # Reject a supplied symlink before resolve() removes the evidence of it.
    supplied_state_root = Path(state_root)
    if supplied_state_root.is_symlink():
      raise Stage2Error("host journal root cannot be a symlink")
    self.state_root = supplied_state_root.resolve()
    self.app_root = Path(writable_app_root).resolve(strict=True)
    temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    if self.state_root == temporary_root or not self.state_root.is_relative_to(temporary_root):
      raise Stage2Error("host journal must be a dedicated directory beneath the temporary root")
    try:
      trust_root = Path(authority.trust_domain_path).resolve(strict=True)
    except Exception as error:
      raise Stage2Error("protected authority trust domain is unavailable") from error
    if (self.state_root == self.app_root or self.state_root.is_relative_to(self.app_root) or
        trust_root == self.app_root or trust_root.is_relative_to(self.app_root) or
        self.state_root == trust_root or self.state_root.is_relative_to(trust_root) or
        trust_root.is_relative_to(self.state_root)):
      raise Stage2Error("app, host journal, and protected authority domains must be separate")
    self.state_root.mkdir(mode=0o700, parents=False, exist_ok=True)
    state_root_info = os.lstat(self.state_root)
    if (stat.S_ISLNK(state_root_info.st_mode) or not stat.S_ISDIR(state_root_info.st_mode) or
        state_root_info.st_uid != os.getuid() or stat.S_IMODE(state_root_info.st_mode) != 0o700):
      raise Stage2Error("host journal root must be a private, owner-controlled real directory")
    self._state_path = self.state_root / "stage2_state.json"
    self._lock_path = self.state_root / "stage2.lock"
    try:
      snapshot = authority.policy_snapshot()
    except Exception as error:
      raise Stage2Error("protected authority policy is unavailable") from error
    self._validate_policy_snapshot(snapshot)
    expected_recovery = RecoveryExpectation(
      snapshot.recovery, os_boot.slot, os_boot.rootfs_measurement, device)
    try:
      recovery = decisions.verify_recovery(recovery_envelope, expected_recovery)
    except Exception as error:
      raise Stage2Error("external immutable recovery approval was rejected") from error
    self._validate_recovery(recovery, expected_recovery)
    # This is only a per-process reference, not tamper-resistant storage.
    self._trusted_recovery = recovery
    with self._locked():
      if not self._state_path.exists():
        self._write_initial(self._initial_state(recovery))
      state = self._load()
      if (_os_boot(state["os_boot"]) != os_boot or _device(state["device"]) != device or
          self._recovery_from_dict(state["recovery"]) != recovery):
        raise Stage2Error("journal is bound to a different OS, device, or recovery approval")
      self._validate_state(state)

  def _validate_policy_snapshot(self, snapshot: PolicySnapshot) -> None:
    if type(snapshot) is not PolicySnapshot:
      raise Stage2Error("authority returned a non-exact policy snapshot")
    snapshot.recovery.validate()
    if snapshot.expected_commit != self.policy.expected_source_commit:
      raise Stage2Error("Stage 2 policy and protected source policy differ")
    if (snapshot.recovery.source_commit != snapshot.expected_commit or
        snapshot.recovery.release_sequence < snapshot.minimum_release_sequence or
        snapshot.recovery.signing_key_id not in {item.get("key_id") for item in snapshot.signing_keys}):
      raise Stage2Error("protected recovery violates protected policy")

  @staticmethod
  def _validate_recovery(recovery: RecoveryApproval, expected: RecoveryExpectation) -> None:
    if type(recovery) is not RecoveryApproval:
      raise Stage2Error("external provider returned a non-exact recovery approval")
    recovery.validate()
    if (recovery.candidate != expected.candidate or recovery.os_slot != expected.os_slot or
        recovery.rootfs_measurement != expected.rootfs_measurement or recovery.device != expected.device):
      raise Stage2Error("recovery approval binding mismatch")

  @staticmethod
  def _recovery_from_dict(value: Any) -> RecoveryApproval:
    if type(value) is not dict or set(value) != {
        "candidate", "os_slot", "rootfs_measurement", "device", "immutable_snapshot_sha256",
        "approval_id", "approval_sequence", "authenticated"}:
      raise Stage2Error("journal recovery approval is malformed")
    try:
      recovery = RecoveryApproval(
        candidate=_candidate(value["candidate"]), os_slot=OsSlot(value["os_slot"]),
        rootfs_measurement=value["rootfs_measurement"], device=_device(value["device"]),
        immutable_snapshot_sha256=value["immutable_snapshot_sha256"],
        approval_id=value["approval_id"], approval_sequence=value["approval_sequence"],
        authenticated=value["authenticated"])
    except (TypeError, ValueError) as error:
      raise Stage2Error("journal recovery approval is malformed") from error
    recovery.validate()
    return recovery

  @staticmethod
  def _gate_from_dict(value: Any) -> PhysicalGateDecision:
    if type(value) is not dict:
      raise Stage2Error("journal physical gate is malformed")
    expected = {
      "candidate", "os_boot", "device", "gate_nonce", "gate_sequence",
      "owner_approval_sha256", "evidence_manifest_sha256", "disposition",
      "evidence_classification", "authenticated", "physical_gate_passed",
      "neutral_can_confirmed",
    }
    if set(value) != expected:
      raise Stage2Error("journal physical gate is malformed")
    gate = PhysicalGateDecision(
      candidate=_candidate(value["candidate"]), os_boot=_os_boot(value["os_boot"]),
      device=_device(value["device"]), **{key: value[key] for key in expected - {
        "candidate", "os_boot", "device"}})
    gate.validate()
    return gate

  @staticmethod
  def _health_from_dict(value: Any) -> HealthDecision:
    if type(value) is not dict:
      raise Stage2Error("journal health decision is malformed")
    expected = {
      "candidate", "os_boot", "device", "gate_nonce", "gate_sequence", "attempt_nonce",
      "attempts_consumed", "owner_approval_sha256", "measurement_sha256", "decision",
      "authenticated", "independent_attester",
    }
    if set(value) != expected:
      raise Stage2Error("journal health decision is malformed")
    health = HealthDecision(
      candidate=_candidate(value["candidate"]), os_boot=_os_boot(value["os_boot"]),
      device=_device(value["device"]), **{key: value[key] for key in expected - {
        "candidate", "os_boot", "device"}})
    health.validate()
    return health

  @staticmethod
  def _receipt_from_dict(value: Any) -> HealthReceipt:
    if type(value) is not dict or set(value) != {
        "generation", "epoch", "candidate", "ticket_id", "attestation_sha256"}:
      raise Stage2Error("journal health receipt is malformed")
    receipt = HealthReceipt(
      generation=value["generation"], epoch=value["epoch"],
      candidate=_candidate(value["candidate"]), ticket_id=value["ticket_id"],
      attestation_sha256=value["attestation_sha256"])
    if (type(receipt.generation) is not int or receipt.generation < 1 or
        type(receipt.epoch) is not int or receipt.epoch < 1 or
        not _HEX16.fullmatch(receipt.ticket_id) or not _HEX64.fullmatch(receipt.attestation_sha256)):
      raise Stage2Error("journal health receipt is malformed")
    return receipt

  def _initial_state(self, recovery: RecoveryApproval) -> dict[str, Any]:
    return {
      "schema": STATE_SCHEMA, "classification": PROTOTYPE_CLASSIFICATION,
      "revision": 0, "sequence": 0, "phase": Phase.RECOVERY_PINNED.value,
      "last_event": "EXTERNALLY_APPROVED_IMMUTABLE_RECOVERY_PINNED",
      "os_boot": asdict(self.os_boot), "device": asdict(self.device),
      "recovery": asdict(recovery), "last_gate_sequence": 0,
      "trial": None, "ticket": None, "gate": None, "start_request_id": None,
      "attempts_consumed": 0, "attempts_limit": 0, "current_attempt_nonce": None,
      "used_attempt_nonces": [], "health": None, "health_receipt": None,
    }

  def _locked(self):
    class Lock:
      def __init__(inner, outer: "Stage2Supervisor"):
        inner.outer = outer
        inner.fd: int | None = None

      def __enter__(inner):
        try:
          inner.fd = os.open(inner.outer._lock_path,
                             os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) |
                             getattr(os, "O_NOFOLLOW", 0), 0o600)
          lock_info = os.fstat(inner.fd)
          if (not stat.S_ISREG(lock_info.st_mode) or lock_info.st_uid != os.getuid() or
              stat.S_IMODE(lock_info.st_mode) != 0o600 or lock_info.st_nlink != 1):
            raise OSError("journal lock is not a private regular file")
          fcntl.flock(inner.fd, fcntl.LOCK_EX)
        except OSError as error:
          if inner.fd is not None:
            os.close(inner.fd)
          raise Stage2Error("host journal lock is unavailable") from error
        return inner

      def __exit__(inner, *_exc: object) -> bool:
        if inner.fd is not None:
          os.close(inner.fd)
        return False

    return Lock(self)

  def _write_initial(self, state: dict[str, Any]) -> None:
    self._validate_state(state)
    payload = _canonical(state)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
      descriptor = os.open(self._state_path, flags, 0o600)
      try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
      finally:
        os.close(descriptor)
      directory = os.open(self.state_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
      try:
        os.fsync(directory)
      finally:
        os.close(directory)
    except OSError as error:
      raise Stage2Error("cannot initialize host journal") from error

  def _load(self) -> dict[str, Any]:
    try:
      before = os.lstat(self._state_path)
      if (not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode) or
          before.st_size <= 0 or before.st_size > MAX_STATE_BYTES):
        raise Stage2Error("host journal is not a bounded regular file")
      descriptor = os.open(self._state_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
      try:
        opened = os.fstat(descriptor)
        raw = os.read(descriptor, MAX_STATE_BYTES + 1)
        after = os.fstat(descriptor)
      finally:
        os.close(descriptor)
      identity = lambda info: (info.st_dev, info.st_ino, info.st_mode, info.st_size,
                               info.st_mtime_ns, info.st_ctime_ns)
      if identity(before) != identity(opened) or identity(opened) != identity(after):
        raise Stage2Error("host journal changed while read")
      value = json.loads(raw)
      if type(value) is not dict or _canonical(value) != raw:
        raise Stage2Error("host journal is not canonical JSON")
      self._validate_state(value)
      if (_os_boot(value["os_boot"]) != self.os_boot or
          _device(value["device"]) != self.device or
          self._recovery_from_dict(value["recovery"]) != self._trusted_recovery):
        raise Stage2Error("host journal changed its pinned OS, device, or recovery identity")
      return value
    except Stage2Error:
      raise
    except (OSError, ValueError, TypeError) as error:
      raise Stage2Error("host journal is missing, corrupt, or unreadable") from error

  def _commit(self, state: dict[str, Any], event: str, phase: Phase | None = None) -> None:
    if phase is not None:
      state["phase"] = phase.value
    state["revision"] += 1
    state["sequence"] += 1
    state["last_event"] = event
    self._validate_state(state)
    payload = _canonical(state)
    self.faults.hit("journal_prewrite")
    descriptor, temporary = tempfile.mkstemp(prefix="stage2.tmp.", dir=self.state_root)
    try:
      with os.fdopen(descriptor, "wb") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
      self.faults.hit("journal_before_replace")
      os.replace(temporary, self._state_path)
      directory = os.open(self.state_root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
      try:
        os.fsync(directory)
      finally:
        os.close(directory)
      self.faults.hit("journal_committed")
    except SimulatedPowerInterruption:
      raise
    except BaseException:
      try:
        os.unlink(temporary)
      except FileNotFoundError:
        pass
      raise

  def _validate_state(self, state: Any) -> None:
    if type(state) is not dict or set(state) != self._STATE_KEYS:
      raise Stage2Error("host journal schema is malformed")
    if state["schema"] != STATE_SCHEMA or state["classification"] != PROTOTYPE_CLASSIFICATION:
      raise Stage2Error("host journal schema or classification mismatch")
    if (type(state["revision"]) is not int or state["revision"] < 0 or
        type(state["sequence"]) is not int or state["sequence"] < 0 or
        type(state["last_gate_sequence"]) is not int or state["last_gate_sequence"] < 0 or
        type(state["last_event"]) is not str or not state["last_event"]):
      raise Stage2Error("host journal counters or event are malformed")
    try:
      phase = Phase(state["phase"])
    except (TypeError, ValueError) as error:
      raise Stage2Error("host journal phase is malformed") from error
    _os_boot(state["os_boot"])
    _device(state["device"])
    recovery = self._recovery_from_dict(state["recovery"])
    if recovery.candidate.source_commit != self.policy.expected_source_commit:
      raise Stage2Error("journal recovery violates source policy")
    attempts, limit = state["attempts_consumed"], state["attempts_limit"]
    if (type(attempts) is not int or type(limit) is not int or attempts < 0 or limit < 0 or
        attempts > limit or limit > MAX_ATTEMPTS):
      raise Stage2Error("journal attempt accounting is malformed")
    used = state["used_attempt_nonces"]
    if (type(used) is not list or len(used) != len(set(used)) or
        any(type(item) is not str or not _HEX64.fullmatch(item) for item in used)):
      raise Stage2Error("journal attempt nonce history is malformed")
    current = state["current_attempt_nonce"]
    if current is not None and (not _HEX64.fullmatch(current) or current not in used):
      raise Stage2Error("journal current attempt nonce is malformed")
    trial_fields = (state["trial"], state["gate"], state["start_request_id"])
    stable = {Phase.RECOVERY_PINNED, Phase.ROLLED_BACK, Phase.PROMOTED_MODEL_ONLY}
    if phase in stable:
      if any(item is not None for item in trial_fields + (
          state["ticket"], current, state["health"], state["health_receipt"])):
        raise Stage2Error("stable journal retained trial authority")
      if attempts != 0 or limit != 0:
        raise Stage2Error("stable journal retained attempt accounting")
      return
    if phase == Phase.HOLD:
      return
    if any(item is None for item in trial_fields):
      raise Stage2Error("active journal lacks trial, gate, or request binding")
    trial = _candidate(state["trial"])
    gate = self._gate_from_dict(state["gate"])
    if (trial.source_commit != self.policy.expected_source_commit or
        gate.os_boot != self.os_boot or gate.device != self.device):
      raise Stage2Error("active journal has a different pinned source, OS, or device")
    if trial != gate.candidate or gate.gate_sequence != state["last_gate_sequence"]:
      raise Stage2Error("active journal gate does not bind the trial")
    if type(state["start_request_id"]) is not str or not _HEX64.fullmatch(state["start_request_id"]):
      raise Stage2Error("active journal start request id is malformed")
    if phase == Phase.PREAUTHORIZING:
      if state["ticket"] is not None or attempts != 0 or limit != self.policy.max_attempts:
        raise Stage2Error("preauthorization journal is inconsistent")
      return
    if state["ticket"] is None or _ticket(state["ticket"]).candidate != trial:
      raise Stage2Error("active journal lacks an exact protected ticket")
    if limit != self.policy.max_attempts:
      raise Stage2Error("active journal retry limit differs from strict policy")
    consumed_phases = {Phase.ATTEMPT_CONSUMED, Phase.PROBATION, Phase.HEALTH_ATTESTED}
    if phase in consumed_phases and (attempts < 1 or current is None):
      raise Stage2Error("consumed phase lacks attempt binding")
    if phase in {Phase.TRIAL_AUTHORIZED, Phase.RETRY_READY} and current is not None:
      raise Stage2Error("unconsumed phase retained a current attempt")
    if phase == Phase.HEALTH_ATTESTED:
      health = self._health_from_dict(state["health"])
      receipt = self._receipt_from_dict(state["health_receipt"])
      if health.candidate != trial or receipt.candidate != trial:
        raise Stage2Error("health state is not bound to the trial")
    elif state["health"] is not None or state["health_receipt"] is not None:
      raise Stage2Error("health material exists outside the attested phase")

  @staticmethod
  def _clear_trial(state: dict[str, Any]) -> None:
    for field in ("trial", "ticket", "gate", "start_request_id", "current_attempt_nonce",
                  "health", "health_receipt"):
      state[field] = None
    state["attempts_consumed"] = 0
    state["attempts_limit"] = 0

  @staticmethod
  def _match_gate(decision: PhysicalGateDecision, expected: GateExpectation) -> None:
    if type(decision) is not PhysicalGateDecision:
      raise Stage2Error("external provider returned a non-exact physical gate decision")
    decision.validate()
    comparable = (
      decision.candidate, decision.os_boot, decision.device, decision.gate_nonce,
      decision.gate_sequence, decision.owner_approval_sha256)
    wanted = (
      expected.candidate, expected.os_boot, expected.device, expected.gate_nonce,
      expected.gate_sequence, expected.owner_approval_sha256)
    if comparable != wanted:
      raise Stage2Error("physical gate decision binding mismatch")

  def authorize_trial(self, candidate: CandidateIdentity, *, gate_envelope: dict[str, Any],
                      intent_envelope: dict[str, Any], gate_nonce: str, gate_sequence: int,
                      owner_approval_sha256: str, start_request_id: str) -> TrialTicket:
    if type(candidate) is not CandidateIdentity:
      raise Stage2Error("application candidate must use CandidateIdentity, never an OS slot type")
    try:
      candidate.validate()
    except Exception as error:
      raise Stage2Error("application candidate identity is malformed") from error
    if (candidate.source_commit != self.policy.expected_source_commit or
        not _HEX64.fullmatch(gate_nonce) or not _HEX64.fullmatch(owner_approval_sha256) or
        not _HEX64.fullmatch(start_request_id) or type(gate_sequence) is not int):
      raise Stage2Error("trial request source, nonce, sequence, or owner binding is malformed")
    with self._locked():
      state = self._load()
      if (state["start_request_id"] == start_request_id and state["trial"] == asdict(candidate) and
          state["ticket"] is not None and Phase(state["phase"]) != Phase.HOLD):
        return _ticket(state["ticket"])
      if Phase(state["phase"]) not in {
          Phase.RECOVERY_PINNED, Phase.ROLLED_BACK, Phase.PROMOTED_MODEL_ONLY}:
        raise Stage2Error("double start or overlapping trial refused")
      if gate_sequence <= state["last_gate_sequence"]:
        raise Stage2Error("stale or replayed physical gate sequence")
      expected = GateExpectation(
        candidate, self.os_boot, self.device, gate_nonce, gate_sequence,
        owner_approval_sha256, self.policy.neutral_can_required)
      try:
        decision = self.decisions.verify_physical_gate(gate_envelope, expected)
      except Exception as error:
        raise Stage2Error("external physical gate authentication failed") from error
      self._match_gate(decision, expected)
      state.update({
        "trial": asdict(candidate), "gate": asdict(decision),
        "start_request_id": start_request_id, "ticket": None,
        "last_gate_sequence": gate_sequence, "attempts_consumed": 0,
        "attempts_limit": self.policy.max_attempts, "current_attempt_nonce": None,
        "health": None, "health_receipt": None,
      })
      self._commit(state, "EXTERNAL_PHYSICAL_GATE_ACCEPTED_PREAUTHORIZING", Phase.PREAUTHORIZING)
      try:
        ticket = self.authority.authorize_trial(
          candidate, self.policy.max_attempts, intent_envelope)
      except Exception as error:
        state = self._load()
        self._commit(state, "PROTECTED_TRIAL_AUTHORIZATION_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected trial authorization failed") from error
      self.faults.hit("after_authority_authorize")
      if type(ticket) is not TrialTicket or ticket.candidate != candidate:
        state = self._load()
        self._commit(state, "PROTECTED_AUTHORITY_RETURNED_INVALID_TICKET_HOLD", Phase.HOLD)
        raise Stage2Error("protected authority returned an invalid ticket")
      state = self._load()
      state["ticket"] = asdict(ticket)
      self._commit(state, "PROTECTED_TRIAL_AUTHORIZED", Phase.TRIAL_AUTHORIZED)
      return ticket

  @staticmethod
  def _launcher_decision(state: dict[str, Any]) -> LauncherDecision:
    gate = Stage2Supervisor._gate_from_dict(state["gate"])
    if gate.physical_gate_passed is not True:
      raise Stage2Error("launcher observation refused without a passed physical gate")
    return LauncherDecision(
      candidate=_candidate(state["trial"]), os_boot=_os_boot(state["os_boot"]),
      attempt_nonce=state["current_attempt_nonce"],
      attempts_consumed=state["attempts_consumed"], attempts_limit=state["attempts_limit"],
      physical_gate_passed=True)

  def consume_attempt_for_observation(self, *, start_request_id: str,
                                      attempt_nonce: str) -> LauncherDecision:
    if not _HEX64.fullmatch(start_request_id) or not _HEX64.fullmatch(attempt_nonce):
      raise Stage2Error("start request id or attempt nonce is malformed")
    with self._locked():
      state = self._load()
      if (Phase(state["phase"]) == Phase.ATTEMPT_CONSUMED and
          state["start_request_id"] == start_request_id and
          state["current_attempt_nonce"] == attempt_nonce):
        # Never return an old journal decision after protected authority revocation.
        try:
          ticket = _ticket(state["ticket"])
          policy_snapshot = self.authority.policy_snapshot()
          active_attempts = self.authority.protected_attempts()
          expected_recovery = self._recovery_from_dict(state["recovery"])
          if (policy_snapshot.generation != ticket.generation or
              policy_snapshot.epoch != ticket.epoch or
              policy_snapshot.recovery != expected_recovery.candidate or
              active_attempts != (state["attempts_consumed"], state["attempts_limit"])):
            raise Stage2Error("protected authority state no longer matches cached trial")
        except Exception as error:
          self._commit(state, "CACHED_GRANT_PROTECTED_AUTHORITY_DIVERGENCE_HOLD", Phase.HOLD)
          raise Stage2Error("protected authority revoked or changed cached trial") from error
        return self._launcher_decision(state)
      if Phase(state["phase"]) not in {Phase.TRIAL_AUTHORIZED, Phase.RETRY_READY}:
        raise Stage2Error("attempt consumption requires an authorized retry-ready trial")
      if state["start_request_id"] != start_request_id:
        raise Stage2Error("stale start request id")
      if attempt_nonce in state["used_attempt_nonces"]:
        raise Stage2Error("stale or replayed attempt nonce")
      trial, ticket = _candidate(state["trial"]), _ticket(state["ticket"])
      try:
        grant = self.authority.consume_attempt(trial, ticket.epoch, ticket)
      except Exception as error:
        self._commit(state, "PROTECTED_ATTEMPT_CONSUMPTION_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected attempt consumption failed") from error
      self.faults.hit("after_authority_consume")
      if type(grant) is not BootGrant:
        self._commit(state, "PROTECTED_AUTHORITY_RETURNED_INVALID_GRANT_HOLD", Phase.HOLD)
        raise Stage2Error("protected authority returned a non-exact boot grant")
      if grant.disposition == "recovery":
        recovery = self._recovery_from_dict(state["recovery"])
        if grant.candidate != recovery.candidate:
          self._commit(state, "UNAPPROVED_RECOVERY_IDENTITY_HOLD", Phase.HOLD)
          raise Stage2Error("authority selected a recovery identity without exact approval")
        self._cancel_to_recovery_locked(state, "ATTEMPT_BUDGET_EXHAUSTED_ROLLBACK")
        raise Stage2Error("attempt budget exhausted; immutable recovery selected")
      if (grant.disposition != "trial" or grant.candidate != trial or
          grant.attempts_limit != self.policy.max_attempts or
          grant.attempts_consumed != state["attempts_consumed"] + 1):
        self._commit(state, "PROTECTED_AUTHORITY_RETURNED_INVALID_GRANT_HOLD", Phase.HOLD)
        raise Stage2Error("protected boot grant binding or counter is invalid")
      state["attempts_consumed"] = grant.attempts_consumed
      state["current_attempt_nonce"] = attempt_nonce
      state["used_attempt_nonces"].append(attempt_nonce)
      self._commit(state, "ATTEMPT_DURABLY_CONSUMED_BEFORE_OBSERVATION",
                   Phase.ATTEMPT_CONSUMED)
      return self._launcher_decision(state)

  def observe_startup(self, passed: bool) -> None:
    if type(passed) is not bool:
      raise Stage2Error("startup result must be an exact boolean")
    with self._locked():
      state = self._load()
      if Phase(state["phase"]) != Phase.ATTEMPT_CONSUMED:
        raise Stage2Error("startup observation requires a consumed attempt")
      if passed:
        self._commit(state, "NEUTRAL_CAN_PROBATION_AWAITING_AUTHENTICATED_HEALTH",
                     Phase.PROBATION)
      elif state["attempts_consumed"] >= state["attempts_limit"]:
        self._cancel_to_recovery_locked(state, "MAXIMUM_ATTEMPTS_FAILED_ROLLBACK")
      else:
        state["current_attempt_nonce"] = None
        self._commit(state, "STARTUP_FAILED_BOUNDED_RETRY_READY", Phase.RETRY_READY)

  @staticmethod
  def _match_health(decision: HealthDecision, expected: HealthExpectation) -> None:
    if type(decision) is not HealthDecision:
      raise Stage2Error("external provider returned a non-exact health decision")
    decision.validate()
    comparable = (
      decision.candidate, decision.os_boot, decision.device, decision.gate_nonce,
      decision.gate_sequence, decision.attempt_nonce, decision.attempts_consumed,
      decision.owner_approval_sha256)
    wanted = (
      expected.candidate, expected.os_boot, expected.device, expected.gate_nonce,
      expected.gate_sequence, expected.attempt_nonce, expected.attempts_consumed,
      expected.owner_approval_sha256)
    if comparable != wanted:
      raise Stage2Error("authenticated health decision binding mismatch")

  def attest_health(self, *, decision_envelope: dict[str, Any],
                    authority_health_envelope: dict[str, Any]) -> HealthReceipt:
    with self._locked():
      state = self._load()
      if Phase(state["phase"]) != Phase.PROBATION:
        raise Stage2Error("health is accepted only after neutral-CAN probation")
      trial, ticket = _candidate(state["trial"]), _ticket(state["ticket"])
      gate = self._gate_from_dict(state["gate"])
      expected = HealthExpectation(
        trial, self.os_boot, self.device, gate.gate_nonce, gate.gate_sequence,
        state["current_attempt_nonce"], state["attempts_consumed"],
        gate.owner_approval_sha256)
      try:
        decision = self.decisions.verify_health(decision_envelope, expected)
      except Exception as error:
        self._commit(state, "EXTERNAL_HEALTH_AUTHENTICATION_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("external health authentication failed") from error
      try:
        self._match_health(decision, expected)
      except Stage2Error:
        self._commit(state, "EXTERNAL_HEALTH_BINDING_FAILED_HOLD", Phase.HOLD)
        raise
      # Both attestations must describe the identical startup measurement.
      # The protected authority subsequently verifies its own signature; this
      # comparison does not treat an unsigned envelope as authenticated.
      protected_payload = (authority_health_envelope.get("payload")
                           if type(authority_health_envelope) is dict else None)
      if (type(protected_payload) is not dict or
          protected_payload.get("boot_measurement") != decision.measurement_sha256):
        self._commit(state, "INDEPENDENT_AND_PROTECTED_HEALTH_MEASUREMENT_DISAGREE_HOLD",
                     Phase.HOLD)
        raise Stage2Error("independent and protected health measurements disagree")
      try:
        receipt = self.authority.attest_health(
          trial, ticket.epoch, ticket, authority_health_envelope)
      except Exception as error:
        self._commit(state, "PROTECTED_HEALTH_AUTHENTICATION_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected health authority rejected the receipt") from error
      self.faults.hit("after_authority_health")
      if (type(receipt) is not HealthReceipt or receipt.candidate != trial or
          receipt.ticket_id != ticket.ticket_id or receipt.epoch != ticket.epoch):
        self._commit(state, "PROTECTED_HEALTH_RECEIPT_BINDING_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected health receipt binding mismatch")
      state["health"] = asdict(decision)
      state["health_receipt"] = asdict(receipt)
      self._commit(state, "AUTHENTICATED_HEALTH_RECORDED_PROMOTION_NOT_IMPLIED",
                   Phase.HEALTH_ATTESTED)
      return receipt

  def promote_model_only(self, promotion_envelope: dict[str, Any]) -> PolicySnapshot:
    """Promote only after a second external immutable-recovery approval."""
    with self._locked():
      state = self._load()
      if Phase(state["phase"]) != Phase.HEALTH_ATTESTED:
        raise Stage2Error("promotion requires authenticated health")
      health = self._health_from_dict(state["health"])
      receipt = self._receipt_from_dict(state["health_receipt"])
      old_recovery = self._recovery_from_dict(state["recovery"])
      try:
        approval = self.decisions.verify_promotion(
          promotion_envelope, PromotionExpectation(health, receipt, old_recovery))
      except Exception as error:
        self._commit(state, "EXTERNAL_PROMOTION_APPROVAL_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("external promotion approval failed") from error
      expected = RecoveryExpectation(
        health.candidate, self.os_boot.slot, self.os_boot.rootfs_measurement, self.device)
      self._validate_recovery(approval, expected)
      if approval.approval_sequence <= old_recovery.approval_sequence:
        self._commit(state, "STALE_PROMOTION_APPROVAL_HOLD", Phase.HOLD)
        raise Stage2Error("promotion approval sequence is not monotonic")
      try:
        snapshot = self.authority.promote_recovery(receipt)
      except Exception as error:
        self._commit(state, "PROTECTED_PROMOTION_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected promotion failed") from error
      if (snapshot.recovery != approval.candidate or
          snapshot.minimum_release_sequence < approval.candidate.release_sequence):
        self._commit(state, "PROTECTED_PROMOTION_BINDING_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected promotion result does not match approval")
      state["recovery"] = asdict(approval)
      self._clear_trial(state)
      # Match the new authenticated recovery pin before writing its journal.
      self._trusted_recovery = approval
      self._commit(state, "PROMOTED_MODEL_ONLY_NONDEPLOYABLE", Phase.PROMOTED_MODEL_ONLY)
      return snapshot

  def _cancel_to_recovery_locked(self, state: dict[str, Any], event: str) -> None:
    recovery = self._recovery_from_dict(state["recovery"])
    trial, ticket = _candidate(state["trial"]), _ticket(state["ticket"])
    try:
      snapshot = self.authority.cancel_trial(trial, ticket.epoch, ticket)
    except Exception as error:
      try:
        observed = self.authority.policy_snapshot()
      except Exception:
        self._commit(state, "RECOVERY_RECONCILIATION_FAILED_HOLD", Phase.HOLD)
        raise Stage2Error("protected cancellation and reconciliation failed") from error
      if observed.recovery != recovery.candidate or observed.epoch <= ticket.epoch:
        self._commit(state, "AMBIGUOUS_PROTECTED_CANCELLATION_HOLD", Phase.HOLD)
        raise Stage2Error("protected cancellation outcome is ambiguous") from error
      snapshot = observed
    if snapshot.recovery != recovery.candidate:
      self._commit(state, "UNAPPROVED_ROLLBACK_TARGET_HOLD", Phase.HOLD)
      raise Stage2Error("rollback target is not the separately approved immutable recovery")
    self._clear_trial(state)
    self._commit(state, event, Phase.ROLLED_BACK)

  def recover_after_power_interruption(self, new_os_boot: OsBootIdentity) -> None:
    """Conservatively cancel an in-flight trial; never infer startup or health."""
    new_os_boot.validate()
    with self._locked():
      state = self._load()
      old = _os_boot(state["os_boot"])
      if (new_os_boot.boot_sequence <= old.boot_sequence or
          new_os_boot.boot_nonce == old.boot_nonce):
        raise Stage2Error("power recovery requires a fresh monotonic OS boot identity")
      if (new_os_boot.slot != old.slot or
          new_os_boot.rootfs_measurement != old.rootfs_measurement or
          new_os_boot.agnos_version != old.agnos_version):
        self._commit(state, "OS_SLOT_OR_ROOT_CHANGED_WITHOUT_NEW_RECOVERY_APPROVAL_HOLD", Phase.HOLD)
        raise Stage2Error("OS A/B or rootfs change cannot be treated as an app-slot restart")
      phase = Phase(state["phase"])
      if phase == Phase.HOLD:
        raise Stage2Error("HOLD requires external protected-state reconciliation")
      state["os_boot"] = asdict(new_os_boot)
      self.os_boot = new_os_boot
      if phase == Phase.PREAUTHORIZING:
        self._commit(state, "POWER_LOSS_WITHOUT_DURABLE_TICKET_HOLD", Phase.HOLD)
        raise Stage2Error("ambiguous preauthorization cannot be recovered automatically")
      if phase in {Phase.TRIAL_AUTHORIZED, Phase.ATTEMPT_CONSUMED, Phase.PROBATION,
                   Phase.RETRY_READY, Phase.HEALTH_ATTESTED}:
        self._cancel_to_recovery_locked(state, "POWER_INTERRUPTION_ROLLBACK")
      else:
        self._commit(state, "POWER_INTERRUPTION_RECOVERY_STABLE", phase)

  def snapshot(self) -> dict[str, Any]:
    """Diagnostics only; this dictionary is never an authorization source."""
    with self._locked():
      state = self._load()
      return {
        "schema": STATE_SCHEMA,
        "classification": PROTOTYPE_CLASSIFICATION,
        "phase": state["phase"], "sequence": state["sequence"],
        "last_event": state["last_event"], "os_slot": state["os_boot"]["slot"],
        "app_trial": state["trial"], "recovery": state["recovery"]["candidate"],
        "attempts_consumed": state["attempts_consumed"],
        "attempts_limit": state["attempts_limit"],
        "physical_gate_passed": state["gate"] is not None and
          state["gate"].get("physical_gate_passed") is True,
        "health_authenticated": state["health_receipt"] is not None,
        "process_started": False, "installation_authorized": False,
        "boot_operations_authorized": False, "panda_or_can_authorized": False,
        "production_approved": False,
      }


def source_sha256() -> str:
  """Audit helper for evidence binding; performs no authorization."""
  return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

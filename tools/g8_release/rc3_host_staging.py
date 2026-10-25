#!/usr/bin/env python3
"""Disposable inactive-application-slot state-machine simulation for RC3.

This is a host-only dry-run model.  It creates both simulated application slots
inside the host temporary-filesystem tree, never executes a launcher, and has
no installation override, device access, AGNOS, abctl, Panda, CAN, SSH,
flashing, reboot, mount, or privilege operations.  A caller may select a path
beneath the host temp directory to test process-death/reopen behavior; that
path policy is not a platform-enforced device security boundary.
"""
from __future__ import annotations

import json
import os
import secrets
import stat
import tempfile
from pathlib import Path
from typing import Any

from rc3_external_trust import ExternalTrustVerifier, TrustError, canonical_json
from rc3_package_planner import FROZEN_COMMIT, FROZEN_TREE, inventory_sha256

STATE_SCHEMA = "G8_F12_RC3_HOST_APP_SLOT_STATE_V1"
SLOT_SCHEMA = "G8_F12_RC3_HOST_APP_SLOT_IDENTITY_V1"
STATE_KEYS = {
  "schema", "active_slot", "recovery_slot", "candidate_slot",
  "candidate_inventory_sha256", "phase", "attempt", "trial_nonce",
  "startup_passed", "probation_complete", "boot_success",
  "installation_authorized", "device_operations_authorized", "last_event",
}
PHASE_EVENTS = {
  "IDLE": {"SIMULATOR_INITIALIZED", "INTERRUPTED_STAGING_DISCARDED"},
  "STAGED": {"INERT_CANDIDATE_STAGED"},
  "TRIAL_PENDING": {"TRIAL_ATTEMPT_CONSUMED_BEFORE_STARTUP"},
  "PROBATION": {"STARTUP_PASSED_AWAITING_SIGNED_HEALTH"},
  "ROLLED_BACK": {"FAILED_STARTUP_ROLLBACK", "POWER_INTERRUPTION_OR_RESTART_ROLLBACK"},
  "PROMOTED_HOST_SIMULATION_ONLY": {"SIGNED_HOST_HEALTH_ACCEPTED"},
}


class SimulationError(RuntimeError):
  """A host-only state transition was rejected."""


class SimulatedPowerLoss(BaseException):
  """Intentional host-process interruption after a persisted boundary."""


class HostOnlySlotSimulation:
  """Two disposable app directories with fail-safe trial/recovery ordering."""

  def __init__(self, source_root: Path, plan: dict[str, Any], *,
               policy_path: Path, keyring_path: Path,
               simulation_root: Path | None = None, resume: bool = False):
    self.source_root = source_root.resolve(strict=True)
    self.plan = plan
    self._validate_plan()
    self._verifier = ExternalTrustVerifier(self.source_root, policy_path, keyring_path)
    self._temporary: tempfile.TemporaryDirectory[str] | None = None
    temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    if simulation_root is None:
      if resume:
        raise SimulationError("resume requires an explicit persisted simulation root")
      self._temporary = tempfile.TemporaryDirectory(prefix="g8-rc3-host-app-slots-")
      self.root = Path(self._temporary.name).resolve(strict=True)
    else:
      requested = Path(simulation_root)
      if not requested.is_absolute():
        raise SimulationError("explicit simulation root must be absolute")
      try:
        parent = requested.parent.resolve(strict=True)
      except OSError as error:
        raise SimulationError("simulation-root parent is unavailable") from error
      if not parent.is_relative_to(temporary_root):
        raise SimulationError("simulation root must remain beneath the host temporary directory")
      if requested.exists() or requested.is_symlink():
        try:
          info = os.lstat(requested)
        except OSError as error:
          raise SimulationError("persisted simulation root is unavailable") from error
        if not resume or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
          raise SimulationError("existing simulation root is only accepted for explicit resume")
        self.root = requested.resolve(strict=True)
      else:
        if resume:
          raise SimulationError("persisted simulation root is missing")
        try:
          requested.mkdir(mode=0o700)
        except OSError as error:
          raise SimulationError("cannot create persisted simulation root") from error
        self.root = requested.resolve(strict=True)
    if not self.root.is_relative_to(temporary_root):
      if self._temporary is not None:
        self._temporary.cleanup()
      raise SimulationError("host simulation root escaped the system temporary directory")
    self.slots = self.root / "application_slots"
    self.state_path = self.root / "state.json"
    if resume:
      self._validate_reopened_storage()
      return
    self.slots.mkdir(mode=0o700)
    (self.slots / "app_a").mkdir(mode=0o700)
    (self.slots / "app_b").mkdir(mode=0o700)
    self._write_slot("app_a", "SIMULATED_RECOVERY_BASELINE", "0" * 64)
    self._write_state({
      "schema": STATE_SCHEMA,
      "active_slot": "app_a",
      "recovery_slot": "app_a",
      "candidate_slot": "app_b",
      "candidate_inventory_sha256": self.plan["inventory_sha256"],
      "phase": "IDLE",
      "attempt": 0,
      "trial_nonce": None,
      "startup_passed": False,
      "probation_complete": False,
      "boot_success": False,
      "installation_authorized": False,
      "device_operations_authorized": False,
      "last_event": "SIMULATOR_INITIALIZED",
    })

  def __enter__(self) -> "HostOnlySlotSimulation":
    return self

  def __exit__(self, *_: Any) -> None:
    self.close()

  def close(self) -> None:
    if self._temporary is not None:
      self._temporary.cleanup()

  def _validate_plan(self) -> None:
    if type(self.plan) is not dict:
      raise SimulationError("package plan must be an object")
    if (self.plan.get("schema") != "G8_F12_RC3_DEVELOPMENT_PACKAGE_PLAN_V1" or
        self.plan.get("classification") != "UNSIGNED DEVELOPMENT PACKAGE" or
        self.plan.get("package_manifest_signed") is not False):
      raise SimulationError("unsupported or overstated development package plan")
    inventory = self.plan.get("inventory")
    if type(inventory) is not dict or inventory_sha256(inventory) != self.plan.get("inventory_sha256"):
      raise SimulationError("package inventory digest mismatch")
    if (inventory.get("frozen_git_commit") != FROZEN_COMMIT or
        inventory.get("frozen_git_tree") != FROZEN_TREE or
        inventory.get("launcher", {}).get("exit_78_guard_verified") is not True):
      raise SimulationError("package plan is not pinned to guarded frozen RC3")
    qualification = self.plan.get("qualification")
    if (type(qualification) is not dict or qualification.get("content_integrity_verified") is not True or
        qualification.get("production_approved") is not False or
        qualification.get("installation_authorized") is not False or
        qualification.get("device_operations_authorized") is not False):
      raise SimulationError("package plan violates host-only HOLD invariants")

  @staticmethod
  def _slot_document(label: str, kind: str, digest: str) -> dict[str, Any]:
    return {"schema": SLOT_SCHEMA, "slot": label, "kind": kind,
            "inventory_sha256": digest, "executable": False}

  def _write_slot(self, label: str, kind: str, digest: str) -> None:
    path = self.slots / label / "identity.json"
    if path.exists() or path.is_symlink():
      raise SimulationError("simulated slot identity already exists")
    self._write_new(path, canonical_json(self._slot_document(label, kind, digest)))

  @staticmethod
  def _write_new(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
      flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
      stream.write(payload)
      stream.flush()
      os.fsync(stream.fileno())

  def _write_state(self, state: dict[str, Any]) -> None:
    temporary = self.root / ".state.next"
    if temporary.exists() or temporary.is_symlink():
      raise SimulationError("unexpected temporary state file")
    self._write_new(temporary, canonical_json(state))
    os.replace(temporary, self.state_path)
    directory = os.open(self.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
      os.fsync(directory)
    finally:
      os.close(directory)

  @staticmethod
  def _read_canonical_object(path: Path, label: str) -> dict[str, Any]:
    try:
      info = os.lstat(path)
      if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise SimulationError(f"{label} is not a regular non-symlink file")
      raw = path.read_bytes()
      value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as error:
      raise SimulationError(f"{label} is unreadable") from error
    if type(value) is not dict or canonical_json(value) != raw:
      raise SimulationError(f"{label} is malformed or noncanonical")
    return value

  def _validate_slot_identity(self, label: str, expected_kind: str,
                              expected_digest: str) -> None:
    document = self._read_canonical_object(self.slots / label / "identity.json",
                                           f"simulated {label} identity")
    if document != self._slot_document(label, expected_kind, expected_digest):
      raise SimulationError(f"simulated {label} identity mismatch")

  def _validate_reopened_storage(self) -> None:
    for path in (self.slots, self.slots / "app_a", self.slots / "app_b"):
      try:
        info = os.lstat(path)
      except OSError as error:
        raise SimulationError("persisted simulation storage is incomplete") from error
      if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise SimulationError("persisted simulation storage contains an unsafe directory")
    state = self.state()
    self._validate_slot_identity("app_a", "SIMULATED_RECOVERY_BASELINE", "0" * 64)
    candidate = self.slots / "app_b" / "identity.json"
    if state["phase"] == "IDLE":
      if candidate.exists() or candidate.is_symlink():
        # This exact state is the intentional crash boundary during staging.
        self._validate_slot_identity(
          "app_b", "UNSIGNED_DEVELOPMENT_CANDIDATE", self.plan["inventory_sha256"])
    else:
      self._validate_slot_identity(
        "app_b", "UNSIGNED_DEVELOPMENT_CANDIDATE", self.plan["inventory_sha256"])

  def _validate_state_invariants(self, state: dict[str, Any]) -> None:
    if set(state) != STATE_KEYS or state.get("schema") != STATE_SCHEMA:
      raise SimulationError("simulated state schema is invalid")
    phase = state.get("phase")
    if type(phase) is not str or phase not in PHASE_EVENTS:
      raise SimulationError("simulated state phase is invalid")
    if state.get("last_event") not in PHASE_EVENTS[phase]:
      raise SimulationError("simulated state event/phase combination is invalid")
    if (state.get("active_slot") not in {"app_a", "app_b"} or
        state.get("recovery_slot") not in {"app_a", "app_b"} or
        state.get("candidate_slot") != "app_b"):
      raise SimulationError("simulated state slot selection is invalid")
    if state.get("candidate_inventory_sha256") != self.plan["inventory_sha256"]:
      raise SimulationError("simulated state candidate inventory is invalid")
    attempt = state.get("attempt")
    if type(attempt) is not int or not 0 <= attempt <= 3:
      raise SimulationError("simulated state attempt counter is invalid")
    for field in ("startup_passed", "probation_complete", "boot_success",
                  "installation_authorized", "device_operations_authorized"):
      if type(state.get(field)) is not bool:
        raise SimulationError(f"simulated state {field} is not an exact boolean")
    if state["installation_authorized"] or state["device_operations_authorized"]:
      raise SimulationError("simulated state violates immutable host-only denial")

    nonce = state.get("trial_nonce")
    before_trial = phase in {"IDLE", "STAGED"}
    if before_trial:
      if attempt != 0 or nonce is not None:
        raise SimulationError("pre-trial state has consumed-attempt data")
    elif (attempt < 1 or type(nonce) is not str or len(nonce) != 64 or
          any(character not in "0123456789abcdef" for character in nonce)):
      raise SimulationError("trial state has invalid persisted nonce or attempt")

    expected = {
      "IDLE": ("app_a", "app_a", False, False, False),
      "STAGED": ("app_a", "app_a", False, False, False),
      "TRIAL_PENDING": ("app_b", "app_a", False, False, False),
      "PROBATION": ("app_b", "app_a", True, False, False),
      "ROLLED_BACK": ("app_a", "app_a", False, False, False),
      "PROMOTED_HOST_SIMULATION_ONLY": ("app_b", "app_b", True, True, True),
    }[phase]
    observed = (state["active_slot"], state["recovery_slot"], state["startup_passed"],
                state["probation_complete"], state["boot_success"])
    if observed != expected:
      raise SimulationError("simulated state violates phase/slot/health invariants")

  def state(self) -> dict[str, Any]:
    state = self._read_canonical_object(self.state_path, "simulated state")
    self._validate_state_invariants(state)
    return state

  def _policy(self) -> dict[str, Any]:
    try:
      return self._verifier.verify_policy(
        frozen_commit=FROZEN_COMMIT, frozen_tree=FROZEN_TREE,
        inventory_sha256=self.plan["inventory_sha256"])
    except TrustError as error:
      raise SimulationError(f"caller-supplied host policy rejected: {error}") from error

  def stage_candidate(self, *, power_loss_after_write: bool = False) -> dict[str, Any]:
    """Write inert identity metadata only; there is no payload copy or execution."""
    state = self.state()
    if state["phase"] != "IDLE":
      raise SimulationError("candidate may only be staged from IDLE")
    self._write_slot("app_b", "UNSIGNED_DEVELOPMENT_CANDIDATE", self.plan["inventory_sha256"])
    if power_loss_after_write:
      raise SimulatedPowerLoss("after_candidate_identity_write")
    state["phase"] = "STAGED"
    state["last_event"] = "INERT_CANDIDATE_STAGED"
    self._write_state(state)
    return self.state()

  def begin_trial(self, *, power_loss_after_persist: bool = False) -> dict[str, Any]:
    policy = self._policy()  # Rechecked immediately before trial authorization.
    state = self.state()
    if state["phase"] != "STAGED":
      raise SimulationError("trial requires a completely staged candidate")
    attempt = state["attempt"] + 1
    if attempt > policy["max_trial_attempts"]:
      raise SimulationError("external policy trial-attempt limit exhausted")
    state.update({
      "active_slot": "app_b",
      "phase": "TRIAL_PENDING",
      "attempt": attempt,
      "trial_nonce": secrets.token_hex(32),
      "startup_passed": False,
      "probation_complete": False,
      "boot_success": False,
      "last_event": "TRIAL_ATTEMPT_CONSUMED_BEFORE_STARTUP",
    })
    self._write_state(state)
    if power_loss_after_persist:
      raise SimulatedPowerLoss("after_trial_attempt_persist")
    return self.state()

  def observe_startup(self, passed: bool, *, power_loss_after_persist: bool = False) -> dict[str, Any]:
    if type(passed) is not bool:
      raise SimulationError("startup result must be an exact boolean")
    state = self.state()
    if state["phase"] != "TRIAL_PENDING":
      raise SimulationError("startup observation requires a pending trial")
    if passed:
      state["phase"] = "PROBATION"
      state["startup_passed"] = True
      state["last_event"] = "STARTUP_PASSED_AWAITING_SIGNED_HEALTH"
    else:
      state = self._rollback_state(state, "FAILED_STARTUP_ROLLBACK")
    self._write_state(state)
    if power_loss_after_persist:
      raise SimulatedPowerLoss("after_startup_observation_persist")
    return self.state()

  @staticmethod
  def _rollback_state(state: dict[str, Any], event: str) -> dict[str, Any]:
    state.update({
      "active_slot": state["recovery_slot"],
      "phase": "ROLLED_BACK",
      "startup_passed": False,
      "probation_complete": False,
      "boot_success": False,
      "last_event": event,
    })
    return state

  def recover_after_restart(self) -> dict[str, Any]:
    state = self.state()
    if state["phase"] in {"TRIAL_PENDING", "PROBATION"}:
      state = self._rollback_state(state, "POWER_INTERRUPTION_OR_RESTART_ROLLBACK")
      self._write_state(state)
    elif state["phase"] == "IDLE" and (self.slots / "app_b" / "identity.json").exists():
      # Interrupted staging never changes active state; discard inert metadata.
      (self.slots / "app_b" / "identity.json").unlink()
      state["last_event"] = "INTERRUPTED_STAGING_DISCARDED"
      self._write_state(state)
    return self.state()

  def accept_health(self, health_path: Path, *, power_loss_before_promotion: bool = False) -> dict[str, Any]:
    policy = self._policy()  # Rechecked immediately before health acceptance.
    state = self.state()
    if state["phase"] != "PROBATION" or state["startup_passed"] is not True:
      raise SimulationError("signed health is only accepted after startup probation begins")
    try:
      self._verifier.verify_health(
        health_path, inventory_sha256=self.plan["inventory_sha256"],
        policy_id=policy["policy_id"], trial_nonce=state["trial_nonce"], attempt=state["attempt"])
    except TrustError as error:
      raise SimulationError(f"caller-supplied health receipt rejected: {error}") from error
    if power_loss_before_promotion:
      raise SimulatedPowerLoss("after_health_verification_before_promotion")
    state.update({
      "recovery_slot": "app_b",
      "phase": "PROMOTED_HOST_SIMULATION_ONLY",
      "probation_complete": True,
      "boot_success": True,
      "last_event": "SIGNED_HOST_HEALTH_ACCEPTED",
    })
    self._write_state(state)
    return self.state()

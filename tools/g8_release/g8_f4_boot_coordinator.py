#!/usr/bin/env python3
"""NON-DEPLOYABLE host-only F4 boot coordination reference.

This coordinator never starts a process.  It asks an external authority for a
decision, deep-verifies the exact sealed F1 slot against the authority's policy,
repairs the mutable ``live`` link to that approved slot, verifies again, and
returns a descriptive launcher selection.  Hardened mode has no F1 fallback.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any

import g8_manifest as gm
import g8_slot_supervisor as sv
from g8_protected_authority import (
  AuthorityError,
  CandidateIdentity,
  HealthReceipt,
  PolicySnapshot,
  ProtectedAuthority,
  TrialTicket,
)


class CoordinatorError(Exception):
  """Fail-closed coordinator error; no launcher has been authorized."""


class CoordinatorCrash(BaseException):
  """Host-only process-death injection before an external call."""


@dataclass(frozen=True)
class LaunchSelection:
  disposition: str
  candidate: CandidateIdentity
  launcher_path: str
  attempts_consumed: int
  attempts_limit: int
  executed: bool = False


class CoordinatorFaults:
  def __init__(self, crash_at: str | None = None):
    self.crash_at = crash_at
    self.points_seen: list[str] = []

  def hit(self, point: str) -> None:
    self.points_seen.append(point)
    if point == self.crash_at:
      raise CoordinatorCrash(point)


class BootCoordinator:
  def __init__(self, app_root: str | os.PathLike[str], authority: ProtectedAuthority | None,
               *, hardened: bool = True, faults: CoordinatorFaults | None = None):
    self.app_root = os.path.abspath(os.fspath(app_root))
    self.authority = authority
    self.hardened = hardened
    self.faults = faults or CoordinatorFaults()
    if not hardened:
      raise CoordinatorError("F4 reference supports hardened fail-closed mode only")
    if authority is None:
      raise CoordinatorError("hardened F4 requires an external protected authority")
    self._require_separate_trust_domain()

  def _require_separate_trust_domain(self) -> None:
    assert self.authority is not None
    app = os.path.realpath(self.app_root)
    protected = os.path.realpath(self.authority.trust_domain_path)
    try:
      shared = os.path.commonpath((app, protected))
    except ValueError as error:
      raise CoordinatorError("cannot establish authority trust-domain separation") from error
    if shared == app:
      raise CoordinatorError("mock protected authority must live outside the mutable application tree")

  @staticmethod
  def _supervisor(app_root: str, policy: PolicySnapshot, *, trial: str | None = None,
                  health: str | None = None) -> sv.Supervisor:
    trust = {"trusted_keys": [dict(item) for item in policy.signing_keys]}
    return sv.Supervisor(
      app_root, trust=trust, expected_commit=policy.expected_commit,
      minimum_release_sequence=policy.minimum_release_sequence,
      approved_recovery_slot=policy.recovery.slot_id,
      approved_trial_slot=trial, approved_health_slot=health,
    )

  def _identity(self, slot_id: str, policy: PolicySnapshot) -> CandidateIdentity:
    supervisor = self._supervisor(self.app_root, policy)
    try:
      manifest = supervisor.verify_slot(slot_id, deep=True)
      manifest_path = os.path.join(supervisor.slot_dir(slot_id), sv.MANIFEST_NAME)
      signature_path = os.path.join(supervisor.slot_dir(slot_id), sv.SIGNATURE_NAME)
      manifest_bytes = supervisor._read_regular(manifest_path)
      signature = json.loads(supervisor._read_regular(signature_path))
      identity = CandidateIdentity(
        slot_id=slot_id,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        source_commit=manifest["source_commit"],
        release_sequence=manifest["release_sequence"],
        signing_key_id=signature["key_id"],
      )
      identity.validate()
      if gm.canonical(manifest) != manifest_bytes:
        raise CoordinatorError("slot manifest is not canonical")
      return identity
    except (sv.SlotInvalid, AuthorityError, OSError, KeyError, TypeError, ValueError) as error:
      raise CoordinatorError(f"slot identity/deep verification failed: {error}") from error

  def inspect_candidate(self, slot_id: str) -> CandidateIdentity:
    assert self.authority is not None
    policy = self.authority.policy_snapshot()
    return self._identity(slot_id, policy)

  def authorize_trial(self, slot_id: str, max_attempts: int,
                      intent_envelope: dict[str, Any]) -> TrialTicket:
    assert self.authority is not None
    policy = self.authority.policy_snapshot()
    candidate = self._identity(slot_id, policy)
    return self.authority.authorize_trial(candidate, max_attempts, intent_envelope)

  def _select(self, disposition: str, candidate: CandidateIdentity,
              attempts_consumed: int, attempts_limit: int) -> LaunchSelection:
    assert self.authority is not None
    policy = self.authority.policy_snapshot()
    if disposition == "recovery" and candidate != policy.recovery:
      raise CoordinatorError("recovery grant is stale or not the current protected recovery")
    if disposition not in ("trial", "recovery"):
      raise CoordinatorError("authority returned an unknown boot disposition")
    actual = self._identity(candidate.slot_id, policy)
    if actual != candidate:
      raise CoordinatorError("authority choice does not equal the deep-verified slot identity")
    supervisor = self._supervisor(self.app_root, policy, trial=candidate.slot_id)
    try:
      if supervisor.live_slot() != candidate.slot_id:
        supervisor._switch_live(candidate.slot_id)
      if supervisor.live_slot() != candidate.slot_id or self._identity(candidate.slot_id, policy) != candidate:
        raise CoordinatorError("live link or slot identity changed during selection")
      launcher = os.path.join(supervisor.slot_dir(candidate.slot_id), sv.LAUNCHER)
      launcher_real = os.path.realpath(launcher)
      slot_real = os.path.realpath(supervisor.slot_dir(candidate.slot_id))
      if os.path.commonpath((launcher_real, slot_real)) != slot_real or not os.path.isfile(launcher):
        raise CoordinatorError("launcher path escaped the authorized slot")
      return LaunchSelection(disposition, candidate, launcher, attempts_consumed, attempts_limit, False)
    except sv.SlotInvalid as error:
      raise CoordinatorError(f"cannot establish approved live slot: {error}") from error

  def prepare_recovery(self) -> LaunchSelection:
    assert self.authority is not None
    policy = self.authority.policy_snapshot()
    return self._select("recovery", policy.recovery, 0, 0)

  def prepare_trial_boot(self, ticket: TrialTicket) -> LaunchSelection:
    """Consume externally first; a later crash or verify failure cannot refund."""
    assert self.authority is not None
    self.faults.hit("prepare_before_consume")
    try:
      grant = self.authority.consume_attempt(ticket.candidate, ticket.epoch, ticket)
    except AuthorityError as error:
      raise CoordinatorError(f"protected attempt authorization failed: {error}") from error
    self.faults.hit("prepare_after_consume")
    return self._select(grant.disposition, grant.candidate, grant.attempts_consumed, grant.attempts_limit)

  def attest_and_promote(self, ticket: TrialTicket, attestation_envelope: dict[str, Any]) -> PolicySnapshot:
    """Deep-verify, record authenticated health, then atomically promote."""
    assert self.authority is not None
    policy = self.authority.policy_snapshot()
    actual = self._identity(ticket.candidate.slot_id, policy)
    if actual != ticket.candidate:
      raise CoordinatorError("trial changed before health promotion")
    try:
      receipt = self.authority.attest_health(ticket.candidate, ticket.epoch, ticket, attestation_envelope)
      self.faults.hit("promotion_after_attest")
      if self._identity(ticket.candidate.slot_id, self.authority.policy_snapshot()) != ticket.candidate:
        raise CoordinatorError("trial changed after health attestation")
      return self.authority.promote_recovery(receipt)
    except AuthorityError as error:
      raise CoordinatorError(f"protected health promotion failed: {error}") from error

  def promote_with_receipt(self, receipt: HealthReceipt) -> PolicySnapshot:
    """Exposed for process-restart completion; the authority validates receipt."""
    assert self.authority is not None
    if self._identity(receipt.candidate.slot_id, self.authority.policy_snapshot()) != receipt.candidate:
      raise CoordinatorError("promotion receipt candidate is no longer deep-verified")
    try:
      return self.authority.promote_recovery(receipt)
    except AuthorityError as error:
      raise CoordinatorError(f"protected promotion receipt rejected: {error}") from error

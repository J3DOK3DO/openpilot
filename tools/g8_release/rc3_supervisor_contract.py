#!/usr/bin/env python3
"""NON-DEPLOYABLE OS-resident RC3 supervisor contract and state model.

This module emits no systemd unit, starts no process, selects no executable,
and has no install, boot-slot, Panda, CAN, network, mount, or device interface.
It is a host-test design model around the existing ProtectedAuthority protocol
from ``g8_protected_authority``.  Ordinary files used by that module's mock are
not secure hardware and cannot qualify a device.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from g8_protected_authority import (
  BootGrant,
  CandidateIdentity,
  HealthReceipt,
  PolicySnapshot,
  ProtectedAuthority,
  TrialTicket,
)


SERVICE_CONTRACT_SCHEMA = "G8_F12_RC3_OS_SUPERVISOR_DESIGN_CONTRACT_V1"
MODEL_SCHEMA = "G8_F12_RC3_NON_DEPLOYABLE_SUPERVISOR_MODEL_V1"

# This is data for design review, deliberately not valid unit-file text.
SYSTEMD_DESIGN_CONTRACT: dict[str, Any] = {
  "schema": SERVICE_CONTRACT_SCHEMA,
  "classification": "NON_DEPLOYABLE_DESIGN_ONLY",
  "unit_file_emitted": False,
  "executable_implemented": False,
  "installation_authorized": False,
  "boot_operations_authorized": False,
  "actuation_authorized": False,
  "required_placement": {
    "unit": "/usr/lib/systemd/system/",
    "supervisor": "/usr/libexec/",
    "protected_state": "HARDWARE_BACKED_ROLLBACK_RESISTANT_AUTHORITY",
    "forbidden_writable_prefix": "/data/openpilot/",
  },
  "required_ordering": [
    "after-verified-os-root",
    "before-replaceable-application",
    "before-any-pandad-or-can-capable-process",
  ],
  "required_sandbox": [
    "NoNewPrivileges=yes",
    "ProtectSystem=strict",
    "ProtectHome=yes",
    "PrivateTmp=yes",
    "RestrictAddressFamilies=AF_UNIX",
    "DevicePolicy=closed",
    "CapabilityBoundingSet=",
  ],
  "authority_protocol": "g8_protected_authority.ProtectedAuthority",
  "immutable_snapshot_protocol": "g8_f6_early_boot_boundary.EarlyBootAdapter",
  "required_transition_order": [
    "authorize-trial",
    "consume-attempt-durably-before-observation",
    "observe-startup-with-neutralized-can",
    "authenticate-health",
    "atomically-promote-recovery",
  ],
  "forbidden_actions": [
    "execute-application",
    "mark-os-slot-successful",
    "install-package",
    "write-boot-control",
    "open-panda",
    "send-can",
    "enable-actuation",
    "accept-owner-waiver-as-health",
  ],
}


class ContractError(RuntimeError):
  """Fail-closed model transition or authority failure."""


class State(str, Enum):
  RECOVERY_PINNED = "RECOVERY_PINNED"
  TRIAL_AUTHORIZED = "TRIAL_AUTHORIZED"
  ATTEMPT_CONSUMED = "ATTEMPT_CONSUMED"
  PROBATION = "PROBATION"
  HEALTH_ATTESTED = "HEALTH_ATTESTED"
  PROMOTED_MODEL_ONLY = "PROMOTED_MODEL_ONLY"
  ROLLED_BACK = "ROLLED_BACK"
  HOLD = "HOLD"


@dataclass(frozen=True)
class ObservationDecision:
  """Metadata-only result.  It intentionally contains no executable pathname."""

  disposition: str
  candidate: CandidateIdentity
  attempts_consumed: int
  attempts_limit: int
  observe_only: bool = True
  actuation_authorized: bool = False
  installation_authorized: bool = False
  boot_operations_authorized: bool = False


class NonDeployableSupervisorModel:
  """State transition checker backed by the existing protected-authority API."""

  def __init__(self, authority: ProtectedAuthority, writable_app_root: str | os.PathLike[str]):
    if authority is None:
      raise ContractError("a protected authority adapter is mandatory")
    self.authority = authority
    try:
      app = Path(writable_app_root).resolve(strict=True)
      trust = Path(authority.trust_domain_path).resolve(strict=True)
      if trust == app or trust.is_relative_to(app):
        raise ContractError("authority trust domain must be outside writable application storage")
      self.policy = authority.policy_snapshot()
    except ContractError:
      raise
    except Exception as error:
      raise ContractError("protected authority is unavailable") from error
    self.state = State.RECOVERY_PINNED
    self.recovery = self.policy.recovery
    self.trial: CandidateIdentity | None = None
    self.ticket: TrialTicket | None = None
    self.grant: BootGrant | None = None
    self.receipt: HealthReceipt | None = None
    self.sequence = 0
    self.last_event = "MODEL_INITIALIZED_WITH_PROTECTED_RECOVERY"
    self._validate()

  def _hold(self, event: str, error: Exception) -> ContractError:
    self.state = State.HOLD
    self.last_event = event
    self.sequence += 1
    return ContractError(event)

  def _advance(self, state: State, event: str) -> None:
    self.state = state
    self.last_event = event
    self.sequence += 1
    self._validate()

  def _clear_trial(self) -> None:
    self.trial = None
    self.ticket = None
    self.grant = None
    self.receipt = None

  def _validate_candidate_against_policy(self, candidate: CandidateIdentity) -> None:
    candidate.validate()
    allowed_keys = {item.get("key_id") for item in self.policy.signing_keys}
    if (candidate.source_commit != self.policy.expected_commit or
        candidate.release_sequence < self.policy.minimum_release_sequence or
        candidate.signing_key_id not in allowed_keys):
      raise ContractError("candidate violates protected commit, rollback, or signing policy")

  def _validate(self) -> None:
    self.recovery.validate()
    if (self.recovery.source_commit != self.policy.expected_commit or
        self.recovery.release_sequence < self.policy.minimum_release_sequence):
      raise ContractError("protected recovery violates the current policy")
    if self.state == State.HOLD:
      if (self.trial is None) != (self.ticket is None):
        raise ContractError("HOLD retained only part of the protected trial binding")
      return
    trial_states = {
      State.TRIAL_AUTHORIZED, State.ATTEMPT_CONSUMED, State.PROBATION, State.HEALTH_ATTESTED,
    }
    if self.state in trial_states:
      if self.trial is None or self.ticket is None or self.ticket.candidate != self.trial:
        raise ContractError("trial state lacks an exact protected ticket binding")
      self._validate_candidate_against_policy(self.trial)
    elif any(item is not None for item in (self.trial, self.ticket, self.grant, self.receipt)):
      raise ContractError("non-trial state retained mutable trial authorization")
    if self.state in {State.ATTEMPT_CONSUMED, State.PROBATION, State.HEALTH_ATTESTED}:
      if self.grant is None or self.grant.disposition != "trial" or self.grant.candidate != self.trial:
        raise ContractError("observation state lacks a consumed trial attempt")
    elif self.grant is not None:
      raise ContractError("grant exists before consumption or after trial closure")
    if self.state == State.HEALTH_ATTESTED:
      if (self.receipt is None or self.receipt.candidate != self.trial or
          self.receipt.ticket_id != self.ticket.ticket_id):
        raise ContractError("health state lacks an exact authenticated receipt")
    elif self.receipt is not None:
      raise ContractError("health receipt exists outside the attested state")

  def authorize_trial(self, candidate: CandidateIdentity, max_attempts: int,
                      intent_envelope: dict[str, Any]) -> TrialTicket:
    if self.state not in {State.RECOVERY_PINNED, State.ROLLED_BACK, State.PROMOTED_MODEL_ONLY}:
      raise ContractError("trial authorization is not allowed from the current state")
    self._validate_candidate_against_policy(candidate)
    try:
      ticket = self.authority.authorize_trial(candidate, max_attempts, intent_envelope)
    except Exception as error:
      raise self._hold("AUTHORITY_REJECTED_TRIAL_HOLD", error) from error
    if ticket.candidate != candidate:
      raise self._hold("AUTHORITY_RETURNED_MISMATCHED_TICKET_HOLD", ContractError("mismatch"))
    self.trial, self.ticket = candidate, ticket
    self._advance(State.TRIAL_AUTHORIZED, "PROTECTED_TRIAL_AUTHORIZED")
    return ticket

  def consume_attempt_before_observation(self) -> ObservationDecision:
    if self.state != State.TRIAL_AUTHORIZED or self.trial is None or self.ticket is None:
      raise ContractError("attempt consumption requires an authorized trial")
    try:
      grant = self.authority.consume_attempt(self.trial, self.ticket.epoch, self.ticket)
    except Exception as error:
      raise self._hold("ATTEMPT_CONSUMPTION_FAILED_HOLD", error) from error
    if grant.disposition == "recovery":
      try:
        policy = self.authority.cancel_trial(self.trial, self.ticket.epoch, self.ticket)
      except Exception as error:
        raise self._hold("EXHAUSTED_TRIAL_CANCELLATION_FAILED_HOLD", error) from error
      if policy.recovery != grant.candidate:
        raise self._hold("EXHAUSTED_RECOVERY_MISMATCH_HOLD", ContractError("mismatch"))
      self.policy, self.recovery = policy, policy.recovery
      decision = ObservationDecision("recovery", grant.candidate,
                                     grant.attempts_consumed, grant.attempts_limit)
      self._clear_trial()
      self._advance(State.ROLLED_BACK, "ATTEMPT_BUDGET_EXHAUSTED_RECOVERY_SELECTED")
      return decision
    if grant.disposition != "trial" or grant.candidate != self.trial:
      raise self._hold("AUTHORITY_RETURNED_INVALID_GRANT_HOLD", ContractError("invalid grant"))
    self.grant = grant
    self._advance(State.ATTEMPT_CONSUMED, "ATTEMPT_DURABLY_CONSUMED_BEFORE_OBSERVATION")
    return ObservationDecision("trial-observation-only", grant.candidate,
                               grant.attempts_consumed, grant.attempts_limit)

  def observe_startup(self, passed: bool) -> None:
    if type(passed) is not bool:
      raise ContractError("startup observation must be an exact boolean")
    if self.state != State.ATTEMPT_CONSUMED or self.trial is None or self.ticket is None:
      raise ContractError("startup may only be observed after durable attempt consumption")
    if passed:
      self._advance(State.PROBATION, "NEUTRAL_CAN_STARTUP_OBSERVED_AWAITING_HEALTH")
      return
    self._safe_cancel("STARTUP_FAILURE_ROLLBACK")

  def attest_health(self, health_envelope: dict[str, Any]) -> HealthReceipt:
    if self.state != State.PROBATION or self.trial is None or self.ticket is None:
      raise ContractError("health cannot be accepted before complete startup probation")
    try:
      receipt = self.authority.attest_health(
        self.trial, self.ticket.epoch, self.ticket, health_envelope)
    except Exception as error:
      raise self._hold("HEALTH_AUTHENTICATION_FAILED_HOLD", error) from error
    if receipt.candidate != self.trial or receipt.ticket_id != self.ticket.ticket_id:
      raise self._hold("HEALTH_RECEIPT_BINDING_MISMATCH_HOLD", ContractError("mismatch"))
    self.receipt = receipt
    self._advance(State.HEALTH_ATTESTED, "AUTHENTICATED_HEALTH_RECORDED_NOT_PROMOTED")
    return receipt

  def promote_model_only(self) -> PolicySnapshot:
    if self.state != State.HEALTH_ATTESTED or self.receipt is None or self.trial is None:
      raise ContractError("promotion requires a protected authenticated health receipt")
    promoted_candidate = self.trial
    try:
      policy = self.authority.promote_recovery(self.receipt)
    except Exception as error:
      raise self._hold("TRANSACTIONAL_PROMOTION_FAILED_HOLD", error) from error
    if (policy.recovery != promoted_candidate or
        policy.minimum_release_sequence < promoted_candidate.release_sequence):
      raise self._hold("PROMOTED_POLICY_BINDING_MISMATCH_HOLD", ContractError("mismatch"))
    self.policy, self.recovery = policy, policy.recovery
    self._clear_trial()
    self._advance(State.PROMOTED_MODEL_ONLY, "MODEL_PROMOTION_RECORDED_NON_DEPLOYABLE")
    return policy

  def recover_after_restart(self) -> None:
    """Conservatively cancel any modeled in-flight trial; never infer health."""
    if self.state in {State.RECOVERY_PINNED, State.ROLLED_BACK, State.PROMOTED_MODEL_ONLY}:
      self._validate()
      return
    if self.state == State.HOLD:
      raise ContractError("HOLD requires external protected-state reconciliation")
    self._safe_cancel("RESTART_WITH_UNCONFIRMED_TRIAL_ROLLBACK")

  def _safe_cancel(self, event: str) -> None:
    if self.trial is None or self.ticket is None:
      raise ContractError("no exact protected ticket is available for cancellation")
    try:
      policy = self.authority.cancel_trial(self.trial, self.ticket.epoch, self.ticket)
    except Exception as error:
      raise self._hold("PROTECTED_CANCELLATION_FAILED_HOLD", error) from error
    self.policy, self.recovery = policy, policy.recovery
    self._clear_trial()
    self._advance(State.ROLLED_BACK, event)

  def snapshot(self) -> dict[str, Any]:
    """Return diagnostics only; fields are never an authorization source."""
    self._validate()
    return {
      "schema": MODEL_SCHEMA,
      "classification": "NON_DEPLOYABLE_HOST_MODEL",
      "state": self.state.value,
      "sequence": self.sequence,
      "last_event": self.last_event,
      "recovery": asdict(self.recovery),
      "trial": asdict(self.trial) if self.trial is not None else None,
      "attempts_consumed": self.grant.attempts_consumed if self.grant is not None else 0,
      "attempts_limit": self.grant.attempts_limit if self.grant is not None else 0,
      "health_authenticated": self.receipt is not None,
      "installation_authorized": False,
      "boot_operations_authorized": False,
      "actuation_authorized": False,
      "production_approved": False,
    }

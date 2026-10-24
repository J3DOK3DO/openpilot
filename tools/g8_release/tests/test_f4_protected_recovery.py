import base64
import copy
import errno
import hashlib
import json
import os
from dataclasses import asdict, replace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import g8_manifest as gm
import g8_slot_supervisor as sv
from g8_f4_boot_coordinator import BootCoordinator, CoordinatorCrash, CoordinatorError, CoordinatorFaults
from g8_protected_authority import (
  AuthorityError,
  AuthorityFaults,
  CandidateIdentity,
  HEALTH_DOMAIN,
  INTENT_DOMAIN,
  REVOKE_DOMAIN,
  HealthReceipt,
  MockProtectedAuthority,
  SIMULATED_TRUST_LABEL,
  SimulatedPowerLoss,
  TrialTicket,
  canonical,
  health_payload,
  revoke_payload,
  trial_intent_payload,
)


COMMIT = "c" * 40


def public_raw(private_key):
  return private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def public_b64(private_key):
  return base64.b64encode(public_raw(private_key)).decode()


def key_id(private_key):
  return hashlib.sha256(public_raw(private_key)).hexdigest()[:16]


def envelope(private_key, domain, payload):
  return {
    "alg": "ed25519",
    "key_id": key_id(private_key),
    "payload": payload,
    "signature": base64.b64encode(private_key.sign(domain + canonical(payload))).decode(),
    "trust": SIMULATED_TRUST_LABEL,
  }


def package(path, tag):
  path.mkdir()
  launcher = path / sv.LAUNCHER
  launcher.write_text(f"#!/bin/sh\necho {tag}\n")
  launcher.chmod(0o755)
  (path / "version.txt").write_text(tag)


def identity(app, sid):
  manifest_bytes = (app / "slots" / sid / sv.MANIFEST_NAME).read_bytes()
  manifest = json.loads(manifest_bytes)
  signature = json.loads((app / "slots" / sid / sv.SIGNATURE_NAME).read_bytes())
  return CandidateIdentity(
    sid, hashlib.sha256(manifest_bytes).hexdigest(), manifest["source_commit"],
    manifest["release_sequence"], signature["key_id"],
  )


@pytest.fixture
def f4(tmp_path):
  release_key = Ed25519PrivateKey.generate()
  decision_key = Ed25519PrivateKey.generate()
  health_key = Ed25519PrivateKey.generate()
  trust_key = {
    "key_id": gm.key_id(public_raw(release_key)),
    "pubkey_b64": public_b64(release_key),
    "purpose": "production",
  }
  trust = {"trusted_keys": [trust_key]}
  app = tmp_path / "mutable_app"
  app.mkdir()
  supervisor = sv.Supervisor(app, trust=trust, expected_commit=COMMIT, minimum_release_sequence=10)
  slots = {}
  for offset, tag in enumerate(("recovery", "trial")):
    source = tmp_path / f"package_{tag}"
    package(source, tag)
    manifest = gm.build_manifest(source, COMMIT, with_elf_detail=False, release_sequence=10 + offset)
    signature = gm.sign_manifest(manifest, release_key, SIMULATED_TRUST_LABEL)
    slots[tag] = supervisor.stage(source, manifest, COMMIT, signature)
  supervisor._switch_live(slots["recovery"])
  identities = {name: identity(app, sid) for name, sid in slots.items()}
  protected = tmp_path / "mock_protected_authority"
  authority = MockProtectedAuthority.create(
    protected,
    recovery=identities["recovery"],
    expected_commit=COMMIT,
    minimum_release_sequence=10,
    signing_keys=[trust_key],
    decision_pubkey_b64=public_b64(decision_key),
    health_pubkey_b64=public_b64(health_key),
  )
  coordinator = BootCoordinator(app, authority)
  return type("F4", (), {
    "tmp": tmp_path, "app": app, "protected": protected, "authority": authority,
    "coordinator": coordinator, "slots": slots, "ids": identities, "trust_key": trust_key,
    "release_key": release_key, "decision_key": decision_key, "health_key": health_key,
  })()


def authorize(env, attempts=3):
  policy = env.authority.policy_snapshot()
  payload = trial_intent_payload(policy, env.ids["trial"], attempts)
  return env.coordinator.authorize_trial(
    env.slots["trial"], attempts, envelope(env.decision_key, INTENT_DOMAIN, payload))


def healthy_envelope(env, ticket, measurement="a" * 64):
  return envelope(env.health_key, HEALTH_DOMAIN, health_payload(ticket, measurement))


def forge_app_attempts(env, value):
  state_path = env.app / "state.json"
  state = json.loads(state_path.read_text())
  state["pending"] = {
    "slot": env.slots["trial"], "from": env.slots["recovery"], "attempts_left": value,
  }
  state["last_good"] = env.slots["recovery"]
  state_path.write_text(json.dumps(state))


def test_legitimate_lifecycle_consumes_health_attests_and_promotes(f4):
  ticket = authorize(f4, 3)
  selection = f4.coordinator.prepare_trial_boot(ticket)
  assert selection.disposition == "trial"
  assert selection.candidate == f4.ids["trial"]
  assert selection.executed is False
  assert selection.launcher_path is None  # fail closed: no executable pathname handoff
  promoted = f4.coordinator.attest_and_promote(ticket, healthy_envelope(f4, ticket))
  assert promoted.recovery == f4.ids["trial"]
  assert promoted.minimum_release_sequence == 11
  assert promoted.generation == 2
  assert f4.coordinator.prepare_recovery().candidate == f4.ids["trial"]


def test_single_app_state_forge_does_not_refund_protected_attempt(f4):
  ticket = authorize(f4, 2)
  assert f4.coordinator.prepare_trial_boot(ticket).attempts_consumed == 1
  forge_app_attempts(f4, 99)
  assert f4.coordinator.prepare_trial_boot(ticket).attempts_consumed == 2
  assert f4.authority.protected_attempts() == (2, 2)


def test_repeated_bounded_state_rewrite_cannot_extend_budget(f4):
  ticket = authorize(f4, 3)
  for consumed in range(1, 4):
    forge_app_attempts(f4, 3)
    selection = f4.coordinator.prepare_trial_boot(ticket)
    assert (selection.disposition, selection.attempts_consumed) == ("trial", consumed)
  forge_app_attempts(f4, 3)
  exhausted = f4.coordinator.prepare_trial_boot(ticket)
  assert exhausted.disposition == "recovery"
  assert exhausted.candidate == f4.ids["recovery"]
  assert f4.authority.protected_attempts() == (3, 3)


def test_app_replay_after_simulated_restart_keeps_monotonic_counter(f4):
  ticket = authorize(f4, 3)
  pristine_app_state = (f4.app / "state.json").read_bytes()
  f4.coordinator.prepare_trial_boot(ticket)
  (f4.app / "state.json").write_bytes(pristine_app_state)
  restarted_authority = MockProtectedAuthority(f4.protected)
  restarted = BootCoordinator(f4.app, restarted_authority)
  assert restarted.prepare_trial_boot(ticket).attempts_consumed == 2
  assert restarted_authority.protected_attempts() == (2, 3)


def test_hardened_mode_requires_authority_and_has_no_f1_fallback(f4):
  with pytest.raises(CoordinatorError, match="requires an external"):
    BootCoordinator(f4.app, None)
  with pytest.raises(CoordinatorError, match="hardened"):
    BootCoordinator(f4.app, f4.authority, hardened=False)


def test_authority_must_be_outside_mutable_application_tree(f4):
  nested = f4.app / "fake_protected"
  nested_authority = MockProtectedAuthority.create(
    nested, recovery=f4.ids["recovery"], expected_commit=COMMIT, minimum_release_sequence=10,
    signing_keys=[f4.trust_key], decision_pubkey_b64=public_b64(f4.decision_key),
    health_pubkey_b64=public_b64(f4.health_key),
  )
  with pytest.raises(CoordinatorError, match="outside"):
    BootCoordinator(f4.app, nested_authority)


def test_missing_and_corrupt_authority_fail_closed(f4):
  os.unlink(f4.protected / "protected_state.json")
  with pytest.raises(AuthorityError, match="missing, corrupt, or unreadable"):
    MockProtectedAuthority(f4.protected)
  (f4.protected / "protected_state.json").write_text("{not-json")
  with pytest.raises(AuthorityError, match="missing, corrupt, or unreadable"):
    MockProtectedAuthority(f4.protected)


def test_no_health_and_forged_app_confirmation_cannot_promote(f4):
  ticket = authorize(f4, 2)
  f4.coordinator.prepare_trial_boot(ticket)
  forge_app_attempts(f4, 0)
  state = json.loads((f4.app / "state.json").read_text())
  state["pending"] = None
  state["last_good"] = f4.slots["trial"]
  (f4.app / "state.json").write_text(json.dumps(state))
  fake_receipt = HealthReceipt(
    ticket.generation, ticket.epoch, ticket.candidate, ticket.ticket_id, "f" * 64)
  with pytest.raises(AuthorityError, match="lacks the protected authenticated health"):
    f4.authority.promote_recovery(fake_receipt)
  assert f4.authority.policy_snapshot().recovery == f4.ids["recovery"]


def test_wrong_health_key_or_wrong_trial_is_rejected(f4):
  ticket = authorize(f4, 2)
  f4.coordinator.prepare_trial_boot(ticket)
  wrong_key = Ed25519PrivateKey.generate()
  with pytest.raises(CoordinatorError, match="authenticated decision"):
    f4.coordinator.attest_and_promote(
      ticket, envelope(wrong_key, HEALTH_DOMAIN, health_payload(ticket, "b" * 64)))
  wrong_candidate = replace(ticket.candidate, manifest_sha256="f" * 64)
  bad_payload = health_payload(ticket, "b" * 64)
  bad_payload["candidate"] = asdict(wrong_candidate)
  with pytest.raises(CoordinatorError, match="candidate mismatch"):
    f4.coordinator.attest_and_promote(ticket, envelope(f4.health_key, HEALTH_DOMAIN, bad_payload))
  assert f4.authority.policy_snapshot().recovery == f4.ids["recovery"]


def test_consume_rejects_caller_bypass_mixed_epoch_and_malformed_ticket(f4):
  ticket = authorize(f4, 2)
  forged_identity = replace(ticket.candidate, manifest_sha256="0" * 64)
  with pytest.raises(AuthorityError, match="mismatch"):
    f4.authority.consume_attempt(forged_identity, ticket.epoch, ticket)
  with pytest.raises(AuthorityError, match="mismatch"):
    f4.authority.consume_attempt(ticket.candidate, ticket.epoch + 1, ticket)
  malformed = replace(ticket, secret="../not-a-token")
  with pytest.raises(AuthorityError, match="malformed"):
    f4.authority.consume_attempt(ticket.candidate, ticket.epoch, malformed)
  assert f4.authority.protected_attempts() == (0, 2)


def test_old_ticket_replay_fails_after_promotion_generation_change(f4):
  ticket = authorize(f4, 1)
  f4.coordinator.prepare_trial_boot(ticket)
  f4.coordinator.attest_and_promote(ticket, healthy_envelope(f4, ticket))
  with pytest.raises(CoordinatorError, match="no protected active trial"):
    f4.coordinator.prepare_trial_boot(ticket)


def test_release_signature_mismatch_is_rejected_before_authority(f4):
  signature_path = f4.app / "slots" / f4.slots["trial"] / sv.SIGNATURE_NAME
  signature = json.loads(signature_path.read_text())
  signature["signature"] = base64.b64encode(b"x" * 64).decode()
  signature_path.write_bytes(gm.canonical(signature))
  seal_path = f4.app / "slots" / f4.slots["trial"] / sv.SEAL_NAME
  seal = json.loads(seal_path.read_text())
  seal["signature_sha256"] = hashlib.sha256(gm.canonical(signature)).hexdigest()
  seal_path.write_bytes(gm.canonical(seal))
  policy = f4.authority.policy_snapshot()
  intent = envelope(f4.decision_key, INTENT_DOMAIN, trial_intent_payload(policy, f4.ids["trial"], 2))
  with pytest.raises(CoordinatorError, match="signature"):
    f4.coordinator.authorize_trial(f4.slots["trial"], 2, intent)
  assert f4.authority.protected_attempts() == (0, 0)


def test_malformed_candidate_identity_fails_closed(f4):
  malformed = replace(f4.ids["trial"], slot_id="../../escape")
  policy = f4.authority.policy_snapshot()
  with pytest.raises(AuthorityError, match="malformed candidate slot"):
    trial_intent_payload(policy, malformed, 2)
  assert f4.authority.protected_attempts() == (0, 0)


def test_cancel_and_authenticated_revoke_invalidate_ticket(f4):
  first = authorize(f4, 2)
  snapshot = f4.authority.cancel_trial(first.candidate, first.epoch, first)
  assert snapshot.epoch == first.epoch + 1
  with pytest.raises(AuthorityError, match="no protected active"):
    f4.authority.consume_attempt(first.candidate, first.epoch, first)

  second = authorize(f4, 2)
  policy = f4.authority.policy_snapshot()
  payload = revoke_payload(policy, second, "offline test revocation")
  revoked = f4.authority.revoke_trial(
    second.candidate, second.epoch, second, "offline test revocation",
    envelope(f4.decision_key, REVOKE_DOMAIN, payload),
  )
  assert revoked.epoch == second.epoch + 1
  with pytest.raises(AuthorityError, match="no protected active"):
    f4.authority.consume_attempt(second.candidate, second.epoch, second)


def test_changed_commit_minimum_or_key_bootstrap_conflict_fails_closed(f4):
  with pytest.raises(AuthorityError, match="expected_commit"):
    MockProtectedAuthority(f4.protected, expected_commit="d" * 40)
  with pytest.raises(AuthorityError, match="minimum_release_sequence"):
    MockProtectedAuthority(f4.protected, minimum_release_sequence=99)
  wrong_key = copy.deepcopy(f4.trust_key)
  wrong_key["purpose"] = "dev-disposable"
  with pytest.raises(AuthorityError, match="signing_keys"):
    MockProtectedAuthority(f4.protected, signing_keys=[wrong_key])


def test_rollback_minimum_blocks_older_signed_candidate(f4):
  old_source = f4.tmp / "package_old"
  package(old_source, "old")
  manifest = gm.build_manifest(old_source, COMMIT, with_elf_detail=False, release_sequence=9)
  signature = gm.sign_manifest(manifest, f4.release_key, SIMULATED_TRUST_LABEL)
  permissive = sv.Supervisor(f4.app, trust={"trusted_keys": [f4.trust_key]}, expected_commit=COMMIT)
  old_sid = permissive.stage(old_source, manifest, COMMIT, signature)
  with pytest.raises(CoordinatorError, match="below pinned minimum"):
    f4.coordinator.inspect_candidate(old_sid)


def test_exact_exhaustion_returns_only_preverified_recovery(f4):
  ticket = authorize(f4, 1)
  first = f4.coordinator.prepare_trial_boot(ticket)
  second = f4.coordinator.prepare_trial_boot(ticket)
  assert first.disposition == "trial"
  assert second.disposition == "recovery"
  assert second.candidate == f4.authority.policy_snapshot().recovery
  assert second.launcher_path is None  # verified recovery identity is not an execution grant


def test_prepare_crash_before_consume_preserves_budget_after_consume_spends_it(f4):
  ticket = authorize(f4, 2)
  f4.coordinator.faults = CoordinatorFaults(crash_at="prepare_before_consume")
  with pytest.raises(CoordinatorCrash):
    f4.coordinator.prepare_trial_boot(ticket)
  assert f4.authority.protected_attempts() == (0, 2)
  f4.coordinator.faults = CoordinatorFaults(crash_at="prepare_after_consume")
  with pytest.raises(CoordinatorCrash):
    f4.coordinator.prepare_trial_boot(ticket)
  assert f4.authority.protected_attempts() == (1, 2)


def test_consume_postcommit_power_loss_is_conservatively_durable(f4):
  ticket = authorize(f4, 2)
  f4.authority.faults = AuthorityFaults(crash_at="consume_committed")
  with pytest.raises(SimulatedPowerLoss):
    f4.coordinator.prepare_trial_boot(ticket)
  restarted = MockProtectedAuthority(f4.protected)
  assert restarted.protected_attempts() == (1, 2)
  assert BootCoordinator(f4.app, restarted).prepare_trial_boot(ticket).attempts_consumed == 2


def test_promotion_precommit_crash_keeps_old_recovery_postcommit_keeps_new(f4):
  ticket = authorize(f4, 2)
  f4.coordinator.prepare_trial_boot(ticket)
  receipt = f4.authority.attest_health(
    ticket.candidate, ticket.epoch, ticket, healthy_envelope(f4, ticket))
  f4.authority.faults = AuthorityFaults(crash_at="promote_precommit")
  with pytest.raises(SimulatedPowerLoss):
    f4.authority.promote_recovery(receipt)
  assert MockProtectedAuthority(f4.protected).policy_snapshot().recovery == f4.ids["recovery"]
  restarted = MockProtectedAuthority(f4.protected, faults=AuthorityFaults(crash_at="promote_committed"))
  with pytest.raises(SimulatedPowerLoss):
    restarted.promote_recovery(receipt)
  final = MockProtectedAuthority(f4.protected).policy_snapshot()
  assert final.recovery == f4.ids["trial"]
  assert final.generation == 2


@pytest.mark.parametrize("error_number", [errno.EROFS, errno.EIO, errno.ENOSPC])
def test_authority_storage_errors_fail_closed_without_spending_or_granting(f4, error_number):
  ticket = authorize(f4, 2)
  f4.authority.faults = AuthorityFaults(oserror_at={"authority_write": error_number})
  with pytest.raises(OSError) as raised:
    f4.coordinator.prepare_trial_boot(ticket)
  assert raised.value.errno == error_number
  assert MockProtectedAuthority(f4.protected).protected_attempts() == (0, 2)


def test_wrong_live_symlink_is_restored_to_authority_choice(f4):
  ticket = authorize(f4, 2)
  os.unlink(f4.app / "live")
  os.symlink("slots/not-a-slot", f4.app / "live")
  selected = f4.coordinator.prepare_trial_boot(ticket)
  assert selected.candidate == f4.ids["trial"]
  assert os.readlink(f4.app / "live") == f"slots/{f4.slots['trial']}"


def test_corrupt_or_symlinked_launcher_is_rejected_after_attempt_consumption(f4):
  ticket = authorize(f4, 2)
  launcher = f4.app / "slots" / f4.slots["trial"] / sv.LAUNCHER
  launcher.unlink()
  launcher.symlink_to(f4.app / "slots" / f4.slots["recovery"] / sv.LAUNCHER)
  with pytest.raises(CoordinatorError, match="deep verification"):
    f4.coordinator.prepare_trial_boot(ticket)
  assert f4.authority.protected_attempts() == (1, 2)


def test_exhausted_budget_with_corrupt_recovery_returns_no_launcher(f4):
  ticket = authorize(f4, 1)
  assert f4.coordinator.prepare_trial_boot(ticket).disposition == "trial"
  recovery_launcher = f4.app / "slots" / f4.slots["recovery"] / sv.LAUNCHER
  recovery_launcher.write_text("#!/bin/sh\necho forged\n")
  with pytest.raises(CoordinatorError, match="deep verification"):
    f4.coordinator.prepare_trial_boot(ticket)
  assert f4.authority.protected_attempts() == (1, 1)


def test_host_coordinator_rejects_duck_typed_attacker_authority(f4):
  class ForgedAuthority:
    trust_domain_path = "/outside/trusted"
    def policy_snapshot(self):
      return f4.authority.policy_snapshot()
    def consume_attempt(self, *args):
      return object()
  with pytest.raises(CoordinatorError, match="exact mock-authority"):
    BootCoordinator(f4.app, ForgedAuthority())


def test_host_selection_never_hands_out_a_mutable_executable_path(f4):
  ticket = authorize(f4, 1)
  trial = f4.coordinator.prepare_trial_boot(ticket)
  recovery = f4.coordinator.prepare_trial_boot(ticket)
  assert trial.disposition == "trial" and recovery.disposition == "recovery"
  for result in (trial, recovery):
    assert result.launcher_path is None
    assert result.executed is False
    assert result.candidate is not None

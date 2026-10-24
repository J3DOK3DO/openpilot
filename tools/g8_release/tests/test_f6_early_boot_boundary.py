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
from g8_f6_early_boot_boundary import (
  CONSUME_DOMAIN,
  GRANT_DOMAIN,
  HEALTH_DOMAIN,
  HEALTH_RECEIPT_DOMAIN,
  POLICY_DOMAIN,
  BoundaryError,
  BoundaryFaults,
  CallerIdentity,
  ImmutableSnapshotQualifier,
  MockEarlyBootAdapter,
  SimulatedBoundaryPowerLoss,
  SnapshotProvenance,
  _sign,
  health_payload,
  public_key_b64,
  sign_health,
  verify_envelope,
)
from g8_protected_authority import CandidateIdentity, PolicySnapshot, SIMULATED_TRUST_LABEL, canonical


COMMIT = "e" * 40
AUTHORITY_ID = "mock.early-boot.authority"


def _public_raw(private_key):
  return private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _public_b64(private_key):
  return base64.b64encode(_public_raw(private_key)).decode()


def _identity(app, slot_id):
  directory = app / "slots" / slot_id
  manifest_bytes = (directory / sv.MANIFEST_NAME).read_bytes()
  manifest = json.loads(manifest_bytes)
  signature = json.loads((directory / sv.SIGNATURE_NAME).read_bytes())
  return CandidateIdentity(
    slot_id, hashlib.sha256(manifest_bytes).hexdigest(), manifest["source_commit"],
    manifest["release_sequence"], signature["key_id"],
  )


def _package(path, tag):
  path.mkdir()
  launcher = path / sv.LAUNCHER
  launcher.write_text(f"#!/bin/sh\necho {tag}\n")
  launcher.chmod(0o755)
  (path / "version.txt").write_text(tag)


@pytest.fixture
def f6(tmp_path):
  release_key = Ed25519PrivateKey.generate()
  authority_key = Ed25519PrivateKey.generate()
  health_key = Ed25519PrivateKey.generate()
  trust_key = {
    "key_id": gm.key_id(_public_raw(release_key)),
    "pubkey_b64": _public_b64(release_key),
    "purpose": "production",
  }
  trust = {"trusted_keys": [trust_key]}
  app = tmp_path / "mutable_app"
  app.mkdir()
  supervisor = sv.Supervisor(app, trust=trust, expected_commit=COMMIT, minimum_release_sequence=20)
  identities = {}
  slots = {}
  for sequence, tag in ((20, "old"), (21, "current")):
    source = tmp_path / f"package_{tag}"
    _package(source, tag)
    manifest = gm.build_manifest(source, COMMIT, with_elf_detail=False, release_sequence=sequence)
    signature = gm.sign_manifest(manifest, release_key, SIMULATED_TRUST_LABEL)
    slot = supervisor.stage(source, manifest, COMMIT, signature)
    identities[tag] = _identity(app, slot)
    slots[tag] = slot
  policy_core = {
    "generation": 4,
    "epoch": 7,
    "recovery": asdict(identities["current"]),
    "expected_commit": COMMIT,
    "minimum_release_sequence": 21,
    "signing_keys": [trust_key],
  }
  policy = PolicySnapshot(
    4, 7, identities["current"], COMMIT, 21, (trust_key,),
    hashlib.sha256(canonical(policy_core)).hexdigest(),
  )
  caller = CallerIdentity("g8.f6.qualifier", "1" * 64)
  provenance = SnapshotProvenance.create(
    os_slot="a", mount_source="/dev/mapper/verified-app-a", verity_root_digest="2" * 64)
  protected = tmp_path / "obviously_insecure_mock_trust_domain"
  adapter = MockEarlyBootAdapter.create(
    protected, authority_id=AUTHORITY_ID, caller=caller, authorized_os_slot="a", policy=policy,
    candidate=identities["current"], provenance=provenance, authority_private_key=authority_key,
    health_pubkey_b64=_public_b64(health_key),
  )
  qualifier = ImmutableSnapshotQualifier(
    app, adapter, caller, AUTHORITY_ID, public_key_b64(authority_key))
  return type("F6", (), {
    "tmp": tmp_path, "app": app, "protected": protected, "adapter": adapter,
    "qualifier": qualifier, "caller": caller, "provenance": provenance, "policy": policy,
    "ids": identities, "slots": slots, "authority_key": authority_key, "health_key": health_key,
    "authority_public": public_key_b64(authority_key),
  })()


def _begin(env, nonce="a" * 64):
  return env.qualifier.begin_boot(nonce)


def _grant_without_consume(env, nonce="b" * 64):
  context, boot = env.qualifier.begin_boot(nonce)
  grant = env.adapter.authorize_snapshot(boot, env.ids["current"], env.provenance)
  return context, boot, grant


@pytest.mark.SIMULATED_TEST_TRUST
def test_exact_signed_boot_policy_snapshot_and_consumed_grant_qualify(f6):
  context, boot = _begin(f6)
  with f6.qualifier.qualify(context, boot, f6.ids["current"], f6.provenance) as qualified:
    assert qualified.context == context
    assert qualified.candidate == f6.ids["current"]
    assert qualified.provenance.snapshot_fingerprint == f6.provenance.snapshot_fingerprint
    assert qualified.immutable_precondition_verified is True
    assert qualified.executed is False
    assert qualified.pinned_release.executed is False
    assert qualified.authorization.consume_sequence == 1
    qualified.pinned_release.revalidate()
  assert f6.adapter.protected_counters() == (1, 1)


@pytest.mark.SIMULATED_TEST_TRUST
def test_canonical_grant_binds_all_required_decision_fields(f6):
  context, boot, grant = _grant_without_consume(f6)
  payload = verify_envelope(grant, GRANT_DOMAIN, f6.authority_public)
  assert payload["authority_id"] == AUTHORITY_ID
  assert payload["caller"] == asdict(f6.caller)
  assert payload["policy_generation"] == f6.policy.generation
  assert payload["epoch"] == f6.policy.epoch
  assert payload["boot_nonce"] == context.boot_nonce
  assert payload["authorized_os_slot"] == context.os_slot
  assert payload["candidate"] == asdict(f6.ids["current"])
  assert payload["snapshot"]["snapshot_fingerprint"] == f6.provenance.snapshot_fingerprint


@pytest.mark.SIMULATED_TEST_TRUST
def test_forged_snapshot_fingerprint_fails_closed(f6):
  context, boot = _begin(f6)
  forged = replace(f6.provenance, snapshot_fingerprint="f" * 64)
  with pytest.raises(BoundaryError, match="fingerprint"):
    f6.qualifier.qualify(context, boot, f6.ids["current"], forged)
  assert f6.adapter.protected_counters() == (1, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_wrong_authenticated_os_slot_fails_before_grant(f6):
  context, boot = _begin(f6)
  wrong = SnapshotProvenance.create(
    os_slot="b", mount_source="/dev/mapper/verified-app-b", verity_root_digest="3" * 64)
  with pytest.raises(BoundaryError, match="wrong authenticated OS slot"):
    f6.qualifier.qualify(context, boot, f6.ids["current"], wrong)
  assert f6.adapter.protected_counters() == (1, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_two_boots_with_same_nonce_are_rejected(f6):
  _begin(f6, "4" * 64)
  with pytest.raises(BoundaryError, match="nonce replay"):
    _begin(f6, "4" * 64)
  assert f6.adapter.protected_counters() == (1, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_prior_boot_context_is_stale_after_next_boot(f6):
  old_context, old_boot = _begin(f6, "5" * 64)
  _begin(f6, "6" * 64)
  with pytest.raises(BoundaryError, match="stale"):
    f6.qualifier.qualify(old_context, old_boot, f6.ids["current"], f6.provenance)


@pytest.mark.SIMULATED_TEST_TRUST
def test_stale_epoch_in_signed_policy_envelope_is_rejected(f6, monkeypatch):
  context, boot = _begin(f6)
  original = f6.adapter.policy_for_boot(boot)
  payload = copy.deepcopy(original["payload"])
  payload["policy"]["epoch"] -= 1
  stale = _sign(f6.authority_key, POLICY_DOMAIN, payload)
  monkeypatch.setattr(f6.adapter, "policy_for_boot", lambda _boot: stale)
  with pytest.raises(BoundaryError, match="stale|mismatched|candidate"):
    f6.qualifier.qualify(context, boot, f6.ids["current"], f6.provenance)
  assert f6.adapter.protected_counters() == (1, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_health_before_consumed_trial_is_rejected(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  health = sign_health(f6.health_key, grant, "7" * 64)
  with pytest.raises(BoundaryError, match="consumed"):
    f6.adapter.record_health(grant, health)


@pytest.mark.SIMULATED_TEST_TRUST
def test_separate_authenticated_health_receipt_and_replay_rejection(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  consumed = f6.adapter.consume_authorization(grant)
  health = sign_health(f6.health_key, grant, "8" * 64)
  receipt = f6.adapter.record_health(grant, health)
  payload = verify_envelope(receipt, HEALTH_RECEIPT_DOMAIN, f6.authority_public)
  assert payload["consume_sequence"] == consumed.consume_sequence
  assert payload["boot_nonce"] == grant["payload"]["boot_nonce"]
  assert payload["snapshot_fingerprint"] == f6.provenance.snapshot_fingerprint
  with pytest.raises(BoundaryError, match="replay"):
    f6.adapter.record_health(grant, health)


@pytest.mark.SIMULATED_TEST_TRUST
def test_forged_health_signature_is_rejected(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  f6.adapter.consume_authorization(grant)
  forged = sign_health(Ed25519PrivateKey.generate(), grant, "9" * 64)
  with pytest.raises(BoundaryError, match="public key identity mismatch|authentication"):
    f6.adapter.record_health(grant, forged)


@pytest.mark.SIMULATED_TEST_TRUST
def test_health_for_other_snapshot_is_rejected(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  f6.adapter.consume_authorization(grant)
  payload = health_payload(grant, "a" * 64)
  payload["snapshot_fingerprint"] = "b" * 64
  wrong = _sign(f6.health_key, HEALTH_DOMAIN, payload)
  with pytest.raises(BoundaryError, match="stale or mismatched"):
    f6.adapter.record_health(grant, wrong)


@pytest.mark.SIMULATED_TEST_TRUST
def test_replay_of_consumed_grant_is_rejected_monotonically(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  first = f6.adapter.consume_authorization(grant)
  assert first.consume_sequence == 1
  with pytest.raises(BoundaryError, match="replay"):
    f6.adapter.consume_authorization(grant)
  assert f6.adapter.protected_counters() == (1, 1)


@pytest.mark.SIMULATED_TEST_TRUST
def test_package_change_after_consume_fails_but_does_not_refund(f6):
  version = f6.app / "slots" / f6.slots["current"] / "version.txt"
  original = version.read_bytes()

  def mutate():
    version.write_bytes(b"X" * len(original))

  context, boot = _begin(f6)
  qualifier = ImmutableSnapshotQualifier(
    f6.app, f6.adapter, f6.caller, AUTHORITY_ID, f6.authority_public,
    faults=BoundaryFaults(action_at={"after_consume": mutate}),
  )
  with pytest.raises(Exception, match="hash mismatch|changed"):
    qualifier.qualify(context, boot, f6.ids["current"], f6.provenance)
  assert f6.adapter.protected_counters() == (1, 1)


@pytest.mark.SIMULATED_TEST_TRUST
def test_other_valid_signed_package_is_not_authority_selected(f6):
  context, boot = _begin(f6)
  with pytest.raises(BoundaryError, match="authority-selected"):
    f6.qualifier.qualify(context, boot, f6.ids["old"], f6.provenance)
  assert f6.adapter.protected_counters() == (1, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_forged_boot_signature_is_rejected(f6):
  context, boot = _begin(f6)
  boot["signature"] = base64.b64encode(b"x" * 64).decode()
  with pytest.raises(BoundaryError, match="authentication"):
    f6.qualifier.qualify(context, boot, f6.ids["current"], f6.provenance)


@pytest.mark.SIMULATED_TEST_TRUST
def test_wrong_caller_identity_cannot_begin_boot(f6):
  attacker = CallerIdentity("attacker", "c" * 64)
  with pytest.raises(BoundaryError, match="caller"):
    f6.adapter.begin_boot(attacker, "d" * 64)
  assert f6.adapter.protected_counters() == (0, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_writable_or_unverified_snapshot_claims_fail_closed(f6):
  context, boot = _begin(f6)
  for forged in (
      replace(f6.provenance, read_only=False),
      replace(f6.provenance, verity_verified=False),
      replace(f6.provenance, filesystem_type="ext4")):
    with pytest.raises(BoundaryError, match="provenance"):
      f6.qualifier.qualify(context, boot, f6.ids["current"], forged)


@pytest.mark.SIMULATED_TEST_TRUST
def test_app_writable_state_cannot_authorize_or_refund(f6):
  fake = f6.app / "f6_authority_state.json"
  fake.write_text(json.dumps({"authorize": True, "consume_sequence": 0, "boot_nonce": "0" * 64}))
  context, boot = _begin(f6)
  with f6.qualifier.qualify(context, boot, f6.ids["current"], f6.provenance):
    pass
  fake.write_text(json.dumps({"authorize": True, "consume_sequence": 0, "boot_nonce": "e" * 64}))
  assert f6.adapter.protected_counters() == (1, 1)


@pytest.mark.SIMULATED_TEST_TRUST
@pytest.mark.parametrize("number", [errno.ENOSPC, errno.EIO, errno.EROFS])
def test_authority_storage_faults_fail_closed_without_boot_grant(f6, number):
  f6.adapter.faults = BoundaryFaults(oserror_at={"authority_write": number})
  with pytest.raises(OSError) as raised:
    f6.adapter.begin_boot(f6.caller, "f" * 64)
  assert raised.value.errno == number
  restarted = MockEarlyBootAdapter(f6.protected, f6.authority_key)
  assert restarted.protected_counters() == (0, 0)


@pytest.mark.SIMULATED_TEST_TRUST
def test_power_loss_before_begin_boot_commit_does_not_create_context(f6):
  f6.adapter.faults = BoundaryFaults(crash_at="begin_boot_precommit")
  with pytest.raises(SimulatedBoundaryPowerLoss):
    f6.adapter.begin_boot(f6.caller, "1" * 64)
  restarted = MockEarlyBootAdapter(f6.protected, f6.authority_key)
  assert restarted.protected_counters() == (0, 0)
  assert restarted.begin_boot(f6.caller, "1" * 64)["payload"]["boot_counter"] == 1


@pytest.mark.SIMULATED_TEST_TRUST
def test_power_loss_after_begin_boot_commit_burns_nonce(f6):
  f6.adapter.faults = BoundaryFaults(crash_at="begin_boot_committed")
  with pytest.raises(SimulatedBoundaryPowerLoss):
    f6.adapter.begin_boot(f6.caller, "2" * 64)
  restarted = MockEarlyBootAdapter(f6.protected, f6.authority_key)
  assert restarted.protected_counters() == (1, 0)
  with pytest.raises(BoundaryError, match="nonce replay"):
    restarted.begin_boot(f6.caller, "2" * 64)


@pytest.mark.SIMULATED_TEST_TRUST
def test_power_loss_before_consume_commit_does_not_claim_consumed(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  f6.adapter.faults = BoundaryFaults(crash_at="consume_precommit")
  with pytest.raises(SimulatedBoundaryPowerLoss):
    f6.adapter.consume_authorization(grant)
  restarted = MockEarlyBootAdapter(f6.protected, f6.authority_key)
  assert restarted.protected_counters() == (1, 0)
  assert restarted.consume_authorization(grant).consume_sequence == 1


@pytest.mark.SIMULATED_TEST_TRUST
def test_power_loss_after_consume_commit_cannot_refund_or_replay(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  f6.adapter.faults = BoundaryFaults(crash_at="consume_committed")
  with pytest.raises(SimulatedBoundaryPowerLoss):
    f6.adapter.consume_authorization(grant)
  restarted = MockEarlyBootAdapter(f6.protected, f6.authority_key)
  assert restarted.protected_counters() == (1, 1)
  with pytest.raises(BoundaryError, match="replay"):
    restarted.consume_authorization(grant)


@pytest.mark.SIMULATED_TEST_TRUST
def test_missing_mock_protected_state_fails_closed(f6):
  os.unlink(f6.protected / "mock_f6_state.json")
  with pytest.raises(BoundaryError, match="missing, corrupt, or unreadable"):
    MockEarlyBootAdapter(f6.protected, f6.authority_key)


@pytest.mark.SIMULATED_TEST_TRUST
def test_corrupt_mock_protected_state_fails_closed(f6):
  (f6.protected / "mock_f6_state.json").write_text("{not-json")
  with pytest.raises(BoundaryError, match="missing, corrupt, or unreadable"):
    MockEarlyBootAdapter(f6.protected, f6.authority_key)


@pytest.mark.SIMULATED_TEST_TRUST
def test_mock_authority_inside_application_tree_is_rejected(f6):
  nested = f6.app / "fake_trust"
  adapter = MockEarlyBootAdapter.create(
    nested, authority_id=AUTHORITY_ID, caller=f6.caller, authorized_os_slot="a",
    policy=f6.policy, candidate=f6.ids["current"], provenance=f6.provenance,
    authority_private_key=Ed25519PrivateKey.generate(),
    health_pubkey_b64=_public_b64(Ed25519PrivateKey.generate()),
  )
  with pytest.raises(BoundaryError, match="outside"):
    ImmutableSnapshotQualifier(
      f6.app, adapter, f6.caller, AUTHORITY_ID, adapter._load()["authority_pubkey_b64"])


@pytest.mark.SIMULATED_TEST_TRUST
def test_consume_receipt_signature_and_sequence_are_bound(f6):
  _context, _boot, grant = _grant_without_consume(f6)
  consumed = f6.adapter.consume_authorization(grant)
  receipt = verify_envelope(consumed.consume_receipt, CONSUME_DOMAIN, f6.authority_public)
  assert receipt["grant_id"] == grant["payload"]["grant_id"]
  assert receipt["consume_sequence"] == 1
  forged = copy.deepcopy(consumed.consume_receipt)
  forged["payload"]["consume_sequence"] = 0
  with pytest.raises(BoundaryError, match="authentication"):
    verify_envelope(forged, CONSUME_DOMAIN, f6.authority_public)

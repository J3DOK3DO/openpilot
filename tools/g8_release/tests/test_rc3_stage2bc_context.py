"""NON-DEPLOYABLE Stage 2B/C test-only full-context signature specimens."""
from __future__ import annotations

import ast
import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import rc3_stage2bc_context as bc

pytestmark = pytest.mark.SIMULATED_TEST_TRUST


def fixture_data():
  private = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
  pub = private.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  context = {
    "schema": bc.SCHEMA, "trust": bc.TRUST, "platform": bc.PLATFORM,
    "agnos": "19.8.1", "os_slot": "OS_A", "os_boot_nonce": "1"*64,
    "os_boot_sequence": 101, "rootfs_sha256": "2"*64,
    "comma_identity_sha256": "3"*64, "panda_identity_sha256": "4"*64,
    "source_commit": "7"*40, "manifest_sha256": "5"*64,
    "app_snapshot_sha256": "6"*64, "recovery_snapshot_sha256": "8"*64,
    "gate_receipt_sha256": "9"*64, "attempt_nonce": "a"*64,
    "attempt_number": 1, "monotonic_epoch": 9,
    "neutral_can": True, "physical_gate_observed": False,
    "operation": "HOST_MODEL_CONTEXT_ONLY",
  }
  return private, pub, context


def sign(context, private=None, pub=None):
  if private is None or pub is None:
    private, pub, _ = fixture_data()
  envelope = {
    "schema": bc.SCHEMA, "trust": bc.TRUST,
    "key_id": hashlib.sha256(pub).hexdigest()[:16],
    "context": copy.deepcopy(context),
    "signature": base64.b64encode(private.sign(bc.DOMAIN + bc._canonical(context))).decode(),
  }
  return bc._canonical(envelope)


def verify(blob=None, context=None, pub=None, floor=8):
  k, pk, sample = fixture_data()
  sample = context or sample
  return bc.verify_signed_test_context(
    blob if blob is not None else sign(sample, k, pk),
    expected_context=sample, pinned_test_public_key=pub if pub is not None else pk,
    protected_epoch_floor=floor)


def test_strict_signed_full_context_host_model_never_authorizes():
  result = verify()
  assert result.signature_matched_pinned_test_key is True
  assert result.monotonic_epoch == 9
  assert result.source_commit == "7"*40
  assert all(getattr(result, field) is False for field in (
    "trusted_hardware_root_proven", "hardware_antirollback_proven",
    "protected_journal_proven", "physical_honda_can_qualified",
    "installation_authorized", "boot_slot_change_authorized",
    "panda_can_actuation_authorized", "road_use_authorized"))


@pytest.mark.parametrize(("field", "value"), [
  ("platform", "TOYOTA"), ("os_slot", "OS_C"), ("os_slot", 1),
  ("source_commit", "0"*40), ("manifest_sha256", "0"*64),
  ("app_snapshot_sha256", "0"*64), ("recovery_snapshot_sha256", "0"*64),
  ("gate_receipt_sha256", "0"*64), ("os_boot_nonce", "0"*64),
  ("os_boot_sequence", 102), ("rootfs_sha256", "0"*64),
  ("comma_identity_sha256", "0"*64), ("panda_identity_sha256", "0"*64),
  ("attempt_number", 2), ("attempt_nonce", "0"*64), ("monotonic_epoch", 10),
  ("agnos", "19.9.0"), ("physical_gate_observed", True),
  ("neutral_can", False), ("operation", "START_PANDAD"),
  ("trust", "REAL_PRODUCTION_APPROVAL"),
])
def test_every_full_context_change_causes_rejection(field, value):
  k, pub, expected = fixture_data()
  changed = copy.deepcopy(expected)
  changed[field] = value
  # Correctly re-signed by test key, but not equal to pinned expected context.
  with pytest.raises(bc.ContextVerificationError):
    bc.verify_signed_test_context(
      sign(changed,k,pub), expected_context=expected,
      pinned_test_public_key=pub, protected_epoch_floor=8)


@pytest.mark.parametrize("change", ["signature", "key_id", "schema", "trust", "extra", "missing"])
def test_signature_identity_and_envelope_schema_rejected(change):
  k,pub,context=fixture_data()
  e=json.loads(sign(context,k,pub))
  if change=="signature":e["signature"]=base64.b64encode(b"0"*64).decode()
  if change=="key_id":e["key_id"]="b"*16
  if change=="schema":e["schema"]="UNKNOWN"
  if change=="trust":e["trust"]="REAL_HARDWARE"
  if change=="extra":e["untrusted_override"]=True
  if change=="missing":e.pop("signature")
  with pytest.raises(bc.ContextVerificationError):
    verify(bc._canonical(e))


@pytest.mark.parametrize(("text"), [
  '{"a":1,"a":1}',
  '{"a":NaN}',
  '{"a":1e0}',
  '{ "a": 1 }',
  '{"a": 1}\n',
])
def test_noncanonical_duplicate_invalid_json_rejected(text):
  with pytest.raises(bc.ContextVerificationError):
    bc.strict_json_decode(text.encode())


@pytest.mark.parametrize("floor", [9, 10, 100, -1, True, 1.3])
def test_untrusted_or_stale_monotonic_floor_fails(floor):
  with pytest.raises(bc.ContextVerificationError):
    verify(floor=floor)


@pytest.mark.parametrize("field", ["source_commit","rootfs_sha256","manifest_sha256","attempt_nonce"])
def test_malformed_digest_rejected_before_signature(field):
  k,pub,expected=fixture_data()
  wrong=copy.deepcopy(expected);wrong[field]="not_hex"
  with pytest.raises(bc.ContextVerificationError):
    bc.verify_signed_test_context(
      sign(wrong,k,pub),expected_context=wrong,pinned_test_public_key=pub,
      protected_epoch_floor=8)


def test_test_key_substitution_cannot_verify():
  k,pub,context=fixture_data()
  other=Ed25519PrivateKey.from_private_bytes(b"Z"*32)
  other_pub=other.public_key().public_bytes(
    serialization.Encoding.Raw,serialization.PublicFormat.Raw)
  with pytest.raises(bc.ContextVerificationError):
    verify(sign(context,k,pub),pub=other_pub)


def test_model_contract_denies_every_runtime_action():
  r=bc.integration_constraints()
  assert r["production_install"] is False
  assert r["boot_slot_switch"] is False
  assert r["panda_can"] is False
  assert r["road_use"] is False
  assert r["os_resident_service_installed"] is False
  assert r["root_of_trust_provisioned"] is False


def test_verifier_has_no_signing_or_device_action_surface():
  path=Path(bc.__file__)
  source=path.read_text()
  tree=ast.parse(source)
  imported={alias.name for node in ast.walk(tree)
            if isinstance(node,(ast.Import,ast.ImportFrom)) for alias in node.names}
  assert not ({"subprocess","socket","requests","can","panda","shutil","fcntl"} & imported)
  assert "Ed25519PrivateKey" not in source
  assert not any(x in source for x in ("abctl", "systemctl", "ExecStart=", "Popen("))

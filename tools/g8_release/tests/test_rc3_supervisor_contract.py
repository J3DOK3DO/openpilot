"""Invariant tests for the non-deployable RC3 OS supervisor design model."""
from __future__ import annotations

import ast
import base64
import hashlib
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import rc3_supervisor_contract as contract
from g8_protected_authority import (
  HEALTH_DOMAIN,
  INTENT_DOMAIN,
  CandidateIdentity,
  MockProtectedAuthority,
  SIMULATED_TRUST_LABEL,
  canonical,
  health_payload,
  trial_intent_payload,
)


pytestmark = pytest.mark.SIMULATED_TEST_TRUST
COMMIT = "9" * 40


def _raw(private_key):
  return private_key.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _b64(private_key):
  return base64.b64encode(_raw(private_key)).decode("ascii")


def _key_id(private_key):
  return hashlib.sha256(_raw(private_key)).hexdigest()[:16]


def _envelope(private_key, domain, payload):
  return {
    "alg": "ed25519",
    "key_id": _key_id(private_key),
    "payload": payload,
    "signature": base64.b64encode(private_key.sign(domain + canonical(payload))).decode("ascii"),
    "trust": SIMULATED_TRUST_LABEL,
  }


@pytest.fixture
def model_env(tmp_path):
  release_key = Ed25519PrivateKey.generate()
  decision_key = Ed25519PrivateKey.generate()
  health_key = Ed25519PrivateKey.generate()
  signing_key = {
    "key_id": _key_id(release_key), "pubkey_b64": _b64(release_key), "purpose": "production",
  }
  recovery = CandidateIdentity("000001-aaaaaaaaaaaa", "a" * 64, COMMIT, 10, _key_id(release_key))
  candidate = CandidateIdentity("000002-bbbbbbbbbbbb", "b" * 64, COMMIT, 11, _key_id(release_key))
  app = tmp_path / "writable-app"
  app.mkdir()
  authority = MockProtectedAuthority.create(
    tmp_path / "mock-protected-authority", recovery=recovery, expected_commit=COMMIT,
    minimum_release_sequence=10, signing_keys=[signing_key],
    decision_pubkey_b64=_b64(decision_key), health_pubkey_b64=_b64(health_key))
  model = contract.NonDeployableSupervisorModel(authority, app)
  return type("ModelEnvironment", (), {
    "model": model, "authority": authority, "candidate": candidate,
    "decision_key": decision_key, "health_key": health_key, "app": app,
  })()


def _authorize(env, attempts=2):
  payload = trial_intent_payload(env.authority.policy_snapshot(), env.candidate, attempts)
  return env.model.authorize_trial(
    env.candidate, attempts, _envelope(env.decision_key, INTENT_DOMAIN, payload))


def test_complete_model_lifecycle_is_observation_only(model_env):
  ticket = _authorize(model_env)
  after_authorize = model_env.model.snapshot()
  assert after_authorize["state"] == "TRIAL_AUTHORIZED"
  decision = model_env.model.consume_attempt_before_observation()
  assert decision.disposition == "trial-observation-only"
  assert decision.observe_only is True
  assert decision.actuation_authorized is False
  assert decision.installation_authorized is False
  assert not hasattr(decision, "launcher_path")
  model_env.model.observe_startup(True)
  receipt = model_env.model.attest_health(_envelope(
    model_env.health_key, HEALTH_DOMAIN, health_payload(ticket, "c" * 64)))
  assert receipt.candidate == model_env.candidate
  assert model_env.model.snapshot()["state"] == "HEALTH_ATTESTED"
  promoted = model_env.model.promote_model_only()
  assert promoted.recovery == model_env.candidate
  result = model_env.model.snapshot()
  assert result["state"] == "PROMOTED_MODEL_ONLY"
  assert result["installation_authorized"] is False
  assert result["boot_operations_authorized"] is False
  assert result["actuation_authorized"] is False
  assert result["production_approved"] is False


def test_health_and_promotion_cannot_happen_early(model_env):
  ticket = _authorize(model_env)
  health = _envelope(model_env.health_key, HEALTH_DOMAIN, health_payload(ticket, "c" * 64))
  with pytest.raises(contract.ContractError, match="before complete startup"):
    model_env.model.attest_health(health)
  with pytest.raises(contract.ContractError, match="promotion requires"):
    model_env.model.promote_model_only()
  assert model_env.model.snapshot()["state"] == "TRIAL_AUTHORIZED"


def test_attempt_is_consumed_before_any_startup_observation(model_env):
  _authorize(model_env)
  with pytest.raises(contract.ContractError, match="after durable attempt"):
    model_env.model.observe_startup(True)
  assert model_env.authority.protected_attempts() == (0, 2)
  model_env.model.consume_attempt_before_observation()
  assert model_env.authority.protected_attempts() == (1, 2)
  assert model_env.model.snapshot()["attempts_consumed"] == 1


def test_failed_startup_cancels_trial_and_rolls_back(model_env):
  _authorize(model_env)
  model_env.model.consume_attempt_before_observation()
  model_env.model.observe_startup(False)
  result = model_env.model.snapshot()
  assert result["state"] == "ROLLED_BACK"
  assert result["trial"] is None
  assert result["health_authenticated"] is False
  assert result["recovery"]["release_sequence"] == 10
  assert model_env.authority.protected_attempts() == (0, 0)


@pytest.mark.parametrize("stage", ["authorized", "consumed", "probation", "attested"])
def test_restart_never_infers_health_and_rolls_back_inflight_trial(model_env, stage):
  ticket = _authorize(model_env)
  if stage in {"consumed", "probation", "attested"}:
    model_env.model.consume_attempt_before_observation()
  if stage in {"probation", "attested"}:
    model_env.model.observe_startup(True)
  if stage == "attested":
    model_env.model.attest_health(_envelope(
      model_env.health_key, HEALTH_DOMAIN, health_payload(ticket, "d" * 64)))
  model_env.model.recover_after_restart()
  result = model_env.model.snapshot()
  assert result["state"] == "ROLLED_BACK"
  assert result["health_authenticated"] is False
  assert result["installation_authorized"] is False


def test_wrong_commit_and_rollback_sequence_fail_before_authority(model_env):
  wrong_commit = CandidateIdentity(
    "000003-cccccccccccc", "c" * 64, "8" * 40, 11, model_env.candidate.signing_key_id)
  stale = CandidateIdentity(
    "000004-dddddddddddd", "d" * 64, COMMIT, 9, model_env.candidate.signing_key_id)
  for candidate in (wrong_commit, stale):
    with pytest.raises(contract.ContractError, match="violates protected"):
      model_env.model.authorize_trial(candidate, 1, {})
  assert model_env.authority.protected_attempts() == (0, 0)


def test_bad_health_signature_enters_inspectable_hold_without_authorizing(model_env):
  ticket = _authorize(model_env)
  model_env.model.consume_attempt_before_observation()
  model_env.model.observe_startup(True)
  bad_health = _envelope(
    model_env.health_key, HEALTH_DOMAIN, health_payload(ticket, "c" * 64))
  bad_health["signature"] = base64.b64encode(b"x" * 64).decode("ascii")
  with pytest.raises(contract.ContractError, match="HEALTH_AUTHENTICATION_FAILED_HOLD"):
    model_env.model.attest_health(bad_health)
  result = model_env.model.snapshot()
  assert result["state"] == "HOLD"
  assert result["installation_authorized"] is False
  assert result["boot_operations_authorized"] is False
  assert result["actuation_authorized"] is False


def test_authority_inside_writable_application_is_rejected(tmp_path):
  release = Ed25519PrivateKey.generate()
  decision = Ed25519PrivateKey.generate()
  health = Ed25519PrivateKey.generate()
  key = {"key_id": _key_id(release), "pubkey_b64": _b64(release), "purpose": "production"}
  recovery = CandidateIdentity("000001-aaaaaaaaaaaa", "a" * 64, COMMIT, 1, key["key_id"])
  app = tmp_path / "app"
  app.mkdir()
  authority = MockProtectedAuthority.create(
    app / "attacker-controlled-authority", recovery=recovery, expected_commit=COMMIT,
    minimum_release_sequence=1, signing_keys=[key], decision_pubkey_b64=_b64(decision),
    health_pubkey_b64=_b64(health))
  with pytest.raises(contract.ContractError, match="outside writable"):
    contract.NonDeployableSupervisorModel(authority, app)


def test_design_contract_is_not_an_installable_unit_or_executable():
  design = contract.SYSTEMD_DESIGN_CONTRACT
  assert design["classification"] == "NON_DEPLOYABLE_DESIGN_ONLY"
  assert design["unit_file_emitted"] is False
  assert design["executable_implemented"] is False
  assert design["installation_authorized"] is False
  assert design["boot_operations_authorized"] is False
  assert design["actuation_authorized"] is False
  assert design["required_placement"]["forbidden_writable_prefix"] == "/data/openpilot/"
  assert "execute-application" in design["forbidden_actions"]
  assert "open-panda" in design["forbidden_actions"]


def test_model_source_has_no_execution_device_network_or_install_surface():
  source_path = Path(__file__).resolve().parents[1] / "rc3_supervisor_contract.py"
  source = source_path.read_text()
  tree = ast.parse(source)
  imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
              for alias in node.names}
  assert not ({"subprocess", "socket", "can", "panda", "shutil"} & imported)
  assert "ExecStart=" not in source
  assert "abctl" not in source
  assert "os.system" not in source
  assert "Popen" not in source

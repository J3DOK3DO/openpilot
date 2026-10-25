"""Adversarial tests for the NON-DEPLOYABLE Stage 2 supervisor prototype."""
from __future__ import annotations

import ast
import base64
import copy
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import rc3_hardware_readiness_gate as hardware_gate
import rc3_stage2_supervisor as stage2
from g8_protected_authority import (
  HEALTH_DOMAIN,
  INTENT_DOMAIN,
  BootGrant,
  CandidateIdentity,
  MockProtectedAuthority,
  canonical,
  health_payload,
  trial_intent_payload,
)


COMMIT = "7" * 40
pytestmark = pytest.mark.SIMULATED_TEST_TRUST


def _raw_public(private: Ed25519PrivateKey) -> bytes:
  return private.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _b64_public(private: Ed25519PrivateKey) -> str:
  return base64.b64encode(_raw_public(private)).decode("ascii")


def _key_id(private: Ed25519PrivateKey) -> str:
  return hashlib.sha256(_raw_public(private)).hexdigest()[:16]


def _authority_envelope(private: Ed25519PrivateKey, domain: bytes, payload: dict) -> dict:
  return {
    "alg": "ed25519", "key_id": _key_id(private), "payload": payload,
    "signature": base64.b64encode(private.sign(domain + canonical(payload))).decode("ascii"),
    "trust": "SIMULATED_TEST_TRUST",
  }


def _jsonable(value):
  return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":")))


class SignedMockDecisionProvider:
  """Public-key verifier only; test code outside the controller owns the signer."""

  DOMAIN = b"g8-f12-rc3/stage2-external-mock/v1\x00"

  def __init__(self, public_key: bytes):
    self.public_key = public_key

  @staticmethod
  def payload(kind: str, binding, result: dict) -> dict:
    return {"kind": kind, "binding": _jsonable(asdict(binding)), "result": _jsonable(result)}

  @classmethod
  def sign(cls, private: Ed25519PrivateKey, kind: str, binding, result: dict) -> dict:
    payload = cls.payload(kind, binding, result)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    return {"payload": payload,
            "signature": base64.b64encode(private.sign(cls.DOMAIN + encoded)).decode("ascii")}

  def _verify(self, envelope: dict, kind: str, binding) -> dict:
    if type(envelope) is not dict or set(envelope) != {"payload", "signature"}:
      raise ValueError("malformed external decision envelope")
    payload = envelope["payload"]
    if (type(payload) is not dict or set(payload) != {"kind", "binding", "result"} or
        payload["kind"] != kind or payload["binding"] != _jsonable(asdict(binding))):
      raise ValueError("external decision binding mismatch")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    try:
      signature = base64.b64decode(envelope["signature"], validate=True)
      from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
      Ed25519PublicKey.from_public_bytes(self.public_key).verify(
        signature, self.DOMAIN + encoded)
    except (InvalidSignature, TypeError, ValueError) as error:
      raise ValueError("external decision signature mismatch") from error
    return copy.deepcopy(payload["result"])

  @staticmethod
  def _recovery(result: dict) -> stage2.RecoveryApproval:
    return stage2.RecoveryApproval(
      candidate=CandidateIdentity.from_dict(result["candidate"]),
      os_slot=stage2.OsSlot(result["os_slot"]),
      rootfs_measurement=result["rootfs_measurement"],
      device=stage2.DeviceIdentity(**result["device"]),
      immutable_snapshot_sha256=result["immutable_snapshot_sha256"],
      approval_id=result["approval_id"], approval_sequence=result["approval_sequence"],
      authenticated=result["authenticated"])

  def verify_recovery(self, envelope, expected):
    return self._recovery(self._verify(envelope, "recovery", expected))

  def verify_physical_gate(self, envelope, expected):
    result = self._verify(envelope, "gate", expected)
    return stage2.PhysicalGateDecision(
      candidate=CandidateIdentity.from_dict(result.pop("candidate")),
      os_boot=stage2.OsBootIdentity(
        slot=stage2.OsSlot(result["os_boot"].pop("slot")), **result.pop("os_boot")),
      device=stage2.DeviceIdentity(**result.pop("device")), **result)

  def verify_health(self, envelope, expected):
    result = self._verify(envelope, "health", expected)
    return stage2.HealthDecision(
      candidate=CandidateIdentity.from_dict(result.pop("candidate")),
      os_boot=stage2.OsBootIdentity(
        slot=stage2.OsSlot(result["os_boot"].pop("slot")), **result.pop("os_boot")),
      device=stage2.DeviceIdentity(**result.pop("device")), **result)

  def verify_promotion(self, envelope, expected):
    return self._recovery(self._verify(envelope, "promotion", expected))


class Env:
  pass


@pytest.fixture
def env(tmp_path):
  material = Env()
  material.release_key = Ed25519PrivateKey.generate()
  material.intent_key = Ed25519PrivateKey.generate()
  material.health_key = Ed25519PrivateKey.generate()
  material.external_key = Ed25519PrivateKey.generate()
  material.provider = SignedMockDecisionProvider(_raw_public(material.external_key))
  release = {
    "key_id": _key_id(material.release_key), "pubkey_b64": _b64_public(material.release_key),
    "purpose": "production",
  }
  material.recovery = CandidateIdentity(
    "000001-aaaaaaaaaaaa", "a" * 64, COMMIT, 10, release["key_id"])
  material.candidate = CandidateIdentity(
    "000002-bbbbbbbbbbbb", "b" * 64, COMMIT, 11, release["key_id"])
  material.app = tmp_path / "writable-app"
  material.app.mkdir()
  material.authority = MockProtectedAuthority.create(
    tmp_path / "protected-authority", recovery=material.recovery,
    expected_commit=COMMIT, minimum_release_sequence=10, signing_keys=[release],
    decision_pubkey_b64=_b64_public(material.intent_key),
    health_pubkey_b64=_b64_public(material.health_key))
  material.state_root = tmp_path / "stage2-journal"
  material.os_boot = stage2.OsBootIdentity(
    stage2.OsSlot.A, "1" * 64, 100, "2" * 64, "agnos-19.8.1")
  material.device = stage2.DeviceIdentity(stage2.PLATFORM, "3" * 64, "4" * 64)
  material.policy = stage2.SupervisorPolicy(2, COMMIT)
  material.recovery_expectation = stage2.RecoveryExpectation(
    material.recovery, material.os_boot.slot, material.os_boot.rootfs_measurement,
    material.device)
  material.recovery_approval = stage2.RecoveryApproval(
    material.recovery, material.os_boot.slot, material.os_boot.rootfs_measurement,
    material.device, "5" * 64, "recovery-approval-1", 1, True)
  material.recovery_envelope = material.provider.sign(
    material.external_key, "recovery", material.recovery_expectation,
    asdict(material.recovery_approval))

  def controller(*, faults=None, policy=None, os_boot=None, state_root=None, authority=None,
                 recovery_envelope=None):
    return stage2.Stage2Supervisor(
      authority=authority or material.authority, decisions=material.provider,
      state_root=state_root or material.state_root, writable_app_root=material.app,
      os_boot=os_boot or material.os_boot, device=material.device,
      policy=policy or material.policy,
      recovery_envelope=recovery_envelope or material.recovery_envelope, faults=faults)

  material.controller = controller
  material.supervisor = controller()
  return material


def _gate_material(material, *, candidate=None, gate_nonce="6" * 64, gate_sequence=1,
                   owner="7" * 64, mutate=None):
  candidate = candidate or material.candidate
  expected = stage2.GateExpectation(
    candidate, material.supervisor.os_boot, material.device, gate_nonce, gate_sequence,
    owner, True)
  decision = stage2.PhysicalGateDecision(
    candidate, material.supervisor.os_boot, material.device, gate_nonce, gate_sequence,
    owner, "8" * 64, "PHYSICAL_GATE_PASSED_FOR_HOST_MODEL_ONLY",
    "PHYSICAL_DEVICE_EVIDENCE", True, True, True)
  result = asdict(decision)
  if mutate is not None:
    mutate(result)
  envelope = material.provider.sign(material.external_key, "gate", expected, result)
  return expected, envelope


def _intent(material, candidate=None, attempts=None):
  candidate = candidate or material.candidate
  attempts = attempts or material.supervisor.policy.max_attempts
  payload = trial_intent_payload(material.authority.policy_snapshot(), candidate, attempts)
  return _authority_envelope(material.intent_key, INTENT_DOMAIN, payload)


def _authorize(material, *, gate_sequence=1, gate_nonce="6" * 64,
               owner="7" * 64, request="9" * 64, candidate=None, mutate=None):
  candidate = candidate or material.candidate
  _, gate_envelope = _gate_material(
    material, candidate=candidate, gate_sequence=gate_sequence, gate_nonce=gate_nonce,
    owner=owner, mutate=mutate)
  ticket = material.supervisor.authorize_trial(
    candidate, gate_envelope=gate_envelope, intent_envelope=_intent(material, candidate),
    gate_nonce=gate_nonce, gate_sequence=gate_sequence,
    owner_approval_sha256=owner, start_request_id=request)
  return ticket


def _health_material(material, ticket, *, owner="7" * 64, mutate=None):
  state = material.supervisor.snapshot()
  assert state["phase"] == stage2.Phase.PROBATION.value
  expected = stage2.HealthExpectation(
    material.candidate, material.supervisor.os_boot, material.device, "6" * 64, 1,
    "a" * 64, 1, owner)
  decision = stage2.HealthDecision(
    material.candidate, material.supervisor.os_boot, material.device, "6" * 64, 1,
    "a" * 64, 1, owner, "d" * 64, "HEALTHY", True, True)
  result = asdict(decision)
  if mutate is not None:
    mutate(result)
  external = material.provider.sign(material.external_key, "health", expected, result)
  protected = _authority_envelope(
    material.health_key, HEALTH_DOMAIN, health_payload(ticket, "d" * 64))
  return external, protected


def _reach_probation(material):
  ticket = _authorize(material)
  decision = material.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert decision.physical_gate_passed is True
  assert decision.process_started is False
  material.supervisor.observe_startup(True)
  return ticket


def test_launcher_refuses_missing_or_invalid_physical_gate(env):
  with pytest.raises(stage2.Stage2Error, match="authorized retry-ready"):
    env.supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="a" * 64)
  _, envelope = _gate_material(env)
  envelope["signature"] = base64.b64encode(b"x" * 64).decode("ascii")
  with pytest.raises(stage2.Stage2Error, match="authentication failed"):
    env.supervisor.authorize_trial(
      env.candidate, gate_envelope=envelope, intent_envelope=_intent(env),
      gate_nonce="6" * 64, gate_sequence=1,
      owner_approval_sha256="7" * 64, start_request_id="9" * 64)
  assert env.supervisor.snapshot()["physical_gate_passed"] is False


def test_fake_owner_waiver_cannot_replace_physical_gate(env):
  def owner_only(result):
    result["physical_gate_passed"] = False
    result["disposition"] = "OWNER_WAIVER"

  with pytest.raises(stage2.Stage2Error, match="did not pass"):
    _authorize(env, mutate=owner_only)
  assert env.authority.protected_attempts() == (0, 0)


def test_invalid_grant_enters_hold_without_launcher_decision(env):
  class BadGrantAuthority:
    def __init__(self, delegate):
      self.delegate = delegate

    @property
    def trust_domain_path(self):
      return self.delegate.trust_domain_path

    def __getattr__(self, name):
      return getattr(self.delegate, name)

    def consume_attempt(self, trial, epoch, ticket):
      grant = self.delegate.consume_attempt(trial, epoch, ticket)
      return BootGrant("trial", grant.candidate, grant.attempts_consumed + 1,
                       grant.attempts_limit)

  root = env.state_root.parent / "bad-grant-journal"
  supervisor = env.controller(state_root=root, authority=BadGrantAuthority(env.authority))
  env.supervisor = supervisor
  _authorize(env)
  with pytest.raises(stage2.Stage2Error, match="grant binding"):
    supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value


def test_insecure_or_invalid_health_fails_closed(env):
  ticket = _reach_probation(env)
  external, protected = _health_material(
    env, ticket, mutate=lambda result: result.update(independent_attester=False))
  with pytest.raises(stage2.Stage2Error, match="independent healthy"):
    env.supervisor.attest_health(
      decision_envelope=external, authority_health_envelope=protected)
  result = env.supervisor.snapshot()
  assert result["phase"] == stage2.Phase.HOLD.value
  assert result["health_authenticated"] is False


def test_invalid_protected_health_signature_fails_closed(env):
  ticket = _reach_probation(env)
  external, protected = _health_material(env, ticket)
  protected["signature"] = base64.b64encode(b"z" * 64).decode("ascii")
  with pytest.raises(stage2.Stage2Error, match="protected health authority"):
    env.supervisor.attest_health(
      decision_envelope=external, authority_health_envelope=protected)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value


def test_power_interruption_after_consumption_rolls_back_without_refund_claim(env):
  _authorize(env)
  env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert env.authority.protected_attempts() == (1, 2)
  new_boot = stage2.OsBootIdentity(
    stage2.OsSlot.A, "f" * 64, 101, env.os_boot.rootfs_measurement, env.os_boot.agnos_version)
  env.supervisor.recover_after_power_interruption(new_boot)
  result = env.supervisor.snapshot()
  assert result["phase"] == stage2.Phase.ROLLED_BACK.value
  assert result["recovery"] == asdict(env.recovery)
  assert env.authority.protected_attempts() == (0, 0)


def test_crash_after_protected_consumption_is_reconciled_to_approved_recovery(env):
  env.supervisor.faults = stage2.Stage2Faults("after_authority_consume")
  _authorize(env)
  with pytest.raises(stage2.SimulatedPowerInterruption):
    env.supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert env.authority.protected_attempts() == (1, 2)
  reopened = env.controller()
  new_boot = stage2.OsBootIdentity(
    stage2.OsSlot.A, "f" * 64, 101, env.os_boot.rootfs_measurement, env.os_boot.agnos_version)
  reopened.recover_after_power_interruption(new_boot)
  assert reopened.snapshot()["phase"] == stage2.Phase.ROLLED_BACK.value
  assert env.authority.protected_attempts() == (0, 0)


def test_bounded_retry_then_maximum_attempts_rolls_back(env):
  _authorize(env)
  env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  env.supervisor.observe_startup(False)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.RETRY_READY.value
  env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="b" * 64)
  env.supervisor.observe_startup(False)
  result = env.supervisor.snapshot()
  assert result["phase"] == stage2.Phase.ROLLED_BACK.value
  assert result["recovery"] == asdict(env.recovery)
  with pytest.raises(stage2.Stage2Error, match="authorized retry-ready"):
    env.supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="c" * 64)


def test_stale_attempt_nonce_and_stale_gate_sequence_are_rejected(env):
  _authorize(env)
  env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  env.supervisor.observe_startup(False)
  with pytest.raises(stage2.Stage2Error, match="replayed attempt nonce"):
    env.supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="a" * 64)
  env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="b" * 64)
  env.supervisor.observe_startup(False)
  with pytest.raises(stage2.Stage2Error, match="gate sequence"):
    _authorize(env, gate_sequence=1, gate_nonce="c" * 64, request="d" * 64)


def test_idempotent_concurrent_double_start_returns_one_ticket(env):
  _, gate_envelope = _gate_material(env)
  intent = _intent(env)

  def start():
    return env.supervisor.authorize_trial(
      env.candidate, gate_envelope=gate_envelope, intent_envelope=intent,
      gate_nonce="6" * 64, gate_sequence=1,
      owner_approval_sha256="7" * 64, start_request_id="9" * 64)

  with ThreadPoolExecutor(max_workers=6) as pool:
    tickets = list(pool.map(lambda _: start(), range(12)))
  assert len({ticket.ticket_id for ticket in tickets}) == 1
  assert env.authority.protected_attempts() == (0, 2)
  with pytest.raises(stage2.Stage2Error, match="double start"):
    env.supervisor.authorize_trial(
      env.candidate, gate_envelope=gate_envelope, intent_envelope=intent,
      gate_nonce="6" * 64, gate_sequence=2,
      owner_approval_sha256="7" * 64, start_request_id="8" * 64)


def test_attempt_consumption_is_idempotent_only_for_exact_nonce(env):
  _authorize(env)
  first = env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  second = env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert first == second
  assert env.authority.protected_attempts() == (1, 2)
  with pytest.raises(stage2.Stage2Error, match="requires"):
    env.supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="b" * 64)


def test_os_slot_and_application_slot_types_cannot_be_confused(env):
  _, gate_envelope = _gate_material(env)
  with pytest.raises(stage2.Stage2Error, match="never an OS slot"):
    env.supervisor.authorize_trial(  # type: ignore[arg-type]
      env.os_boot, gate_envelope=gate_envelope, intent_envelope={},
      gate_nonce="6" * 64, gate_sequence=1,
      owner_approval_sha256="7" * 64, start_request_id="9" * 64)
  _authorize(env)
  changed_os = stage2.OsBootIdentity(
    stage2.OsSlot.B, "f" * 64, 101, env.os_boot.rootfs_measurement, env.os_boot.agnos_version)
  with pytest.raises(stage2.Stage2Error, match="cannot be treated as an app-slot"):
    env.supervisor.recover_after_power_interruption(changed_os)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value


def test_wrong_candidate_manifest_is_rejected_even_when_signed_by_mock_provider(env):
  def wrong_manifest(result):
    result["candidate"]["manifest_sha256"] = "0" * 64

  with pytest.raises(stage2.Stage2Error, match="binding mismatch"):
    _authorize(env, mutate=wrong_manifest)
  assert env.authority.protected_attempts() == (0, 0)


def test_wrong_source_is_rejected_before_external_or_protected_authority(env):
  wrong = CandidateIdentity(
    "000003-cccccccccccc", "c" * 64, "8" * 40, 12, env.candidate.signing_key_id)
  _, gate = _gate_material(env, candidate=wrong)
  with pytest.raises(stage2.Stage2Error, match="source"):
    env.supervisor.authorize_trial(
      wrong, gate_envelope=gate, intent_envelope={}, gate_nonce="6" * 64,
      gate_sequence=1, owner_approval_sha256="7" * 64, start_request_id="9" * 64)


def test_wrong_device_identity_in_gate_is_rejected(env):
  def wrong_device(result):
    result["device"]["comma_serial_sha256"] = "0" * 64

  with pytest.raises(stage2.Stage2Error, match="binding mismatch"):
    _authorize(env, mutate=wrong_device)


@pytest.mark.parametrize("policy", [
  stage2.SupervisorPolicy(0, COMMIT),
  stage2.SupervisorPolicy(4, COMMIT),
  stage2.SupervisorPolicy(1, COMMIT, require_physical_gate=False),
  stage2.SupervisorPolicy(1, COMMIT, neutral_can_required=False),
  stage2.SupervisorPolicy(1, "x" * 40),
])
def test_invalid_or_waivable_policy_is_rejected(env, policy):
  with pytest.raises(stage2.Stage2Error):
    env.controller(policy=policy, state_root=env.state_root.parent / hashlib.sha256(
      repr(policy).encode()).hexdigest()[:12])


def test_changing_owner_approval_between_gate_and_health_is_rejected(env):
  ticket = _reach_probation(env)
  external, protected = _health_material(env, ticket, owner="0" * 64)
  with pytest.raises(stage2.Stage2Error, match="authentication failed"):
    env.supervisor.attest_health(
      decision_envelope=external, authority_health_envelope=protected)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value


def test_tampered_journal_manifest_binding_fails_closed(env):
  _authorize(env)
  path = env.state_root / "stage2_state.json"
  state = json.loads(path.read_bytes())
  state["trial"]["manifest_sha256"] = "0" * 64
  path.write_bytes(stage2._canonical(state))
  with pytest.raises(stage2.Stage2Error, match="does not bind"):
    env.supervisor.snapshot()


def test_promotion_requires_separate_monotonic_immutable_recovery_approval(env):
  ticket = _reach_probation(env)
  external, protected = _health_material(env, ticket)
  receipt = env.supervisor.attest_health(
    decision_envelope=external, authority_health_envelope=protected)
  state = env.supervisor._load()
  health = env.supervisor._health_from_dict(state["health"])
  expected = stage2.PromotionExpectation(health, receipt, env.recovery_approval)
  stale = stage2.RecoveryApproval(
    env.candidate, env.os_boot.slot, env.os_boot.rootfs_measurement, env.device,
    "f" * 64, "candidate-recovery-approval", 1, True)
  stale_envelope = env.provider.sign(env.external_key, "promotion", expected, asdict(stale))
  with pytest.raises(stage2.Stage2Error, match="not monotonic"):
    env.supervisor.promote_model_only(stale_envelope)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value



def test_independent_and_protected_health_measurements_must_match(env):
  ticket = _reach_probation(env)
  external, _correct = _health_material(env, ticket)
  mismatch = _authority_envelope(
    env.health_key, HEALTH_DOMAIN, health_payload(ticket, "e" * 64))
  with pytest.raises(stage2.Stage2Error, match="measurements disagree"):
    env.supervisor.attest_health(
      decision_envelope=external, authority_health_envelope=mismatch)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value


def test_cached_launcher_decision_rechecks_revoked_protected_authority(env):
  ticket = _authorize(env)
  first = env.supervisor.consume_attempt_for_observation(
    start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert first.process_started is False
  env.authority.cancel_trial(env.candidate, ticket.epoch, ticket)
  with pytest.raises(stage2.Stage2Error, match="protected authority revoked"):
    env.supervisor.consume_attempt_for_observation(
      start_request_id="9" * 64, attempt_nonce="a" * 64)
  assert env.supervisor.snapshot()["phase"] == stage2.Phase.HOLD.value


def test_coordinated_os_and_gate_journal_tamper_rejected(env):
  _authorize(env)
  path = env.state_root / "stage2_state.json"
  state = json.loads(path.read_bytes())
  state["os_boot"]["boot_nonce"] = "b" * 64
  state["gate"]["os_boot"]["boot_nonce"] = "b" * 64
  path.write_bytes(stage2._canonical(state))
  with pytest.raises(stage2.Stage2Error, match="pinned source, OS, or device|pinned OS"):
    env.supervisor.snapshot()


def test_explicit_symlinked_state_root_refused(env):
  alias = env.state_root.parent / "sym-host-journal"
  alias.symlink_to(env.state_root, target_is_directory=True)
  with pytest.raises(stage2.Stage2Error, match="symlink"):
    env.controller(state_root=alias)


def test_successful_health_does_not_self_promote_or_authorize_install(env):
  ticket = _reach_probation(env)
  external, protected = _health_material(env, ticket)
  env.supervisor.attest_health(
    decision_envelope=external, authority_health_envelope=protected)
  result = env.supervisor.snapshot()
  assert result["phase"] == stage2.Phase.HEALTH_ATTESTED.value
  assert result["recovery"] == asdict(env.recovery)
  assert result["installation_authorized"] is False
  assert result["boot_operations_authorized"] is False
  assert result["panda_or_can_authorized"] is False
  assert result["production_approved"] is False


def test_recovery_approval_must_be_external_exact_and_immutable(env):
  bad = copy.deepcopy(env.recovery_envelope)
  bad["signature"] = base64.b64encode(b"q" * 64).decode("ascii")
  with pytest.raises(stage2.Stage2Error, match="approval was rejected"):
    env.controller(state_root=env.state_root.parent / "bad-recovery", recovery_envelope=bad)


def test_custom_readiness_gate_crypto_is_explicit_production_hold():
  contract = stage2.PRODUCTION_CRYPTO_REQUIREMENT
  assert contract["custom_ed25519_implementation_allowed"] is False
  assert contract["existing_readiness_gate_custom_ed25519_is_production_acceptable"] is False
  source = Path(hardware_gate.__file__).read_text()
  tree = ast.parse(source)
  imported = {alias.name for node in ast.walk(tree)
              if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
  assert "cryptography" not in imported
  assert "def verify_ed25519" in source
  assert "_scalar_mult" in source
  assert contract["status"] == "UNSATISFIED_EXTERNAL_REQUIREMENT"


def test_systemd_contract_is_documentation_only_and_models_required_boundaries():
  contract = stage2.OS_INTEGRATION_CONTRACT
  assert contract["classification"] == "DOCUMENTATION_ONLY_NONINSTALLABLE"
  assert contract["unit_emitted"] is False
  assert contract["start_command_defined"] is False
  assert contract["verified_rootfs_required"] is True
  assert "TEE_OR_RPMB" in contract["rollback_resistant_state_required"]
  assert contract["selinux_agnos_19_8_1"] == "PERMISSIVE_IS_NOT_A_SECURITY_BOUNDARY"
  assert contract["os_slots_are_application_slots"] is False
  assert contract["physical_key_custody_assumed"] is False


def test_source_has_no_process_network_device_install_or_actuation_surface():
  source_path = Path(__file__).resolve().parents[1] / "rc3_stage2_supervisor.py"
  source = source_path.read_text()
  tree = ast.parse(source)
  imported = {alias.name for node in ast.walk(tree)
              if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
  assert not ({"subprocess", "socket", "requests", "urllib", "can", "panda", "shutil"} & imported)
  for forbidden in ("os.system", "Popen", "execv", "abctl", "systemctl", "sudo ", "mount("):
    assert forbidden not in source
  assert "process_started: bool = False" in source
  assert "installation_authorized: bool = False" in source

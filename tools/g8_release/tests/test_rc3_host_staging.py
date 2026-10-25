"""Host-only inactive-application-slot trial, crash, health and rollback tests."""
from __future__ import annotations

import ast
import base64
import json
import tempfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import rc3_external_trust as trust
import rc3_host_staging as staging
import rc3_package_planner as planner

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.SIMULATED_TEST_TRUST


def _signed_envelope(private_key, key_id, domain, payload_key, payload):
  signature = private_key.sign(domain + trust.canonical_json(payload))
  return {"algorithm": "ed25519", "key_id": key_id, payload_key: payload,
          "signature_b64": base64.b64encode(signature).decode("ascii")}


@pytest.fixture(scope="module")
def frozen_inventory():
  return planner.build_inventory(ROOT)


@pytest.fixture
def trusted_host_policy(tmp_path, frozen_inventory):
  private_key = Ed25519PrivateKey.generate()
  public_key = private_key.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  key_id = "ephemeral-host-simulation-test-key"
  keyring = {
    "schema": trust.KEYRING_SCHEMA,
    "keys": [{"key_id": key_id, "algorithm": "ed25519", "purpose": "host-simulation-only",
              "public_key_b64": base64.b64encode(public_key).decode("ascii")}],
  }
  policy = {
    "schema": trust.POLICY_SCHEMA,
    "scope": trust.HOST_SCOPE,
    "policy_id": "rc3-host-test-policy",
    "frozen_commit": planner.FROZEN_COMMIT,
    "frozen_tree": planner.FROZEN_TREE,
    "inventory_sha256": planner.inventory_sha256(frozen_inventory),
    "release_sequence": 1,
    "max_trial_attempts": 2,
    "installation_authorized": False,
    "device_operations_authorized": False,
  }
  keyring_path = tmp_path / "keyring.json"
  policy_path = tmp_path / "policy.json"
  keyring_path.write_bytes(trust.canonical_json(keyring))
  policy_path.write_bytes(trust.canonical_json(
    _signed_envelope(private_key, key_id, trust.POLICY_DOMAIN, "policy", policy)))
  plan = planner.build_plan(ROOT, policy_path=policy_path, keyring_path=keyring_path)
  assert plan["external_trust"]["status"] == (
    "CALLER_SUPPLIED_HOST_SIMULATION_KEY_CRYPTOGRAPHICALLY_VERIFIED")
  assert plan["external_trust"]["caller_supplied_signature_verified"] is True
  assert plan["external_trust"]["independent_trust_anchor_verified"] is False
  assert plan["external_trust"]["production_release_authority"] is False
  assert plan["qualification"]["external_trust_verified"] is False
  assert plan["qualification"]["production_approved"] is False
  return {"private_key": private_key, "key_id": key_id, "keyring": keyring_path,
          "policy": policy_path, "policy_payload": policy, "plan": plan, "directory": tmp_path}


def _sim(material):
  return staging.HostOnlySlotSimulation(
    ROOT, material["plan"], policy_path=material["policy"], keyring_path=material["keyring"])


def _health_file(material, state, *, mutate=None):
  receipt = {
    "schema": trust.HEALTH_SCHEMA,
    "scope": trust.HOST_SCOPE,
    "policy_id": material["policy_payload"]["policy_id"],
    "inventory_sha256": material["plan"]["inventory_sha256"],
    "trial_nonce": state["trial_nonce"],
    "attempt": state["attempt"],
    "startup_passed": True,
    "probation_complete": True,
    "boot_success_not_marked_early": True,
    "device_operations_authorized": False,
  }
  if mutate:
    mutate(receipt)
  envelope = _signed_envelope(material["private_key"], material["key_id"],
                              trust.HEALTH_DOMAIN, "receipt", receipt)
  path = material["directory"] / f"health-{len(list(material['directory'].iterdir()))}.json"
  path.write_bytes(trust.canonical_json(envelope))
  return path


def test_no_early_boot_success_and_signed_health_required(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    assert simulation.stage_candidate()["boot_success"] is False
    trial = simulation.begin_trial()
    assert trial["phase"] == "TRIAL_PENDING"
    assert trial["boot_success"] is False
    probation = simulation.observe_startup(True)
    assert probation["phase"] == "PROBATION"
    assert probation["boot_success"] is False
    with pytest.raises(staging.SimulationError, match="health receipt"):
      simulation.accept_health(trusted_host_policy["directory"] / "missing-health.json")
    promoted = simulation.accept_health(_health_file(trusted_host_policy, probation))
    assert promoted["phase"] == "PROMOTED_HOST_SIMULATION_ONLY"
    assert promoted["boot_success"] is True
    assert promoted["recovery_slot"] == "app_b"
    assert promoted["installation_authorized"] is False
    assert promoted["device_operations_authorized"] is False


def test_failed_startup_rolls_back_without_boot_success(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    simulation.stage_candidate()
    simulation.begin_trial()
    state = simulation.observe_startup(False)
    assert state["phase"] == "ROLLED_BACK"
    assert state["active_slot"] == "app_a"
    assert state["recovery_slot"] == "app_a"
    assert state["boot_success"] is False


def test_power_interruption_after_trial_consumption_rolls_back(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    simulation.stage_candidate()
    with pytest.raises(staging.SimulatedPowerLoss, match="trial"):
      simulation.begin_trial(power_loss_after_persist=True)
    pending = simulation.state()
    assert pending["attempt"] == 1
    assert pending["active_slot"] == "app_b"
    assert pending["boot_success"] is False
    recovered = simulation.recover_after_restart()
    assert recovered["phase"] == "ROLLED_BACK"
    assert recovered["active_slot"] == "app_a"
    assert recovered["attempt"] == 1  # interruption cannot refund an attempt


def test_process_death_reopen_preserves_nonce_and_consumed_attempt(trusted_host_policy):
  persisted = trusted_host_policy["directory"] / "persisted-simulation"
  simulation = staging.HostOnlySlotSimulation(
    ROOT, trusted_host_policy["plan"], policy_path=trusted_host_policy["policy"],
    keyring_path=trusted_host_policy["keyring"], simulation_root=persisted)
  simulation.stage_candidate()
  with pytest.raises(staging.SimulatedPowerLoss, match="trial"):
    simulation.begin_trial(power_loss_after_persist=True)
  before_death = simulation.state()
  simulation.close()

  reopened = staging.HostOnlySlotSimulation(
    ROOT, trusted_host_policy["plan"], policy_path=trusted_host_policy["policy"],
    keyring_path=trusted_host_policy["keyring"], simulation_root=persisted, resume=True)
  try:
    after_reopen = reopened.state()
    assert after_reopen["attempt"] == before_death["attempt"] == 1
    assert after_reopen["trial_nonce"] == before_death["trial_nonce"]
    assert after_reopen["phase"] == "TRIAL_PENDING"
    recovered = reopened.recover_after_restart()
    assert recovered["phase"] == "ROLLED_BACK"
    assert recovered["attempt"] == 1
  finally:
    reopened.close()


def test_power_interruption_during_staging_never_switches_slot(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    with pytest.raises(staging.SimulatedPowerLoss, match="candidate"):
      simulation.stage_candidate(power_loss_after_write=True)
    assert simulation.state()["active_slot"] == "app_a"
    recovered = simulation.recover_after_restart()
    assert recovered["phase"] == "IDLE"
    assert recovered["active_slot"] == "app_a"
    assert not (simulation.slots / "app_b" / "identity.json").exists()


def test_power_interruption_after_health_check_before_promotion_rolls_back(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    simulation.stage_candidate()
    simulation.begin_trial()
    probation = simulation.observe_startup(True)
    health = _health_file(trusted_host_policy, probation)
    with pytest.raises(staging.SimulatedPowerLoss, match="health"):
      simulation.accept_health(health, power_loss_before_promotion=True)
    assert simulation.state()["boot_success"] is False
    recovered = simulation.recover_after_restart()
    assert recovered["active_slot"] == "app_a"
    assert recovered["phase"] == "ROLLED_BACK"


def test_wrong_health_binding_rejected_without_promotion(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    simulation.stage_candidate()
    simulation.begin_trial()
    probation = simulation.observe_startup(True)
    bad = _health_file(trusted_host_policy, probation,
                       mutate=lambda receipt: receipt.__setitem__("inventory_sha256", "f" * 64))
    with pytest.raises(staging.SimulationError, match="different trial"):
      simulation.accept_health(bad)
    assert simulation.state()["boot_success"] is False
    assert simulation.state()["recovery_slot"] == "app_a"


def test_signed_health_receipt_cannot_be_replayed_across_simulator_runs(trusted_host_policy):
  first_root = trusted_host_policy["directory"] / "first-run"
  first = staging.HostOnlySlotSimulation(
    ROOT, trusted_host_policy["plan"], policy_path=trusted_host_policy["policy"],
    keyring_path=trusted_host_policy["keyring"], simulation_root=first_root)
  first.stage_candidate()
  first.begin_trial()
  first_probation = first.observe_startup(True)
  old_receipt = _health_file(trusted_host_policy, first_probation)
  first.close()

  second_root = trusted_host_policy["directory"] / "second-run"
  second = staging.HostOnlySlotSimulation(
    ROOT, trusted_host_policy["plan"], policy_path=trusted_host_policy["policy"],
    keyring_path=trusted_host_policy["keyring"], simulation_root=second_root)
  try:
    second.stage_candidate()
    second.begin_trial()
    second_probation = second.observe_startup(True)
    assert second_probation["trial_nonce"] != first_probation["trial_nonce"]
    with pytest.raises(staging.SimulationError, match="different trial"):
      second.accept_health(old_receipt)
    assert second.state()["boot_success"] is False
  finally:
    second.close()


@pytest.mark.parametrize("mutate", [
  lambda state: state.__setitem__("phase", "ATTACKER_SELECTED"),
  lambda state: state.__setitem__("active_slot", "app_b"),
  lambda state: state.__setitem__("attempt", 4),
  lambda state: state.__setitem__("attempt", True),
  lambda state: state.__setitem__("boot_success", True),
  lambda state: state.__setitem__("unexpected", "field"),
])
def test_corrupted_state_schema_phase_slot_counter_or_health_is_rejected(
    trusted_host_policy, mutate):
  with _sim(trusted_host_policy) as simulation:
    state = simulation.state()
    mutate(state)
    simulation.state_path.write_bytes(trust.canonical_json(state))
    with pytest.raises(staging.SimulationError, match="state"):
      simulation.state()


def test_noncanonical_or_duplicate_state_is_rejected(trusted_host_policy):
  with _sim(trusted_host_policy) as simulation:
    state = simulation.state()
    raw = json.dumps(state, indent=2).encode("ascii")
    simulation.state_path.write_bytes(raw)
    with pytest.raises(staging.SimulationError, match="noncanonical"):
      simulation.state()


def test_missing_external_trust_fails_closed_before_trial(tmp_path, frozen_inventory):
  plan = planner.build_plan(ROOT)
  simulation = staging.HostOnlySlotSimulation(
    ROOT, plan, policy_path=tmp_path / "missing-policy.json",
    keyring_path=tmp_path / "missing-keyring.json")
  try:
    simulation.stage_candidate()
    with pytest.raises(staging.SimulationError, match="host policy"):
      simulation.begin_trial()
    assert simulation.state()["active_slot"] == "app_a"
    assert simulation.state()["boot_success"] is False
  finally:
    simulation.close()


def test_policy_mutation_after_planning_fails_closed(trusted_host_policy):
  trusted_host_policy["policy"].write_bytes(b'{}\n')
  with _sim(trusted_host_policy) as simulation:
    simulation.stage_candidate()
    with pytest.raises(staging.SimulationError, match="host policy"):
      simulation.begin_trial()


def test_simulator_has_no_device_operation_or_process_execution_calls(trusted_host_policy):
  path = ROOT / "tools/g8_release/rc3_host_staging.py"
  tree = ast.parse(path.read_text())
  imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
              for alias in node.names}
  assert "subprocess" not in imported
  calls = []
  for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
      calls.append((getattr(node.func.value, "id", None), node.func.attr))
  for forbidden in (("os", "system"), ("os", "execv"), ("os", "execve"),
                    ("subprocess", "run"), ("subprocess", "Popen")):
    assert forbidden not in calls
  with _sim(trusted_host_policy) as simulation:
    assert simulation.root.is_relative_to(Path(tempfile.gettempdir()).resolve())
    assert simulation.state()["device_operations_authorized"] is False


def test_explicit_persistence_path_is_temp_host_policy_not_device_barrier(trusted_host_policy):
  with pytest.raises(staging.SimulationError, match="temporary directory"):
    staging.HostOnlySlotSimulation(
      ROOT, trusted_host_policy["plan"], policy_path=trusted_host_policy["policy"],
      keyring_path=trusted_host_policy["keyring"], simulation_root=ROOT / "not-a-device-slot")

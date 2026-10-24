"""F7 host-only adverse cases. No device, launcher, Panda, CAN, or abctl calls."""
import ast
import base64
import copy
import dataclasses
import hashlib
import inspect
import json

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import g8_f7_offline_gate as gate
from g8_f7_offline_gate import (
  BUNDLE_SCHEMA, EVIDENCE_ASSERTION_KEYS, F6_OPEN_IDS, F6_REFERENCE, MAX_JSON_BYTES,
  REQUIRED_EVIDENCE_KINDS, RESULT_SCHEMA, SIGNING_DOMAIN, SIMULATION_ONLY,
  MockTrial, OfflineGateResult, Phase, ProtocolError, analyze_canonical_bundle, canonical, evidence_payload,
  evaluate_signed_bundle, f7a_minimal_observed_gatecard, parse_canonical_json,
  unresolved_f6_items, verify_detached_evidence,
)

NOW = 1_800_000_000
D = "a" * 64
N1 = "1" * 64
N2 = "2" * 64


@pytest.fixture
def signer():
  private = Ed25519PrivateKey.generate()  # ephemeral test key, never persisted
  raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  key_id = hashlib.sha256(raw).hexdigest()[:16]
  return private, key_id, base64.b64encode(raw).decode()


def assertions(kind):
  values = {
    "boot_chain": {"agnos_version": "19.8.1", "os_slot": "_a", "verity_root_sha256": D,
                   "boot_chain_measured": True},
    "protected_state": {"counter": 7, "nonce_history_protected": True, "rollback_protected": True},
    "early_boot": {"authority_precedes_mutable_launcher": True, "boot_success_deferred": True},
    "immutable_runtime": {"full_runtime_immutable": True, "data_mount_read_only": True,
                          "dependency_closure_verified": True},
    "independent_health": {"boot_nonce": N1, "counter": 7, "heartbeat_fresh": True,
                           "signer_independent": True, "tests_passed": True},
    "key_lifecycle": {"production_custody": True, "rotation_defined": True, "revocation_defined": True},
    "native_abi": {"agnos_version": "19.8.1", "aarch64_native_verified": True,
                   "loader_closure_verified": True},
    "bench_recovery": {"power_loss_matrix_complete": True, "storage_fault_matrix_complete": True,
                       "rollback_verified": True},
    "panda_can": {"static_source_reviewed": True, "host_safety_tests_passed": True,
                  "physical_vehicle_qualified": True},
    "regression": {"f7_host_suite_passed": True, "aarch64_suite_passed": True,
                   "broad_non_honda_failures_resolved": True},
  }
  return values[kind]


def envelope(signer, kind, *, mutate=None, issued=NOW - 10, expires=NOW + 10):
  private, key_id, _ = signer
  payload = evidence_payload(kind, assertions(kind), issued_at=issued, expires_at=expires,
                             evidence_id="ev-" + kind)
  if mutate:
    mutate(payload)
  raw = canonical(payload)
  signature = base64.b64encode(private.sign(SIGNING_DOMAIN + raw)).decode()
  return {"payload": raw, "signature": signature, "key_id": key_id}


def bundle(signer):
  return [envelope(signer, kind) for kind in REQUIRED_EVIDENCE_KINDS]


_DEFAULT = object()


def assess(signer, *, f7a=_DEFAULT, opens=_DEFAULT, evidence=_DEFAULT, keys=_DEFAULT):
  _, key_id, public = signer
  return evaluate_signed_bundle(
    f7a_minimal_observed_gatecard() if f7a is _DEFAULT else f7a,
    unresolved_f6_items() if opens is _DEFAULT else opens,
    bundle(signer) if evidence is _DEFAULT else evidence,
    {key_id: public} if keys is _DEFAULT else keys,
    assessment_time=NOW,
  )


def transport_bundle(signer):
  return {
    "schema": BUNDLE_SCHEMA,
    "simulation_marker": SIMULATION_ONLY,
    "f7a_gatecard": f7a_minimal_observed_gatecard(),
    "f6_open_items": unresolved_f6_items(),
    "evidence": [{"payload_b64": base64.b64encode(item["payload"]).decode(),
                  "signature": item["signature"], "key_id": item["key_id"]}
                 for item in bundle(signer)],
  }


def trial(**kwargs):
  return MockTrial(slot="_a", image_digest=D, **kwargs)


def good_begin(t, nonce=N1, **kwargs):
  t.begin(nonce=nonce, reported_slot="_a", measured_digest=D,
          provenance_authenticated=True, **kwargs)


def good_health(t, nonce=N1, **kwargs):
  t.health(nonce=nonce, reported_slot="_a", measured_digest=D,
           signer_authenticated=True, tests_passed=True, **kwargs)


def test_complete_signed_simulation_is_still_hold(signer):
  result = assess(signer)
  assert result.offline_review == "SIMULATED_EVIDENCE_COMPLETE"
  assert result.production_trust == "UNKNOWN"
  assert result.production_release == "HOLD"
  assert not result.installation_authorized
  assert not result.device_actions_authorized
  assert result.simulation_marker == SIMULATION_ONLY
  assert set(result.reason_codes) == {"OBSERVED_DATA_MOUNT_MUTABLE", "SOFTWARE_SIGNATURE_IS_NOT_HARDWARE_PROOF"}


def test_result_json_is_canonical_and_sanitized(signer):
  result = assess(signer)
  assert parse_canonical_json(canonical(result.as_dict()))["schema"] == RESULT_SCHEMA
  assert all("<" not in code and "/" not in code for code in result.reason_codes)


def test_strict_canonical_transport_bundle(signer):
  _, key_id, public = signer
  result = analyze_canonical_bundle(canonical(transport_bundle(signer)), {key_id: public},
                                    assessment_time=NOW)
  assert result.offline_review == "SIMULATED_EVIDENCE_COMPLETE"
  assert result.production_release == "HOLD"


def test_transport_bundle_extra_field_rejected(signer):
  value = transport_bundle(signer)
  value["input_path"] = "/tmp/attacker"
  with pytest.raises(ProtocolError, match="bundle"):
    analyze_canonical_bundle(canonical(value), {signer[1]: signer[2]}, assessment_time=NOW)


def test_transport_bundle_does_not_accept_path_string(signer):
  with pytest.raises(ProtocolError, match="bytes"):
    analyze_canonical_bundle("/tmp/evidence.json", {signer[1]: signer[2]}, assessment_time=NOW)


@pytest.mark.parametrize("field,value", [
  ("production_release", "GO"), ("production_trust", "VERIFIED"),
  ("installation_authorized", True), ("device_actions_authorized", True),
])
def test_result_invariants_cannot_be_replaced(signer, field, value):
  with pytest.raises(ProtocolError, match="never authorize"):
    dataclasses.replace(assess(signer), **{field: value})


@pytest.mark.parametrize("data", [b"{}", b'{"x":1}\n ', b"x: 1\n", b"\x80\x04N.", b'{"x":NaN}\n', "{}\n", b""])
def test_noncanonical_yaml_pickle_and_nonbytes_rejected(data):
  with pytest.raises(ProtocolError):
    parse_canonical_json(data)


def test_oversized_json_rejected():
  with pytest.raises(ProtocolError, match="bounded"):
    parse_canonical_json(b" " * (MAX_JSON_BYTES + 1))


def test_duplicate_json_keys_rejected_as_noncanonical():
  with pytest.raises(ProtocolError, match="canonical"):
    parse_canonical_json(b'{"x":1,"x":2}\n')


def test_detached_signature_forgery_rejected(signer):
  item = envelope(signer, "boot_chain")
  item["signature"] = base64.b64encode(b"0" * 64).decode()
  with pytest.raises(ProtocolError, match="invalid"):
    verify_detached_evidence(item["payload"], item["signature"], signer[2],
                             expected_key_id=signer[1], assessment_time=NOW)


def test_untrusted_key_rejected(signer):
  other = Ed25519PrivateKey.generate().public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  item = envelope(signer, "boot_chain")
  with pytest.raises(ProtocolError, match="untrusted"):
    verify_detached_evidence(item["payload"], item["signature"], base64.b64encode(other).decode(),
                             expected_key_id=signer[1], assessment_time=NOW)


@pytest.mark.parametrize("issued,expires", [
  (NOW - 4000, NOW + 1), (NOW + 1, NOW + 10), (NOW - 10, NOW - 1), (NOW, NOW),
])
def test_stale_future_or_invalid_lifetime_rejected(signer, issued, expires):
  item = envelope(signer, "boot_chain", issued=issued, expires=expires)
  with pytest.raises(ProtocolError, match="stale|future"):
    verify_detached_evidence(item["payload"], item["signature"], signer[2],
                             expected_key_id=signer[1], assessment_time=NOW)


def test_wrong_f6_commit_rejected_even_when_signed(signer):
  item = envelope(signer, "boot_chain", mutate=lambda p: p.update(f6_reference_commit="b" * 40))
  with pytest.raises(ProtocolError, match="F6"):
    verify_detached_evidence(item["payload"], item["signature"], signer[2],
                             expected_key_id=signer[1], assessment_time=NOW)


@pytest.mark.parametrize("marker", ["REAL", "simulated", "", SIMULATION_ONLY.lower()])
def test_simulation_marker_case_variants_rejected(signer, marker):
  item = envelope(signer, "boot_chain", mutate=lambda p: p.update(simulation_marker=marker))
  with pytest.raises(ProtocolError, match="simulated"):
    verify_detached_evidence(item["payload"], item["signature"], signer[2],
                             expected_key_id=signer[1], assessment_time=NOW)


def test_extra_claim_field_rejected(signer):
  def mutate(payload):
    payload["assertions"]["shell"] = "/bin/sh"
  item = envelope(signer, "boot_chain", mutate=mutate)
  with pytest.raises(ProtocolError, match="assertions"):
    verify_detached_evidence(item["payload"], item["signature"], signer[2],
                             expected_key_id=signer[1], assessment_time=NOW)


@pytest.mark.parametrize("kind", REQUIRED_EVIDENCE_KINDS)
def test_each_missing_evidence_kind_blocks(signer, kind):
  evidence = [item for item in bundle(signer) if json.loads(item["payload"])["kind"] != kind]
  assert assess(signer, evidence=evidence).offline_review == "BLOCKED"


@pytest.mark.parametrize("kind", REQUIRED_EVIDENCE_KINDS)
def test_each_negative_evidence_kind_blocks(signer, kind):
  key = next(k for k, v in assertions(kind).items() if type(v) is bool)
  evidence = []
  for candidate in REQUIRED_EVIDENCE_KINDS:
    mutate = (lambda p, key=key: p["assertions"].update({key: False})) if candidate == kind else None
    evidence.append(envelope(signer, candidate, mutate=mutate))
  assert "EVIDENCE_NEGATIVE_" + kind.upper() in assess(signer, evidence=evidence).reason_codes


@pytest.mark.parametrize("agnos", ["20.0", "19.8.0", "019.8.1"])
def test_stale_or_mismatched_agnos_blocks(signer, agnos):
  evidence = [envelope(signer, k, mutate=(lambda p: p["assertions"].update(agnos_version=agnos))
                       if k == "boot_chain" else None) for k in REQUIRED_EVIDENCE_KINDS]
  assert "STALE_OR_MISMATCHED_AGNOS" in assess(signer, evidence=evidence).reason_codes


def test_stale_os_slot_blocks(signer):
  evidence = [envelope(signer, k, mutate=(lambda p: p["assertions"].update(os_slot="_b"))
                       if k == "boot_chain" else None) for k in REQUIRED_EVIDENCE_KINDS]
  assert "STALE_OR_MISMATCHED_OS_SLOT" in assess(signer, evidence=evidence).reason_codes


def test_missing_protected_counter_claim_rejected(signer):
  def mutate(payload):
    del payload["assertions"]["counter"]
  item = envelope(signer, "protected_state", mutate=mutate)
  with pytest.raises(ProtocolError, match="assertions"):
    verify_detached_evidence(item["payload"], item["signature"], signer[2],
                             expected_key_id=signer[1], assessment_time=NOW)


def test_health_counter_mismatch_blocks(signer):
  evidence = [envelope(signer, k, mutate=(lambda p: p["assertions"].update(counter=8))
                       if k == "independent_health" else None) for k in REQUIRED_EVIDENCE_KINDS]
  assert "HEALTH_COUNTER_MISMATCH" in assess(signer, evidence=evidence).reason_codes


def test_mutable_runtime_blocks(signer):
  evidence = [envelope(signer, k, mutate=(lambda p: p["assertions"].update(data_mount_read_only=False))
                       if k == "immutable_runtime" else None) for k in REQUIRED_EVIDENCE_KINDS]
  result = assess(signer, evidence=evidence)
  assert "MUTABLE_RUNTIME" in result.reason_codes
  assert result.production_release == "HOLD"


@pytest.mark.parametrize("change", [
  {"F6_reference_commit": "b" * 40}, {"reported_boot_slot": "_b"},
  {"device_AGNOS": "20.0"}, {"production_security_feasibility": "PASS"},
  {"F7B_installation": "GO"}, {"device_modified": True},
  {"data_mount": "/data read-only"},
])
def test_f7a_mismatch_variants_block(signer, change):
  f7a = f7a_minimal_observed_gatecard()
  f7a.update(change)
  assert assess(signer, f7a=f7a).offline_review == "BLOCKED"


@pytest.mark.parametrize("bad", [None, [], {}, "closed"])
def test_missing_or_malformed_f6_register_blocks(signer, bad):
  assert assess(signer, opens=bad).offline_review == "BLOCKED"


@pytest.mark.parametrize("item", F6_OPEN_IDS)
def test_each_f6_item_must_remain_open(signer, item):
  opens = unresolved_f6_items()
  opens[item] = "CLOSED"
  assert "F6_OPEN_ITEM_NOT_RETAINED" in assess(signer, opens=opens).reason_codes


def test_attacker_text_does_not_reach_result_or_xss(signer):
  bad = {"payload": b'<script>alert(1)</script>', "signature": "<img>", "key_id": "path"}
  result = assess(signer, evidence=[bad])
  encoded = canonical(result.as_dict())
  assert b"script" not in encoded and b"img" not in encoded and b"alert" not in encoded


def test_duplicate_kind_and_evidence_id_rejected(signer):
  evidence = bundle(signer)
  evidence.append(copy.deepcopy(evidence[0]))
  result = assess(signer, evidence=evidence)
  assert "EVIDENCE_REJECTED" in result.reason_codes


def test_no_trust_store_blocks(signer):
  assert "TRUST_STORE_MISSING" in assess(signer, keys={}).reason_codes


@pytest.mark.parametrize("bound", [0, 6, True, 1.5])
def test_invalid_attempt_bounds_fail(bound):
  with pytest.raises(ProtocolError):
    trial(max_attempts=bound)


@pytest.mark.parametrize("nonce", ["short", "A" * 64, "1" * 63, "1" * 65, 1])
def test_invalid_boot_nonce_and_case_variants_fail(nonce):
  with pytest.raises(ProtocolError, match="nonce"):
    good_begin(trial(), nonce=nonce)


def test_wrong_boot_nonce_consumption_fails():
  t = trial()
  good_begin(t)
  with pytest.raises(ProtocolError, match="consumed"):
    t.consume(nonce=N2)


@pytest.mark.parametrize("slot,digest,authenticated", [("_b", D, True), ("_a", "b" * 64, True), ("_a", D, False)])
def test_wrong_slot_image_or_provenance_fails(slot, digest, authenticated):
  with pytest.raises(ProtocolError, match="provenance"):
    trial().begin(nonce=N1, reported_slot=slot, measured_digest=digest,
                  provenance_authenticated=authenticated)


@pytest.mark.parametrize("counter", [0, 2, True, -1])
def test_reused_or_jumped_counter_fails(counter):
  with pytest.raises(ProtocolError, match="counter"):
    good_begin(trial(), counter=counter)


def test_health_before_consume_fails():
  t = trial()
  good_begin(t)
  with pytest.raises(ProtocolError, match="Health|health"):
    good_health(t)


@pytest.mark.parametrize("signer_ok,tests_ok,heartbeat", [(False, True, True), (True, False, True), (True, True, False)])
def test_wrong_health_signer_unhealthy_or_missing_heartbeat_fails(signer_ok, tests_ok, heartbeat):
  t = trial()
  good_begin(t)
  t.consume(nonce=N1)
  with pytest.raises(ProtocolError, match="unauthenticated|heartbeat"):
    t.health(nonce=N1, reported_slot="_a", measured_digest=D,
             signer_authenticated=signer_ok, tests_passed=tests_ok, heartbeat_fresh=heartbeat)


def test_stale_health_counter_fails():
  t = trial()
  good_begin(t, counter=1)
  t.consume(nonce=N1)
  with pytest.raises(ProtocolError, match="counter"):
    good_health(t, counter=0)


def test_premature_success_fails():
  t = trial()
  good_begin(t)
  with pytest.raises(ProtocolError, match="premature"):
    t.simulated_success(nonce=N1)


def test_complete_trial_returns_only_simulated_token():
  t = trial()
  good_begin(t, counter=1)
  t.consume(nonce=N1)
  good_health(t, counter=1)
  assert t.simulated_success(nonce=N1) == "SIMULATED_BOOT_SUCCESS_NOT_ABCTL"
  assert t.phase == Phase.HEALTH_VERIFIED


@pytest.mark.parametrize("fault", ["powercut", "storage_fault"])
def test_interrupted_activation_retains_nonce_and_counter(fault):
  t = trial()
  good_begin(t, counter=1)
  getattr(t, fault)()
  assert t.phase == Phase.ABORTED and t.protected_counter == 1 and N1 in t.seen_nonces
  with pytest.raises(ProtocolError, match="replay"):
    good_begin(t, nonce=N1, counter=2)


def test_new_nonce_after_fault_uses_next_counter_and_attempt():
  t = trial()
  good_begin(t, counter=1)
  t.powercut()
  good_begin(t, nonce=N2, counter=2)
  assert (t.attempts, t.protected_counter) == (2, 2)


def test_exhausted_attempts_fail_closed():
  t = trial(max_attempts=1)
  good_begin(t)
  t.powercut()
  with pytest.raises(ProtocolError, match="limit"):
    good_begin(t, nonce=N2)


def test_old_state_restore_always_fails():
  with pytest.raises(ProtocolError, match="cannot authenticate"):
    trial().restore_state_from_old_copy({"counter": 0, "nonces": []})


def test_source_has_no_execution_network_or_path_open_capability():
  tree = ast.parse(inspect.getsource(gate))
  denied_modules = {"subprocess", "socket", "paramiko", "fabric", "asyncssh", "yaml", "pickle"}
  denied_calls = {"open", "system", "popen", "execv", "execve", "run", "Panda", "can_send"}
  for node in ast.walk(tree):
    if isinstance(node, ast.Import):
      assert all(name.name.split(".")[0] not in denied_modules for name in node.names)
    if isinstance(node, ast.ImportFrom):
      assert (node.module or "").split(".")[0] not in denied_modules
    if isinstance(node, ast.Call):
      name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
      assert name not in denied_calls

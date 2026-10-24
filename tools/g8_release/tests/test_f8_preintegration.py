"""F8 host-only negative/boundary guards; no path, device, Panda, CAN or boot calls."""
import ast
import copy
import json

import pytest

import g8_f8_preintegration as f8


NOW = 1_800_000_000
DIGEST = "a" * 64
NONCE = "b" * 64


def component(name, role, mount="VERIFIED_APP_IMAGE", read_only=True, executable=True):
  return {"name": name, "role": role, "sha256": DIGEST, "mount_class": mount,
          "read_only": read_only, "executable": executable}


def manifest():
  return {
    "schema": f8.MANIFEST_SCHEMA, "generated_at": NOW - 5, "agnos_version": "19.8.1",
    "kernel": "4.9.103", "architecture": "aarch64", "interpreter": "python",
    "loader": "ld-linux", "components": [
      component("app", "application"), component("python", "interpreter"),
      component("ld-linux", "loader", "VERIFIED_ROOT"), component("libcrypto", "crypto"),
    ],
  }


def evidence(control):
  synthetic = control in f8.HARDWARE_CONTROLS
  return {
    "control": control,
    "evidence_type": "SOFTWARE_SIGNED_SYNTHETIC" if synthetic else "SOURCE_DERIVED",
    "claim": True, "issued_at": NOW - 10, "expires_at": NOW + 10, "slot": "_a",
    "boot_nonce": NONCE, "counter": 7, "attempt": 2, "image_digest": DIGEST,
  }


def bundle():
  return {
    "schema": f8.BUNDLE_SCHEMA, "marker": f8.OFFLINE_MARKER,
    "f7_reference": f8.F7_REFERENCE, "assessment_time": NOW,
    "observed": copy.deepcopy(f8.OBSERVED_LIMITS),
    "contract_evidence": [evidence(c) for c in f8.REQUIRED_CONTROLS],
    "runtime_manifest": manifest(),
  }


def assess(value=None):
  return f8.assess_canonical_bundle(f8.canonical(bundle() if value is None else value))


def test_complete_docs_are_only_conditionally_prepared_and_never_go():
  result = assess()
  assert result.docs_prepared
  assert result.offline_preintegration == "CONDITIONALLY_PREPARED"
  assert not result.hardware_qualified
  assert not result.production_release_go
  assert not result.installation_authorized
  assert not result.device_actions_authorized
  assert "HARDWARE_ROOTED_ATTESTATION_NOT_DEMONSTRATED" in result.reason_codes


@pytest.mark.parametrize("bad", [None, "x", {}, [], bytearray(b"{}\n")])
def test_non_bytes_inputs_rejected(bad):
  with pytest.raises(f8.AssessmentError):
    f8.parse_canonical_json(bad)


def test_noncanonical_json_rejected():
  with pytest.raises(f8.AssessmentError):
    f8.parse_canonical_json(b'{"x": 1}\n')


def test_duplicate_json_key_rejected():
  with pytest.raises(f8.AssessmentError):
    f8.parse_canonical_json(b'{"x":1,"x":1}\n')


def test_oversized_input_rejected():
  with pytest.raises(f8.AssessmentError):
    f8.parse_canonical_json(b"x" * (f8.MAX_JSON_BYTES + 1))


@pytest.mark.parametrize("field,value", [
  ("schema", "wrong"), ("marker", "deployable"), ("f7_reference", "0" * 40),
])
def test_bundle_identity_is_pinned(field, value):
  value_bundle = bundle()
  value_bundle[field] = value
  with pytest.raises(f8.AssessmentError):
    assess(value_bundle)


def test_extra_bundle_field_rejected():
  value = bundle()
  value["go"] = True
  with pytest.raises(f8.AssessmentError):
    assess(value)


def test_forged_hardware_provenance_rejected():
  value = bundle()
  value["contract_evidence"][0]["evidence_type"] = "HARDWARE_ROOTED"
  with pytest.raises(f8.AssessmentError, match="provenance"):
    assess(value)


def test_secure_root_unavailable_fails_closed():
  value = bundle()
  target = next(x for x in value["contract_evidence"] if x["control"] == "slot_digest_secure_binding")
  target["claim"] = False
  with pytest.raises(f8.AssessmentError, match="negative"):
    assess(value)


def test_unverified_data_mount_cannot_form_manifest():
  value = bundle()
  value["runtime_manifest"]["components"][0]["mount_class"] = "DATA_RW"
  with pytest.raises(f8.AssessmentError, match="mount"):
    assess(value)


@pytest.mark.parametrize("field,value", [
  ("agnos_version", "20.0"), ("kernel", "6.6"), ("architecture", "x86_64"),
])
def test_invalid_target_pin_rejected(field, value):
  value_bundle = bundle()
  value_bundle["runtime_manifest"][field] = value
  with pytest.raises(f8.AssessmentError, match="target"):
    assess(value_bundle)


def test_simulated_early_success_false_rejected():
  value = bundle()
  target = next(x for x in value["contract_evidence"] if x["control"] == "delayed_boot_success")
  target["claim"] = False
  with pytest.raises(f8.AssessmentError):
    assess(value)


@pytest.mark.parametrize("counter", [0, -1, True, 2**63])
def test_invalid_counter_rejected(counter):
  value = bundle()
  value["contract_evidence"][0]["counter"] = counter
  with pytest.raises(f8.AssessmentError):
    assess(value)


def test_wrong_slot_rejected():
  value = bundle()
  value["contract_evidence"][0]["slot"] = "_b"
  with pytest.raises(f8.AssessmentError, match="slot"):
    assess(value)


@pytest.mark.parametrize("nonce", ["", "B" * 64, "b" * 63, "../nonce"])
def test_wrong_nonce_rejected(nonce):
  value = bundle()
  value["contract_evidence"][0]["boot_nonce"] = nonce
  with pytest.raises(f8.AssessmentError, match="nonce"):
    assess(value)


def test_valid_format_nonce_mismatch_rejected():
  value = bundle()
  value["contract_evidence"][1]["boot_nonce"] = "c" * 64
  with pytest.raises(f8.AssessmentError, match="binding"):
    assess(value)


def test_counter_rollback_across_claims_rejected():
  value = bundle()
  value["contract_evidence"][1]["counter"] = 6
  with pytest.raises(f8.AssessmentError, match="rollback"):
    assess(value)


def test_attempt_rollback_across_claims_rejected():
  value = bundle()
  value["contract_evidence"][1]["attempt"] = 1
  with pytest.raises(f8.AssessmentError, match="rollback"):
    assess(value)


def test_image_digest_mismatch_across_claims_rejected():
  value = bundle()
  value["contract_evidence"][1]["image_digest"] = "c" * 64
  with pytest.raises(f8.AssessmentError, match="binding"):
    assess(value)


@pytest.mark.parametrize("issued,expires", [
  (NOW - f8.MAX_AGE_SECONDS - 1, NOW + 1), (NOW + 1, NOW + 2), (NOW - 2, NOW - 1),
])
def test_stale_future_or_expired_claim_rejected(issued, expires):
  value = bundle()
  value["contract_evidence"][0].update(issued_at=issued, expires_at=expires)
  with pytest.raises(f8.AssessmentError, match="stale"):
    assess(value)


def test_volatile_documentation_cannot_satisfy_hardware_control():
  value = bundle()
  target = next(x for x in value["contract_evidence"] if x["control"] == "protected_monotonic_state")
  target["evidence_type"] = "GENERIC_DOCUMENTATION"
  with pytest.raises(f8.AssessmentError, match="synthetic"):
    assess(value)


def test_missing_control_rejected():
  value = bundle()
  value["contract_evidence"].pop()
  with pytest.raises(f8.AssessmentError, match="incomplete"):
    assess(value)


def test_duplicate_control_rejected():
  value = bundle()
  value["contract_evidence"][-1]["control"] = value["contract_evidence"][0]["control"]
  with pytest.raises(f8.AssessmentError, match="duplicate"):
    assess(value)


def test_unknown_control_rejected():
  value = bundle()
  value["contract_evidence"][0]["control"] = "release_go"
  with pytest.raises(f8.AssessmentError):
    assess(value)


def test_bad_digest_rejected():
  value = bundle()
  value["contract_evidence"][0]["image_digest"] = "A" * 64
  with pytest.raises(f8.AssessmentError, match="digest"):
    assess(value)


def test_manifest_staleness_rejected():
  value = bundle()
  value["runtime_manifest"]["generated_at"] = NOW - f8.MAX_AGE_SECONDS - 1
  with pytest.raises(f8.AssessmentError, match="stale"):
    assess(value)


def test_writable_image_rejected():
  value = bundle()
  value["runtime_manifest"]["components"][0]["read_only"] = False
  with pytest.raises(f8.AssessmentError, match="writable"):
    assess(value)


@pytest.mark.parametrize("missing", ["python", "ld-linux", "libcrypto", "app"])
def test_dependency_closure_missing_role_rejected(missing):
  value = bundle()
  value["runtime_manifest"]["components"] = [
    c for c in value["runtime_manifest"]["components"] if c["name"] != missing]
  with pytest.raises(f8.AssessmentError):
    assess(value)


def test_duplicate_component_rejected():
  value = bundle()
  value["runtime_manifest"]["components"].append(
    copy.deepcopy(value["runtime_manifest"]["components"][0]))
  with pytest.raises(f8.AssessmentError, match="duplicate"):
    assess(value)


def test_observed_boundary_cannot_be_upgraded():
  value = bundle()
  value["observed"]["data_read_only"] = True
  with pytest.raises(f8.AssessmentError, match="observed"):
    assess(value)


def test_result_constructor_rejects_release_go():
  result = assess()
  values = result.__dict__ | {"production_release_go": True}
  with pytest.raises(f8.AssessmentError):
    f8.AssessmentResult(**values)


def test_path_and_execution_apis_are_absent():
  tree = ast.parse(open(f8.__file__, encoding="utf-8").read())
  imports = {alias.name.split(".")[0] for node in ast.walk(tree)
             if isinstance(node, ast.Import) for alias in node.names}
  imports |= {node.module.split(".")[0] for node in ast.walk(tree)
              if isinstance(node, ast.ImportFrom) and node.module}
  assert not imports & {"os", "pathlib", "subprocess", "socket", "pickle", "requests", "urllib"}
  calls = {node.func.id for node in ast.walk(tree)
           if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
  assert not calls & {"open", "exec", "eval", "compile", "__import__"}


def test_no_key_generation_or_signing_api():
  names = {name.lower() for name in dir(f8)}
  assert not {"sign", "generate_key", "private_key", "panda", "can_send", "abctl"} & names

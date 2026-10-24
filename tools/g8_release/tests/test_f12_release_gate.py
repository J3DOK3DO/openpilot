import copy
import json

import pytest

from g8_f12_release_gate import (EvidenceError, F8_COMMIT, F8_GATECARD_SHA256, SCHEMA,
                                 assess_release, canonical_json, read_canonical_json)


ZERO = "0" * 64


def binary(name):
  return {"name": name, "path": f"bin/{name}", "sha256": ZERO, "architecture": "AARCH64",
          "source_commit": F8_COMMIT, "source_paths": [f"src/{name}.cc"],
          "built_from_pinned_source": False}


@pytest.fixture
def evidence():
  return {
    "schema": SCHEMA,
    "release_provenance": {"source_commit": F8_COMMIT, "tree_clean": True, "bundle_sha256": ZERO,
                           "provenance_kind": "UNKEYED_SHA256_ONLY", "keyed_signature_verified": False},
    "essential_binaries": [binary(n) for n in ("pandad", "pandad_api_impl", "lateral_mpc", "longitudinal_mpc", "ipc_pyx", "params_pyx")],
    "abi": {"target_arch": "AARCH64", "python_abi": "CPython-3.12", "elf_interpreter": "/lib/ld-linux-aarch64.so.1",
            "agnos_version": "19.8.1", "native_agnos": False, "qemu_userland_only": True,
            "dependency_closure_complete": False, "pinned_sysroot_sha256": None, "rpath_policy_pass": False},
    "device_identity": {"hardware": "comma-three", "agnos_version": "19.8.1",
                        "app_commit": "7b4db9a26010ba9899eef242d3ca49b33cbcca9c", "independently_authenticated": False},
    "prior_f8": {"gatecard_sha256": F8_GATECARD_SHA256, "source_commit": F8_COMMIT,
                 "offline_disposition": "CONDITIONALLY_PASS_PREPARED_NOT_HARDWARE_QUALIFIED",
                 "hardware_trust": "UNKNOWN_NOT_DEMONSTRATED_HOLD"},
    "f7a_trust": {"inventory_pass": True, "hardware_trust": "UNKNOWN_HOLD", "installation": "NO_GO"},
    "regression": {"passed": 3661, "failed": 2, "skipped": 72,
                   "unwaived_failures": ["Chevrolet Bolt", "Hyundai Palisade"]},
    "compiler_artifacts": {"full_clean_build": False, "build_source_commit": F8_COMMIT,
                           "compiler_identity_pinned": False, "artifacts_match_source": False},
    "platform_evidence": {"production_health_signer": False, "protected_monotonic_state": False,
                          "authenticated_boot_measurement": False, "panda_can_hardware_qualified": False,
                          "independent_production_review_go": False},
  }


def mutate(evidence, path, value):
  result = copy.deepcopy(evidence)
  target = result
  for part in path[:-1]:
    target = target[part]
  target[path[-1]] = value
  return result


def test_baseline_is_hold(evidence):
  result = assess_release(evidence)
  assert result.disposition == "SIMULATED_OFFLINE_ASSESSMENT_HOLD"
  assert not result.production_go and not result.installation_authorized and not result.panda_can_authorized


def test_all_caller_flags_true_still_never_go(evidence):
  value = copy.deepcopy(evidence)
  for item in value["essential_binaries"]:
    item["built_from_pinned_source"] = True
  value["abi"].update(native_agnos=True, qemu_userland_only=False, dependency_closure_complete=True,
                      pinned_sysroot_sha256=ZERO, rpath_policy_pass=True)
  value["device_identity"]["independently_authenticated"] = True
  value["compiler_artifacts"].update(full_clean_build=True, compiler_identity_pinned=True, artifacts_match_source=True)
  value["platform_evidence"] = {key: True for key in value["platform_evidence"]}
  result = assess_release(value)
  assert not any((result.production_go, result.installation_authorized, result.device_action_authorized,
                  result.panda_can_authorized, result.hardware_qualified, result.native_agnos_qualified))


@pytest.mark.parametrize(("raw"), [b"", b"[]\n", b'{"a":1}', b'{"a":1, "b":2}\n', b'{"a":1,"a":2}\n',
                                         b'{"x":NaN}\n', b'\xff', b"{}\n" + b" " * 1_048_576])
def test_rejects_bad_canonical_inputs(raw):
  with pytest.raises(EvidenceError):
    read_canonical_json(raw)


def test_canonical_round_trip(evidence):
  assert read_canonical_json(canonical_json(evidence)) == evidence


@pytest.mark.parametrize(("path", "value"), [
  (("schema",), "fake"),
  (("release_provenance", "source_commit"), "f" * 40),
  (("release_provenance", "tree_clean"), 1),
  (("release_provenance", "bundle_sha256"), "ABC"),
  (("release_provenance", "provenance_kind"), "SIGNED"),
  (("release_provenance", "keyed_signature_verified"), True),
  (("prior_f8", "gatecard_sha256"), "1" * 64),
  (("prior_f8", "offline_disposition"), "PASS"),
  (("prior_f8", "hardware_trust"), "PASS"),
  (("f7a_trust", "inventory_pass"), 1),
  (("f7a_trust", "hardware_trust"), "PASS"),
  (("f7a_trust", "installation"), "GO"),
  (("abi", "target_arch"), "x86_64"),
  (("abi", "python_abi"), "CPython-3.11"),
  (("abi", "elf_interpreter"), "/lib64/ld-linux-x86-64.so.2"),
  (("abi", "agnos_version"), "latest"),
  (("abi", "native_agnos"), 1),
  (("device_identity", "agnos_version"), "20.0"),
  (("device_identity", "independently_authenticated"), 1),
  (("regression", "passed"), 3663),
  (("regression", "failed"), 0),
  (("regression", "skipped"), 0),
  (("regression", "unwaived_failures"), []),
  (("compiler_artifacts", "full_clean_build"), "true"),
  (("platform_evidence", "production_health_signer"), 1),
])
def test_counterfeit_evidence_rejected(evidence, path, value):
  with pytest.raises(EvidenceError):
    assess_release(mutate(evidence, path, value))


def test_missing_pandad_rejected(evidence):
  evidence["essential_binaries"] = [x for x in evidence["essential_binaries"] if x["name"] != "pandad"]
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_missing_source_provenance_rejected(evidence):
  evidence["essential_binaries"][0]["source_paths"] = []
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_spoofed_artifact_digest_rejected(evidence):
  evidence["essential_binaries"][0]["sha256"] = "spoofed"
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_native_and_qemu_are_mutually_exclusive(evidence):
  evidence["abi"]["native_agnos"] = True
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_duplicate_binary_rejected(evidence):
  evidence["essential_binaries"].append(copy.deepcopy(evidence["essential_binaries"][0]))
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_extra_binary_rejected(evidence):
  evidence["essential_binaries"].append(binary("unreviewed"))
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_path_escape_rejected(evidence):
  evidence["essential_binaries"][0]["path"] = "../pandad"
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_extra_top_level_key_rejected(evidence):
  evidence["production_go"] = True
  with pytest.raises(EvidenceError):
    assess_release(evidence)


def test_extra_nested_key_rejected(evidence):
  evidence["platform_evidence"]["caller_go"] = True
  with pytest.raises(EvidenceError):
    assess_release(evidence)

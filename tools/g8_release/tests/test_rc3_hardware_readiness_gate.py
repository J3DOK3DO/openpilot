"""Adversarial tests for the offline RC3 physical-evidence gate."""
from __future__ import annotations

import ast
import base64
import copy
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import rc3_hardware_readiness_gate as gate


NOW = datetime(2026, 10, 25, 12, 0, 0, tzinfo=timezone.utc)
pytestmark = pytest.mark.SIMULATED_TEST_TRUST


def _raw_public(private_key: Ed25519PrivateKey) -> bytes:
  return private_key.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _signature(private_key: Ed25519PrivateKey, key_id: str, payload: dict) -> dict:
  signed = private_key.sign(gate.SIGNATURE_DOMAIN + gate.canonical_json(payload))
  return {"algorithm": "Ed25519", "key_id": key_id,
          "signature_b64": base64.b64encode(signed).decode("ascii")}


def _descriptor(path: Path, root: Path, **extra) -> dict:
  raw = path.read_bytes()
  return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
          "size_bytes": len(raw), **extra}


@pytest.fixture
def synthetic_set(tmp_path):
  operator_key = Ed25519PrivateKey.generate()
  reviewer_key = Ed25519PrivateKey.generate()
  operator_id, reviewer_id = "synthetic-operator-key", "synthetic-reviewer-key"
  policy = {
    "schema": gate.TRUST_POLICY_SCHEMA,
    "classification": "SYNTHETIC_TEST_TRUST_POLICY",
    "policy_id": "synthetic-policy-v1",
    "keys": [
      {
        "key_id": operator_id,
        "identity": "synthetic-lab-operator",
        "organization": "synthetic-lab-a",
        "role": "LAB_OPERATOR",
        "purpose": "SYNTHETIC_TEST_ONLY",
        "algorithm": "Ed25519",
        "public_key_b64": base64.b64encode(_raw_public(operator_key)).decode("ascii"),
        "independent_from_owner": True,
        "independent_from_developer": True,
      },
      {
        "key_id": reviewer_id,
        "identity": "synthetic-independent-reviewer",
        "organization": "synthetic-review-org-b",
        "role": "INDEPENDENT_REVIEWER",
        "purpose": "SYNTHETIC_TEST_ONLY",
        "algorithm": "Ed25519",
        "public_key_b64": base64.b64encode(_raw_public(reviewer_key)).decode("ascii"),
        "independent_from_owner": True,
        "independent_from_developer": True,
      },
    ],
  }
  policy_path = tmp_path / "trust-policy.json"
  policy_path.write_bytes(gate.canonical_json(policy))
  policy_sha = hashlib.sha256(policy_path.read_bytes()).hexdigest()
  source = {
    "frozen_commit": gate.FROZEN_COMMIT,
    "frozen_tree": gate.FROZEN_TREE,
    "engineering_commit": gate.ENGINEERING_COMMIT,
    "engineering_tree": gate.ENGINEERING_TREE,
    "package_manifest_sha256": "a" * 64,
    "readiness_gate_sha256": hashlib.sha256(Path(gate.__file__).read_bytes()).hexdigest(),
    "supervisor_contract_sha256": hashlib.sha256(
      Path(gate.__file__).with_name("rc3_supervisor_contract.py").read_bytes()).hexdigest(),
    "launcher_exit_code": 78,
  }
  hardware = {
    "platform": gate.PLATFORM,
    "comma_device_model": "comma-3x-synthetic",
    "comma_serial_sha256": "b" * 64,
    "panda_serial_sha256": "c" * 64,
    "agnos_version": "synthetic-agnos-19.8.1",
    "bootloader_version": "synthetic-boot-1",
  }
  nonce = "d" * 64
  requirements = []
  for requirement_id, (environment, kinds) in gate.REQUIRED_ARTIFACTS.items():
    artifacts = []
    for kind in kinds:
      path = tmp_path / "artifacts" / requirement_id / f"{kind}.txt"
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(f"SYNTHETIC TEST FIXTURE ONLY\n{requirement_id}\n{kind}\n")
      artifacts.append(_descriptor(
        path, tmp_path, kind=kind, media_type="text/plain", capture_mode="SYNTHETIC_GENERATED"))
    payload = {
      "schema": gate.OBSERVATION_SCHEMA,
      "classification": gate.SYNTHETIC,
      "qualification_id": "synthetic-qualification-001",
      "evidence_nonce": nonce,
      "requirement_id": requirement_id,
      "environment": environment,
      "source_binding": copy.deepcopy(source),
      "hardware_binding": copy.deepcopy(hardware),
      "observed_at_utc": "2026-10-25T10:00:00Z",
      "expires_at_utc": "2026-11-01T10:00:00Z",
      "result": "SYNTHETIC_PASS",
      "artifacts": artifacts,
      "operator_key_id": operator_id,
      "reviewer_key_id": reviewer_id,
      "progression_binding": {
        "sequence": 1, "previous_gatecard": None, "run_nonce": nonce,
      },
    }
    requirements.append({
      "payload": payload,
      "signatures": [
        _signature(operator_key, operator_id, payload),
        _signature(reviewer_key, reviewer_id, payload),
      ],
    })
  manifest = {
    "schema": gate.MANIFEST_SCHEMA,
    "classification": gate.SYNTHETIC,
    "qualification_id": "synthetic-qualification-001",
    "created_at_utc": "2026-10-25T10:00:00Z",
    "expires_at_utc": "2026-11-01T10:00:00Z",
    "source": source,
    "hardware": hardware,
    "owner_context": {
      "owner_identity": "synthetic-owner-context",
      "future_operations_authorized": True,
      "risk_accepted": True,
      "statement_sha256": "e" * 64,
    },
    "trust_policy": _descriptor(policy_path, tmp_path),
    "progression": {"sequence": 1, "previous_gatecard": None, "run_nonce": nonce},
    "requirements": requirements,
  }
  manifest_path = tmp_path / "manifest.json"

  def write_manifest() -> None:
    manifest_path.write_bytes(gate.canonical_json(manifest))

  def resign(envelope: dict) -> None:
    envelope["signatures"] = [
      _signature(operator_key, operator_id, envelope["payload"]),
      _signature(reviewer_key, reviewer_id, envelope["payload"]),
    ]

  write_manifest()
  return type("SyntheticEvidence", (), {
    "root": tmp_path, "manifest": manifest, "manifest_path": manifest_path,
    "manifest_relative": "manifest.json", "policy_sha": policy_sha,
    "operator_key": operator_key, "reviewer_key": reviewer_key,
    "operator_id": operator_id, "reviewer_id": reviewer_id,
    "write_manifest": staticmethod(write_manifest), "resign": staticmethod(resign),
  })()


def _assess(material) -> dict:
  return gate.assess(material.root, material.manifest_relative, material.policy_sha, now=NOW)


def test_no_evidence_is_machine_readable_hold(tmp_path):
  result = gate.assess(tmp_path, None, None, now=NOW)
  assert result["disposition"] == "HOLD"
  assert result["technical_evidence_complete"] is False
  assert result["installation_authorized"] is False
  assert result["boot_operations_authorized"] is False
  assert result["production_approved"] is False
  assert result["validated_requirements"] == []


def test_complete_cryptographically_valid_synthetic_fixture_remains_hold(synthetic_set):
  result = _assess(synthetic_set)
  assert result["validated_requirements"] == list(gate.REQUIRED_ARTIFACTS)
  assert result["independent_attestations_verified"] is True
  assert result["evidence_classification"] == gate.SYNTHETIC
  assert result["disposition"] == "HOLD_SYNTHETIC_EVIDENCE_NON_DEPLOYABLE"
  assert result["technical_evidence_complete"] is False
  assert result["installation_authorized"] is False
  assert result["boot_operations_authorized"] is False
  assert result["production_approved"] is False
  assert result["owner_authorization_observed"] is True
  assert result["owner_risk_acceptance_observed"] is True


def test_spoofed_owner_approval_cannot_replace_evidence(synthetic_set):
  synthetic_set.manifest["requirements"] = []
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert result["technical_evidence_complete"] is False
  assert result["installation_authorized"] is False


def test_operator_self_attestation_cannot_fill_reviewer_role(synthetic_set):
  envelope = synthetic_set.manifest["requirements"][0]
  envelope["signatures"][1] = _signature(
    synthetic_set.operator_key, synthetic_set.operator_id, envelope["payload"])
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "role" in result["validation_errors"][0]


def test_tampered_artifact_digest_fails_closed(synthetic_set):
  descriptor = synthetic_set.manifest["requirements"][0]["payload"]["artifacts"][0]
  (synthetic_set.root / descriptor["path"]).write_text("tampered but descriptor unchanged\n")
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "SHA256" in result["validation_errors"][0]


@pytest.mark.parametrize("platform", ["honda_accord_11g", "HONDA_ACCORD_10G", "Honda_Accord_11G"])
def test_wrong_platform_or_case_mismatch_is_rejected(synthetic_set, platform):
  synthetic_set.manifest["hardware"]["platform"] = platform
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "platform" in result["validation_errors"][0]


def test_stale_evidence_is_rejected(synthetic_set):
  synthetic_set.manifest["created_at_utc"] = "2026-08-01T00:00:00Z"
  synthetic_set.manifest["expires_at_utc"] = "2026-08-02T00:00:00Z"
  synthetic_set.write_manifest()
  assert _assess(synthetic_set)["disposition"] == "HOLD"


def test_truncated_manifest_is_rejected(synthetic_set):
  raw = synthetic_set.manifest_path.read_bytes()
  synthetic_set.manifest_path.write_bytes(raw[:len(raw) // 2])
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "JSON" in result["validation_errors"][0]


def test_replayed_observation_qualification_binding_is_rejected(synthetic_set):
  envelope = synthetic_set.manifest["requirements"][0]
  envelope["payload"]["qualification_id"] = "old-qualification-replay"
  synthetic_set.resign(envelope)
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "binding" in result["validation_errors"][0]


def test_duplicate_manifest_field_is_rejected(synthetic_set):
  raw = synthetic_set.manifest_path.read_bytes()
  assert raw.startswith(b'{"classification":')
  synthetic_set.manifest_path.write_bytes(
    raw.replace(b'{"classification":', b'{"schema":"duplicate","classification":', 1))
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "duplicate" in result["validation_errors"][0]


def test_symlink_artifact_is_rejected(synthetic_set):
  descriptor = synthetic_set.manifest["requirements"][0]["payload"]["artifacts"][0]
  path = synthetic_set.root / descriptor["path"]
  outside = synthetic_set.root / "outside.txt"
  outside.write_bytes(path.read_bytes())
  path.unlink()
  path.symlink_to(outside)
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "symlinked" in result["validation_errors"][0]


def test_path_traversal_is_rejected_even_with_valid_new_signatures(synthetic_set):
  envelope = synthetic_set.manifest["requirements"][0]
  envelope["payload"]["artifacts"][0]["path"] = "../outside.txt"
  synthetic_set.resign(envelope)
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "traversal" in result["validation_errors"][0]


def test_weakened_signature_algorithm_string_is_rejected(synthetic_set):
  synthetic_set.manifest["requirements"][0]["signatures"][0]["algorithm"] = "ed25519"
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "algorithm" in result["validation_errors"][0]


def test_wrong_or_missing_external_trust_policy_pin_is_rejected(synthetic_set):
  for pin in (None, "0" * 64, synthetic_set.policy_sha.upper()):
    result = gate.assess(
      synthetic_set.root, synthetic_set.manifest_relative, pin, now=NOW)
    assert result["disposition"] == "HOLD"
    assert result["technical_evidence_complete"] is False


def test_reused_artifact_path_cannot_satisfy_two_checks(synthetic_set):
  first = synthetic_set.manifest["requirements"][0]["payload"]["artifacts"][0]
  second_envelope = synthetic_set.manifest["requirements"][1]
  second_envelope["payload"]["artifacts"][0].update({
    key: first[key] for key in ("path", "sha256", "size_bytes")
  })
  synthetic_set.resign(second_envelope)
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "replayed" in result["validation_errors"][0]


def test_monotone_second_record_binds_exact_predecessor_and_new_nonce(synthetic_set):
  first = _assess(synthetic_set)
  previous_path = synthetic_set.root / "gatecard-1.json"
  previous_path.write_bytes(gate.canonical_json(first))
  new_nonce = "f" * 64
  progression = {
    "sequence": 2,
    "previous_gatecard": _descriptor(previous_path, synthetic_set.root),
    "run_nonce": new_nonce,
  }
  synthetic_set.manifest["progression"] = progression
  for envelope in synthetic_set.manifest["requirements"]:
    envelope["payload"]["evidence_nonce"] = new_nonce
    envelope["payload"]["progression_binding"] = copy.deepcopy(progression)
    synthetic_set.resign(envelope)
  synthetic_set.write_manifest()
  second = _assess(synthetic_set)
  assert second["disposition"] == "HOLD_SYNTHETIC_EVIDENCE_NON_DEPLOYABLE"
  assert second["progression"]["sequence"] == 2
  assert second["progression"]["previous_gatecard_sha256"] == hashlib.sha256(
    previous_path.read_bytes()).hexdigest()


def test_progression_nonce_replay_is_rejected(synthetic_set):
  first = _assess(synthetic_set)
  previous_path = synthetic_set.root / "gatecard-1.json"
  previous_path.write_bytes(gate.canonical_json(first))
  progression = {
    "sequence": 2,
    "previous_gatecard": _descriptor(previous_path, synthetic_set.root),
    "run_nonce": synthetic_set.manifest["progression"]["run_nonce"],
  }
  synthetic_set.manifest["progression"] = progression
  for envelope in synthetic_set.manifest["requirements"]:
    envelope["payload"]["progression_binding"] = copy.deepcopy(progression)
    synthetic_set.resign(envelope)
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "monotone predecessor" in result["validation_errors"][0]


def test_minimal_forged_predecessor_gatecard_is_rejected(synthetic_set):
  previous_path = synthetic_set.root / "gatecard-forged.json"
  previous_path.write_bytes(gate.canonical_json({
    "schema": gate.GATECARD_SCHEMA,
    "qualification_id": synthetic_set.manifest["qualification_id"],
    "progression": {"sequence": 1, "run_nonce": "1" * 64},
    "validated_requirements": list(gate.REQUIRED_ARTIFACTS),
  }))
  progression = {
    "sequence": 2,
    "previous_gatecard": _descriptor(previous_path, synthetic_set.root),
    "run_nonce": "f" * 64,
  }
  synthetic_set.manifest["progression"] = progression
  for envelope in synthetic_set.manifest["requirements"]:
    envelope["payload"]["evidence_nonce"] = progression["run_nonce"]
    envelope["payload"]["progression_binding"] = copy.deepcopy(progression)
    synthetic_set.resign(envelope)
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert "previous gatecard schema" in result["validation_errors"][0]


def test_relabeling_synthetic_manifest_as_physical_cannot_upgrade_it(synthetic_set):
  synthetic_set.manifest["classification"] = gate.PHYSICAL
  synthetic_set.write_manifest()
  result = _assess(synthetic_set)
  assert result["disposition"] == "HOLD"
  assert result["technical_evidence_complete"] is False
  assert result["installation_authorized"] is False


def test_gate_source_has_no_external_operation_surface():
  source_path = Path(__file__).resolve().parents[1] / "rc3_hardware_readiness_gate.py"
  source = source_path.read_text()
  tree = ast.parse(source)
  imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
              for alias in node.names}
  assert not ({"socket", "subprocess", "requests", "urllib", "can", "panda"} & imported)
  assert "abctl" not in source
  assert "--install" not in source
  assert "--boot" not in source
  assert "os.system" not in source
  assert "Popen" not in source

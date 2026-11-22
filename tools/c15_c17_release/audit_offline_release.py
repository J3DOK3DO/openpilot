#!/usr/bin/env python3
"""C15/C17 bounded offline release-evidence auditor.

Read-only verification, not a build, safety approval, receipt generator or install tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BUILT = "586da6b91ffb43e2a1e114072104b694d3c8a2b3"
C14 = "49059309672f3044f6ef4b9ca995e9c2eb146127"
C11_LOG_SHA = "4391fa9076bc12dab90dfbf43a7bce6e3e2cd1b2e2073d198d3afcbf7eaaefea"
C11_MANIFEST_SHA = "4d31e11e07f708ce84ecc286fbae9f7ea88f77ecaed6268d6bde09a5439177b9"
C11_TEST_SHA = "daf0de067e3d19e26a30188e1e6b99d14c0cd1cbbe4241c9565cd4659718441a"
REPORTS = {
    "build": ("C11_C12_HYBRID_BUILD.exit", "0"),
    "honda_arm64": ("C11_C12_FINAL_HONDA_ARM64_TESTS.exit", "0"),
    "cached_qcom_inputs": ("C11_C12_QCOM_CONTRACT.exit", "0"),
    "elf_architecture": ("C11_C12_NATIVE_ELF_ARCHITECTURE.exit", "0"),
    "artifact_manifest": ("C11_C12_ARTIFACT_SUMMARY.exit", "0"),
    "production_receipt_historically_missing": ("C11_C12_PREBUILT_RECEIPT.exit", "1"),
}
INPUT_SHA = {
    "C11_C12_SCONS_hybrid_product.log": C11_LOG_SHA,
    "C11_C12_NATIVE_ARTIFACTS_FINAL.json": C11_MANIFEST_SHA,
    "C11_C12_FINAL_HONDA_ARM64_TESTS.log": C11_TEST_SHA,
}

def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True, timeout=40).strip()

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def is_only_tools_delta(paths: list[str]) -> bool:
    return bool(paths) and all(p.startswith("tools/") and ".." not in p.split("/") for p in paths)

def decisions(data: dict) -> dict:
    source = (data.get("source_unchanged_since_build") is True and data.get("offline_evidence_verifiable") is True)
    physical = (data.get("device_qualified") is True and data.get("independent_vehicle_safety_review") is True)
    exact_receipt = data.get("current_exact_commit_production_receipt") is True
    qcom = data.get("qcom_target_inference") is True
    return {
        "c15_offline_provenance_closeable": source,
        "c15_full_production_complete": source and physical and exact_receipt and qcom,
        "c17_source_only_release_permitted": source,
        "c17_installable_release_approved": source and physical and exact_receipt and qcom,
        "c17_road_use_approved": source and physical and exact_receipt and qcom,
    }

def inspect(repo: Path, evidence: Path) -> dict:
    head = git(repo, "rev-parse", "HEAD")
    git(repo, "merge-base", "--is-ancestor", C14, head)
    changed = git(repo, "diff", "--name-only", BUILT, head).splitlines()
    assert is_only_tools_delta(changed), "Non-documentation/non-tools production code changed since C11 build"
    assert git(repo, "diff", "--name-only", BUILT, head, "--", "opendbc_repo", "openpilot", "panda", "prebuilt.json") == "", "Protected source changed"

    old = evidence / "C11_C12_COMBINED_20261121"
    assert old.is_dir(), "C11/C12 original evidence missing"
    original = (old / "C11_C12_EXACT_BUILD_RECEIPT.txt").read_text()
    assert f"EXACT_BUILD_HEAD={BUILT}" in original
    assert "FULL_GRAPH_EXIT=0" in original and "HONDA_TEST_EXIT=0" in original
    for label, (name, expected) in REPORTS.items():
        assert (old/name).read_text().strip() == expected, f"Evidence gate {label} not verified"
    for name, digest in INPUT_SHA.items():
        assert sha256(old/name) == digest, f"Evidence digest drift {name}"
        assert f"{digest}  " in original, f"Historic proof excludes digest {name}"

    assert "190 passed" in (old/"C11_C12_FINAL_HONDA_ARM64_TESTS.log").read_text()
    assert "verified_targets 5" in (old/"C11_C12_QCOM_CONTRACT.log").read_text()
    target_log = (old/"C11_C12_QCOM_TARGET_HARDWARE.log").read_text()
    target_device_missing = "/dev/kgsl-3d0 ABSENT" in target_log and "QCOM_MODE=INPUT_CONTRACT_ONLY" in target_log
    assert target_device_missing, "Never infer target GPU success from historical cached-input contract"
    assert (old/"C11_C12_DOC_COMMIT_PREBUILT_RECEIPT.exit").read_text().strip() == "1"

    p = subprocess.run([sys.executable, str(repo/"tools/ci/check_prebuilt_receipt.py"),
                        "--repo", str(repo), "--revision", "HEAD"],
                       text=True, capture_output=True, timeout=40)
    current_receipt = p.returncode == 0
    checks = {
      "checked_git_commit": head, "built_control_source_git_commit": BUILT,
      "base_c14": C14, "source_unchanged_since_build": True,
      "changed_paths_since_build_total": len(changed),
      "changed_paths_since_build_tools_only": True,
      "offline_evidence_verifiable": True,
      "prior_full_arm64_build": "PASS_REUSED_AT_BUILT_COMMIT",
      "prior_honda_arm64_tests": "190_PASS_REUSED",
      "prior_elf_architecture": "152_OF_152_AARCH64_REUSED",
      "prior_qcom_inputs": "5_CACHED_INPUTS_ONLY",
      "current_exact_commit_production_receipt": current_receipt,
      "current_receipt_validator_exit": p.returncode,
      "current_receipt_validator_reason": (p.stderr or p.stdout).strip()[-600:],
      "qcom_target_inference": False,
      "independent_vehicle_safety_review": False,
      "device_qualified": False,
      "c16_physical_gate_status": "DEFERRED_NOT_WAIVED",
      "current_firmware_identity": "NOT_VERIFIED",
      "physical_can2_controlsmismatch": "NOT_VERIFIED",
      "installation": "PROHIBITED",
      "road_use": "PROHIBITED",
    }
    checks["decision"] = decisions(checks)
    return checks

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--evidence-root", type=Path,
                        default=Path("/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence"))
    parser.add_argument("--output", type=Path)
    a = parser.parse_args()
    result = inspect(a.repo.resolve(), a.evidence_root.resolve())
    output = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(output)
    else:
        print(output)
    assert result["decision"]["c17_source_only_release_permitted"]
    assert not result["decision"]["c17_installable_release_approved"]
    assert not result["decision"]["c17_road_use_approved"]
    print("C15_OFFLINE_EVIDENCE_PASS; C17_SOURCE_ONLY_GO; C17_PRODUCTION_AND_ROAD_NO_GO")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, ValueError, FileNotFoundError, subprocess.CalledProcessError) as err:
        print("OFFLINE_AUDIT_FAIL: "+str(err), file=sys.stderr)
        raise SystemExit(1)

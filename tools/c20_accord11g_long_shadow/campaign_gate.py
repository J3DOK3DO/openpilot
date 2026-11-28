"""Deterministic R10-R13 research gate; never authorizes vehicle control."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .bundle import MAX_BYTES, MAX_MEMBERS, _check_public_entry
from .platform_receipt import BASELINE, inventory, verify_pinned_inventory
from .release_gate import gate
from .shadow_advisory import ShadowConfig
from .telemetry_gate import MAX_CAPTURE, MAX_MANIFEST, audit, read_bounded

BRANCH = "c20-r10-r12-combined-r13-prep-20261128"


def _run(args: list[str], timeout: int = 60, env: dict | None = None) -> subprocess.CompletedProcess:
  return subprocess.run(args, capture_output=True, text=True, check=False, timeout=timeout, env=env)


def privacy_scan(repo: Path) -> dict:
  listing = _run(["git", "-C", str(repo), "ls-files", "--cached", "--others", "--exclude-standard",
                  "--", "tools/c20_accord11g_long_shadow/"])
  if listing.returncode:
    return {"status": "FAIL", "files": 0}
  names = sorted(set(listing.stdout.splitlines()))
  if not names or len(names) > MAX_MEMBERS:
    return {"status": "FAIL", "files": len(names)}
  total = 0
  try:
    for name in names:
      path = repo / name
      if path.is_symlink() or not path.is_file():
        raise ValueError("nonregular entry")
      with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
      total += len(data)
      if total > MAX_BYTES:
        raise ValueError("aggregate size exceeded")
      _check_public_entry(name, data)
  except (OSError, ValueError):
    return {"status": "FAIL", "files": len(names)}
  return {"status": "PASS", "files": len(names)}


def summary(repo: Path, c19: Path, manifest: Path | None = None, capture: Path | None = None,
            run_tests: bool = False, check_receipt: bool = False) -> dict:
  if bool(manifest) != bool(capture):
    raise ValueError("manifest and capture must be supplied together")
  scope = gate(repo)
  platform = inventory(c19)
  try:
    pinned = verify_pinned_inventory(c19, Path(__file__).resolve().parent / "fixtures/r10_platform_receipt.json")
  except (OSError, ValueError, KeyError, TypeError):
    pinned = {"status": "MISMATCH", "mismatches": ["pinned inventory unreadable"]}
  branch = _run(["git", "-C", str(repo), "branch", "--show-current"]).stdout.strip()
  head = _run(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()
  original = _run(["git", "-C", str(c19), "rev-parse", "HEAD"]).stdout.strip()
  diff_check = _run(["git", "-C", str(repo), "diff", "--check"])
  privacy = privacy_scan(repo)
  no_raw = privacy["status"] == "PASS"
  tests = {"status": "NOT_RUN", "count": None}
  if run_tests:
    test_env = dict(os.environ, C20_C19_REPO=str(c19))
    result = _run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                   str(repo / "tools/c20_accord11g_long_shadow/tests"), "-q"], timeout=120, env=test_env)
    match = re.search(r"Ran (\d+) tests? in", result.stderr)
    tests = {"status": "PASS" if result.returncode == 0 and match else "FAIL",
             "count": int(match.group(1)) if match else None}
  receipt = {"status": "NOT_RUN", "c19_revision": BASELINE}
  if check_receipt:
    result = _run([sys.executable, "-B", str(c19 / "tools/ci/check_prebuilt_receipt.py"),
                   "--repo", str(c19), "--revision", BASELINE], timeout=60)
    receipt["status"] = "PASS" if result.returncode == 0 and BASELINE in result.stdout else "FAIL"
  telemetry = {"status": "NOT_SUPPLIED", "custody_authenticated": False}
  if manifest:
    try:
      report = audit(read_bounded(manifest, MAX_MANIFEST), read_bounded(capture, MAX_CAPTURE))
      telemetry = {"status": report["quality_state"], "faults": report["faults"],
                   "capture_digest_match": report["capture_digest_match"],
                   "custody_authenticated": False, "semantic_source_equivalence": report["semantic_source_equivalence"]}
    except (OSError, ValueError, TypeError, KeyError):
      telemetry = {"status": "FAIL_CLOSED", "faults": ["INVALID_INPUT"],
                   "capture_digest_match": False, "custody_authenticated": False}
  source_pass = scope["source_audit"]["status"] == "PASS" and branch == BRANCH
  baseline_pass = original == BASELINE and pinned["status"] == "MATCH"
  telemetry_pass = telemetry["status"] == "PASS_SYNTHETIC_ONLY" and telemetry.get("capture_digest_match") is True
  default_off = ShadowConfig().enabled is False
  offline_working = (source_pass and baseline_pass and diff_check.returncode == 0 and no_raw and default_off
                     and tests["status"] == "PASS" and receipt["status"] == "PASS")
  research_candidate = offline_working and telemetry_pass
  if research_candidate:
    r12_stage = "WORKING_RESEARCH_CANDIDATE"
    r13_stage = "WORKING_CANDIDATE_PENDING_COMMIT_AND_INDEPENDENT_REVIEW"
    release_decision = "PENDING_COMMIT_AND_INDEPENDENT_REVIEW"
  elif manifest and not telemetry_pass:
    r12_stage = r13_stage = "BLOCKED_TELEMETRY"
    release_decision = "NO_GO_INVALID_TELEMETRY"
  elif not manifest:
    r12_stage = r13_stage = "NOT_SUPPLIED"
    release_decision = "NO_GO_NO_TELEMETRY"
  else:
    r12_stage = r13_stage = "PENDING_CHECKS"
    release_decision = "NO_GO_CHECKS_INCOMPLETE"
  return {"schema_version": 1, "classification": "TEST_ONLY_RESEARCH", "branch": branch, "head": head,
          "c19_baseline": original, "c19_baseline_matches": original == BASELINE,
          "c19_pinned_inventory": pinned,
          "source_audit": scope["source_audit"]["status"], "source_audit_findings": scope["source_audit"]["findings"],
          "diff_check": "PASS" if diff_check.returncode == 0 else "FAIL",
          "raw_data_scope": privacy, "tests": tests, "c19_prebuilt_receipt": receipt,
          "platform": {"status": platform["native_execution_eligibility"],
                       "solver_architecture": (platform["artifacts"]["c_generated_code/acados_ocp_solver_pyx.so"] or {}).get("architecture"),
                       "host_architecture": platform["host_architecture"], "reasons": platform["reasons"],
                       "executed_solver": False},
          "telemetry": telemetry, "default_off": default_off,
          "offline_research_release_decision": release_decision,
          "stage_eligibility": {"R10_source_and_solver_prep": "SOURCE_RECEIPT_ONLY" if baseline_pass else "BLOCKED",
                                "R11_current_capture": "BLOCKED_UNVERIFIED_CUSTODY",
                                "R12_audit_only": r12_stage,
                                "R13_offline_research": r13_stage,
                                "R13_display_only_device": "BLOCKED_BUILD_AND_HARDWARE",
                                "R13_active_alpha_long": "NO_GO"},
          "A1_A5": {key: scope["gates"][key] for key in ("A1", "A2", "A3", "A4", "A5")},
          "active_alpha_long": "NO_GO", "road_deployment": "NO_GO", "archive_ready": False,
          "product_build_receipt": "NOT_VERIFIED", "independent_review": "PENDING"}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo", type=Path, default=Path.cwd())
  parser.add_argument("--c19", type=Path, required=True)
  parser.add_argument("--manifest", type=Path)
  parser.add_argument("--capture", type=Path)
  parser.add_argument("--run-tests", action="store_true")
  parser.add_argument("--check-c19-receipt", action="store_true")
  args = parser.parse_args()
  print(json.dumps(summary(args.repo, args.c19, args.manifest, args.capture,
                           args.run_tests, args.check_c19_receipt), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

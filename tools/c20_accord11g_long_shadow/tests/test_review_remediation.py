"""Focused regressions for the R10-R13 independent review findings."""
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from tools.c20_accord11g_long_shadow.bundle import PREFIX, verify
from tools.c20_accord11g_long_shadow.campaign_gate import BRANCH, summary
from tools.c20_accord11g_long_shadow.platform_receipt import BASELINE, verify_pinned_inventory
from tools.c20_accord11g_long_shadow.telemetry_gate import audit

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
MANIFEST = json.loads((FIXTURES / "r10_r12_synthetic_manifest.json").read_text())
CAPTURE = json.loads((FIXTURES / "r10_r12_synthetic_capture.json").read_text())


def encoded(value: dict) -> bytes:
  return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


class BundleManifestReviewTests(unittest.TestCase):
  def test_private_route_only_in_manifest_rejected(self):
    name = PREFIX + "example.txt"
    body = b"public synthetic evidence\n"
    manifest = {"schema": 1, "revision": "a" * 40, "branch": BRANCH, "scope": PREFIX,
                "active_alpha_long": "NO_GO", "road_deployment": "NO_GO",
                "files": {name: {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}}}
    with tempfile.TemporaryDirectory() as directory:
      path = Path(directory) / "research.tar.gz"
      def write_archive(metadata, raw_manifest=None):
        with tarfile.open(path, "w:gz") as archive:
          for member_name, content in ((name, body), ("RESEARCH_MANIFEST.json", raw_manifest or encoded(metadata))):
            info = tarfile.TarInfo(member_name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
      write_archive(manifest)
      self.assertEqual(verify(path)["files"][name]["sha256"], hashlib.sha256(body).hexdigest())
      private = copy.deepcopy(manifest)
      private["extra"] = "1234abcd" + "--" + "0123456789"
      write_archive(private)
      with self.assertRaisesRegex(ValueError, "private route"):
        verify(path)
      private["extra"] = "unrecognized metadata"
      write_archive(private)
      with self.assertRaisesRegex(ValueError, "manifest schema"):
        verify(path)
      encoded_route = copy.deepcopy(manifest)
      encoded_route["branch"] = "topic/" + "1234abcd" + "--" + "0123456789"
      route_bytes = encoded(encoded_route).replace(b"1234abcd", b"\\u0031234abcd")
      write_archive(encoded_route, route_bytes)
      with self.assertRaisesRegex(ValueError, "private route"):
        verify(path)


class PinnedInventoryReviewTests(unittest.TestCase):
  def test_host_facts_are_informational_but_missing_or_changed_artifact_blocks(self):
    fixture = json.loads((FIXTURES / "r10_platform_receipt.json").read_text())
    observed = copy.deepcopy(fixture)
    observed["host_architecture"] = "aarch64"
    observed["python_version"] = "3.14.0"
    observed["readelf_version"] = "other readelf"
    observed["python_dependencies"] = {"numpy": False}
    observed["reasons"] = ["host differs"]
    observed["native_execution_eligibility"] = "PLATFORM_ONLY_INPUTS_PENDING"
    receipt = FIXTURES / "r10_platform_receipt.json"
    with patch("tools.c20_accord11g_long_shadow.platform_receipt.inventory", return_value=observed):
      self.assertEqual(verify_pinned_inventory(Path("/unused"), receipt)["status"], "MATCH")
    solver = "c_generated_code/acados_ocp_solver_pyx.so"
    for changed in (None, {**observed["artifacts"][solver], "sha256": "0" * 64}):
      altered = copy.deepcopy(observed)
      altered["artifacts"][solver] = changed
      with patch("tools.c20_accord11g_long_shadow.platform_receipt.inventory", return_value=altered):
        result = verify_pinned_inventory(Path("/unused"), receipt)
      self.assertEqual(result["status"], "MISMATCH")
      self.assertIn("artifact: " + solver, result["mismatches"])
      self.assertFalse(result["executed_solver"])


class ModelHistoryReviewTests(unittest.TestCase):
  def report(self, mutate):
    capture = copy.deepcopy(CAPTURE)
    mutate(capture)
    raw = encoded(capture)
    manifest = copy.deepcopy(MANIFEST)
    manifest["capture_sha256"] = hashlib.sha256(raw).hexdigest()
    return audit(encoded(manifest), raw)

  def test_radar_selected_60ms_prior_model_frame_passes(self):
    def select_prior(capture):
      first, second = capture["cycles"]
      second["radar_md_mono_time_ns"] = first["services"]["modelV2"]["source_t_ns"]
      second["model_leads"] = copy.deepcopy(first["model_leads"])
    report = self.report(select_prior)
    self.assertEqual(report["quality_state"], "PASS_SYNTHETIC_ONLY")
    self.assertEqual(CAPTURE["cycles"][1]["cycle_t_ns"] - CAPTURE["cycles"][0]["services"]["modelV2"]["source_t_ns"], 60_000_000)

  def test_unknown_future_and_stale_history_rejected(self):
    unknown = self.report(lambda c: c["cycles"][1].update(radar_md_mono_time_ns=1_010_000_000))
    self.assertIn("MODEL_LEAD_SOURCE_MISMATCH", unknown["faults"])
    future = self.report(lambda c: c["cycles"][1]["model_leads"][0].update(source_t_ns=1_060_000_000))
    self.assertIn("FUTURE_SAMPLE", future["faults"])
    stale = self.report(lambda c: c["cycles"][1]["model_lead_history"][0].update(source_t_ns=1))
    self.assertIn("SENSOR_STALE", stale["faults"])


class CampaignDecisionReviewTests(unittest.TestCase):
  def mocked_summary(self, manifest=None, capture=None, pinned_status="MATCH"):
    def fake_run(args, timeout=60, env=None):
      if "unittest" in args:
        return subprocess.CompletedProcess(args, 0, "", "Ran 75 tests in 0.1s\n\nOK\n")
      if "check_prebuilt_receipt.py" in " ".join(args):
        return subprocess.CompletedProcess(args, 0, BASELINE, "")
      if "branch" in args:
        output = BRANCH
      elif "rev-parse" in args:
        output = BASELINE
      else:
        output = ""
      return subprocess.CompletedProcess(args, 0, output, "")
    scope = {"source_audit": {"status": "PASS", "findings": []},
             "gates": {key: "NO_GO" for key in ("A1", "A2", "A3", "A4", "A5")}}
    platform = {"native_execution_eligibility": "BLOCKED", "host_architecture": "x86_64",
                "artifacts": {"c_generated_code/acados_ocp_solver_pyx.so": {"architecture": "aarch64"}},
                "reasons": ["host mismatch"]}
    with patch("tools.c20_accord11g_long_shadow.campaign_gate.gate", return_value=scope), \
         patch("tools.c20_accord11g_long_shadow.campaign_gate.inventory", return_value=platform), \
         patch("tools.c20_accord11g_long_shadow.campaign_gate.verify_pinned_inventory",
               return_value={"status": pinned_status, "mismatches": ["artifact changed"] if pinned_status != "MATCH" else []}), \
         patch("tools.c20_accord11g_long_shadow.campaign_gate.privacy_scan", return_value={"status": "PASS", "files": 1}), \
         patch("tools.c20_accord11g_long_shadow.campaign_gate._run", side_effect=fake_run):
      return summary(Path("/unused/repo"), Path("/unused/c19"), manifest, capture, True, True)

  def test_bad_supplied_capture_blocks_r12_r13_with_other_checks_passing(self):
    with tempfile.TemporaryDirectory() as directory:
      bad = Path(directory) / "bad.json"
      bad.write_text("{}")
      report = self.mocked_summary(FIXTURES / "r10_r12_synthetic_manifest.json", bad)
    self.assertEqual(report["telemetry"]["status"], "FAIL_CLOSED")
    self.assertEqual(report["stage_eligibility"]["R10_source_and_solver_prep"], "SOURCE_RECEIPT_ONLY")
    self.assertEqual(report["stage_eligibility"]["R12_audit_only"], "BLOCKED_TELEMETRY")
    self.assertEqual(report["stage_eligibility"]["R13_offline_research"], "BLOCKED_TELEMETRY")
    self.assertEqual(report["active_alpha_long"], "NO_GO")

  def test_valid_synthetic_digest_required_and_absence_is_explicit(self):
    good = self.mocked_summary(FIXTURES / "r10_r12_synthetic_manifest.json",
                               FIXTURES / "r10_r12_synthetic_capture.json")
    self.assertEqual(good["stage_eligibility"]["R12_audit_only"], "WORKING_RESEARCH_CANDIDATE")
    self.assertEqual(good["stage_eligibility"]["R13_offline_research"],
                     "WORKING_CANDIDATE_PENDING_COMMIT_AND_INDEPENDENT_REVIEW")
    absent = self.mocked_summary()
    self.assertEqual(absent["telemetry"]["status"], "NOT_SUPPLIED")
    self.assertEqual(absent["stage_eligibility"]["R12_audit_only"], "NOT_SUPPLIED")
    self.assertEqual(absent["stage_eligibility"]["R13_offline_research"], "NOT_SUPPLIED")
    with tempfile.TemporaryDirectory() as directory:
      tampered = Path(directory) / "capture.json"
      content = copy.deepcopy(CAPTURE)
      content["cycles"][0]["gas_pressed"] = True
      tampered.write_bytes(encoded(content))
      digest_failure = self.mocked_summary(FIXTURES / "r10_r12_synthetic_manifest.json", tampered)
    self.assertFalse(digest_failure["telemetry"]["capture_digest_match"])
    self.assertEqual(digest_failure["stage_eligibility"]["R13_offline_research"], "BLOCKED_TELEMETRY")

  def test_pinned_artifact_mismatch_blocks_r10_and_working_candidates(self):
    report = self.mocked_summary(FIXTURES / "r10_r12_synthetic_manifest.json",
                                 FIXTURES / "r10_r12_synthetic_capture.json", pinned_status="MISMATCH")
    self.assertEqual(report["c19_baseline"], BASELINE)
    self.assertEqual(report["c19_pinned_inventory"]["status"], "MISMATCH")
    self.assertEqual(report["stage_eligibility"]["R10_source_and_solver_prep"], "BLOCKED")
    self.assertNotIn("WORKING", report["stage_eligibility"]["R12_audit_only"])
    self.assertNotIn("WORKING", report["stage_eligibility"]["R13_offline_research"])


if __name__ == "__main__":
  unittest.main()

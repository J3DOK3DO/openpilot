"""R14 local native evidence and sanitized temporal audit regressions."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.c20_accord11g_long_shadow import campaign_gate, native_host
from tools.c20_accord11g_long_shadow.platform_receipt import BASELINE
from tools.c20_accord11g_long_shadow.telemetry_gate import audit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "fixtures/r10_r12_synthetic_manifest.json").read_text())
CAPTURE = json.loads((ROOT / "fixtures/r10_r12_synthetic_capture.json").read_text())
C19 = Path(os.environ.get("C20_C19_REPO", "/home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124"))
CAPTURED_C19 = Path("/home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124")
ACADOS = Path("/home/jdkd/.cache/uv/archive-v0/JcZjHB62Lhiu78Ir/comma_deps_acados-0.2.2.post103.data/purelib/acados/install")
EVIDENCE = Path("/home/jdkd/C20_RESEARCH_EVIDENCE_R14_SOFTWARE_20261128/native_x86")
RECEIPT_SHA = "07452c960a0fd47211d26a2b81bcc135cafbf794a3a136e17c3db709fcc60b4c"


def encoded(value: dict) -> bytes:
  return (json.dumps(value, sort_keys=True) + "\n").encode()


class NativeHostVerifierTests(unittest.TestCase):
  def setUp(self):
    self.temporary = tempfile.TemporaryDirectory()
    self.addCleanup(self.temporary.cleanup)
    self.root = Path(self.temporary.name)
    self.repo = self.root / "c19"
    self.acados = self.root / "acados"
    self.output = self.root / "evidence"
    self.src = [self.repo / native_host.GENERATED / "main_long.c"]
    self.output.mkdir()
    (self.output / "main_long_x86").write_bytes(b"synthetic test binary")
    logs = {"build_stdout.log": b"", "build_stderr.log": b"", "run_stderr.log": b"",
            "run_stdout.log": b"solved ocp 1 times, solution printed above\nlong_acados_solve(): SUCCESS!\n SQP iterations  1\n"}
    for name, content in logs.items():
      (self.output / name).write_bytes(content)
    self.receipt = {"schema_version": 1, "classification": "REBUILT_GENERATED_SOLVER_CYCLE",
                    "source_commit": BASELINE, "host_architecture": "x86_64", "compiler": "test gcc",
                    "source_sha256": {"main_long.c": "a" * 64},
                    "library_sha256": {"libacados.so": "b" * 64},
                    "cached_headers_tree_sha256": "c" * 64,
                    "build_command": native_host._build_command(self.repo, self.acados, self.output, self.src),
                    "build_exit": 0, "run_exit": 0, "cycle_count": 1, "sqp_iterations": 1,
                    "binary_sha256": native_host.digest(self.output / "main_long_x86"),
                    "log_sha256": {name: native_host.digest(self.output / name) for name in logs},
                    "planner_replay": "NOT_DONE", "input_classification": "SYNTHETIC_GENERATED_MAIN",
                    "independent_authenticity": "UNVERIFIED"}

  def verify(self):
    raw = encoded(self.receipt)
    (self.output / "native_receipt.json").write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    with patch.object(native_host, "_revision", return_value=BASELINE), \
         patch.object(native_host, "_clean", return_value=True), \
         patch.object(native_host, "source_hashes", return_value={"main_long.c": "a" * 64}), \
         patch.object(native_host, "library_hashes", return_value={"libacados.so": "b" * 64}), \
         patch.object(native_host, "header_tree_digest", return_value="c" * 64), \
         patch.object(native_host, "sources", return_value=self.src), \
         patch.object(native_host, "elf_machine", return_value="x86_64"):
      return native_host.verify(self.repo, self.acados, self.output, expected)

  def test_consistent_receipt_never_authenticates_origin(self):
    result = self.verify()
    self.assertEqual(result["status"], "LOCAL_EVIDENCE_CONSISTENT_UNAUTHENTICATED")
    self.assertFalse(result["independent_authenticity_verified"])

  def test_source_or_binary_substitution_fails(self):
    self.receipt["source_sha256"]["main_long.c"] = "0" * 64
    self.assertIn("generated source mismatch", self.verify()["reasons"])
    self.receipt["source_sha256"]["main_long.c"] = "a" * 64
    (self.output / "main_long_x86").write_bytes(b"different")
    self.assertIn("binary mismatch or architecture", self.verify()["reasons"])

  def test_cycle_and_log_substitution_fails(self):
    self.receipt["cycle_count"] = 2
    self.assertIn("cycle claim mismatch", self.verify()["reasons"])
    self.receipt["cycle_count"] = 1
    (self.output / "run_stdout.log").write_bytes(b"invented success")
    reasons = self.verify()["reasons"]
    self.assertIn("log digest mismatch: run_stdout.log", reasons)
    self.assertIn("cycle claim mismatch", reasons)

  def test_rehashed_false_build_command_and_input_variants_fail(self):
    self.assertEqual(self.verify()["status"], "LOCAL_EVIDENCE_CONSISTENT_UNAUTHENTICATED")
    canonical = self.receipt["build_command"]
    for changed in (["true"], [*canonical[:3], "-O2", *canonical[3:]],
                    [arg.replace("-I", "-I/other/") if arg.startswith("-I") else arg for arg in canonical],
                    [arg.replace("-L", "-L/other/") if arg.startswith("-L") else arg for arg in canonical],
                    ["-lwrong" if arg == "-lacados" else arg for arg in canonical],
                    [arg.replace("main_long_x86", "other_binary") for arg in canonical],
                    [arg.replace("main_long.c", "other.c") for arg in canonical]):
      self.receipt["build_command"] = changed
      with self.subTest(changed=changed):
        self.assertIn("build command mismatch", self.verify()["reasons"])
    self.receipt["build_command"] = canonical


class NativeOutputSafetyTests(unittest.TestCase):
  def test_unsafe_paths_abort_before_any_subprocess_or_write(self):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      c19 = root / "c19"
      c19.mkdir()
      acados = root / "acados"
      acados.mkdir()
      evidence = root / "evidence"
      evidence.mkdir()
      linked_parent = root / "linked_parent"
      linked_parent.symlink_to(c19, target_is_directory=True)
      linked_output = root / "linked_output"
      linked_output.symlink_to(c19, target_is_directory=True)
      artifact_target = root / "target"
      artifact_target.write_text("untouched")
      with patch.object(native_host, "_run", side_effect=AssertionError("subprocess ran")):
        for unsafe in (linked_parent / "nested", linked_parent / ".." / "evidence" / "new",
                       linked_output, c19, c19 / "generated",
                       ROOT / "unsafe_output_regression"):
          with self.subTest(unsafe=unsafe), self.assertRaises(ValueError):
            native_host.build(c19, acados, unsafe)
        for name in native_host.OUTPUT_FILES:
          link = evidence / name
          link.symlink_to(artifact_target)
          with self.subTest(name=name), self.assertRaises(ValueError):
            native_host.build(c19, acados, evidence)
          link.unlink()
      self.assertEqual(artifact_target.read_text(), "untouched")
      self.assertFalse((c19 / "generated").exists())


@unittest.skipUnless(C19 == CAPTURED_C19 and ACADOS.is_dir() and
                     (EVIDENCE / "native_receipt.json").is_file(), "captured native evidence unavailable")
class CapturedNativeAndCampaignTests(unittest.TestCase):
  def test_captured_command_is_canonical_and_receipt_verifies(self):
    captured = json.loads((EVIDENCE / "native_receipt.json").read_text())
    expected = native_host._build_command(C19.resolve(), ACADOS.resolve(), EVIDENCE.resolve(),
                                          native_host.sources(C19.resolve() / native_host.GENERATED))
    self.assertEqual(captured["build_command"], expected)
    self.assertEqual(native_host.verify(C19, ACADOS, EVIDENCE, RECEIPT_SHA)["status"],
                     "LOCAL_EVIDENCE_CONSISTENT_UNAUTHENTICATED")

  def test_r14_gate_blocks_absent_and_tampered_native_evidence(self):
    original_run = campaign_gate._run
    def completed_checks(args, timeout=60, env=None):
      if args[-2:] == ['branch', '--show-current']:
        return subprocess.CompletedProcess(args, 0, campaign_gate.R15_BRANCH + '\n', '')
      if "unittest" in args:
        return subprocess.CompletedProcess(args, 0, "", "Ran 86 tests in 0.1s\n\nOK\n")
      if any("check_prebuilt_receipt.py" in str(arg) for arg in args):
        return subprocess.CompletedProcess(args, 0, BASELINE, "")
      return original_run(args, timeout=timeout, env=env)
    manifest = ROOT / "fixtures/r10_r12_synthetic_manifest.json"
    capture = ROOT / "fixtures/r10_r12_synthetic_capture.json"
    historical_scope = campaign_gate.gate(ROOT.parents[1])
    historical_scope['source_audit'] = {'status': 'PASS', 'findings': []}
    with patch.object(campaign_gate, "_run", side_effect=completed_checks), \
         patch.object(campaign_gate, 'gate', return_value=historical_scope):
      absent = campaign_gate.summary(ROOT.parents[1], C19, manifest, capture, True, True)
      tampered = campaign_gate.summary(ROOT.parents[1], C19, manifest, capture, True, True,
                                       ACADOS, EVIDENCE, "0" * 64)
      good = campaign_gate.summary(ROOT.parents[1], C19, manifest, capture, True, True,
                                   ACADOS, EVIDENCE, RECEIPT_SHA)
    for report in (absent, tampered):
      self.assertEqual(report["offline_research_release_decision"], "BLOCKED_NATIVE_OR_SOFTWARE_CHECKS")
      self.assertEqual(report["stage_eligibility"]["R14_software_research"],
                       report["offline_research_release_decision"])
      self.assertEqual(report["active_alpha_long"], "NO_GO")
      self.assertEqual(report["road_deployment"], "NO_GO")
    self.assertEqual(tampered["native_x86_generated_cycle"]["status"], "REJECTED")
    self.assertEqual(good["offline_research_release_decision"], "PENDING_HOST_COMMIT_AND_INDEPENDENT_REVIEW")
    self.assertEqual(good["stage_eligibility"]["R14_software_research"],
                     good["offline_research_release_decision"])
    self.assertEqual(good["hardware_qualification"]["verification"], "UNVERIFIED")
    self.assertEqual(good["active_alpha_long"], "NO_GO")
    self.assertEqual(good["road_deployment"], "NO_GO")


class TemporalJoinTests(unittest.TestCase):
  def report(self, change=None):
    capture = copy.deepcopy(CAPTURE)
    manifest = copy.deepcopy(MANIFEST)
    if change:
      change(capture)
    raw = encoded(capture)
    manifest["capture_sha256"] = hashlib.sha256(raw).hexdigest()
    return audit(encoded(manifest), raw)

  def test_prior_observed_model_frame_can_join(self):
    def change(capture):
      cycle = capture["cycles"][1]
      prior = cycle["model_lead_history"][0]
      cycle["radar_md_mono_time_ns"] = prior["source_t_ns"]
      for lead, digest in zip(cycle["model_leads"], prior["lead_payload_sha256"], strict=True):
        lead.update(source_t_ns=prior["source_t_ns"], receipt_t_ns=prior["receipt_t_ns"], payload_sha256=digest)
    report = self.report(change)
    self.assertEqual(report["classification"], "SANITIZED_TEMPORAL_JOIN")
    self.assertEqual(report["quality_state"], "PASS_SYNTHETIC_ONLY")
    self.assertEqual(report["native_c19_planner_replay"], "NOT_DONE")

  def test_fault_event_locks_and_records_cycle(self):
    report = self.report(lambda c: c["cycles"][1].update(brake_pressed=True))
    self.assertEqual(report["audit_state"], "FAULT_LOCKED")
    self.assertEqual(report["fault_events"][1]["new_faults"], ["DRIVER_OVERRIDE"])

  def test_cross_service_source_skew_fails_closed(self):
    report = self.report(lambda c: c["cycles"][0]["services"]["carControl"].update(source_t_ns=700_000_000))
    self.assertIn("SOURCE_SKEW", report["faults"])
    self.assertEqual(report["source_skew_ns"]["max_ns"], 290_000_000)


if __name__ == "__main__":
  unittest.main()

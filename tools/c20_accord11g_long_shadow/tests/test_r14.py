"""R14 local native evidence and sanitized temporal audit regressions."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.c20_accord11g_long_shadow import native_host
from tools.c20_accord11g_long_shadow.platform_receipt import BASELINE
from tools.c20_accord11g_long_shadow.telemetry_gate import audit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "fixtures/r10_r12_synthetic_manifest.json").read_text())
CAPTURE = json.loads((ROOT / "fixtures/r10_r12_synthetic_capture.json").read_text())


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
                    "cached_headers_tree_sha256": "c" * 64, "build_command": ["gcc"],
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

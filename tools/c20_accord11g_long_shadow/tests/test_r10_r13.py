"""Negative evidence and audit-only fault tests. Fixtures are synthetic."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.c20_accord11g_long_shadow.platform_receipt import BASELINE, inventory, verify_external, verify_pinned_inventory
from tools.c20_accord11g_long_shadow.bundle import _check_public_entry
from tools.c20_accord11g_long_shadow.telemetry_gate import (MAX_CAPTURE, MAX_MANIFEST, audit, csv_summary,
                                                             read_bounded)

ROOT = Path(__file__).resolve().parents[1]
C19 = Path("/home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124")
MANIFEST = json.loads((ROOT / "fixtures/r10_r12_synthetic_manifest.json").read_text())
CAPTURE = json.loads((ROOT / "fixtures/r10_r12_synthetic_capture.json").read_text())


def encoded(obj: dict) -> bytes:
  return (json.dumps(obj, sort_keys=True, indent=2) + "\n").encode()


def result(change=None, manifest_change=None, bind=True):
  c = copy.deepcopy(CAPTURE)
  m = copy.deepcopy(MANIFEST)
  if change:
    change(c)
  if manifest_change:
    manifest_change(m)
  raw = encoded(c)
  if bind:
    m["capture_sha256"] = hashlib.sha256(raw).hexdigest()
  return audit(encoded(m), raw)


class TelemetryGateTests(unittest.TestCase):
  def test_synthetic_only_and_deterministic_csv(self):
    one = result()
    self.assertEqual(one["quality_state"], "PASS_SYNTHETIC_ONLY")
    self.assertEqual(one["audit_state"], "OBSERVING")
    self.assertFalse(one["custody_authenticated"])
    self.assertEqual(one["semantic_source_equivalence"], "UNVERIFIED_SERIALIZED_MESSAGES_ABSENT")
    self.assertEqual(one["gaps_ns"]["modelV2"]["p90_ns"], 50_000_000)
    self.assertEqual(csv_summary(one), csv_summary(result()))
    self.assertNotIn("acceleration", csv_summary(one))

  def test_current_self_report_never_qualifies(self):
    report = result(lambda c: c.update(label="CURRENT_UNVERIFIED"),
                    lambda m: m.update(label="CURRENT_UNVERIFIED"))
    self.assertEqual(report["quality_state"], "FAIL_CLOSED")
    self.assertEqual(report["provenance"], "UNVERIFIED_SELF_REPORT")

  def test_bad_attestation_rejected(self):
    with self.assertRaises(ValueError):
      result(manifest_change=lambda m: m.update(attestation="SIGNED"))

  def test_duplicate_key_rejected(self):
    raw = encoded(CAPTURE).replace(b'"schema_version": 1,', b'"schema_version": 1, "schema_version": 1,')
    with self.assertRaises(ValueError):
      audit(encoded(MANIFEST), raw)

  def test_unknown_key_rejected(self):
    with self.assertRaises(ValueError):
      result(lambda c: c["cycles"][0].update(route_id="private"))

  def test_oversize_and_symlink_rejected(self):
    with self.assertRaises(ValueError):
      audit(b" " * (MAX_MANIFEST + 1), encoded(CAPTURE))
    with tempfile.TemporaryDirectory() as d:
      p = Path(d) / "large"
      p.write_bytes(b"x" * (MAX_CAPTURE + 1))
      with self.assertRaises(ValueError):
        read_bounded(p, MAX_CAPTURE)
      link = Path(d) / "link"
      link.symlink_to(p)
      with self.assertRaises(ValueError):
        read_bounded(link, MAX_CAPTURE)

  def test_capture_digest_substitution(self):
    report = result(lambda c: c["cycles"][0].update(gas_pressed=True), bind=False)
    self.assertIn("CAPTURE_DIGEST_MISMATCH", report["faults"])
    self.assertEqual(report["audit_state"], "FAULT_LOCKED")

  def test_conflicting_source_identity(self):
    report = result(lambda c: c.update(dbc_sha256="0" * 64, ecu_firmware_sha256="1" * 64))
    self.assertIn("SOURCE_IDENTITY_CONFLICT", report["faults"])

  def test_missing_receipt(self):
    report = result(lambda c: c["cycles"][1]["services"]["modelV2"].pop("receipt_t_ns"))
    self.assertIn("RECEIPT_OR_PAYLOAD_MISSING", report["faults"])
    self.assertEqual(report["type_length_validation"], "FAIL")

  def test_stale_and_future(self):
    stale = result(lambda c: c["cycles"][1]["services"]["radarState"].update(source_t_ns=1))
    self.assertIn("SENSOR_STALE", stale["faults"])
    future = result(lambda c: c["cycles"][1]["services"]["carState"].update(source_t_ns=2_000_000_000))
    self.assertIn("FUTURE_SAMPLE", future["faults"])

  def test_model_lead_dropped_and_source_mismatch(self):
    dropped = result(lambda c: c["cycles"][1].update(model_leads=[]))
    self.assertIn("MODEL_LEAD_DROPPED", dropped["faults"])
    mismatch = result(lambda c: c["cycles"][1]["model_leads"][0].update(source_t_ns=1_020_000_000))
    self.assertIn("MODEL_LEAD_SOURCE_MISMATCH", mismatch["faults"])

  def test_lead_loss_and_driver_override(self):
    report = result(lambda c: c["cycles"][1].update(lead_present=False, gas_pressed=True, brake_pressed=True))
    self.assertIn("LEAD_LOSS", report["faults"])
    self.assertIn("DRIVER_OVERRIDE", report["faults"])

  def test_reset_and_replay_across_drives(self):
    reset = result(lambda c: c["cycles"][1].update(reset_boundary=True))
    self.assertIn("UNEXPECTED_RESET", reset["faults"])
    changed = result(lambda c: c["cycles"][1].update(drive_token_sha256="f" * 64))
    self.assertIn("ROUTE_MISMATCH", changed["faults"])
    self.assertIn("RESET_BOUNDARY_MISSING", changed["faults"])

  def test_clock_disagreement_and_nonmonotonic(self):
    clock = result(lambda c: c["cycles"][1].update(clock_disagreement=True))
    self.assertIn("CLOCK_DISAGREEMENT", clock["faults"])
    repeated = result(lambda c: c["cycles"][1].update(cycle_t_ns=c["cycles"][0]["cycle_t_ns"]))
    self.assertIn("NONMONOTONIC_CYCLE", repeated["faults"])
    service = result(lambda c: c["cycles"][1]["services"]["carState"].update(source_t_ns=980_000_000))
    self.assertIn("NONMONOTONIC_SERVICE", service["faults"])

  def test_measured_service_gap_fault(self):
    def change(c):
      second = c["cycles"][1]
      second["cycle_t_ns"] += 600_000_000
      for sample in list(second["services"].values()) + second["model_leads"]:
        sample["source_t_ns"] += 600_000_000
        sample["receipt_t_ns"] += 600_000_000
    report = result(change)
    self.assertIn("SERVICE_GAP", report["faults"])
    self.assertEqual(report["gaps_ns"]["modelV2"]["max_ns"], 650_000_000)

  def test_missing_state_and_source_integrity(self):
    report = result(lambda c: (c["cycles"][1]["state_sha256"].pop("preferences"),
                               c["cycles"][1].update(source_integrity=False)))
    self.assertIn("PLANNER_STATE_MISSING", report["faults"])
    self.assertIn("SOURCE_INTEGRITY_FAILURE", report["faults"])


class PlatformReceiptTests(unittest.TestCase):
  def test_pinned_source_receipt_is_not_execution(self):
    report = inventory(C19)
    self.assertEqual(report["c19_commit"], BASELINE)
    self.assertEqual(report["model_options"]["N"], 12)
    self.assertEqual(report["native_execution_eligibility"], "BLOCKED")
    self.assertEqual(report["artifacts"]["c_generated_code/acados_ocp_solver_pyx.so"]["architecture"], "aarch64")
    self.assertFalse(report["executed_solver"])
    self.assertEqual(verify_pinned_inventory(C19, ROOT / "fixtures/r10_platform_receipt.json")["status"], "MATCH")

  def test_external_reference_only(self):
    local = inventory(C19)
    receipt = {"schema_version": 1, "classification": "EXTERNAL_NATIVE_EXECUTION", "source_commit": BASELINE,
               "solver_sha256": local["artifacts"]["c_generated_code/acados_ocp_solver_pyx.so"]["sha256"],
               "solver_architecture": "aarch64", "execution_architecture": "aarch64", "executed_solver": True,
               "cycle_count": 2, "input_digest_sha256": "2" * 64}
    with tempfile.TemporaryDirectory() as d:
      path = Path(d) / "receipt.json"
      path.write_bytes(encoded(receipt))
      digest = hashlib.sha256(path.read_bytes()).hexdigest()
      report = verify_external(C19, path, digest)
      self.assertEqual(report["status"], "REFERENCE_MATCH_UNVERIFIED")
      self.assertFalse(report["executed_solver_verified"])
      self.assertEqual(verify_external(C19, path, "0" * 64)["status"], "REJECTED")
      receipt["execution_architecture"] = "x86_64"
      path.write_bytes(encoded(receipt))
      report = verify_external(C19, path, hashlib.sha256(path.read_bytes()).hexdigest())
      self.assertIn("solver/execution architecture mismatch", report["reasons"])
      receipt["execution_architecture"] = "aarch64"
      receipt["solver_sha256"] = None
      path.write_bytes(encoded(receipt))
      report = verify_external(C19, path, hashlib.sha256(path.read_bytes()).hexdigest())
      self.assertIn("solver artifact digest mismatch", report["reasons"])


class ArchivePrivacyTests(unittest.TestCase):
  def test_raw_media_and_route_stem_rejected(self):
    _check_public_entry("tools/c20_accord11g_long_shadow/fixture.json", b'{"label":"SYNTHETIC"}')
    with self.assertRaises(ValueError):
      _check_public_entry("tools/c20_accord11g_long_shadow/log.rlog", b"x")
    with self.assertRaises(ValueError):
      _check_public_entry("tools/c20_accord11g_long_shadow/fixture.json", b'"1234abcd' + b'--0123456789"')


if __name__ == "__main__":
  unittest.main()

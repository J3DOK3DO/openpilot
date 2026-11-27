from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.c20_accord11g_long_shadow.admission import admit, reference_digest, Status, validate_rows
from tools.c20_accord11g_long_shadow.inventory import inventory
from tools.c20_accord11g_long_shadow.native_preflight import elf_machine, qualify
from tools.c20_accord11g_long_shadow.release_gate import source_audit
from tools.c20_accord11g_long_shadow.scenarios import suite
from tools.c20_accord11g_long_shadow.tests.test_research import TRACE, ROWS, manifest, reference

ROOT = Path(__file__).resolve().parents[3]


class InventoryTests(unittest.TestCase):
  def test_bounded_hash_and_no_identity_inference(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      (root / "rlog.zst").write_bytes(b"example")
      (root / "manifest.json").write_text('{"route_id":"x"}')
      found = inventory([root], max_files=3)
      self.assertEqual(found["authentic_verified_routes"], 0)
      self.assertEqual(len(found["entries"]), 2)
      self.assertEqual(next(x for x in found["entries"] if x["kind"] == "RAW_LOG")["sha256"], hashlib.sha256(b"example").hexdigest())
      (root / "rlog.bz2").symlink_to(root / "rlog.zst")
      self.assertEqual(inventory([root], max_files=4)["authentic_verified_routes"], 0)
      self.assertTrue(any(x["kind"] == "REJECTED_SYMLINK_OR_NONFILE" for x in inventory([root], max_files=4)["entries"]))
      with self.assertRaises(ValueError):
        inventory([root], max_files=2001)


class NativeTests(unittest.TestCase):
  def test_elf_parser_and_no_execution_claim(self):
    with tempfile.TemporaryDirectory() as temp:
      path = Path(temp) / "solver.so"
      path.write_bytes(b"\x7fELF" + bytes([2, 1]) + bytes(12) + (0xb7).to_bytes(2, "little"))
      self.assertEqual(elf_machine(path), "aarch64")
    report = qualify(ROOT)
    self.assertEqual(report["label"], "NATIVE_C19_MPC")
    self.assertFalse(report["executed_solver"])
    self.assertEqual(report["status"], "BLOCKED")


class AdversarialTests(unittest.TestCase):
  def test_reference_binds_timestamps_and_units(self):
    m = manifest()
    for field, value in (("start_ns", 9), ("units", {"speed": "mph"}), ("source_kind", "SIMULATED")):
      r = reference(m)
      r[field] = value
      self.assertEqual(admit(m, TRACE, r, reference_digest(r)).status, Status.MISMATCH)

  def test_partial_stale_future_and_duplicate_record_rejected(self):
    rows = copy.deepcopy(ROWS)
    rows[1]["lead"]["t_ns"] = 1
    self.assertTrue(validate_rows(rows))
    rows = copy.deepcopy(ROWS)
    del rows[1]["signal_t_ns"]["pitch"]
    self.assertTrue(validate_rows(rows))
    rows = copy.deepcopy(ROWS)
    rows[2]["signal_t_ns"]["v_ego"] = rows[2]["t_ns"] + 1
    self.assertTrue(validate_rows(rows))

  def test_scenarios_same_cycle_and_bounded(self):
    output = suite()
    self.assertEqual(output["mode"], "SIMULATED")
    self.assertFalse(output["vehicle_response_verified"])
    self.assertGreaterEqual(len(output["cases"]), 8)
    for item in output["cases"].values():
      self.assertEqual(item["c6"]["samples"], item["c19"]["samples"])
      self.assertEqual(len(item["deltas"]), item["c6"]["samples"])
      self.assertTrue(all(abs(x["c6_minus_c19_accel_mps2"]) <= 14 for x in item["deltas"]))
    self.assertGreater(output["cases"]["cut_in"]["c6"]["counts"].get("lead_transition", 0), 0)
    self.assertGreater(output["cases"]["phantom"]["c6"]["counts"].get("low_confidence_vision_ignored", 0), 0)

  def test_scope_audit(self):
    audit = source_audit(ROOT)
    self.assertEqual(audit["status"], "PASS", audit["findings"])


if __name__ == "__main__":
  unittest.main()

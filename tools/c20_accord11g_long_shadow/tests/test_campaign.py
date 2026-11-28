from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.c20_accord11g_long_shadow.admission import admit, reference_digest, Status, validate_rows
from tools.c20_accord11g_long_shadow import inventory as inventory_module
from tools.c20_accord11g_long_shadow.inventory import inventory
from tools.c20_accord11g_long_shadow.native_preflight import LIBRARIES, SOLVER, elf_machine, qualify
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

  def test_metadata_fields_are_from_hashed_snapshot(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      path = root / "manifest.json"
      original = b'{"route_id":"first"}'
      path.write_bytes(original)
      read_snapshot = inventory_module._read_snapshot

      def mutate_after_snapshot(file_path, *, metadata):
        result = read_snapshot(file_path, metadata=metadata)
        file_path.write_bytes(b'{"vehicle":"second"}')
        return result

      with patch.object(inventory_module, "_read_snapshot", side_effect=mutate_after_snapshot):
        item = inventory([root])["entries"][0]
      self.assertEqual(item["sha256"], hashlib.sha256(original).hexdigest())
      self.assertEqual(item["bytes"], len(original))
      self.assertEqual(item["fields_present"], ["route_id"])

  def test_disappearing_metadata_fails_closed(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      path = root / "manifest.json"
      path.write_bytes(b'{}')
      read_snapshot = inventory_module._read_snapshot

      def remove_before_open(file_path, *, metadata):
        file_path.unlink()
        return read_snapshot(file_path, metadata=metadata)

      with patch.object(inventory_module, "_read_snapshot", side_effect=remove_before_open):
        self.assertEqual(inventory([root])["entries"][0]["kind"], "UNSTABLE_OR_UNREADABLE")

  def test_empty_directories_have_independent_bound(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      for index in range(12):
        (root / f"folder-{index:02d}").mkdir()
      wide = inventory([root], max_files=1, max_dirs=3)
      self.assertTrue(wide["truncated"])
      self.assertEqual(wide["truncation_reason"], "MAX_DIRS")
      self.assertLessEqual(wide["examined_dirs"], 3)
      self.assertEqual(wide["examined_files"], 0)
      nested = root / "nested"
      nested.mkdir()
      for index in range(8):
        nested = nested / f"level-{index}"
        nested.mkdir()
      deep = inventory([root / "nested"], max_files=1, max_dirs=3)
      self.assertTrue(deep["truncated"])
      self.assertEqual(deep["truncation_reason"], "MAX_DIRS")
      with self.assertRaises(ValueError):
        inventory([root], max_dirs=2001)

  def test_file_bound_reason_and_symlink_directory(self):
    with tempfile.TemporaryDirectory() as temp:
      root = Path(temp)
      (root / "a.txt").write_bytes(b"a")
      (root / "b.txt").write_bytes(b"b")
      (root / "link").symlink_to(root, target_is_directory=True)
      found = inventory([root], max_files=1, max_dirs=10)
      self.assertTrue(found["truncated"])
      self.assertEqual(found["truncation_reason"], "MAX_FILES")
      self.assertEqual(found["examined_files"], 1)
      self.assertEqual(found["examined_dirs"], 1)


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

  def test_qpoases_is_required_and_arch_checked_without_execution(self):
    with tempfile.TemporaryDirectory() as temp:
      repo = Path(temp)
      solver = repo / SOLVER
      solver.parent.mkdir(parents=True)
      arm = b"\x7fELF" + bytes([2, 1]) + bytes(12) + (0xb7).to_bytes(2, "little")
      x86 = b"\x7fELF" + bytes([2, 1]) + bytes(12) + (0x3e).to_bytes(2, "little")
      solver.write_bytes(arm)
      for name in LIBRARIES:
        if name != "libqpOASES_e.so.3.1":
          (solver.parent / name).write_bytes(arm)
      with patch("tools.c20_accord11g_long_shadow.native_preflight.platform.machine", return_value="aarch64"), \
           patch("tools.c20_accord11g_long_shadow.native_preflight.importlib.util.find_spec", return_value=object()):
        missing = qualify(repo)
        self.assertEqual(missing["status"], "BLOCKED")
        self.assertIn("libqpOASES_e.so.3.1 absent or incompatible", missing["reasons"])
        self.assertFalse(missing["executed_solver"])
        (solver.parent / "libqpOASES_e.so.3.1").write_bytes(x86)
        wrong_arch = qualify(repo)
        self.assertEqual(wrong_arch["status"], "BLOCKED")
        self.assertEqual(wrong_arch["libraries"]["libqpOASES_e.so.3.1"], "x86_64")
        (solver.parent / "libqpOASES_e.so.3.1").write_bytes(arm)
        ready = qualify(repo)
        self.assertEqual(ready["status"], "READY_FOR_ISOLATED_EXECUTION")
        self.assertFalse(ready["executed_solver"])


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
    # R19's research-only gate must reject R25's deliberate product integration.
    self.assertEqual(audit["status"], "FAIL")
    self.assertIn("working tree contains out-of-scope changes", audit["findings"])

  def test_scope_audit_catches_new_nested_and_dynamic_imports(self):
    with tempfile.TemporaryDirectory() as temp:
      repo = Path(temp)
      package = repo / "tools/c20_accord11g_long_shadow"
      (package / "tests").mkdir(parents=True)
      (package / "new_research").mkdir()
      (package / "__init__.py").write_text("from openpilot.selfdrive import controls\n")
      (package / "tests/test_extra.py").write_text("import panda\n")
      (package / "new_research/loader.py").write_text("import importlib\nimportlib.import_module('openpilot.selfdrive.controls')\n")
      with patch("tools.c20_accord11g_long_shadow.release_gate.subprocess.check_output", return_value=""):
        audit = source_audit(repo)
      self.assertEqual(audit["status"], "FAIL")
      self.assertTrue(any("__init__.py: forbidden import openpilot.selfdrive" in x for x in audit["findings"]))
      self.assertTrue(any("tests/test_extra.py: forbidden import panda" in x for x in audit["findings"]))
      self.assertTrue(any("new_research/loader.py: dynamic import" in x for x in audit["findings"]))

  def test_scope_audit_rejects_symlinked_source_tree(self):
    with tempfile.TemporaryDirectory() as temp:
      repo = Path(temp)
      package = repo / "tools/c20_accord11g_long_shadow"
      package.mkdir(parents=True)
      (package / "__init__.py").write_text("pass\n")
      (package / "outside").symlink_to(repo, target_is_directory=True)
      with patch("tools.c20_accord11g_long_shadow.release_gate.subprocess.check_output", return_value=""):
        audit = source_audit(repo)
      self.assertEqual(audit["status"], "FAIL")
      self.assertTrue(any("symlinked directory outside" in x for x in audit["findings"]))

  def test_scope_audit_rejects_control_bindings_and_dynamic_execution(self):
    with tempfile.TemporaryDirectory() as temp:
      repo = Path(temp)
      package = repo / "tools/c20_accord11g_long_shadow"
      package.mkdir(parents=True)
      (package / "__init__.py").write_text("x = CarParams\ny = Panda\nz.send(1)\neval('1')\n")
      with patch("tools.c20_accord11g_long_shadow.release_gate.subprocess.check_output", return_value=""):
        audit = source_audit(repo)
      self.assertEqual(audit["status"], "FAIL")
      self.assertTrue(any("forbidden control binding CarParams" in x for x in audit["findings"]))
      self.assertTrue(any("forbidden control binding Panda" in x for x in audit["findings"]))
      self.assertTrue(any("forbidden attribute send" in x for x in audit["findings"]))
      self.assertTrue(any("dynamic execution" in x for x in audit["findings"]))


if __name__ == "__main__":
  unittest.main()

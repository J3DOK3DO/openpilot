from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

from tools.c20_accord11g_long_shadow.bundle import MAX_BYTES, MAX_MEMBERS, build, verify, verify_release
from tools.c20_accord11g_long_shadow.historical_audit import audit_csv
from tools.c20_accord11g_long_shadow.native_gap import PROVENANCE, SERVICES, analyze
from tools.c20_accord11g_long_shadow.rawlog_census import ROOT
from tools.c20_accord11g_long_shadow.shadow_advisory import HistoricalSample, ShadowConfig, observe

HISTORY = ROOT.parents[4] if ROOT.is_absolute() else Path("__R8_HISTORY_UNAVAILABLE__")


class HistoricalTests(unittest.TestCase):
  def test_actual_columns_and_claimed_counts(self):
    expected = {"LS001": (1433, 407, -2.3), "LS003": (690, 214, -0.67), "LS004": (1122, 62, -2.0)}
    for event, (rows, boundary, can_min) in expected.items():
      path = HISTORY / f"{event}_FULL_RATE.csv"
      if not path.is_file():
        self.skipTest("historical read-only source unavailable")
      report = audit_csv(path)
      self.assertEqual(report["counts"]["event_rows"], rows)
      self.assertEqual(report["counts"]["negative_boundary_rows"], boundary)
      self.assertAlmostEqual(report["minima"]["can"]["value_mps2"], can_min)
      self.assertEqual(report["native_same_cycle"]["status"], "FAIL_MISSING_REQUIRED_INPUTS")
      self.assertEqual(analyze(path)["status"], "FAIL_MISSING_REQUIRED_INPUTS")

  def test_faults_fail_closed(self):
    source = HISTORY / "LS003_FULL_RATE.csv"
    if not source.is_file():
      self.skipTest("historical read-only source unavailable")
    with source.open(newline="") as stream:
      reader = csv.DictReader(stream)
      fields = reader.fieldnames
      rows = list(reader)
    variants = {
      "future": (1, "carState_logMonoTime", str(int(rows[1]["logMonoTime"]) + 1)),
      "delta": (1, "longcontrol_to_final_can_delta", "1"),
      "nan": (1, "carState.aEgo", "nan"),
      "duplicate": (1, "logMonoTime", rows[0]["logMonoTime"]),
      "brake_bit": (1, "BRAKE_REQUEST", "-1"),
      "outside_window_flag": (0, "in_qualifying_event", "True"),
      "inside_window_flag": (next(i for i, row in enumerate(rows) if row["in_qualifying_event"] == "True"), "in_qualifying_event", "False"),
      "segment_mismatch": (1, "segment", "999"),
      "wrong_event_segment": (next(i for i, row in enumerate(rows) if row["in_qualifying_event"] == "True"), "segment", "105"),
      "unknown_event": (0, "event_id", "LS999"),
    }
    with tempfile.TemporaryDirectory() as temp:
      target = Path(temp) / "fault.csv"
      for _, (index, key, value) in variants.items():
        altered = [dict(row) for row in rows]
        altered[index][key] = value
        with target.open("w", newline="") as stream:
          writer = csv.DictWriter(stream, fields)
          writer.writeheader()
          writer.writerows(altered)
        with self.assertRaises(ValueError):
          audit_csv(target)
      with target.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, [x for x in fields if x != "carState.aEgo"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows[:2])
      with self.assertRaises(ValueError):
        audit_csv(target)

  def test_ls004_legitimate_segment_crossing(self):
    path = HISTORY / "LS004_FULL_RATE.csv"
    if not path.is_file():
      self.skipTest("historical read-only source unavailable")
    with path.open(newline="") as stream:
      rows = list(csv.DictReader(stream))
    self.assertTrue(any(row["segment"] == "6" and row["in_qualifying_event"] == "True" for row in rows))
    self.assertEqual(audit_csv(path)["counts"]["event_rows"], 1122)

  def test_inert_advisory_default_and_failure(self):
    sample = HistoricalSample(10, -1.0, -0.7, "a" * 64)
    self.assertEqual(observe(sample)["status"], "DISABLED")
    enabled = observe(sample, ShadowConfig(True))
    self.assertEqual(enabled["status"], "HISTORICAL_UNVERIFIED")
    self.assertFalse(enabled["autonomous_braking"])
    self.assertNotIn("proposed_accel", enabled)
    self.assertEqual(observe(HistoricalSample(10, float("nan"), -0.7, "a" * 64), ShadowConfig(True))["status"], "FAILED_INPUT")

  def test_commit_pinned_bundle_is_deterministic_and_dirty_tree_rejected(self):
    with tempfile.TemporaryDirectory() as temp:
      repo = Path(temp) / "repo"
      repo.mkdir()
      subprocess.check_call(["git", "init", "-q", str(repo)])
      subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "R8 Test"])
      subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "r8@example.invalid"])
      source = repo / "tools/c20_accord11g_long_shadow/example.py"
      source.parent.mkdir(parents=True)
      source.write_text("VALUE = 1\n")
      subprocess.check_call(["git", "-C", str(repo), "add", "."])
      subprocess.check_call(["git", "-C", str(repo), "commit", "-q", "-m", "test"])
      first = Path(temp) / "first.tar.gz"
      second = Path(temp) / "second.tar.gz"
      one, two = build(repo, first), build(repo, second)
      self.assertEqual(one["sha256"], two["sha256"])
      self.assertEqual(verify(first)["revision"], one["revision"])
      self.assertEqual(verify_release(first)["sha256"], one["sha256"])
      self.assertIn("tools/c20_accord11g_long_shadow/example.py", verify(first)["files"])
      source.write_text("VALUE = 2\n")
      with self.assertRaises(ValueError):
        build(repo, Path(temp) / "dirty.tar.gz")

  def test_manifest_counts_toward_build_limit(self):
    with tempfile.TemporaryDirectory() as temp:
      repo = Path(temp) / "repo"
      repo.mkdir()
      subprocess.check_call(["git", "init", "-q", str(repo)])
      subprocess.check_call(["git", "-C", str(repo), "config", "user.name", "R8 Test"])
      subprocess.check_call(["git", "-C", str(repo), "config", "user.email", "r8@example.invalid"])
      source = repo / "tools/c20_accord11g_long_shadow/compressible.txt"
      source.parent.mkdir(parents=True)
      source.write_bytes(b"A" * (MAX_BYTES - 1))
      subprocess.check_call(["git", "-C", str(repo), "add", "."])
      subprocess.check_call(["git", "-C", str(repo), "commit", "-q", "-m", "near limit"])
      output = Path(temp) / "overflow.tar.gz"
      with self.assertRaisesRegex(ValueError, "uncompressed archive"):
        build(repo, output)
      self.assertFalse(output.exists())

  def test_verify_rejects_aggregate_oversize_and_member_flood(self):
    with tempfile.TemporaryDirectory() as temp:
      archive_path = Path(temp) / "oversize.tar.gz"
      with tarfile.open(archive_path, "w:gz") as archive:
        for name, data in (("RESEARCH_MANIFEST.json", b"{}"),
                           ("tools/c20_accord11g_long_shadow/compressible.txt", b"A" * (MAX_BYTES - 1))):
          info = tarfile.TarInfo(name)
          info.size = len(data)
          archive.addfile(info, io.BytesIO(data))
      with self.assertRaisesRegex(ValueError, "uncompressed archive"):
        verify(archive_path)
      archive_path = Path(temp) / "many.tar.gz"
      with tarfile.open(archive_path, "w:gz") as archive:
        for index in range(MAX_MEMBERS + 1):
          info = tarfile.TarInfo(f"tools/c20_accord11g_long_shadow/{index}")
          archive.addfile(info, io.BytesIO())
      with self.assertRaisesRegex(ValueError, "member limit"):
        verify(archive_path)


class NativeGapTests(unittest.TestCase):
  def _inventory(self) -> dict:
    cycle = {"t_ns": 100, "source_t_ns": {service: 90 for service in SERVICES[:-2]},
             "receipt_t_ns": {service: 95 for service in SERVICES[:-2]},
             "drive_reset_boundary": True, "drive_id": "test-drive", "model_trajectories": [1],
             "lead_history": [{"source_t_ns": 90, "receipt_t_ns": 95}],
             "driver_override": {"gas_pressed": False, "brake_pressed": False}}
    cycle.update({service: {"field": 1} for service in SERVICES})
    return {"provenance": {key: "present" for key in PROVENANCE}, "cycles": [cycle]}

  def _analyze(self, data: dict, directory: Path) -> dict:
    path = directory / "cycle.json"
    path.write_text(json.dumps(data))
    return analyze(path)

  def test_initial_reset_boundary_and_valid_receipts_are_schema_only(self):
    with tempfile.TemporaryDirectory() as temp:
      report = self._analyze(self._inventory(), Path(temp))
    self.assertEqual(report["status"], "SCHEMA_PRESENT_EXECUTION_UNVERIFIED")
    self.assertFalse(report["executed_solver"])
    self.assertEqual(report["missing_cycle_fields"], [])

  def test_missing_invalid_and_out_of_order_receipts_fail_closed(self):
    with tempfile.TemporaryDirectory() as temp:
      for value in (None, -1, 0, True, "95", 89, 101):
        data = self._inventory()
        if value is None:
          del data["cycles"][0]["receipt_t_ns"]["carState"]
        else:
          data["cycles"][0]["receipt_t_ns"]["carState"] = value
        report = self._analyze(data, Path(temp))
        self.assertEqual(report["status"], "FAIL_MISSING_REQUIRED_INPUTS")
        self.assertIn("valid_carState_receipt_t_ns", report["missing_cycle_fields"])
      data = self._inventory()
      del data["cycles"][0]["source_t_ns"]["carState"]
      self.assertIn("valid_carState_source_t_ns", self._analyze(data, Path(temp))["missing_cycle_fields"])
      data = self._inventory()
      data["cycles"][0]["source_t_ns"]["CP"] = 90
      self.assertIn("valid_CP_receipt_t_ns", self._analyze(data, Path(temp))["missing_cycle_fields"])
      for value in (None, "false", 0):
        data = self._inventory()
        if value is None:
          del data["cycles"][0]["drive_reset_boundary"]
        else:
          data["cycles"][0]["drive_reset_boundary"] = value
        self.assertIn("drive_reset_boundary", self._analyze(data, Path(temp))["missing_cycle_fields"])


if __name__ == "__main__":
  unittest.main()

from __future__ import annotations

import csv
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.c20_accord11g_long_shadow.bundle import build, verify, verify_release
from tools.c20_accord11g_long_shadow.historical_audit import audit_csv
from tools.c20_accord11g_long_shadow.native_gap import analyze
from tools.c20_accord11g_long_shadow.shadow_advisory import HistoricalSample, ShadowConfig, observe

HISTORY = Path("/home/jdkd/AI_Workspace/projects/accord11g-starpilot/c2-low-speed-causal-20260914_202004")


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


if __name__ == "__main__":
  unittest.main()

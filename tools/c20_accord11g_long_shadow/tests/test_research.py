from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.c20_accord11g_long_shadow.admission import EXPECTED_VEHICLE, UNITS, Status, admit, load_json_bytes, reference_digest, validate_rows
from tools.c20_accord11g_long_shadow.policies import (LeadMemory, ResponseFactors, c6_track_window,
                                                       mvl_coast_reference, mvl_factor_reference,
                                                       mvl_wind_reference, response_reference, step)
from tools.c20_accord11g_long_shadow.replay import compare, compare_recorded


ROOT = Path(__file__).resolve().parents[1]
TRACE = (ROOT / "fixtures/synthetic_trace.json").read_bytes()
ROWS = json.loads(TRACE)


def manifest():
  return {"source_kind": "RECORDED", "carFingerprint": "HONDA_ACCORD_11G",
          "vehicle": copy.deepcopy(EXPECTED_VEHICLE), "route_id": "test-route-001",
          "ecu_firmware": {"radar": "test-radar-01", "camera": "test-camera-01", "brake": "test-brake-01"},
          "software_sha": "a" * 64, "dbc_sha": "b" * 64,
          "trace_sha256": hashlib.sha256(TRACE).hexdigest(),
          "start_ns": ROWS[0]["t_ns"], "end_ns": ROWS[-1]["t_ns"], "units": UNITS.copy()}


def reference(m):
  return {**copy.deepcopy(m), "authenticated": True}


class AdmissionTests(unittest.TestCase):
  def test_exact_reference_match_remains_unverified(self):
    m = manifest()
    r = reference(m)
    self.assertEqual(admit(m, TRACE, r, reference_digest(r)).status, Status.REFERENCE_MATCH_UNVERIFIED)

  def test_without_reference_is_unverified(self):
    self.assertEqual(admit(manifest(), TRACE).status, Status.COMPATIBLE_BUT_UNVERIFIED)

  def test_fingerprint_and_vehicle_mismatch(self):
    for key, value in (("carFingerprint", "HONDA_CRV_6G"), ("vehicle", {**EXPECTED_VEHICLE, "year": 2023})):
      with self.subTest(key=key):
        m = manifest(); r = reference(m); m[key] = value
        self.assertEqual(admit(m, TRACE, r, reference_digest(r)).status, Status.MISMATCH)

  def test_firmware_software_dbc_route_and_artifact_mismatch(self):
    for key, value in (("ecu_firmware", {"radar": "other", "camera": "test-camera-01", "brake": "test-brake-01"}),
                       ("software_sha", "c" * 64), ("dbc_sha", "d" * 64),
                       ("route_id", "unrelated-route"), ("trace_sha256", "f" * 64)):
      with self.subTest(key=key):
        m = manifest(); r = reference(m); m[key] = value
        self.assertEqual(admit(m, TRACE, r, reference_digest(r)).status, Status.MISMATCH)

  def test_unknown_firmware_route_units_and_partial_data(self):
    edits = (("ecu_firmware", {"radar": "UNVERIFIED", "camera": "x", "brake": "y"}),
             ("route_id", "UNVERIFIED"), ("units", {"speed": "mph"}),
             ("start_ns", 0))
    for key, value in edits:
      with self.subTest(key=key):
        m = manifest(); m[key] = value
        self.assertEqual(admit(m, TRACE).status, Status.INSUFFICIENT_EVIDENCE)
    partial = copy.deepcopy(ROWS); del partial[0]["brake_pressed"]
    self.assertTrue(validate_rows(partial))

  def test_stale_future_and_nonmonotonic(self):
    for lead_ts in (1, 1_300_000_000):
      rows = copy.deepcopy(ROWS); rows[1]["lead"]["t_ns"] = lead_ts
      self.assertTrue(any("lead" in x for x in validate_rows(rows)))
    rows = copy.deepcopy(ROWS); rows[2]["t_ns"] = rows[1]["t_ns"]
    self.assertTrue(any("nonmonotonic" in x for x in validate_rows(rows)))
    rows = copy.deepcopy(ROWS); rows[1]["signal_t_ns"]["stock_aeb"] = 1
    self.assertTrue(any("stock_aeb timestamp" in x for x in validate_rows(rows)))

  def test_reference_authentication_required(self):
    m = manifest(); r = reference(m); r["authenticated"] = False
    self.assertEqual(admit(m, TRACE, r, reference_digest(r)).status, Status.INSUFFICIENT_EVIDENCE)
    self.assertEqual(admit(m, TRACE, reference(m)).status, Status.INSUFFICIENT_EVIDENCE)
    self.assertEqual(admit(m, TRACE, reference(m), "0" * 64).status, Status.MISMATCH)

  def test_duplicate_json_fields_are_rejected(self):
    with self.assertRaises(ValueError):
      load_json_bytes(b'{"route_id":"trusted","route_id":"other"}')


class PolicyTests(unittest.TestCase):
  def test_c6_window_bounds(self):
    self.assertTrue(c6_track_window(20, 30, 18, radar=True))
    self.assertFalse(c6_track_window(20, 280, 18, radar=True))
    self.assertFalse(c6_track_window(float("nan"), 30, 18, radar=False))

  def test_response_reference_is_bounded_and_not_equivalent(self):
    self.assertAlmostEqual(mvl_coast_reference(0), -0.3)
    self.assertAlmostEqual(mvl_wind_reference(22.4), 0.136)
    self.assertFalse(response_reference(20, 0, 0, None)["model_equivalence"])
    with self.assertRaises(ValueError):
      response_reference(20, 1.0, 0, None)

  def test_mvl_factor_reference_freezes_on_override(self):
    prior = ResponseFactors()
    self.assertEqual(mvl_factor_reference(1.0, 0.5, 20, 0.01, prior,
                                          min_gas_mps2=0.0, active=True, driver_override=True), prior)
    updated = mvl_factor_reference(1.0, 0.5, 20, 0.01, prior,
                                   min_gas_mps2=0.0, active=True, driver_override=False)
    self.assertGreater(updated.gas, prior.gas)
    self.assertGreater(updated.wind, prior.wind)

  def test_track_replacement_clears_hold(self):
    row = copy.deepcopy(ROWS[1]); row["v_ego"] = 0.1; row["lead"]["speed"] = 0.0; row["lead"]["distance"] = 5.0
    first = step(row, "c6_behavioral", LeadMemory())
    self.assertTrue(first.brake_hold)
    replacement = copy.deepcopy(row); replacement["t_ns"] += 100_000_000
    replacement["lead"]["t_ns"] = replacement["t_ns"]
    replacement["lead"]["track_id"] = "replacement"
    replacement["lead"]["distance"] = 30.0
    next_result = step(replacement, "c6_behavioral", first.memory)
    self.assertTrue(next_result.lead_transition)
    self.assertFalse(next_result.brake_hold)
    self.assertEqual(next_result.memory.track_id, "replacement")

  def test_observed_braking_and_aeb_not_masked(self):
    row = copy.deepcopy(ROWS[3]); row["raw_accel"] = -8.0
    for strategy in ("c6_behavioral", "c19_behavioral"):
      self.assertLessEqual(step(row, strategy).accel, -8.0)

  def test_stale_lead_not_used(self):
    row = copy.deepcopy(ROWS[1]); row["lead"]["t_ns"] = 1
    result = step(row, "c6_behavioral")
    self.assertFalse(result.lead_fresh)
    self.assertEqual(result.reason, "stale_lead_ignored")
    self.assertIsNone(result.memory.track_id)


class ReplayTests(unittest.TestCase):
  def test_deterministic_and_metrics_present(self):
    one = compare(ROWS, mode="SIMULATED", admission_status=Status.COMPATIBLE_BUT_UNVERIFIED.value)
    two = compare(copy.deepcopy(ROWS), mode="SIMULATED", admission_status=Status.COMPATIBLE_BUT_UNVERIFIED.value)
    self.assertEqual(json.dumps(one, sort_keys=True), json.dumps(two, sort_keys=True))
    self.assertEqual(one["strategies"]["c6_behavioral"]["counts"]["lead_transition"], 3)
    self.assertEqual(one["mode"], "SIMULATED")

  def test_standstill_hold_and_track_transition_in_replay(self):
    rows = []
    for index in range(3):
      row = copy.deepcopy(ROWS[1])
      row["t_ns"] = 1_100_000_000 + index * 100_000_000
      row["signal_t_ns"] = {key: row["t_ns"] for key in row["signal_t_ns"]}
      row["v_ego"] = 0.1
      row["v_cruise"] = 0.0
      row["lead"]["t_ns"] = row["t_ns"]
      row["lead"]["speed"] = 0.0
      row["lead"]["distance"] = 5.0 if index < 2 else 20.0
      row["lead"]["track_id"] = "stop-A" if index < 2 else "stop-B"
      rows.append(row)
    result = compare(rows)["strategies"]["c6_behavioral"]["counts"]
    self.assertEqual(result["standstill"], 3)
    self.assertEqual(result["brake_hold"], 2)
    self.assertEqual(result["lead_transition"], 2)

  def test_recorded_requires_reference_match_and_stays_unverified(self):
    with self.assertRaises(ValueError):
      compare(ROWS, mode="RECORDED_VERIFIED", admission_status=Status.COMPATIBLE_BUT_UNVERIFIED.value)
    with self.assertRaises(ValueError):
      compare(ROWS, mode="RECORDED_VERIFIED", admission_status=Status.REFERENCE_MATCH_UNVERIFIED.value)
    m = manifest()
    with self.assertRaises(ValueError):
      compare_recorded(TRACE, m, reference(m), "0" * 64)
    self.assertEqual(compare_recorded(TRACE, m, reference(m), reference_digest(reference(m)))["mode"], "RECORDED_REFERENCE_MATCH_UNVERIFIED")

  def test_no_actuation_imports_or_hooks(self):
    allowed = {"__future__", "argparse", "collections", "dataclasses", "enum", "hashlib",
               "json", "math", "pathlib", "re", "typing", "admission", "policies"}
    for name in ("admission.py", "policies.py", "replay.py"):
      tree = ast.parse((ROOT / name).read_text())
      imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
      imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
      self.assertTrue(all(x in allowed for x in imports), imports)
      self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr in ("send", "forward", "connect", "transmit")
                           for n in ast.walk(tree)))


if __name__ == "__main__":
  unittest.main()

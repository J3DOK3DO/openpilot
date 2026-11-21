"""Synthetic negative controls for static MVL/DOM tune comparisons."""
import pathlib
import subprocess
import unittest
import read_only_tuning as audit

DOM = """def example(candidate):
    if candidate == CAR.HONDA_ACCORD_11G:
        ret.steerActuatorDelay = 0.3
        ret.lateralTuning.pid.kf = 0.000035
        ret.lateralTuning.pid.kpV = [0.115]
        ret.lateralTuning.pid.kiV = [0.052]
"""
MVL = """def example(candidate):
    if candidate == CAR.HONDA_ACCORD_11G:
        ret.steerActuatorDelay = 0.3
        ret.lateralTuning.pid.kf = 0.000035
        ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.115], [0.052]]
"""

class TestHonda11GPinAudit(unittest.TestCase):
    def test_same_values_different_assignment_shapes(self):
        result = audit.compare(DOM, MVL)
        self.assertTrue(result["same_four_numeric_values"])
        self.assertEqual(len(result["differences"]), 4)
        self.assertTrue(all(x == 0 for x in result["differences"].values()))

    def test_detects_steer_gain_drift(self):
        result = audit.compare(DOM.replace("0.115", "0.125"), MVL)
        self.assertFalse(result["same_four_numeric_values"])
        self.assertAlmostEqual(result["differences"]["kpV"], 0.010)

    def test_detects_delay_drift(self):
        result = audit.compare(DOM.replace("0.3", "0.4"), MVL)
        self.assertFalse(result["same_four_numeric_values"])

    def test_missing_pid_incomplete(self):
        with self.assertRaises(ValueError):
            audit.extract_profile(DOM.replace("ret.lateralTuning.pid.kiV", "ret.nonmatching.ki"))

    def test_rejects_wrong_vehicle(self):
        with self.assertRaises(ValueError):
            audit.extract_profile(DOM.replace("HONDA_ACCORD_11G", "HONDA_CRV_6G"))

    def test_does_not_execute_source(self):
        dangerous = DOM + "\nraise RuntimeError('must never execute')\n"
        result = audit.extract_profile(dangerous)
        self.assertEqual(result["steerActuatorDelay"], 0.3)

    def test_real_pins_when_both_available(self):
        dom = pathlib.Path(__file__).resolve().parents[2]
        mvl = pathlib.Path("/mnt/commadrive/_mvl_opendbc_sp_honda_dev_202608_review")
        if not mvl.exists():
            self.skipTest("Exact MVL source pin not installed on this machine")
        old = audit.git(dom, "show", audit.DOM_C13_PIN+":opendbc_repo/opendbc/car/honda/interface.py")
        new = audit.git(mvl, "show", audit.MVL_OPENDDBC_PIN+":opendbc/car/honda/interface.py")
        self.assertTrue(audit.compare(old, new)["same_four_numeric_values"])

if __name__ == "__main__":
    unittest.main()

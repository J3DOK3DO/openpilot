"""C15/C17 offline source-auditor regression with fail-closed negative cases."""
import pathlib
import subprocess
import sys
import unittest
import audit_offline_release as audit

class OfflineReleaseTests(unittest.TestCase):
    def test_tools_only_scope(self):
        self.assertTrue(audit.is_only_tools_delta(["tools/c14_mvl_gap/test.py", "tools/c15_c17_release/report.md"]))
        for changes in (["openpilot/selfdrive/selfdrived/selfdrived.py"],
                        ["opendbc_repo/opendbc/safety/modes/honda.h"],
                        ["prebuilt.json"], []):
            self.assertFalse(audit.is_only_tools_delta(changes))

    def test_physical_c16_missing_never_approves_road(self):
        x = dict(source_unchanged_since_build=True, offline_evidence_verifiable=True,
                 device_qualified=False, independent_vehicle_safety_review=True,
                 current_exact_commit_production_receipt=True, qcom_target_inference=True)
        r = audit.decisions(x)
        self.assertTrue(r["c17_source_only_release_permitted"])
        self.assertFalse(r["c17_installable_release_approved"])
        self.assertFalse(r["c17_road_use_approved"])
        self.assertEqual(r["c16"], "DEFERRED_NOT_WAIVED")

    def test_receipt_missing_blocks_product(self):
        x = dict(source_unchanged_since_build=True, offline_evidence_verifiable=True,
                 device_qualified=True, independent_vehicle_safety_review=True,
                 current_exact_commit_production_receipt=False, qcom_target_inference=True)
        self.assertFalse(audit.decisions(x)["c15_full_production_complete"])

    def test_qcom_unverified_blocks_product(self):
        x = dict(source_unchanged_since_build=True, offline_evidence_verifiable=True,
                 device_qualified=True, independent_vehicle_safety_review=True,
                 current_exact_commit_production_receipt=True, qcom_target_inference=False)
        self.assertFalse(audit.decisions(x)["c17_installable_release_approved"])

    def test_no_reuse_when_code_changes(self):
        self.assertFalse(audit.is_only_tools_delta(["tools/c15_report.md", "opendbc_repo/opendbc/car/honda/interface.py"]))

    def test_even_all_hypothetical_inputs_cannot_authorize_vehicle(self):
        x = dict(source_unchanged_since_build=True, offline_evidence_verifiable=True,
                 device_qualified=True, independent_vehicle_safety_review=True,
                 current_exact_commit_production_receipt=True, qcom_target_inference=True,
                 c16_physically_passed=True, installed_panda_agnos_build_identity=True)
        r = audit.decisions(x)
        self.assertTrue(r["c17_source_only_release_permitted"])
        self.assertFalse(r["c17_installable_release_approved"])
        self.assertFalse(r["c17_road_use_approved"])
        self.assertFalse(r["c15_full_production_complete"])

    def test_python_optimized_mode_cannot_bypass_evidence_guard(self):
        cmd = ("import sys; sys.path.insert(0, 'tools/c15_c17_release'); "
               "from audit_offline_release import require; require(False, 'must fail')")
        x = subprocess.run([sys.executable, "-O", "-c", cmd],
                           cwd=pathlib.Path(__file__).resolve().parents[2],
                           capture_output=True, text=True, timeout=10)
        self.assertNotEqual(x.returncode, 0)
        self.assertIn("must fail", x.stderr)

    def test_local_real_evidence_invariants(self):
        repo = pathlib.Path(__file__).resolve().parents[2]
        original = pathlib.Path("/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence")
        if not original.is_dir():
            self.skipTest("C11 native build evidence unavailable")
        a = audit.inspect(repo, original)
        self.assertTrue(a["source_unchanged_since_build"])
        self.assertTrue(a["offline_evidence_verifiable"])
        self.assertEqual(a["current_receipt_validator_exit"], 1)
        self.assertFalse(a["decision"]["c17_road_use_approved"])

if __name__ == "__main__":
    unittest.main()

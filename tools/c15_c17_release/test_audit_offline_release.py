"""Synthetic negative tests and one real pinned-readonly evidence run."""
import pathlib
import unittest
import audit_offline_release as audit


class OfflineReleaseTests(unittest.TestCase):
    def test_tools_only_scope(self):
        self.assertTrue(audit.is_only_tools_delta(["tools/c14_mvl_gap/test.py", "tools/c15_c17_release/report.md"]))
        self.assertFalse(audit.is_only_tools_delta(["openpilot/selfdrive/selfdrived/selfdrived.py"]))
        self.assertFalse(audit.is_only_tools_delta(["opendbc_repo/opendbc/safety/modes/honda.h"]))
        self.assertFalse(audit.is_only_tools_delta(["prebuilt.json"]))
        self.assertFalse(audit.is_only_tools_delta([]))

    def test_physical_c16_missing_never_approves_road(self):
        x={"source_unchanged_since_build":True,"offline_evidence_verifiable":True,
           "device_qualified":False,"independent_vehicle_safety_review":True,
           "current_exact_commit_production_receipt":True,"qcom_target_inference":True}
        r=audit.decisions(x)
        self.assertTrue(r["c17_source_only_release_permitted"])
        self.assertFalse(r["c17_installable_release_approved"])
        self.assertFalse(r["c17_road_use_approved"])

    def test_receipt_missing_blocks_product(self):
        x={"source_unchanged_since_build":True,"offline_evidence_verifiable":True,
           "device_qualified":True,"independent_vehicle_safety_review":True,
           "current_exact_commit_production_receipt":False,"qcom_target_inference":True}
        self.assertFalse(audit.decisions(x)["c15_full_production_complete"])

    def test_qcom_unverified_blocks_product(self):
        x={"source_unchanged_since_build":True,"offline_evidence_verifiable":True,
           "device_qualified":True,"independent_vehicle_safety_review":True,
           "current_exact_commit_production_receipt":True,"qcom_target_inference":False}
        self.assertFalse(audit.decisions(x)["c17_installable_release_approved"])

    def test_no_reuse_when_code_changes(self):
        self.assertFalse(audit.is_only_tools_delta(["tools/c15_report.md", "opendbc_repo/opendbc/car/honda/interface.py"]))

    def test_complete_verified_dependencies_only(self):
        x=dict(source_unchanged_since_build=True,offline_evidence_verifiable=True,
               device_qualified=True,independent_vehicle_safety_review=True,
               current_exact_commit_production_receipt=True,qcom_target_inference=True)
        self.assertTrue(audit.decisions(x)["c17_installable_release_approved"])
        x["offline_evidence_verifiable"] = False
        self.assertFalse(audit.decisions(x)["c17_road_use_approved"])

    def test_local_real_evidence_invariants(self):
        repo = pathlib.Path(__file__).resolve().parents[2]
        original = pathlib.Path("/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence")
        if not original.is_dir():
            self.skipTest("C11 native build evidence unavailable")
        a = audit.inspect(repo, original)
        self.assertTrue(a["source_unchanged_since_build"])
        self.assertTrue(a["offline_evidence_verifiable"])
        self.assertEqual(a["current_receipt_validator_exit"],1)
        self.assertFalse(a["decision"]["c17_road_use_approved"])

if __name__ == "__main__":
    unittest.main()

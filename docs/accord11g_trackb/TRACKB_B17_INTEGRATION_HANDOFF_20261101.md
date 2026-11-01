# Track B17 offline simulation — integration handoff (2026-11-01)

**Result:** the 17 retained IDs now have deterministic, pure-Python, non-actuating simulation coverage. No production Honda, Panda, packer, interface, controller, or evidence-register path was changed. Operational readiness is **NOT_ESTABLISHED**.

## ID-to-artifact mapping

| Retained IDs | Offline implementation | Result boundary |
| --- | --- | --- |
| BC-009, BC-010, BC-011, BC-012 | `OwnershipTransitionResearch` in `tools/trackb_research/mvl_retained_sim.py` | Source-only stock-owner label, stale source, unknown AEB, ambiguous relay, duplicate/order, and silent-transition-failure classification. No ECU ownership inference. |
| BC-020, BC-021, BC-022, BC-023, BC-024 | `RadarMetadataResearch` in the same module | `hud`, `tick`, `mux`, `lead`, and `checksum` source metadata plus missing/stale/anomaly/duplicate classification. No frames, identifiers, payloads, timing, packer, or checksum. |
| DRV-001, DRV-003, DRV-005, DRV-006, DRV-007, DRV-008, DRV-009, DRV-010 | `BrakeSelectionResearch` in the same module | Symbolic selection, re-entry suppression, driver exclusivity, bounded negative integrator, fault/restart rearm, target/corrected distinction, one-sided relaxation, and near-zero-negative handling. No motion, actuator, or transport output. |

The detailed per-ID provenance, source claim boundary, test, status, and evidence requirement is in `TRACKB_B17_RETAINED_PATCH_SIMULATION_MATRIX_20261101.tsv`. The owner risk acknowledgement and CMBS/AEB/FCW consequence record is in `TRACKB_B17_MVL_HAZARD_AND_ARCHITECTURE_20261101.md`.

## Reproducible verification

Executed from the repository root using the installed Python/pytest environment:

```sh
python3 -m pytest tools/trackb_research/tests/test_mvl_retained_sim.py tools/trackb_research/tests/test_architectural_isolation.py -q
# 32 passed in 0.57s, exit 0

# After restoring the existing project source directories to this isolated sparse checkout:
# git sparse-checkout add openpilot/cereal opendbc_repo/opendbc/dbc/generator/honda
python3 -m pytest tools/trackb_research/tests -q
# 498 passed in 0.79s, exit 0; zero failures and no omitted tests
```

During the initial sparse checkout, three test cases failed because `openpilot/cereal/log.capnp` and `opendbc_repo/opendbc/dbc/generator/honda/honda_common_canfd.dbc` were absent. Both source paths were restored through sparse-checkout, **without changing any test**, and the unmodified full suite subsequently passed (498/498). Complete retest evidence: `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/trackab-native-continuation-artifacts-20261101/b17_mvl_sim_20261101/PYTEST_FULL_AFTER_SPARSE_FIX.log`.

## Remaining operational blockers

1. All B1 gates remain **HOLD**: authenticated 2025 US Hybrid command ownership, CMBS/AEB precedence, CAN-FD topology/arbitration, and an OEM-supported owner transition preserving stock safety functions.
2. The owner’s accepted expected loss of CMBS/AEB/FCW in the proposed separate alpha-long architecture is a hazard acknowledgement, not a safe-design finding. Factory collision-warning/automatic-braking protection cannot be guaranteed by that architecture.
3. Fault latch, stock ECU recovery, relay state, source silence, availability, and driver override are unqualified on target hardware. The symbolic tests are not recovery or override performance evidence.
4. The DEBUG Panda and AGNOS raw-hash mismatch are accepted research deviations only. B3 target release identity and B4 installed-device identity are not qualified.
5. B5 isolated bench and B6 controlled vehicle remain OUT_OF_SCOPE / NOT_EVALUATED and continue to block every operational release claim.

The full-suite prerequisite is now resolved, and this handoff reflects the committed-source candidate pending independent read-only review; no vehicle/operational qualification is inferred.

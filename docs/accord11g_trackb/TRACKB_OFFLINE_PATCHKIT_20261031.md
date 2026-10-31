# Track B offline patch-kit matrix — 2026-10-31

## Source pin and safety boundary

- Base and parent: `27295eabc179a888e52d593cf722243cc8fa1fdc`.
- This patch-kit adds only `tools/trackb_research` modules, their tests, and this record.
- It does not alter `openpilot/`, `opendbc_repo/opendbc/`, `panda/`, production DBCs, firmware, vehicle interfaces, CAN/UDS paths, or Panda permissions.
- `OwnershipEvidenceModel` accepts manually supplied synthetic observations and rejects diagnostic/radar-suppression requests. `BrakeHoldContract` has symbolic test thresholds only; its output is not a vehicle command.

## Disposition matrix

| Patch IDs | Disposition | Offline result / blocker |
| --- | --- | --- |
| BC-007 | DEFER | Gas mapping equivalence requires authenticated protocol evidence; no candidate generation. |
| BC-008–BC-014 | PREPARE DISABLED | `ownership_evidence_model.py` records source-only retained-stock ownership and fails closed for incomplete, duplicate/out-of-order, backward-clock, AEB/CMBS, stock-ACC, and physical-claim evidence. |
| BC-015–BC-019 | EXCLUDE | ECU diagnostics, radar ownership and relay mirroring are prohibited operational paths; model rejects diagnostic and radar-suppression requests. |
| BC-020–BC-024 | PREPARE DISABLED | Existing deterministic CAN-FD source dictionary and synthetic fixtures retained; no transmitter, checksum authentication claim, or operational parser added. |
| BC-027 | RETAIN UPSTREAM | Existing stock safety/profile selection remains untouched. |
| BC-028 | DEFER | Any longitudinal bounds could imply control authority; current source is retained. |
| BC-029, BC-031 | PREPARE DISABLED | Policy evidence only; no UDS whitelist or forwarding policy modification. |
| BC-032 | DEFER | OEM CMBS/AEB/FCW precedence requires target-specific OEM evidence; unknown/active synthetic state fails closed. |
| DRV-001–DRV-010 | PREPARE DISABLED | `brake_hold_contract.py` supplies an isolated, symbolic brake/gas/hold state contract with driver, stock-ACC and AEB gates; no production integration. |
| DRV-011–DRV-017 | PREPARE DISABLED | Existing `plan_controller_sim.py` remains the only non-actuating downstream contract; it consumes a published synthetic target and cannot plan or actuate. |
| DRV-018–DRV-031 | DEFER | Lead handling, coasting, catch-up and cruise ceilings require independently qualified planner/source evidence; no duplicate policy module introduced. |
| DRV-034 | RETAIN UPSTREAM | Shared LongControl is unchanged pending a demonstrated current-source defect. |

## Exact Patch-ID coverage

- BC: BC-007, BC-008, BC-009, BC-010, BC-011, BC-012, BC-013, BC-014, BC-015, BC-016, BC-017, BC-018, BC-019, BC-020, BC-021, BC-022, BC-023, BC-024, BC-027, BC-028, BC-029, BC-031, BC-032.
- DRV: DRV-001, DRV-002, DRV-003, DRV-004, DRV-005, DRV-006, DRV-007, DRV-008, DRV-009, DRV-010, DRV-011, DRV-012, DRV-013, DRV-014, DRV-015, DRV-016, DRV-017, DRV-018, DRV-019, DRV-020, DRV-021, DRV-022, DRV-023, DRV-024, DRV-025, DRV-026, DRV-027, DRV-028, DRV-029, DRV-030, DRV-031, DRV-034.

## Validation and rollback

Run the tests listed in `B1_B2_TEST_RESULTS_20261031.md` plus the two new test files. The architectural-isolation test must remain green. Roll back by reverting this branch commit or by omitting its patch; no runtime state, vehicle state, or safety configuration requires rollback.

## Model-usage record

| Activity | Model / evidence |
| --- | --- |
| Prior B1/B2 implementation and review | Existing Qwen3-Coder review record and 169-test evidence; not re-claimed as a review of this delta. |
| This offline research implementation | Codex, limited to non-actuating standalone modules and documentation. |
| Fresh tests and source review | Recorded from commands executed on this branch. |
| Independent review of this delta | Required before publication; record actual reviewer and findings below. |
## Post-review source-only correction

The ownership model now rejects non-string relay/topology claims without throwing exceptions. The symbolic brake/hold model clears its historical braking latch on any invalid, duplicate, override, or withdrawn event; new tests demonstrate that a fresh sub-threshold acceleration cannot inherit the previous engagement's brake state. This change remains isolated to research code. The monotonic observation field is not an authenticated freshness measurement: without a trusted current time or physical signal source, no age or vehicle freshness qualification is claimed.

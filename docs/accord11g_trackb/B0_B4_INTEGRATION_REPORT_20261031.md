# Accord 11G Track B B0--B4 source-only integration report — 2026-10-31

## Scope, source identity, and boundary

- Starting baseline and current `HEAD` before this uncommitted source-only delta:
  `d0c2067cb9086335a625f935d58f39dfb43254f6`.
- Read-only B4 source identity: `openpilot/common/hardware/comma/agnos.json`
  is tracked at blob `b3a23b4c28269fef31ae94f5560c876ce8c1acba` (also the
  current worktree `git hash-object` result). Its `system` record declares
  sparse-stream hash `9c753bdd90e6079b2cf525659d7523d0ebc0a375bd61e61cca628f1db3832cfd`,
  raw hash `98e15de07c39a19b5fa17c96a67e66d4362f9ebaf7827b640f4127e3b6417da8`,
  and on-device comparison hash `9625ec32df735b26ea6b0b62834addc8b522108d5f5c4a2aebcb98fc2b94f4e9`.
  They are manifest text values only, not a measured installed-image identity.
- This delta changes only Track B documentation, the pure
  `tools/trackb_research/brake_hold_contract.py` model, and its test. It changes
  no production openpilot/opendbc/Panda safety source, DBC, firmware, vehicle
  interface, CAN/UDS path, or installed comma software.
- No vehicle actuation, diagnostic command, radar disable/suppression, safety
  permission change, flashing, network publication, push, merge, device access,
  or CAN/UDS traffic occurred.

## B0--B4 disposition

| Band | Actual source-only result | Status / hold |
| --- | --- | --- |
| B0 | Existing stock-longitudinal and parked-audit regressions passed. FR-B0-01--04 are source/audit evidence only. | FR-B0-05 is **HOLD / UNVERIFIED** pending authoritative OEM, protocol, RELEASE, target, and independent-review evidence. |
| B1 | Current Bosch-C/11G source evidence remains explicitly marked source-derived. | **HOLD / UNVERIFIED**: this worktree has no authoritative OEM service/protocol evidence and no physical vehicle, ECU, bus, Panda, firmware, or installed-image observation. |
| B2 | The isolated PlanControllerSimulation, OwnershipEvidenceModel, and BrakeHoldContract remain non-actuating. BrakeHoldContract now rejects negative synthetic speed and a standstill claim above the symbolic standstill bound. | Synthetic test evidence only; no controller, calibration, protocol decoder, or vehicle acceptance claim. |
| B3 | Existing Honda `release=True` host-library deny-policy tests passed for stock words 80/81, alternative experiences 0/32, controls allowed true/false, generic Bosch-long examples, and the listed tester-present packet shape. | Host-source negative evidence only; no Panda RELEASE binary, flash, or target authorization. No safety-policy modification. |
| B4 | Source pin, clean baseline comparison, tracked AGNOS manifest object, and static isolation were checked read-only. | **HOLD / UNVERIFIED**: no device architecture/slot, installed AGNOS measurement, Panda firmware identity, or source-to-installed-build provenance was observed. |

## Exact 55-ID traceability

The traceability set is exactly 55 unique IDs (23 `BC`, 32 `DRV`), counted from
`TRACKB_OFFLINE_PATCHKIT_20261031.md`. Every ID remains non-executable and takes
the disposition in that record; it is not an authorization to implement or run
an on-vehicle patch.

- BC (23): BC-007, BC-008, BC-009, BC-010, BC-011, BC-012, BC-013, BC-014,
  BC-015, BC-016, BC-017, BC-018, BC-019, BC-020, BC-021, BC-022, BC-023,
  BC-024, BC-027, BC-028, BC-029, BC-031, BC-032.
- DRV (32): DRV-001, DRV-002, DRV-003, DRV-004, DRV-005, DRV-006, DRV-007,
  DRV-008, DRV-009, DRV-010, DRV-011, DRV-012, DRV-013, DRV-014, DRV-015,
  DRV-016, DRV-017, DRV-018, DRV-019, DRV-020, DRV-021, DRV-022, DRV-023,
  DRV-024, DRV-025, DRV-026, DRV-027, DRV-028, DRV-029, DRV-030, DRV-031,
  DRV-034.

## Executed local validation

| Command | Actual result |
| --- | --- |
| `./dev pytest scripts/tests/test_accord11g_trackb_parked_audit.py tools/trackb_research/tests/test_shadow_synthetic.py tools/trackb_research/tests/test_plan_controller_sim.py tools/trackb_research/tests/test_ownership_evidence_model.py tools/trackb_research/tests/test_brake_hold_contract.py tools/trackb_research/tests/test_architectural_isolation.py tools/trackb_research/tests/test_canfd_dictionary.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_stock_ownership_v4.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_trackb_no_long_authority.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_denials.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py` | **199 passed** in 3.17 s. The native host wrapper built host dependencies; no device path was used. |
| `./dev python -m ruff check --no-cache` on the Track B research, audit, Honda boundary, and RELEASE-denial files | **All checks passed.** (`./dev ruff check` itself is not a supported wrapper subcommand; the supported Python-wrapper form was then used.) |
| `./dev python -m compileall -q` on the same Python scope | Exit status 0. |
| `git diff --check` | Exit status 0. |
| Production-diff and reference scan: `git diff --name-only d0c2067... -- openpilot opendbc_repo/opendbc/car opendbc_repo/opendbc/safety panda opendbc_repo/opendbc/dbc`; `rg` for research-module references outside tests | No production-path delta and no production reference found. The pytest architectural-isolation test also passed. |
| `git rev-parse HEAD`; `git ls-tree HEAD openpilot/common/hardware/comma/agnos.json`; `git hash-object openpilot/common/hardware/comma/agnos.json`; `sed -n` of that manifest; unique-ID count | Baseline `d0c2067...`; AGNOS blob/hash `b3a23b4...`; manifest `system` hashes recorded above; 55 unique IDs. |

## Limitations and review

Passing host tests do not qualify a vehicle, target hardware, firmware, protocol,
OEM ownership/arbitration, braking, CMBS/AEB behavior, or release use. B1 and B4
remain held, and B2/B3 remain isolated source-only evidence.

A separate Codex read-only review found a P2: a malformed non-boolean
`standstill` value whose `__bool__` raises could raise before validation. The
issue was remediated by ordering boolean validation before truth evaluation and
by adding a regression. The final independent re-review found the stale pytest
count (198 rather than 199), which was corrected in this report. This
review/adjudication is not an OEM or device qualification and does not provide a
release verdict.

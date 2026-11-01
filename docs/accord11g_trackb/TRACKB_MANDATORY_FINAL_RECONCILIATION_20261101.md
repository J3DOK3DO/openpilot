# Track B mandatory final reconciliation — 2026-11-01

Base: `3cc065e7b505abeb9c2b56baa90a7505dd414c7e` (branch `accord11g-dom7-trackb-b0-b4-integration-20261031`), six consecutive B0–B4 commits above `5fa8b2ed8`. None were reapplied. Branch for this delta: `accord11g-dom7-trackb-mandatory-final-20261101`.

Historical sources (V3 kit, V4 handoff, C6-12 recovery, Qwen/Codex evidence, earlier patch kits) were used as **research references only**. No C6-12/C7 log, replay, or safety baseline is acceptance evidence, and none was rerun.

## 1. 84-ID reconciliation (V3 `84_TRACEABILITY.tsv` vs current 55-ID matrix)

84 = 33 BC + 34 DRV + 17 ND. The current Track B matrix (`TRACKB_OFFLINE_PATCHKIT_20261031.md`) covers 55 (23 BC + 32 DRV). The remaining 29 are outside the Track B matrix by V3's own `track_B_status`:

| Group | IDs | V3 disposition | This campaign |
| --- | --- | --- | --- |
| Track A stock, preserved | BC-001, 003, 004, 005, 006, 025, 026, 030; ND-006, 010, 012, 013, 015 | KEEP / native-preserved (BC-025/026: A1 candidate, already incorporated as `5fa8b2ed8`) | Already implemented; untouched |
| Verification holds | BC-002; ND-001, 005, 007, 008, 014, 016 | VERIFY / evidence-only | Blocked: needs card/OEM/physical evidence |
| Design / rework / defer | ND-003, 004, 011, 017 | REWORK / DEFER / DESIGN | Optional or blocked; not implemented |
| Excluded from stock | BC-033; DRV-032, 033; ND-002, 009 | EXCLUDE (future Track B needs new safety case) | Excluded |

Total 29, all accounted for; the 55 keep the dispositions in the offline patch-kit matrix:

| Classification | IDs |
| --- | --- |
| Already implemented, source-verified | BC-027, DRV-034 (retain upstream); BC-008–014, BC-020–024, BC-029, BC-031, DRV-001–017 (isolated, non-actuating, PREPARE DISABLED) |
| Already implemented, needs more qualification | Same PREPARE DISABLED set: host/synthetic evidence only; physical, OEM, Panda-target evidence absent |
| Superseded by current Dom | DRV-018–031 planner/lead/coast/cruise behavior (current Dom planner owns it; no duplicate policy added) |
| Optional / excluded | BC-015–019 (diagnostics, radar ownership, relay mirroring: prohibited paths) |
| Blocked by missing evidence | BC-007, BC-028, BC-032 (authenticated protocol / OEM CMBS-AEB precedence) |
| Mandatory, not implemented before this campaign | See §2 (gaps found in existing isolated contracts, not new patch IDs) |

## 2. Mandatory changes made (all MANDATORY; no OPTIONAL work)

| ID | Req | Defect / gap in current source | Change | Test evidence |
| --- | --- | --- | --- | --- |
| M-1 | B2 / FR-B0-06 | `PlanSnapshot` omitted the schema's `fcw` flag; a plan with Forward Collision Warning active could still yield a tracking request. | Added `fcw: bool` (strict-bool validated); `plan_fcw_active` fail-closed withdrawal retiring the engagement token. | `test_plan_controller_sim.py` (fcw rows, non-bool fcw, recovery) |
| M-2 | B2 / FR-B0-07 | Nothing tied `PlanSnapshot` to the real Dom `LongitudinalPlan` schema, so field-set, ordinal or type drift would pass silently. | New contract test parsing `openpilot/cereal/log.capnp`: every schema field is mapped or explicitly acknowledged; snapshot fields equal mapped fields plus log envelope; mapped fields keep pinned ordinal and type. Semantic changes within an unchanged type are not detected. | `test_plan_snapshot_schema_contract.py` |
| M-3 | B0 / FR-B0-08 | Isolation test scanned only `openpilot`, `opendbc_repo/opendbc`, `panda`; `starpilot/`, `system/`, `scripts/`, launchers, `SConstruct` were unscanned. | Added whole-repository tracked-file scan allowing only docs, tests, and the research directory. | `test_architectural_isolation.py` |
| M-4 | B3 / FR-B0-09 | RELEASE denials covered experiences 0/32 and two words only; non-stock experiences, the debug-only Bosch-long bit (2), and non-stock Bosch words were not negative-tested, and no positive control proved the tests discriminate. | Sweep over alternative experiences 0–511 plus every single-bit Int16 value and the signed extremes × words 80/81 × controls allowed/not; all 510 other safety words 0–511; valid (`02 3E 80`) and invalid tester-present forms; DEBUG-vs-RELEASE positive control (Bosch-long and valid UDS). No safety source changed. | `test_accord11g_trackb_release_sweep.py` |

No production source (`openpilot/`, `opendbc_repo/opendbc/car|safety|dbc`, `panda/`) was modified.

## 3. B1 — authoritative evidence still required (per critical item)

All remain **BLOCKED / HOLD**. No generic Bosch ID, DBC name, inferred checksum, or historical C6-12 code is accepted as target authority. Each row needs independently reviewed, target-specific (2025 US Accord Hybrid) OEM service or physical non-actuating evidence:

| Item | Required evidence |
| --- | --- |
| ACC | Owning ECU, command/status frame set, counters/integrity, takeover and fault semantics |
| PCM | Torque/brake arbitration with ACC; accelerator/brake override precedence |
| Radar | Shared radar function with CMBS; confirmation no suppression is required or permitted |
| Camera | Role in LKAS/ACC/CMBS; fault propagation |
| CMBS/AEB | Frame-level state and precedence over any external request; activation/clear semantics |
| Braking | Brake-hold and decel authority owner, limits, failure behavior |
| Gateway/relay | Which bus segments the comma relay isolates; fail-safe relay state; forwarding ownership |
| CAN-FD arbitration | Identifier ownership, bus topology, timing, bus-off and recovery behavior |

## 4. B3 — host library vs target firmware

Results here come from a locally compiled `libsafety` with `release=True` (no `ALLOW_DEBUG`). They are **not** validation of the flashed Panda firmware. Target RELEASE binary hash, build provenance, and flash identity are absent: qualification HOLD.

## 5. B4 — installation preparation

- Candidate is source-only: stock ACC (`pcmCruise=True`, no openpilot longitudinal) is unchanged and Track B modules are not imported by runtime (M-3).
- No comma device was reachable (no ADB/SSH target configured; no network probing was attempted). Zero device observations were made.
- ARM64: Track B research, RELEASE (host library compiled natively under aarch64 emulation), Honda stock-ownership, and parked-audit tests were run in the existing `dom7-trackb-arm64` container (QEMU user-mode, network disabled). This is a source/dependency compatibility check, **not** device or AGNOS evidence. A full ARM64 SCons build of Dom was not performed (see report).
- AGNOS pins are manifest text: `openpilot/common/hardware/comma/agnos.json` blob `b3a23b4c28269fef31ae94f5560c876ce8c1acba`; `system` hash `9c753bdd…3832cfd`. No installed-image measurement exists.

### Rollback (nothing is installed by this branch)

1. Do not flash firmware or change boot slots. Before any later authorized install, record the active device's current branch/commit, `/data/openpilot` state, and Params backup, and confirm a known-good commit exists.
2. Install only by switching the source checkout (e.g. `git checkout <known-good-commit>`) while parked/offroad; the candidate adds no Params, services, or firmware.
3. Rollback is the reverse switch to the recorded known-good commit followed by the parked audit (`B4_PARKED_PROCEDURE.md`). Since this branch changes no runtime state, there is no data migration to undo.

## 6. Requirement → test matrix

| Requirement | Evidence |
| --- | --- |
| FR-B0-01/02 stock ownership | `test_accord11g_stock_ownership_v4.py`, `test_accord11g_trackb_no_long_authority.py` |
| FR-B0-03/04 audit | `scripts/tests/test_accord11g_trackb_parked_audit.py` |
| FR-B0-06 FCW fail-closed | `test_plan_controller_sim.py` |
| FR-B0-07 schema binding | `test_plan_snapshot_schema_contract.py` |
| FR-B0-08 isolation | `test_architectural_isolation.py` |
| FR-B0-09 RELEASE denial | `test_accord11g_trackb_release_denials.py`, `..._rejections_extended.py`, `..._release_sweep.py` |
| Ownership / brake-hold / synthetic faults | `test_ownership_evidence_model.py`, `test_brake_hold_contract.py`, `test_shadow_synthetic.py` |
| FR-B0-05 owner transition | **UNVERIFIED** — blocked on §3 evidence |

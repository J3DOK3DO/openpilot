# Accord 11G Hybrid Release B — readiness matrix and tier verdicts (2026-11-01)

Branch `accord11g-dom7-releaseb-tier2-candidate-20261101`, descended from the verified research baseline
`accord11g-dom7-mvl-architecture-delta-20261101` @ `12021bdc` (which descends from the Claude candidate `bc1eea1a`).
Final SHA: see the continuation handoff and the remote branch.

## Readiness matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Source completeness (non-actuating) | COMPLETE for the offline scope | B0/B2 simulators, B17 symbolic models, MVL delta contracts (`source_evidence_contracts.py`) |
| 17 retained operational IDs | **SYNTHETIC ONLY**: 17 symbolic research models, 0 vehicle implementations | `TRACKB_B17_RETAINED_PATCH_SIMULATION_MATRIX_20261101.tsv` |
| Research tests | 574 passed (500 inherited + 52 delta contracts + 2 RB1 additions + 20 lock-off) | `logs/` in the artifacts directory |
| Honda/Track A/Panda/AOL regression | host 3138 passed, 273 skipped (classified), 0 failed on `6866782c`; RB1 delta re-run 574 passed | `logs/HOST_TESTS_RELEASEB_TIER2_CANDIDATE.log` |
| ARM64 native build | PASS (`BUILD_EXIT=0`, tree `4e3605e6`); later commits change no native input (Python, tests, docs only) | `logs/ARM64_NATIVE_BUILD.log` |
| ARM64 tests | 2101 passed; all 19 Honda CAN-FD AOL lifecycle cases now pass on ARM64 with only the fixture's compiler timeout raised by a test-only plugin (no assertion changed) | `logs/ARM64_HONDA_CANFD_LIFECYCLE_ALL_EXTENDED_COMPILE_TIMEOUT.log`, `audit_tools/arm64_plugin/` |
| ABI | 55 AArch64 ELF; static + device `ldd` evidence | `release/COMMITTED_ELF_ABI_AUDIT_candidate.json`, `release/DEVICE_LDD_REPO_LIBRARIES_20261101.txt` |
| Independent review | Claude-era R1–R3 APPROVE WITH FINDINGS (fixed); post-Claude Codex R4 APPROVE (`1d810b74`); RB1 (`gpt-6-luna`/low) APPROVE WITH FINDINGS, fixed; RB1 also closed the R3 evidence fixes; RB2 (`gpt-6-luna`/low) on the fix: **APPROVE** (reviewer could not execute tests; execution evidence is the 574-pass run) | `review/CODEX_REVIEW_FINAL_MESSAGE_RB1.md`, `_RB2.md` |
| B1 OEM authority (4 gates) | **HOLD**, 0/4 authenticated | `TRACKB_B1_RESEARCH_CONTINUATION_20261101.md` |
| Loss-of-CMBS/AEB/FCW safety case | **HOLD**: no qualified replacement detector or independent emergency braking; CC-01 proposed, not approved | `TRACKB_RELEASE_B_SAFETY_CASE_AND_QUALIFICATION_20261101.md` |
| Target Panda | DEBUG (owner-accepted research deviation DEV-PANDA-DEBUG-001); RELEASE qualification **not met** | device audit |
| Target AGNOS | 19.8.1, raw hash ≠ pinned (DEV-AGNOS-HASH-001); ABI files identical | device audit |
| B5 bench | procedure written; **NOT EXECUTED** | safety case §4 |
| B6 closed course | procedure written; **NOT EXECUTED** | safety case §5 |
| Longitudinal lock-off | ASSERTED by tests: no configuration or preference route gives the 11G openpilot long; Panda words 80/81 only; no radar UDS; research code unreachable | `test_accord11g_releaseb_lockoff.py`, `test_accord11g_debug_release_parity.py`, `test_accord11g_no_radar_uds.py`, `test_architectural_isolation.py` |

## Tier verdicts

| Tier | Verdict | Reason |
| --- | --- | --- |
| **Tier 1 — research complete and reviewable** | **COMPLETE** | all feasible offline contracts, simulations and negative tests in place, reproducible, independently reviewed; no vehicle-facing actuation |
| **Tier 2 — comma-installable engineering candidate** | **ESTABLISHED FOR NON-ACTIVE EVALUATION, NOT INSTALLED** | production delta vs installed Dom is one Python file; all 93 binaries and the Panda firmware identical to the installed car; ARM64 build and tests pass; custom longitudinal locked off. Install by comma installer or git (Fast Update refuses: no valid receipt, none fabricated). Unverified: the install itself and on-device runtime (not authorized). Note: it changes lateral behaviour on the Hybrid (AOL and the Track A takeover become active), which needs a supervised check. |
| **Tier 3 — vehicle-ready operational longitudinal** | **TIER_3_HOLD** | B1 0/4; no replacement for lost CMBS/AEB/FCW; no RELEASE Panda with a B1-derived table; B5/B6 not executed; no independent functional-safety or legal review |

Next concrete evidence for Tier 3: authenticated Honda service/electrical data for longitudinal command ownership and
CMBS/AEB arbitration on the 2025 US Accord Hybrid; then a qualified CMBS replacement or a CMBS-preserving design;
then a RELEASE Panda build; then separately authorized B5 and B6.

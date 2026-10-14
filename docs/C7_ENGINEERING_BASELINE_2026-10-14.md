# C7 engineering baseline — 14 October 2026 (canonical R1 notice)

Status: **SOURCE / OFFLINE REVIEW ONLY. NOT DEVICE QUALIFIED. NOT ROAD APPROVED.**

## Immutable driving-code provenance
- Frozen C6-12 source SHA: `7b4db9a26010ba9899eef242d3ca49b33cbcca9c`.
- Original C7 documentation-only checkpoint: `ec27fb7885707ccb36b6593bc0527c403278d1fd`, a direct child of the frozen C6-12 SHA.
- The review-remediation documentation revision is descended from this checkpoint. No actuation, planner, Panda, native solver, message-schema or system executable change is authorized or part of this documentation update.
- No C6-13A/B merge, private-state observer or related binary/capture device instrumentation is imported.
- C6-12 driving behavior remains the active installed baseline, unmodified on this Ubuntu source tree.

## Pinned upstream sources — evidence only, never wholesale import
- StarPilot Dom base `5c3ddd58e1` → head `b220a37f4bd119e402225a7aa16a7cd84878d0af`: 31 verified local commits, separate audit Git ref `refs/audit/c7/dom-head-20261014`.
- MVL source head `66598eda130dde70fbf84278215adabd174afe36`: 138 right-side / 26 historical-only commits from diverged `66ad9fac65...`.
- MVL opendbc `8901198...cf46117420f283b3e38241c00d728a191aa9fccc`: 116 commits, patch deduplication and pre-base behavior origins require explicit classification.
- MVL Panda health protocol change `ea5a83...74a0adc`: seven commits, no import.
- Never auto-import Dom MPC/solver changes, Panda SPI/health/firmware, Bosch-A radar, Nidec/other-car tuning or generic Bosch stop/PID.

## Supersession: one canonical nine-stage plan
The earlier five-stage shorthand is **withdrawn and non-authoritative**. The governing sequence, action IDs and evidence gates are specified in [C7_REVIEW_REMEDIATION_CANONICAL_R1.md](C7_REVIEW_REMEDIATION_CANONICAL_R1.md) and the R1 master workbook.

**Canonical stages:** C7-0 source/traceability; C7-1 external host-native baseline; C7-2 full replay/CAN; C7-3 issue-specific causal RED; C7-4 isolated conditional implementation; C7-5 offline/ARM64; C7-6 independent source and qualified safety signoff; C7-7 pre-verified rollback and separately authorized parked check; C7-8 pre-authorized controlled test then post-test release verdict.

**Gate states:** G00/G01 source/catalogue proven, G03 source inventory with unresolved semantic origin, G04 pinned Dom31 reproduced. G02 exact patch equivalence HOLD. G05–G19 remain blocked/open/HOLD. G18A (rollback preflight) precedes any staged startup, G18B follows parked evidence. G19A (controlled-evaluation authorization) precedes motion, G19B (release decision) follows evaluation.

**Safety boundaries:** `interruptRateCan2` P0 remains unresolved, not waived. CANFD stock-radar ownership, Panda `0x1DF` semantic checks, headway and physical actuation must be independently qualified before any device/release approval. The offline S01–S16 synthetic detector tests and source-only fault models are NOT qualified vehicle evidence.

**Next permitted work:** Host-only provenance, complete manual source linkage, fixed native test harness and independent evidence collection planning. No comma deployment or road authority is implied.

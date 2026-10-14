# C7 review remediation — canonical execution and release controls (Revision R1)

**Date:** 2026-10-14 Asia/Dubai. **Status:** offline engineering remediation only.
**Canonical phase dictionary:** 9-stage `C7-0 ... C7-8` / 49 work packages / 20 historical gate IDs, as maintained in `Accord11G_C7_Detailed_Stage_Gated_Engineering_Plan_2026-10-14.xlsx`, with the post-authorization split gates below.
**Supersedes:** the earlier 5-stage shorthand `C7-0...C7-4` in `docs/C7_ENGINEERING_BASELINE_2026-10-14.md`. That document remains the Git provenance record, not a release workflow.
**Protected source:** C6-12 `7b4db9a26010ba9899eef242d3ca49b33cbcca9c`, original C7 documentation-only checkpoint `ec27fb7885707ccb36b6593bc0527c403278d1fd`. No C6-13 actuation, planner, Panda or observer import.

## Single governing stage sequence
- **C7-0: Source provenance and traceability.** Exact parent/tree/submodule identity, complete Dom/MVL pinned inventories, all 39 historical IDs, many-to-many SHAs and C6-12 implementation code, no fabricated equivalence. Use G00–G04, with G02 HOLD until exact source-to-behavior mapping accepted. C7-0 may permit C7-1 host tooling before G02 is closed, but no control implementation.
- **C7-1: Out-of-tree x86 host harness.** G05 interpreter, binary, schema, ABI, compiler/loader/import-precedence manifest; G06 fresh entire core baseline with fixed denominator, two repeat runs, no hidden skip or altered production sources.
- **C7-2: Reference replays and CAN proof.** G07 planner (investigate all 17 historical residuals), G08 Honda state selector, G09 independent raw-log baseline CAN full-frame byte/bus/order/counter/checksum/timing oracle; G10 urgent, stop, source ownership and safety contracts. Historical synthetic/pass counts do not close any current gate.
- **C7-3: Per-issue root-cause evidence.** G11 issue-specific failing RED with authentic same-input source; G12 independently measured lateral EPS/yaw and physically calibrated stopping geometry where relevant. Missing ground truth is HOLD, not invented values.
- **C7-4: Isolated, contingent code changes.** G13 only when verified C7-0/G02 scope + approved S01–S16 requirements + fresh baseline + RED oracle and change safety assessment. Minimum code delta; test unaffected CAN exact, target fields only preapproved bounded deviations; no bulk Dom/MVL/Panda/solver change.
- **C7-5: Full offline/ARM64 qualification.** G14 native binaries/source-to-artefact, timing, deterministic retries and G15 host/Panda/firmware/configuration *invariance* demonstrated. G15 DOES NOT constitute independent safety clearance.
- **C7-6: Independent source + safety acceptance.** G16 signed independent code and test review; G17 separately qualified and conflict-free safety assessor, explicit resolution of Panda P0 interruptRateCan2 and Honda 0x1DF safety/radar ownership findings. No waiver-by-exclusion. Any unresolved blocker = HOLD.
- **C7-7: Parked qualification only after rollback preflight.** **G18A** recovery image SHA/hash and rollback method/credentials, loss-of-power drill, explicit parked stage authorization BEFORE candidate staging. **G18B** independently observed parked startup, safety checks, restoration and post-test rollback replay. Parked pass not road approval.
- **C7-8: Controlled evaluation, then release decision.** **G19A** explicit controlled-testing authorization (venue/ODD, trained operator, independent risk owner, abort/incident/rollback conditions) BEFORE moving. **G19B** post-evaluation evidence, objective success/safety checks, signature and release/revert decision. No combined prior authorization and later outcome.

## Gate numbers and current state
| Gate | Canonical acceptance | 2026-10-14 status |
|---|---|---|
| G00 | C6-12/C7 direct source-baseline provenance, zero driving-code diff | PASS (docs-only checkpoint, recheck after new docs commit) |
| G01 | Unique 39 historic IDs and original C5 decisions preserved | PASS — catalogue only |
| G02 | Exact 39 source/feature/11G reachability/equivalence supported by reviewer | HOLD — 39 candidate maps; zero exact semantics approved |
| G03 | MVL 138 current, 26 old-side, opendbc 116 and Panda 7 SHA enumeration with patch-ID dedup & historical origin | INVENTORY COMPLETE; BEHAVIOR/ORIGIN QUALIFICATION HOLD |
| G04 | Locally reproducible 31 Dom commits after `5c3ddd58e1` and risk-filtered manifest | PASS — 31 Git objects fetched; semantics only candidate |
| G05 | x86 host ABI/source/loader and external build trust | BLOCKED |
| G06 | Fresh complete baseline suite, repeatable collection/skip accounting | HOLD |
| G07 | Fresh planner replay and 17 residual dispositions | HOLD |
| G08 | Fresh selector replay, no full-CAN claim | HOLD |
| G09 | Independent baseline CAN frame oracle | HOLD |
| G10 | Urgent, stop, cruise, gas/brake, Panda and radar contracts | HOLD |
| G11 | Each issue's objective RED root cause and independent oracle | HOLD |
| G12 | Measured yaw/EPS and stop-line geometry where relevant | HOLD |
| G13 | Allowlisted isolated GREEN/no regression and reviewed target deltas | HOLD |
| G14 | ARM64 target native/runtime/solver ABI and deadline | HOLD |
| G15 | Panda firmware/host/safety configuration invariance, **not safety approval** | HOLD |
| G16 | Independent source/test signoff | HOLD |
| G17 | External qualified safety acceptance; P0 and S04/S11/S15 blockers resolved | HOLD |
| G18A/B | Rollback preflight and separately authorized parked evaluation & restore | HOLD |
| G19A/B | Prior authorized controlled evaluation, then signed release decision | HOLD |

## Corrected upstream provenance
- **Dom:** baseline `5c3ddd58e1`; fetched public head `b220a37f4bd119e402225a7aa16a7cd84878d0af`; 31 commits verified via local Git audit ref `refs/audit/c7/dom-head-20261014`, no merge.
- **MVL source:** `66ad9fac65...66598eda130d` is diverged: 138 right-side, 26 left-side commits. Its opendbc `8901198...cf461174` has 116 later commits; Panda health ABI `ea5a83...74a0adc` 7 commits.
- **HD-04 ERRATUM:** `8ad8ada7714e` is UI onroad-cycle toggle settings, **not** radar-ownership implementation. The behavior-origin candidate is opendbc `e9c194084780fe14ad13b030b4c9bdfb2ee8ed23`; verify full ancestors/final states. This correction removes the false prior attribution.
- Full 287-SHA inventory **does not** imply 287 unique behaviors: history includes cherry-picks, merges, reverted patches and path-based classifications. Duplicate patch fingerprints and nested pre-base origins must be documented before G03 behavior qualification.
- `39_patch_traceability.csv/json`: 39/39 source candidates, no semantic equivalence automatically marked exact. `G02` remains HOLD. C6-derived labels C4-030–036 must not be mislabeled MVL upstream patches.

## Radar / CAN / Panda safety investigation (READ-ONLY)
**Confirmed static source facts:** C6 `carstate.py` sets `stock_acc_alive=(stock_acc_counter < 4)` and infers `canfd_relay_open` from camera silence or `canfd_frames >= 500`; `carcontroller.py` selects ownership from that inferred relay flag and `not stock_acc_alive`. False silence/wrong bus/parser loss can produce an inferred owner without independent proof of physical relay/radar state. The Panda Honda `0x1DF` TX section checks numeric accel/gas limits but lacks checks for all brake/control/standstill semantic bits. These are source-level hazards, **not proven real incidents**. `radarUnavailable` from planner is not physical radar silence.

**Mandatory fault evidence set:** camera never seen; relay fails closed; physical relay state disagrees with timer; wrong-bus/parser loss; four missing ACC frames; transient stock return; UDS request/ack failure; delayed Panda safety-mode switch; process crash without deinit; reconnect / rapid restart; two producers present; all semantic 0x1DF fields independently mutated; signed host/firmware binaries and unresolved `interruptRateCan2`. Independently captured electrical/CAN state and a safety-approved Panda policy are required. No on-device live injection or firmware flash is permitted in this stage.

**Source-only probe:** `radar_can_source_probe.py` reproduces four simplified counterexamples and verifies the absence of semantic 0x1DF checks. This illustrates hypotheses only; it does not clear G10, G15 or G17.

## Sixteen executable contracts and independent-oracle policy
`run_contracts.py` implements S01–S16 source-derived safety predicates; `16_scenario_manifest.json` preserves names, historical links and externally approved threshold requirements.
- `python3 run_contracts.py --selftest` must pass **16 synthetic positive** and detect **16 deliberately mutated negative controls**. This proves detector plumbing only.
- `python3 run_contracts.py --evidence-dir <authenticated-fixtures-directory>` is fail-closed: missing captures, independently generated source oracles, vehicle identification, source SHA, hash/owner approval or threshold signoffs yield HOLD, not PASS.
- Do not invent numeric bounds for response latency, headway, yaw/stop geometry, IO deadlines, timing or rollback. All are explicitly unapproved until qualified sources supply values. S09/S10 require real independent measurements.
- Before actuation-code work, a qualified reviewer must audit every scenario's initial state, expected outcome, raw-log time bases, boundary transitions, accepted absolute/relative tolerances, negative-control test and rollback.

## Authority and boundaries
- Engineering/QA owner: **TBA** (do not infer user is an accredited safety reviewer).
- Independent source reviewer: Codex Sol High reports are advisory; human reviewer and independence criteria **TBA**.
- Qualified independent automotive/Panda safety owner: **TBA**.
- User authorization covers offline code review, git fetch, documentation and strictly external synthetic/audit harnesses. It does not establish vehicle road safety.

**Outcome:** review workflow and static/intake discrepancies remediated, but G02, G05–G19 and qualified safety acceptance remain HOLD. C6-12 remains deployed; C7 not installed.

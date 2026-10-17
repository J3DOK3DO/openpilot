# C7 versus Dom: 34-Commit Upstream Delta Assessment

**Assessment: 17 October 2026, Asia/Dubai**
**Repository:** J3DOK3DO/openpilot
**Mode:** read-only engineering audit, paused C7 development; no actual merge, cherry-pick, deployment or Panda/CAN access.

## Executive decision

The 34-commit difference is due to intentional divergence: C7 is frozen from a protected C6-12 lineage, while Dom continued evolving. Both branches contain unique work. The counts are NOT equivalent to 34 needed fixes.

C7 assessed head: `4ba1dde4e4d8e8abfca390f25a48d3d9ba9153bf`. Dom head: `823a5d5674ec6635b51dd989884dfbd661f90dc4`. Common ancestor: `5c3ddd58e1b25cf1cf65ebac826f0aefb5f5ec8c`.
C7-only commits: **16**. Dom-only commits: **34**. Files changed from ancestor: Dom **263**, C7 **41**; **13** independently changed files.
Across the 34 Dom commits, **seven commits include binary changes (271 binary-file change events, not distinct binaries)**. Those prebuilt outputs are not trusted release inputs.

| Classification | Commits | C7 disposition |
|---|---:|---|
| **P1 immediate technical review** | **5** | Control/safety/API-sensitive, do not port without isolated tests |
| **P2 compatibility review** | **4** | Conditional relevance; review only if justified |
| **Defer** | **18** | UI and other-make changes not on C7 release critical path |
| **Exclude as commits** | **7** | Primarily binary builds or documentation; do not cherry-pick |
| **TOTAL** | **34** | Every commit individually classified |

## Five P1 engineering findings from actual source diffs

### A. SLC / CSC / message schema: `12947fd616`
Dom adds slcPresentedSpeedLimitSource and slcIsLimitingMaxSet to cereal/custom.capnp and significantly refactors speed-limit-controller behavior. It changes the order of StarPilot vCruise SLC update relative to Curve Speed Controller button handling and changes speed-limit pending-confirmation semantics. C7 has a reviewed curve-speed numerical correction and F8 source-built cereal schema. A partial import could break the schema producer/consumer or change CSC override behavior.
**Assessment:** high interaction risk. Isolated schema ABI reader/writer tests, pending/confirmed speed limit cases, accelerator button/driver override, map source precedence, actual Honda logs. Do not bulk-import the UI and 831-line SLC rewrite.

### B. Params compatibility / boot handoff: `c2109496a7`
Dom creates starpilot/common/cache_compat.py and tests and invokes retire_foreign_caches during manager initialization. Code archives and removes branch-specific cache keys using file locks, checksums and symlink/ownership checks. The C7 source currently lacks this helper. It may matter when switching C6-12, Dom and C7, but it modifies persistent state.
**Assessment:** high startup/data-loss risk. Test only in disposable Params directories with corrupted/oversized files, symlink races, permissions, partial migration and rollback. Never apply directly to device Params.

### C. Longitudinal MPC terminal constraints: `e75470f2e8`
Dom adds terminal con_h_expr_e, terminal bounds and idxsh_e, terminal slack cost vectors, and changes the solver Zl update range from N to N+1. SConscript also adds terminal-constraint generated C files. The currently inspected C7 long_mpc.py lacks these additions. F8 rebuilt Acados from older candidate code; status-zero default solver smoke tests cannot establish that terminal constraints are correct or unnecessary.
**Assessment:** top-priority selective solver trial. Generate old/new Acados C from source under identical pinned toolchain; compare dimensionality, feasibility, solver convergence, N-stage costs, real Honda lead-follow/curve scenarios and timing. Do not use the prebuilt solver binary included upstream.

### D. Stop-light / lead behavior: `956aceaf0a`
Dom introduces model_target_before_lead in ConditionalExperimentalMode and changes shared lead-behavior coast-headway semantics, plus GM/Ford/Tesla features. It modifies starpilot_following.py, which the read-only merge preview reports as a content conflict with the protected C6-12-derived C7 behavior. This overlaps reported premature stop and following concerns.
**Assessment:** high behavior risk. Replay red-light, vision lead, model stop, low-speed transitions, untracked lead, driver inputs and close-lead Honda safety with before/after assertions. Maintain original C6-12 follow/coast protection; no blanket port.

### E. Panda SPI/CAN protocol: `88c73987d0`
Dom adds sequenced SPI CAN-write endpoint 0x83, firmware-side replay suppression and host pandad negotiation/retry/response validation. This is a coupled firmware and host protocol, not merely a Python helper. The same commit contains unrelated other-make tuning and interface changes.
**Assessment:** CRITICAL safety compatibility. Source/firmware attestation, noOutput and controlsAllowed restrictions, lost ACK duplicate-send behavior, sequence wrap, failed negotiation, SPI response bounds and offline CAN fault tests. NEVER move signed Panda artifacts or mix firmware and host changes without a matched gated physical process.

## Four P2 selective-compatibility candidates

- `d2cd3fd0ed`: Honda CR-V 5G STOCK EPS low-speed PID gain, not Accord 11G-specific. Confirm fingerprint guard and unaffected Accord latcontrol behavior; otherwise defer.
- `5e8501002d`: Kia Niro EV follow and slew thresholds implemented in shared longitudinal planner. Check make/vehicle flags and C6-12 Honda coast semantics before even considering a helper port.
- `83f914fc5c`: manager turns RandomEvents off on boot if set. Isolated manager/Params regression and confirmation of intended user preference semantics; possible low-complexity stability patch.
- `b220a37f4b`: moves get_planner_v_ego into vehicle tunes with Kia Ray/GM guards; other-make lateral and read-only Stinger object logging. Verify Honda vEgo behavior and import APIs, not an entire-commit import.

## Full classification — all 34 commits

| # | SHA & date | Title | Classification | Risk | Observed scope and specific disposition |
|---:|---|---|---|---|---|
| 1 | [0857acfc50](https://github.com/J3DOK3DO/openpilot/commit/0857acfc502e10d8b7af5cfda5a75e803090dea7) 2026-10-02 | big ui text size polish | Defer | Low | UI settings typography only: No C7 driving relevance; optional later UI-only visual acceptance |
| 2 | [1aefe9dc82](https://github.com/J3DOK3DO/openpilot/commit/1aefe9dc82ae563ac43aad0cd8d7d9accc1c9a5d) 2026-10-02 | more font size polish | Defer | Low | UI font polish: Defer until UI refresh; screenshot/visual regression only |
| 3 | [4ac874f6b4](https://github.com/J3DOK3DO/openpilot/commit/4ac874f6b43042f952351eb18c1a7c8f63229db3) 2026-10-02 | polish | Defer | Low | UI settings polish: Defer; no Honda behavior evidence |
| 4 | [d2cd3fd0ed](https://github.com/J3DOK3DO/openpilot/commit/d2cd3fd0edf80ba229792c894c09300dfe5b1bb2) 2026-10-02 | Quintessence: A Quest | P2 review | Medium | Honda CR-V 5G PID gain, plus Volvo and Ford: Review Honda-specific code only; verify CR-V 5G guard cannot affect Accord fingerprint, stock/modded EPS and latcontrol tests; no direct Accord tune port |
| 5 | [3293a34219](https://github.com/J3DOK3DO/openpilot/commit/3293a3421917b23770e4a7a514b7bdfa28151c16) 2026-10-02 | build | Exclude | High | Generated Panda/firmware binaries: Do not cherry-pick binaries; independently attest source, board target, signature and firmware before any change |
| 6 | [2efe6017bf](https://github.com/J3DOK3DO/openpilot/commit/2efe6017bfe14cee4807833e05f9a7f6ba255cdb) 2026-10-02 | polish | Defer | Low | StarPilot UI cosmetics: No immediate control/safety value; UI review only |
| 7 | [189f2aafbb](https://github.com/J3DOK3DO/openpilot/commit/189f2aafbb3baccc3097fb07fc0791799a756c04) 2026-10-03 | polish | Defer | Low | Settings / navigation UI: Hold outside C7 runtime; optional UI regression |
| 8 | [12947fd616](https://github.com/J3DOK3DO/openpilot/commit/12947fd616b64507eea878c9f4fbde6a11acccd7) 2026-10-03 | Big Smooshed SLC Stuff (lots) | **P1 REVIEW** | High | SLC/control-target and UI schema refactor: Safety/behavior compatibility: evaluate schema readers/writers, CSC/SLC override ordering, map speed source, confirmed/pending speed targets and conflicts with C7 numerical curve patch; unit + replay tests before any selective port |
| 9 | [7b06ec2ae6](https://github.com/J3DOK3DO/openpilot/commit/7b06ec2ae67097d20bad7471518d1ddb3b26432b) 2026-10-03 | Polish | Defer | Low | UI settings and translations: Defer visual/localization work; no native release gate improvement |
| 10 | [e60595ccc3](https://github.com/J3DOK3DO/openpilot/commit/e60595ccc31b05a7645b374ead816c98851b3d75) 2026-10-03 | Try vert more | Defer | Low | Unified speed vertical UI: Defer; UI visual tests |
| 11 | [f973d151c6](https://github.com/J3DOK3DO/openpilot/commit/f973d151c6718a81c25668d3646534bb50395a76) 2026-10-03 | Try vert more | Defer | Low | Unified speed follow-up styling: Defer with commit #10 as an optional UI bundle |
| 12 | [385428f6ea](https://github.com/J3DOK3DO/openpilot/commit/385428f6ea1c183de4ddcd8604f294abec02a9e8) 2026-10-03 | gv70 | Defer | Medium | Genesis GV70 torque tuning: Non-Honda; preserve Honda tuning; consider only for shared-control test compatibility |
| 13 | [cede5ddc9d](https://github.com/J3DOK3DO/openpilot/commit/cede5ddc9d2ef3f52264353cfcc00f6a44d3898a) 2026-10-03 | Drawer | Defer | Low | Speed source drawer UI: Optional independent UI bundle, avoid partial import without #8 SLC contract |
| 14 | [c2109496a7](https://github.com/J3DOK3DO/openpilot/commit/c2109496a72e85ca702ecef7aff53ff45adcfb8c) 2026-10-03 | Compatibility Shim | **P1 REVIEW** | High | Params/cache compatibility on branch switching: Highly relevant to C6-12↔C7 transitions; potential destructive cache migration. Run isolated temp Params namespace tests, symlink/race/fault injection and rollback; never activate blindly |
| 15 | [15c7110647](https://github.com/J3DOK3DO/openpilot/commit/15c7110647a157d0ce25eaed606ca335eecf5ea8) 2026-10-04 | The Bell | Defer | Medium | Hyundai/Toyota/Ford behaviors and UI: Non-Accord vehicle specifics; no direct cherry-pick. Only shared API compatibility review if necessary |
| 16 | [c582bd3f2d](https://github.com/J3DOK3DO/openpilot/commit/c582bd3f2d7bf03dc0d81c963bb054bb5e402735) 2026-10-04 | Reckoning of Bell | Defer | Medium | Ford lateral/safety refinement: Exclude from Accord-specific integration absent shared regression evidence |
| 17 | [5e8501002d](https://github.com/J3DOK3DO/openpilot/commit/5e8501002de1bd5fa033ca67dedbce723e513b74) 2026-10-05 | Fire Sauce | P2 review | Medium | Kia Niro lead follow in shared longitudinal planner: Check make/fingerprint gating and lead-control interaction with protected C6-12 Honda follow/coast patches; selective utility tests only, no whole commit |
| 18 | [d9bd49fb8a](https://github.com/J3DOK3DO/openpilot/commit/d9bd49fb8afd81323177d426e841f77b318aabed) 2026-10-05 | build | Exclude | High | Panda and native compiled outputs: Treat generated binaries as nonportable and unsigned for this target; never upstream-merge into source-built C7 |
| 19 | [34ecbf9204](https://github.com/J3DOK3DO/openpilot/commit/34ecbf9204f74719f6c9310e8552d89192389da4) 2026-10-05 | Cabo | Defer | Medium | Toyota and Ford lateral refinements: No Accord tune change; defer vehicle-specific code |
| 20 | [6de77049b3](https://github.com/J3DOK3DO/openpilot/commit/6de77049b3c3dc77c7275e9ff724a96f9e72a19d) 2026-10-06 | Potato Ole | Defer | Medium | Volkswagen GPS and cross-car lateral testing: No Honda GPS process identified; defer except reuse neutral tests when needed |
| 21 | [e75470f2e8](https://github.com/J3DOK3DO/openpilot/commit/e75470f2e8bd791f29d3740abd0eaba7b709fc00) 2026-10-07 | Overrun | **P1 REVIEW** | High | Longitudinal MPC terminal constraints: CURRENT C7 long_mpc lacks terminal constraints; F8 re-generated solver from older source. Review dynamics/constraints/feasibility and solver source, regenerate with verified Acados toolchain, test source-built latency/status and 217 higher-decel replay contexts. NEVER copy binary |
| 22 | [934dadbcdb](https://github.com/J3DOK3DO/openpilot/commit/934dadbcdbaaaac78dd6badd09a1ebadd298bae8) 2026-10-08 | Toyota Hold | Defer | Medium | Toyota hold feature: Non-Honda; no direct port |
| 23 | [ebd62915a2](https://github.com/J3DOK3DO/openpilot/commit/ebd62915a25c644833d457b6adf5979bc65f986a) 2026-10-08 | Alan, My Boi | Defer | Medium | Sonata Hybrid LKAS button migration: Other vehicle and generated binaries; no Accord mapping change |
| 24 | [15bbbf3cc4](https://github.com/J3DOK3DO/openpilot/commit/15bbbf3cc4ad251c173abf01fff931951202331a) 2026-10-08 | Quaker Oats | Defer | Medium | Ford/Toyota lateral control: Defer absent evidence for Accord; no generic latcontrol replacement |
| 25 | [51d09a6274](https://github.com/J3DOK3DO/openpilot/commit/51d09a6274c337b520f6e7d40c96b2bb9580c3cd) 2026-10-08 | Boot logo refresh on panel open | Defer | Low | Theme boot logo refresh: Visual side-feature; isolate from C7 safety work |
| 26 | [956aceaf0a](https://github.com/J3DOK3DO/openpilot/commit/956aceaf0ab96afcd737ffdc0758ace7eb9dad48) 2026-10-08 | hiya peach | **P1 REVIEW** | High | Stop-light model target vs lead and following/coast: Directly relevant to reported stop-light distance/lead behavior. Compare with C6-12 protected semantics and test conflicts in starpilot_following, run recorded Honda stop/lead replay, guard non-Honda paths; no blanket port |
| 27 | [61fd19556f](https://github.com/J3DOK3DO/openpilot/commit/61fd19556f985ef462bda9c103396108ea69ad14) 2026-10-08 | panda | Exclude | High | Panda signed firmware build snapshot: Do not copy firmware artifacts; physical Panda attestation and source-qualified build first |
| 28 | [83f914fc5c](https://github.com/J3DOK3DO/openpilot/commit/83f914fc5cc5e1f9a18dfd7ed3c3b41b5759344b) 2026-10-11 | Disable random events on boot if enabled | P2 review | Low | Disable random events on boot: Small startup-stability candidate; determine C7 current RandomEvents defaults and owner intent, add isolated manager init guard tests and verify no undesired user preference override |
| 29 | [88c73987d0](https://github.com/J3DOK3DO/openpilot/commit/88c73987d0a5a471576932896738764036da9984) 2026-10-12 | Green Garden | **P1 REVIEW** | Critical | Panda SPI sequenced CAN-write protocol and control changes: Critical host↔Panda firmware compatibility / double-transmit risk; evaluate board type, firmware ABI, ACK loss/retry semantics, noOutput and controlsAllowed behavior. Require source+firmware integration tests, NEVER deploy by mixing versions; other vehicle tunes excluded |
| 30 | [3ccae7b88d](https://github.com/J3DOK3DO/openpilot/commit/3ccae7b88de336bff5a0f9fc9be925dac0c65de6) 2026-10-12 | build | Exclude | High | Generated Panda/Params binaries + Toyota ARS tweaks: Never port compiled objects; Toyota-only source changes not Accord-relevant |
| 31 | [b220a37f4b](https://github.com/J3DOK3DO/openpilot/commit/b220a37f4bd119e402225a7aa16a7cd84878d0af) 2026-10-13 | Sea Turtles | P2 review | Medium | Shared planner vEgo relocation and other-make control: Check source API semantic equality for Honda and existing C6-12 follow behavior; read-only stinger tool not Honda. Favor targeted tests only, defer other-make additions |
| 32 | [807acc0522](https://github.com/J3DOK3DO/openpilot/commit/807acc05227339a5e377e0f3cfae64bc1de2c4a9) 2026-10-15 | update README.md | Exclude | Low | README-only change: No implementation or release relevance; documentation may be referenced independently |
| 33 | [1391d3a39c](https://github.com/J3DOK3DO/openpilot/commit/1391d3a39c04b800f6ff19c2288f1fbff91f7052) 2026-10-15 | update README.md | Exclude | Low | README follow-up: No implementation or release relevance |
| 34 | [823a5d5674](https://github.com/J3DOK3DO/openpilot/commit/823a5d5674ec6635b51dd989884dfbd661f90dc4) 2026-10-15 | Waffles | Exclude | High | Hyundai/Subaru behavior and Panda binary image refresh: Do not import as a whole; other-make implementation not C7 Accord scoped and signed Panda images must not be reused without matching source/firmware |

## Merge-preview findings: exactly two textual conflicts

The read-only Git merge-tree preview returned two content conflicts and no working-tree merge:
- `selfdrive/controls/tests/test_starpilot_acceleration.py` — F8 source-faithful acceleration fixture versus Dom speed-control tests.
- `starpilot/controls/lib/starpilot_following.py` — preserved C6-12 follow behavior versus Dom changed far-lead headway-call signature.

The 13 changed-on-both paths since the common ancestor were:
- `cereal/custom.capnp`
- `selfdrive/controls/lib/latcontrol_pid.py`
- `selfdrive/controls/lib/lead_behavior.py`
- `selfdrive/controls/lib/longitudinal_planner.py`
- `selfdrive/controls/lib/longitudinal_vehicle_tunes.py`
- `selfdrive/controls/tests/test_latcontrol.py`
- `selfdrive/controls/tests/test_lead_behavior.py`
- `selfdrive/controls/tests/test_longcontrol.py`
- `selfdrive/controls/tests/test_longitudinal_planner.py`
- `selfdrive/controls/tests/test_starpilot_acceleration.py`
- `starpilot/controls/lib/starpilot_following.py`
- `starpilot/controls/starpilot_planner.py`
- `starpilot/controls/tests/test_personality_following_profiles.py`

Even automatically merging the remaining changes would not establish semantic compatibility. Message schema, native MPC source generation and Panda firmware/host protocols can have breaking cross-component effects without textual merge conflicts.

## Gated follow-on audit plan

| Order | Commit set | Tests/evidence required before any port |
|---:|---|---|
| 1 | MPC `e75470f2e8` | Rebuild pre/post solver with same F8 target toolchain; test terminal constraints, dynamic trajectories, runtime and safety envelopes. |
| 2 | Lead/stop `956aceaf0a` | Honda real-log before/after stop/lead/follow replay, C6-12 safety invariants and conflict resolution tests. |
| 3 | Cache `c2109496a7` | Disposable Params migration, corrupt/symlink/race/rollback/boot tests, state-preservation evidence. |
| 4 | SPI/CAN `88c73987d0` | Offline protocol sequence/ACK/fault emulation, exact matched firmware/host source and safety signoff; no device action. |
| 5 | SLC `12947fd616` | Schema and CSC/SLC speed target/button-priority replay, UI confirmation behavior, no curve-limit regressions. |
| 6 | Four P2 commits | Cross-make guards and source/API compatibility tests; selective isolated port only if a proven value exists. |
| 7 | Remaining 25 commits | Defer/exclude; source-reviewed UI-only updates on request, never copy unchecked binaries. |

## Relationship to current C7 release blockers

Nothing about 34-behind changes the C7 F8 verified status: 13 AArch64 source-linked artifacts exist and 7 engineering areas have scoped tests, but **0/7 complete end-to-end release groups** were qualified. Real Honda braking response, complete source-coherent application integration, the 72 skipped AOL tests, three non-Honda calibration failures, 39 patch dispositions, physical Panda/CAN firmware safety, rollback and release-owner approvals remain open. Keep C6-12 active and both protected sources frozen.

## Limits, evidence and preservation

Source basis: actual Git commit objects, file diffs and related code hunks on local J3DOK3DO/openpilot Dom head `823a5d5674ec` compared with C7 head `4ba1dde4e4d8`. Classifications are **engineering judgements** from source review, not proofs that a new Dom feature improves Honda or that everything not selected is harmless. Commit-specific binary blobs have no source-build proof merely by existing.

Machine audit datasets available locally: `data/delta_manifest.json`, `data/engineering_dispositions.json`, `data/upstream_delta_tracker.json`, `data/classification_summary.tsv`, `data/patches/`, and the read-only merge preview under data.

**No actual merge, cherry-pick, C7 code change, device operation, Panda flashing or CAN transmission. C7 release HOLD.**

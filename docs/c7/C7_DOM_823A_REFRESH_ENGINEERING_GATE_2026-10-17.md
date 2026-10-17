# C7 Refresh to Current Dom — Source Integration and Acceptance Gates

**Date:** 17 October 2026 | **Mode:** Experimental offline source merge; no comma deployment or road testing.
**Status:** **SOURCE MERGED; NATIVE/SAFETY RELEASE HOLD**.

## Exact source identity

| Input | Commit |
|---|---|
| Frozen C6-12 operational reference | `7b4db9a26010ba9899eef242d3ca49b33cbcca9c` (clean / not modified) |
| Protected C7 source | `48bd4c1d88f2a964cc9d2f0f58aca9d43681149d` (clean / not modified) |
| Prior C7-F8 offline assessment source | `4ba1dde4e4d8e8abfca390f25a48d3d9ba9153bf` |
| Verified current `J3DOK3DO/openpilot:Dom` head | `823a5d5674ec6635b51dd989884dfbd661f90dc4` |
| MVL source new head (review only, not merged) | `cb15c04e918b759688cb354b1bbc9b3c5a47a65c` |

This experimental merge has **both C7-F8 and current Dom histories as parents**. It is not a rebase of, or write to, protected C7; it is not a statement that the C7-to-Dom semantic and firmware compatibility gates passed. The prior Dom-only comparison recorded 34 incoming Dom commits and 16 C7-only commits.

## Integration actions

1. Source-merged the 34 Dom-only commits into a fresh isolated branch from the published C7-F8 assessment head. **No changes to protected baselines or installed comma.**
2. Resolved both Git content conflicts explicitly:
   - `selfdrive/controls/tests/test_starpilot_acceleration.py`: preserved source enum `log.LongitudinalPersonality.standard` instead of Dom's raw integer `1` in the synthetic fixture.
   - `starpilot/controls/lib/starpilot_following.py`: retained C6-12-derived untracked-vision coast/timer behavior and adopted Dom's newer `should_disable_far_lead_throttle` API with vehicle-specific headway-floor helper. For non-GM vehicles (including Honda), this helper defaults to the prior `1.75` floor. The **semantic safety of the merged following policy is not fully replay-verified**.
3. **Quarantined 95 changed generated artifacts** (Panda bootstubs/firmware images, compiled Params, native libraries): restored their C7-F8 versions in the isolated tree rather than blindly adopting Dom's generated binaries. The resulting binaries are retained legacy products, not source-built release results and may not match refreshed source. Do not execute them on the device.
4. Verified there are no remaining unresolved Git conflicts and no staged binary changes. Scanned **124 changed Python files** for syntactic validity; all parsed successfully.

## Bounded exploratory x86 tests

An **eight-file** regression was executed in an isolated x86 mirror refreshed with Dom Python/source text while retaining old F5 native x86 binaries solely to allow test collection. **This is not a full source-coherent native build.**

| Selected test file | Outcome |
|---|---|
| `test_starpilot_acceleration.py` | 19 pass |
| `test_curve_speed_controller.py` | 44 pass (C7 numerical patch preserved) |
| `test_lead_behavior.py` | 48 pass |
| `test_longitudinal_planner.py` | **TIMEOUT / many visible failures; no finalized JUnit count** |
| `test_latcontrol.py` | 277 pass / 3 fail: inherited Chevrolet Bolt, Hyundai Palisade, Genesis G70 |
| `test_personality_following_profiles.py` | 31 pass |
| `test_personality_longitudinal_profiles.py` | 15 pass |
| `test_niro_lead_follow.py` | 14 pass / **12 fail** |
| **Finalized JUnit records only** | **448 pass / 15 fail out of 463 cases; planner timed out separately** |

**New principal stopper:** the 12 Niro/lead-follow failures and many uncompleted longitudinal-planner assertions produce `AcadosOcpSolverCython.cost_set(): mismatching dimension for field "Zl" at stage 12 with dimension (0,0) (you have (4,0))`. Dom's new `e75470f2e8` longitudinal terminal slack/cost constraints are not compatible with the **old F5 x86 Acados solver binary**. This demonstrates a **source-versus-native dependency mismatch** in the exploratory environment, **not a confirmed defect in newly compiled Dom solver source**. It prohibits accepting the integration until a current-Dom source-consistent MPC solver and wrapper are regenerated, linked and exercised with realistic trajectories. Tests must not be made green by removing the terminal-stage constraints.

## MVL comparison and decision

Latest MVL superproject update is a **single commit**, `cb15c04e`, adding 21 persistent Honda lateral gain/shape/wire/ceiling `FLOAT` parameter names in the Params registry. It has no corresponding actuation/control changes in that commit; its `opendbc_repo` pinned SHA remains `cf46117420f283b3e38241c00d728a191aa9fccc`, unchanged since the previous assessment. These are **P2 future design items**, and **none was imported** into the Dom-refreshed C7 candidate. See `docs/c7/upstream_delta/MVL_Boston_Honda_New_Commit_2026-10-17.md`.

## Explicit HOLD gates before qualifying this refreshed source

- **Current-Dom native rebuild:** regenerate Cereal schema and lateral/longitudinal Acados solvers from the merged source, and rebuild all Python/Cython/Params, messaging, CAN/Panda-safety, locationd and EKF target components without stale binaries. Re-test exact ARM64 AGNOS 19.8.1 ABI/dependency closure.
- **Corrected full host regression:** rerun full 44-file+ Dom-added tests against source-matched native binaries, resolve 12 new terminal-MPC failures and characterize any other planner failures; preserve 3 other-brand calibration exceptions and 72 AOL skips until formally dispositioned.
- **Honda safety:** source-faithful replay of C6-12 following, SLC/CSC, roundabout curve targets, red-light and lead transitions, terminal MPC dynamics; measure actual Honda actuator/braking output where available. Existing F7 5,998-frame mathematical replay is evidence, not vehicle actuation proof.
- **Panda SPI protocol:** Dom's sequenced-write change requires exact host↔firmware version matching and active-CAN ownership/safety gates; no physical firmware or CAN operation is authorized by this source refresh.
- **Owner/independent review:** 39 historical G02 patch dispositions, 72 skipped tests, numerical acceptance, rollback and independent review after Codex Sol High availability. `interruptRateCan2` remains a deferred investigation, not a waived safety issue.

## Decision

**Publishable as experimental GitHub source-review branch only. Not ready for comma installation, Panda flashing, road use or release tagging.** Preserve the earlier working C6-12 and protected C7 unchanged; keep the C7-F8 assessment snapshot as a separate rollback/reference. The old Dom-34 source analysis remains relevant, now supplemented with actual merged-source conflicts and the MVL delta.

# R14 software-only research report — 28 November 2026

Scope: research checkout branch `c20-r14-r10native-r11replay-r12software-20261128`, starting at `17fdbaa4741ba62e5af69b448f6a20cc513efd08`. Code changes are confined to `tools/c20_accord11g_long_shadow/**`. Stable C19 is the clean, unchanged commit `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`. This campaign performs no vehicle, device, firmware, CAN, Panda, physical HIL or road work. Active Alpha Long and road deployment are **NO_GO**.

## R10: generated C solver on x86-64

The checked-in C19 `c_generated_code/main_long.c` invokes `long_acados_create_with_discretization`, sets synthetic zero initial state and six parameters, calls `long_acados_solve` once, prints the solution and SQP statistics, then frees the capsule. It is a generated solver example, not the C19 Python `LongitudinalMpc` or `LongitudinalPlanner`. The checked-in compiled C19 solver and bundled libraries are AArch64. The host is x86-64.

`native_host.py` rebuilt the 18 generated C files and five generated headers using cached x86-64 acados headers and four cached libraries. It uses GCC 13.3.0, `-O0 -std=c99`, bounded subprocess timeouts and output, and keeps all binary and logs in `/home/jdkd/C20_RESEARCH_EVIDENCE_R14_SOFTWARE_20261128/native_x86` (240 KiB). It never runs at import. The first direct execution failed with loader exit 127 because transitive `libqpOASES_e.so.3.1` was absent from the loader path. Setting `LD_LIBRARY_PATH` to the cached acados `lib` directory resolved that concrete blocker. The reproducible script then compiled and ran the example: build exit 0, run exit 0, `long_acados_solve(): SUCCESS!`, one solve, one SQP iteration. The receipt records generated C/header hashes, the cached header tree and library hashes, host/compiler, binary hash, full build command and log hashes. Receipt SHA-256: `07452c960a0fd47211d26a2b81bcc135cafbf794a3a136e17c3db709fcc60b4c`. The binary SHA-256 in that receipt is `2f9faacecb141cd63eacea58d37a9257a51dc4c42f04e4cc5ca57a05d5b5437f`.

`native_host verify` checks the supplied receipt digest against the actual evidence files, pinned clean C19 commit, generated sources, cached headers and libraries, x86 ELF, logs, positive cycle and iteration, and exact classification. Result: `LOCAL_EVIDENCE_CONSISTENT_UNAUTHENTICATED`. A self-reported receipt and digest do **not** prove independent custody or execution authenticity. The original AArch64 product binary was not executed. The Cython wrapper and full Python MPC/planner were not rebuilt or run; this host lacks the product Python dependency environment and authentic same-cycle serialized inputs and prior planner state. Thus `NATIVE_C19_PLANNER_REPLAY=NOT_DONE`. No acceleration or actuator output is used by C20.

## R11: sanitized temporal join

`telemetry_gate.py` consumes versioned manifest/capture JSON containing digests and source/receipt clocks for the seven C19 planner services, plus CP/planner/preference/drive-state digests. It rejects unknown and malformed fields, oversized files, bad capture digests, provenance substitutions, missing services, future or stale samples, broken `source ≤ receipt ≤ cycle`, nonmonotonic clocks, cross-service source skew, source gaps and cross-drive resets. Radar `mdMonoTime` must select an actually observed model frame from at most four frames within 150 ms, with matching lead digests. This follows the observed history association in C19 `long_mpc.py` at the sanitized clock-and-digest level. C19 also checks `timestampEof`, service valid/alive/frequency flags, `car.canValid`, radar errors, lead arrays and planner memory; those are absent from this sanitized contract, so full source equivalence remains unverified.

The two-cycle synthetic fixture passes as `SANITIZED_TEMPORAL_JOIN`, with one 50 ms source gap per service, no faults, and `NATIVE_C19_PLANNER_REPLAY=NOT_DONE`. The output includes deterministic min/p50/p90/p99/max age, receipt latency, source skew, gap and model-association lag summaries. A `CURRENT_UNVERIFIED` self-report never earns a passing quality state. R9 historical counts describe an older Candidate-1 route: 4,800 each of modelV2, radarState and longitudinalPlan, and 23,889 sendcan; these counts do not bind the current vehicle or supply exact planner replay inputs. Zero authenticated current-vehicle captures were admitted.

## R12: software fault assurance

The read-only audit state starts `START`, enters `OBSERVING` for clean synthetic cycles, and locks at `FAULT_LOCKED` on integrity, continuity, clock, stale, lead loss, reset or driver override faults. Per-cycle fault events make the transition reviewable. Unit tests cover prior observed model frame selection, positive local receipt consistency, source/binary/log/cycle substitution, override faults, plus earlier negative cases. The state machine has no vehicle transport or control path. This is software assurance of the audit behavior only.

## R13/14 decision

The integrated campaign gate checks the source audit, privacy scope, baseline C19 inventory and prebuilt receipt, 82 host tests, synthetic join, and the x86 native receipt. It reports `PENDING_HOST_COMMIT_AND_INDEPENDENT_REVIEW` for the **offline research archive candidate**. Source files are still uncommitted, and independent review is pending; no archive was created. `bundle.py` requires an exact clean committed SHA and archives source only. Native binaries and logs stay in the external evidence directory.

Every hardware or device gate A1–A5 and R6 is `EXCLUDED_BY_USER_FOR_SOFTWARE_CAMPAIGN` and `UNVERIFIED`; exclusion is not a pass or a safety waiver. Product build receipt, current-vehicle custody, complete planner input equivalence, independent native evidence authentication and independent review remain unverified. Active Alpha Long and road deployment remain **NO_GO** regardless of the software result.

## Checks performed

| Check | Result |
| --- | --- |
| Generated x86 C example | 1 successful synthetic solve; 1 SQP iteration; local evidence consistent, unauthenticated |
| Original C19 AArch64 prebuilt receipt | PASS; original binary not executed |
| C19 checkout | Clean, pinned commit unchanged |
| Sanitized temporal join | Two synthetic cycles pass; current capture unavailable |
| Host unit suite | 82 tests, 0 failures |
| Recursive source audit and archive privacy scan | PASS; 44 research files scanned at gate run |
| `git diff --check` | PASS |
| Independent review and committed archive | PENDING |

The command sequence and host handoff are in [R14 software release recipe](R14_SOFTWARE_RELEASE_RECIPE.md).

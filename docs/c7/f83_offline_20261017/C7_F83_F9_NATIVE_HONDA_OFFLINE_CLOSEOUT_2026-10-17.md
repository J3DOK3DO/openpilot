# C7 F8.3 / F9 No-Codex Native and Honda Offline Engineering Closeout

**Date:** 17 October 2026, Asia/Dubai
**Source HEAD:** 3643477dfb938c8933c383f2fbbda4c7dc1eccd7
**Dom refreshed baseline:** e997a36ac211cf71a0c03ab5b99c2e3d6385291d
**Verdict:** 13 fresh ARM64 native artifacts PASS at component level; source-built minimal x86 host application PASS; F9 Honda archival inputs prepared; deployment HOLD.

## Native integration evidence

- Rebuilt 9 ARM64 Cereal / Params / msgq / pose / EKF / safety / Cython artifacts and both Acados solvers with Python bindings: 13 fresh ARM64 shared outputs with GNU EH_FRAME and SHA-256 provenance.
- Network-disabled ARM64 QEMU passed same-process Params lifecycle, temporary fake IPC ring including 12-frame restart, safety state reset, EKF finite state, Rednose import, and four synthetic longitudinal MPC solves. A separate source-built lateral MPC 32-step synthetic solve returned status zero.
- Terminal MPC Zl cost update at the final longitudinal solver stage completed correctly. None of these synthetic checks proves physical driving safety.
- Host CAN parser regression: 53 tests plus 602 subtests passed.

## Full source host integration

- The isolated minimal x86 SCons application build completed successfully once the correct pinned cythonize executable was on PATH. It produced host Cereal, Params, IPC, model support, pandad, Panda firmware build products and logger artifacts. No firmware was flashed.
- SCons retained checked-in model and MPC outputs; to make host MPC solver tests source consistent, both x86 solver DSOs and bindings were rebuilt from Dom source and replaced only in the disposable host checkout.
- All 44 test files were SHA-identical to the current isolated C7 commit. Full host result: 3,726 cases, 3,645 passed, 9 failed, 72 skipped, 0 errors.
- The 19 former Hyundai failures were resolved with a synthetic test fixture-only change, not driving-control code.

| Current host test status | Count |
|---|---:|
| Passed | 3,645 |
| Failed | 9 |
| Skipped | 72 |
| Errors | 0 |
| Total | 3,726 |

Remaining failures: six Ford Mach-E stopping assertions and three non-Honda lateral calibration assertions (Chevrolet Bolt, Hyundai Palisade, Genesis G70). They remain owner-review items; none is waived.

## Historical Honda F9 input preparation

Cohort A: 5,998 historical model frames from F7. 5,993 complete model/control/radar/plan joins, but NO active longitudinal requested acceleration; cannot prove braking.
Cohort B: screened 24 C6-12 rlog segments, of which 11 have active longitudinal intervals. Selected five active segments. 5,996 / 6,000 model timestamps joined with preceding car/control/plan/radar/StarPilot signals, at most 250 ms age.

| Historical active frame category (overlap permitted) | Frames |
|---|---:|
| Longitudinal active | 4,564 |
| Negative acceleration request | 1,060 |
| Active red-light indication | 386 |
| Active forced-stop request | 376 |
| Active radar lead | 1423 |
| Active follow/tracking lead | 1,199 |
| Active speed below 5 m/s | 110 |
| Active speed below 2 m/s | 55 |

These archives also contain 137,759 logged outgoing sendcan frames and 1,374,866 logged incoming CAN frames. Outgoing sendcan messages do not demonstrate physical actuator response or Panda acceptance.
Recorded carControl acceleration is a requested command; carState aEgo is a filtered acceleration estimate. These are HISTORICAL C6-12 signals, NOT outputs from the new C7 Dom controller.
The C7 numeric CSC implementation is source-identical to the F7 numerical replay, but the Dom lead/follow and MPC semantics have changed and have not been dynamically replayed with exact restored Params/toggles.

## Prepared F9 scenarios and required next gates

| Scenario | Evidence prepared | Next evidence required |
|---|---|---|
| Red-light / stopped light | 386 active red-light, 376 forced-stop frames | Time-accurate C7 full state replay, hold/creep and requested braking parity |
| Lead-follow | 1,423 active radar-lead frames | C6-12/C7 same-input gap, cut-in, lead-loss, throttle arbitration and bounded jerk comparison |
| Low-speed stop | 55 active below 2 m/s frames | Larger stopped/creep sample plus controller state and physical response; no tuning approval yet |
| Curve speed | Original 5,998 F7 ordered model frames | CurvatureData, modes, weather, actual activation and road radius reconstruction |
| Honda CAN control | 137,759 historical sendcan frames | C7 simulated ACC/steering CAN byte parity under correct Panda/safetyParam state, NO live output |
| Native service start/recovery | 13 ARM64 artifacts + minimal host app | Full AGNOS ARM64 process graph, dependent binaries, manager lifecycle and fault tests |

## Outstanding release blockers

- The AGNOS 19.8.1 ARM64 complete application and real service startup/recovery graph was not built and tested as a whole.
- Minimal host SCons build retained checked-in model artifacts; two MPC solvers required explicit source-built replacement in the disposable host test checkout.
- Synthetic MPC smoke and isolated native interop do not prove representative Honda vehicle motion or brake response.
- Six Ford Mach-E stop and three non-Honda lateral-calibration tests remain failed; 72 fleet AOL skips and 39 historical patch dispositions remain unapproved.
- C7 Dom longitudinal/following/SLC/CSC policies have not been recomputed with complete reconstructed Honda state and compared command by command.
- Logged sendcan frames are historical outgoing requests, not verified Panda delivery or hydraulic brake feedback.
- F7 curve segments had zero active longitudinal output; the active cohort has only 55 aligned under-2-m/s frames.
- Persisted CurvatureData, mode toggles, exact calibration, road friction and production Panda safety ABI are not reconstructed.
- Independent safety review, physical Panda checks, reversible parked qualification, release approval and on-road safety validation are not complete.

## Evidence and preservation

Machine-verified local evidence: /mnt/commadrive/c7-dom-f81-development-20261017/results/F83_F9_FINAL_MACHINE_VERIFIED.json
Private working logs and raw historic CAN/vehicle traces stay on the authorized Ubuntu machine, not in the GitHub report.
Protected C6-12 (7b4db9a260), protected C7 (48bd4c1d88) and published Dom-refreshed review (e997a36ac2) remain clean and unchanged.
Only an isolated Hyundai synthetic test-fixture source change was committed; no MVL source feature port, vehicle code changes, firmware flashing or comma deployment.

**Final C7 release verdict: HOLD / NO-GO. Offline engineering may continue without Codex; independent safety review and separate physical qualification remain required.**

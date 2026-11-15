# Honda Accord 11G C8.2 independent LKAS — offline-only engineering candidate

**STATUS: UNVERIFIED — DO NOT INSTALL, ENABLE OR USE ON ROADS.**
**Base:** C8.1 `9d2da330f6539beb5afb67867b28491526c0e1bd`.
**Target:** 2024/2025 US-spec Honda Accord 11G Hybrid, Bosch-C CAN-FD, stock Honda ACC.
**Scope:** independent LKAS/AOL intent and stationary/non-driving-gear safety boundaries. No custom longitudinal, Panda permissions, CAN transmit, firmware, steering tuning or GUI changes.

## Grounded prior evidence
- C8.1 real route `00000010--d33303548e` (Nov 14, 2026) observed HONDA_ACCORD_11G, Hybrid flags 2180, safety `hondaBosch/80`, `alternativeExperience=32`.
- Installed settings at evidence collection: `AlwaysOnLateral=1`, `LKASButtonControl=3` (Pause steering, **not Toggle AOL**), short and long CANCEL actions 0; VeryLongCancel 8, unrecognized by C8.1 AOL parser.
- Logged physical LKAS presses toggled `pauseLateral`, and CANCEL withdrew ordinary steering while independent `allowedLatch` was not proved armed. No evidence of a persistent Panda refusal of a valid requested lateral axis.
- A later Claude parked-test review found that LKAS=9 could arm while in Park and resume in D without a fresh gesture; only `controlsd` vetoes steering while stopped in D. Panda allows lateral torque at standstill when properly granted. An additional Panda token persistence issue also remains.
- Prior local evidence exists in `evidence/C8_2_INDEPENDENT_LATERAL_20261114/` on the owner's Ubuntu workstation, including `independent_review_20261114/parked_test/PARKED_TEST_PROCEDURE.md`. These files were **not available for direct reinspection** when the remote Windows and Ubuntu connections were offline.

## What this separate branch implements
1. **Accord-11G-specific non-driving gear withdrawal:** In HondaStockCardIntent, an independent AOL latch cannot persist from Park, Neutral, Reverse or Unknown into Drive. Any subsequent rearm requires release/neutral and a fresh physical press. Other Honda profiles' existing reverse-resume policy is preserved.
2. **Second software standstill gate:** In selfdrived, Honda Accord 11G AOL lateral requests are independently inhibited when `CS.standstill`, `abs(vEgo)<=max(minSteerSpeed,0.3)`, or speed inputs are malformed. The existing `controlsd` command veto remains unchanged. **This is not independent sensor redundancy**: both gates may consume related CarState data.
3. **Focused tests:** `test_accord11g_c82_lkas_hardening.py` covers Park/Neutral/Reverse/Unknown stale arms, fresh press after transition, other-Honda preservation, zero/low-speed and malformed values. They must run in the real repository Python environment.

## Mandatory missing gates (not optional tests)
- Restore authorized Ubuntu remote access (currently both Remote Desktop Commander host devices offline); do not change the Comma until reconnected, in PARK with ignition off.
- Run the new tests plus existing `opendbc_repo/opendbc/car/honda/tests/test_stock_aol.py`, Honda 11G current caller/axis lifecycle tests on a separated host checkout. Test real `selfdrived` state and `controlsd` command decisions, not only a pure helper.
- Independently inspect both new host guards and check they never suppress intended stock Honda ACC or AEB.
- Validate at least: LKAS=9 Park press does not produce a pending latch; entering D does not authorize lateral without fresh gesture; stationary D denies both request and command; short CANCEL retains lateral **only** after an independently armed latch and a native current grant; MAIN off, critical fault, stale heartbeat and native denial revoke steering.
- Investigate and resolve remaining **Panda token persistence** and unexpected post-fault/reverse reactivation hazards. Do not loosen Panda or suppress controlsMismatch/CAN2 faults.
- Verify Comma build and prebuilt receipt requirements only if a future release is authorized. This branch deliberately has **no build receipt update** and is **not GUI Fast Update installable**.

## Test plan by priority
P0: lint/py_compile and 11G targeted tests. P0: Honda stock-AOL tests including other-Honda behavior. P0: native Honda 11G lifecycle, Panda safety and independent-lateral current-caller tests on isolated environment. P1: recorded qlog/rlog regression from Nov 14 (no videos), including CANCEL at 212.35 s and 994.98 s, LKAS pause at 79.84 s and 241.88 s; compare to existing release's behavior. P2: independent review + reviewed parked, *non-actuating* observation. Do not execute Option A (arm while in D, stopped) solely on the basis of simulation, because the previous safety review found a single-command guard.

## Release policy
- This branch is **engineering-only**, NOT a vehicle release. Never use it to install onto a car until the required tests, independent approval, receipt, fallback/rollback and device acceptance have passed.
- The installed Comma should remain on `accord11g-dom7-c8-1-gui-release-20261113` SHA `9d2da330f`, or be restored to validated baseline for normal driving.
- All future vehicle tests must be separately authorized and follow a documented independent safety qualification plan. No public road trials of the experimental steering code.

## Known uncertainties
- The actual Claude `PARKED_TEST_PROCEDURE.md` and watcher have not been inspected during this takeover because the host is offline.
- No native or vehicle test has run against this candidate.
- Two software gates are better than one but are not a substitute for Panda/safety-level proof.
- The candidate intentionally does **not** implement a change in CANCEL semantics or auto-enable ACC; those need their own separately reviewed qualification.

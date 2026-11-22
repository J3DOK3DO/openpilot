# C17 — final release decision, C16 deferred

**Decision: SOURCE-ONLY PRERELEASE GO; INSTALLABLE PRODUCT NO-GO; VEHICLE / PUBLIC ROAD NO-GO.**

Date: 2026-11-22, UAE. Honda Accord 11G Hybrid / Bosch-C CAN-FD / Comma 4, retaining original stock Honda ACC.

## Decision authority and scope
This is an **offline engineering release decision** using C11–C15 hash-linked native evidence and an independent scoped review of the new C15/C17 report. It is **not** approval by an independent vehicle functional-safety engineer or a device/vehicle safety certificate.

C15 is closed only for **offline provenance/evidence reconciliation**, not full production readiness. C16 physical tests are intentionally **DEFERRED AT USER REQUEST, NOT WAIVED OR PASSED**. Because these are mandatory for operational approval, C17 rejects an installable or road-usable build.

## Reusable verified evidence
- Genuine ARM64 full product build passed at exact **built control source** `586da6b91ffb43e2a1e114072104b694d3c8a2b3`; C15 and C17 add tools/documentation only.
- Previously passed 190/190 focused Honda ARM64 regressions; 152/152 verified AArch64 ELF; six selected AGNOS loader checks.
- Five cached QCOM inputs had valid source/hash contract; NOT a producer GPU/target inference proof.
- C14 pinned-MVL tune comparison passed; no new steering, acceleration or braking tuning copied or changed.
- Seven new C15 offline auditor tests passed, and original C11 build/test evidence SHA-256 matched.

## Critical open gates that block installation/drive
1. **Actual Qualcomm target inference** and model/warp output qualification on the intended device.
2. **An authentic exact-commit production build receipt**. `tools/ci/check_prebuilt_receipt.py` currently exits 1. Never forge it, copy a receipt from another source revision, or disable checks.
3. **Actual Panda/AGNOS firmware build and installed identity**, paired with final reviewed source.
4. **Independent complete-source functional-safety review**, including Panda native authority, Honda Bosch 80/81 state machine, hardware watchdogs, EPS limits, LKAS and CANCEL.
5. **C16 physical, stationary diagnostic tests** of CAN2 OBD-mux error storm and `controlsMismatch`, native authorization, fail-closed behavior and recovery.
6. **Real hardware rollback and emergency stop qualification.** Prior owner approval for manual reinstall replaces only the proposed full-image rehearsal; it does not establish operational recovery or safety.

## Exact release-type matrix

| Output | C17 decision | Meaning |
|---|---|---|
| Reviewable Git branch and source-only prerelease | **GO** | Documentation/tools plus inherited code; no installation approval |
| Human- or device-installable production image | **NO-GO** | Do not offer a quick-install link, installer or modified firmware |
| Parked non-actuating vehicle diagnostic program | **NOT EXECUTED** | Requires separate physical review/approval |
| Steering, ACC and brake testing/road use | **NO-GO** | No controls engagement or on-road custom actuation |
| New MVL Bosch-C custom tuning/alpha-long | **NOT IN THIS RELEASE** | Investigate separately; stock ACC remains owner |

## Review caveat
A scoped Codex desk review, if recorded as PASS_SCOPED, only establishes this documentation and auditor's internal consistency. It does not satisfy gate 4 above. This decision is robust to a skipped C16 **because it does not claim operational permission**.

## Rollback/version identifiers
Original Dom baseline `ab468b8ecd1baa3e63fb5436b69253213d892b5d`; prior C8.1 GUI release `9d2da330f6539beb5afb67867b28491526c0e1bd`; published C14 branch `49059309672f3044f6ef4b9ca995e9c2eb146127`. These are source history labels, **not** fresh checks of what is installed on the disconnected Comma.

**C17 final verdict:** `SOURCE_ONLY_RELEASE_GO / INSTALL_NO_GO / DRIVE_NO_GO`.

# Honda Accord 11G C8.2 — Campaign 4B combined offline engineering report

**Date:** 2026-11-15 UAE. **Verdict:** PASS_WITH_BLOCKERS for source-only offline engineering; **PHASE4 INDEPENDENT ENGINEERING APPROVAL PENDING; PHASE5 PHYSICAL QUALIFICATION NOT PERFORMED; DEVICE_INSTALL_NO_GO; ROAD_USE_NO_GO.**

## 1. Provenance, scope and execution

Working branch: `accord11g-dom7-c8-2-c4b-offline-20261115`, started clean from C8.2 Phase 2–3 `e54e9cc8c6e8dd7338618e1d22622fb97c6856dc` and applied exactly the previously tested C4 native correction. The carried 3-file patch matches the preserved evidence diff byte-for-byte at SHA-256 `67ff8af9a2fdddf7c5ebff29d01a6ded486d282d8ff3e0a0596d08487caeab13`. Final checkpoint identity is recorded in Git after report preparation, not a device identity.

Owner authorized a combined Codex-led offline campaign, a separate reviewer and omission of redundant/nonrelevant tests. **Codex started and completed 33 native tests, then hit its usage limit at 12:49 UAE** (tool exit 1; `C82_CODEX_C4B_20261115_TRACE.log`). The remaining bounded tests, source comparison and documentation were performed through direct host tools; no later Codex completion is claimed. A Windows OpenCode/Ollama local reviewer was attempted, but had not delivered an independent review at this checkpoint. A previous GPT-6 separate source challenge is retained as AI reviewer evidence; it is not human safety certification.

**No new device connections, CAN transmission, Panda firmware updates, GUI settings, branch publication or installation were performed.** Installed C8.1 is presumed unchanged from its last verified `9d2da330f6539beb5afb67867b28491526c0e1bd`; Comma is currently disconnected, so that identity was **not reconfirmed live**. Original Dom fallback `ab468b8ecd1baa3e63fb5436b69253213d892b5d` is retained.

## 2. Closed offline source defects (not hardware claims)

- **Phase 2–3 — voluntary host withdrawal:** In C8.2 `honda_stock_aol.h:89-100`, an acknowledged zero host request retires the previous Accord 11G Panda token and session. Re-request without fresh physical authorization cannot regain lateral permission; the initial pandad zero-mask handshake is preserved before a physical grant is acknowledged. This was separately red/green tested in Phase 2–3.
- **Campaign 4 — Park-to-Drive pending token:** Original `e54e9cc8` accepted a physical LKAS edge in Park, retained a pending token and later admitted a nonzero steering TX after Drive without a new edge. The exact prepatch native negative test showed **2 failed, 3 passed**; the C4 candidate fixed this. Production `honda_stock_aol.h:190-241` now requires validated Drive for Accord11G MAIN/LKAS token creation and clears token/session when leaving Drive. Restriction is scoped to HondaBosch params **80/81**, with legacy policy unchanged for other Honda profiles. Five direct negative cases passed.
- **Host layer:** Previously merged C8.2 host code clears independent latch outside Drive and at standstill, prevents unexpected gear-change rearm and preserves ordinary stock ACC-linked path. Native and host standstill checks are **not independent sensor redundancy**.

## 3. Tests and skipped work — exact provenance

| Test/evidence | Result | Status in Campaign 4B |
|---|---|---|
| `pytest -q opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py` | **33 PASSED** | Reran successfully twice on Ubuntu host: initial Codex run and direct host rerun; `evidence/C8_2_C4B_OFFLINE_20261115/01_native_honda_aol.log` |
| `pytest -q tools/diagnostics/accord11g_20261113/c7_plus/test_can2_evidence.py` | **1 PASSED** | Direct host run; sanitized source evidence only, not physical fault diagnosis |
| `py_compile` of modified Honda safety Python test | **PASSED** | Direct host run |
| `git diff --check` | **PASSED** | Direct host run |
| Exact C4 prepatch frozen `e54` negative cases | **2 FAILED, 3 PASSED, 28 DESELECTED** | Historical proof of defect, not rerun |
| C4 candidate negative cases | **5 PASSED, 28 DESELECTED** | Historical same source patch, **SHA-256-verified equivalent**, not rerun separately |
| Honda Card/Controls/selfdrived/C++ native lifecycle | **28 PASSED** | Prior C4 execution with **same native patch**, reused as accepted evidence; no needless rerun |
| Affected broader Honda safety | **253 PASSED, 40 SKIPPED, 204 DESELECTED** | Prior C4 execution with **same native patch**, reused as accepted evidence |
| Earlier C8.2 stock/host Honda suites | **365 PASSED** | Prior source/lifecycle baseline; not repeated because host code unchanged |
| Jetlink event-fault cases | **2 FAILED, 5 PASSED** | Both failures reproduced in untouched baseline; not fixed; not rerun as unrelated |
| GUI/MVL tuning/Alpha Long/5,544-case general host suite/full QCOM build | **NOT RUN** | Irrelevant to scoped offline Panda token diff or require separate native release gate |
| Physical standstill, CAN2, EPS, Comma firmware and public-road qualification | **NOT RUN / BLOCKED** | Comma disconnected; cannot infer from simulation |

Test environment used Ubuntu host native `libsafety`; prior real lifecycle test used an x86 Card/Controls/Panda bridge. A cached older x86 acados artifact was used as an **import dependency**, not proof of numerical MPC, Qualcomm or final Panda build validity.

## 4. Remaining safety blockers

**P0 hardware / independent approval:** No independently qualified Panda speed/standstill guard; host dual gates share CarState, and the inspected Panda TX gate allows a permitted steering frame in Drive without separate stationary zero-torque proof. CAN2 `interruptRateCan2` electrical/startup cause is unresolved. Historic `controlsMismatch` and EPS/CANCEL real transition timing are not physically qualified. Firmware and vehicle identity for a future exact C8.2 installation cannot be verified while Comma is disconnected. Independent reviewer/model or professional safety assessor approval of **this final C4B source identity** is pending.

**P1 behavioral:** Independent LKAS after a full stop requires fresh authorization. A short CANCEL may retain lateral only with an independently armed, fresh and native-approved latch. ACC engagement alone must not silently create permission to remain steering after CANCEL. Driver HUD indication and physical button experience need review.

**P1 native lifecycle:** Initial pending grant/host restart timing and simultaneous zero-mask/physical gesture must be evaluated against real pandad timing, and source-level model tests must not be treated as standalone hardware redundancy.

## 5. Release implications

C8.1 `GUI_FAST_UPDATE_READY` did not establish road qualification. Its release required no native rebuild because no native inputs changed. The C8.2 native header **has changed**: before any installable release, native firmware/build provenance, exact protected inventory receipts and physical safety gates are mandatory. Do not reuse Dom/C8.1 `prebuilt.json` blindly.

C8.1 owner acceptance of manual reinstall and waiver of full-image physical restoration rehearsal applies to offline rollback planning only. It does **not** waive hardware safety or firmware validation. See `C4B_C81_ACCEPTANCE_CROSSWALK.md`.

## 6. Next gate

Supply the frozen C4B source and its exact patch + tests to a genuinely independent reviewer, and close any identified source defects with targeted reruns. Phase 5 may begin with **non-actuating read-only inventory preparation** only after separate hardware access and review decisions; do not execute Claude's stationary gear-D Option A. Full device/road safety certification requires later exact-firmware and physical test evidence.

**Evidence:** `evidence/C8_2_C4B_OFFLINE_20261115/` fresh test logs; `evidence/C8_2_C4_INDEPENDENT_REVIEW_20261115/` C4 patch and prior red/green logs; `C4_CODEX_CHALLENGE_RESPONSE.md`; `C4B_CAN2_CONTROLS_MISMATCH_TRIAGE.md`; `C4B_GATE_MATRIX.md`.

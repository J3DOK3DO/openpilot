# C8.2 Campaigns 5+6 combined Codex engineering report

2026-11-15 Asia/Dubai. Author: implementing Codex, **not an independent reviewer**. Scope: offline source correction, tests, fault triage and a nonactuating reviewer packet. **Source-only PASS with blockers; Phase 5 unexecuted; vehicle/install/actuation NO-GO.** No Comma/Panda contact, network, CAN TX, flash, OBD, ignition, gear, steering, installed setting, push or merge occurred.

## Lineage and result

The only writable source checkout began clean on branch `accord11g-dom7-c8-2-c5c6-offline-20261115` at `2fe2061228b2b55ddbe1bff8ccdf394194555f81`, parent `e54e9cc8c6e8dd7338618e1d22622fb97c6856dc`. Historical C8.1 installed identity `9d2da330f6539beb5afb67867b28491526c0e1bd`; Dom rollback `ab468b8ecd1baa3e63fb5436b69253213d892b5d`. These are historical identities, not refreshed on device. The final commit is supplied in the close message and by `git rev-parse HEAD` in this source checkout.

**New source finding 1:** The frozen C4B native policy retired an acknowledged Honda 80/81 token on a host zero mask only when `SESSION` was set. After a previous host request and heartbeat loss, a new physical LKAS edge could make `TOKEN|PENDING` while `SESSION` was clear. A replacement pandad zero handshake left that pending token; a later nonzero host request and heartbeat accepted a nonzero steering TX without another physical edge. The new test against the exact frozen C4B header failed with actual `(flags, request, permission, TX)=(578,1,1,True)` versus required `(576,1,0,False)` ([test_honda_stock_aol.py:182](../../opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py#L182); red log SHA-256 `2aa1d705c0edc192e2823c06c2e95993f303479b1042d9e7d3cbdd6cd0704c24`). This is a source-level host/native handover defect, **not observed vehicle torque**.

**New source finding 2:** Frozen C4B retired the token on non-Drive, but retained `aol_host_axis_mask`. After gear returned to Drive, a new physical LKAS edge accepted nonzero steering TX using the pre-transition host request, with no fresh post-Drive host request. The direct native test failed on the exact frozen C4B header: actual `(permission, TX)=(1,True)` versus required `(0,False)` ([test_honda_stock_aol.py:206](../../opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py#L206); red log SHA-256 `bc26e30ea5c3f375da9f5b65b85132ce82f2d40b832acf601490707d0746e86f`). This also is source-only evidence, not vehicle behavior.

**Minimal 80/81 fixes:** A zero mask now retires an acknowledged **or pending** token after any prior host request has been seen ([honda_stock_aol.h:89](../../opendbc_repo/opendbc/safety/modes/honda_stock_aol.h#L89)). A first startup zero, before any host request, still preserves a fresh pending grant. On validated non-Drive gear and first Drive re-entry, Panda now clears the host mask ([honda_stock_aol.h:228](../../opendbc_repo/opendbc/safety/modes/honda_stock_aol.h#L228)), so a later physical edge needs a post-entry host request. Both are gated by the Accord11G flag, set only for HondaBosch 80/81 ([honda_stock_aol.h:291](../../opendbc_repo/opendbc/safety/modes/honda_stock_aol.h#L291)). Generic Honda TX, ACC/AEB, EPS, interrupt/watchdog, CAN2 mux/bitrate, controlsMismatch, and numerical steering authority were not changed. Header SHA-256: frozen C4B `7b8d6b380cdd7d6191667fd1d420f3214a0b3d5b622dc249f0c8f9b67cffc244` → final `44decb9c4a51953db8434dc54027559aadbdcb7194ae784df56f61de05462882`. Complete new native/test diff SHA-256 `33c02c90206dda4aca7df7dc7f575e44f6a8e43cffedc700430c35673ebf12bd`; see [patch](C6_NATIVE_SOURCE_DIFF.patch).

## Tests and exact limits

Environment: source `/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C8_2_INDEPENDENT_LATERAL_20261114/tools/env.sh`; prepend this checkout's `opendbc_repo` and root to `PYTHONPATH`; use `python3`. Bounded logs are under `/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C8_2_C5C6_OFFLINE_20261115/` and hashes/commands are in [C6 manifest](C6_SOURCE_ONLY_RELEASE_READINESS.md).

| Check | Status | Provenance |
|---|---|---|
| New reconnect negative test, frozen C4B production header | **FRESH RED: 1 failed, 33 deselected** | Actual accepted nonzero native TX before fix. Test-only code added first; production header unchanged during red run. |
| Gear-return stale-mask negative test, frozen C4B production header | **FRESH RED: 1 failed, 34 deselected** | Actual accepted nonzero native TX before second fix. |
| Entire affected Honda native fixture | **FRESH PASS: 35 passed** | After both production fixes, host-built `libsafety.so` with actual Honda TX hook. |
| Card/SelfdriveD/Controls/Panda C++ lifecycle | **FRESH PASS: 28 passed** | Final header copied byte-for-byte into `/tmp/c82_phase23_20261115/x86_mirror`; production C++ pandad bridge. Older cached x86 acados is import-only, not MPC qualification. |
| C8.1 bus-0/HOLD/fault policy selected regression | **FRESH PASS: 8 passed, 48 deselected** | Production transport simulator; no live CAN. |
| Ruff on changed Python, `python3 -m py_compile`, `git diff --check` | **FRESH PASS** | Local checks. |
| Earlier C4B direct native 33/33 and parser 1/1 | **REUSED PASS** | Frozen exact C4B evidence; no new claim that these separately qualify changed C5 header. |
| Earlier same-policy cross-Honda selection | **REUSED: 253 passed, 40 skipped, 204 deselected** | Shared Honda policy unchanged; skips remain skips. Earlier host baseline 365 passed is historical. |
| Earlier C8.1 strict discovery 118 passed | **REUSED PASS** | C5/C6 changed no discovery source; selected 8 were fresh. |
| Jetlink event suite candidate and original | **KNOWN BASELINE: 2 failed, 5 passed** | Not rerun; not reclassified as green. |

First attempted host command used unavailable `python` (exit 127); corrected to `python3`. First x86 runner invocation lacked executable permission (exit 126); corrected to `bash run_x86.sh`. Neither was a test result. The earlier C4 first broad lifecycle invocation had 7 failed/28 passed due imported-class collection environment; its explicit intended 28-node selection passed and the same explicit nodes were freshly rerun here. No broad GUI/MVL/5k suite was run solely to increase counts.

## Issue-by-issue closure matrix

| Issue / severity | Disposition | Evidence and remaining question |
|---|---|---|
| Park-to-Drive token replay, safety critical | **Proven fixed offline** in C4B, retained in C5 | e54 native red and C4B/fresh 35 native green; actual vehicle behavior remains physical-only. |
| Replacement zero handshake after prior request and pending physical grant, safety critical | **Proven source defect fixed offline in C5** | Exact frozen C4B red, final 35/35 native green and 28/28 lifecycle green. Native build/device timing and independent review pending. |
| Gear departure/return reuses pre-transition host mask after new physical grant, safety critical | **Proven source defect fixed offline in C5** | Exact frozen C4B red, final 35/35 native green. Physical timing and independent review pending. |
| MAIN OFF, short CANCEL, EPS 2/6, invalid RX, timeout, gear departure, 16/17 scope, safety critical | **Supported test only** | Native tests and source matrix; physical timing/driver outcome unverified. |
| Full stop/standstill independent lateral, safety critical | **Physically unknown; NO-GO** | Host CarState guards and simulation only. Panda has no separately verified standstill speed veto or numerical torque bound ([stock_intent.py:9](../../openpilot/starpilot/car/honda/stock_intent.py#L9), [honda.h:310](../../opendbc_repo/opendbc/safety/modes/honda.h#L310)). |
| CAN2 interrupt storm and actual controlsMismatch root cause, safety critical | **Physically unknown; NO-GO** | Historical ELM327/0 IRQ ~17,862/s and errors ~35K precede hondaBosch/80; later route different. Strict bus-0/HOLD source regression passed; no hardware diagnosis. |
| Exact native Panda/Qualcomm build identity and firmware qualification, safety critical | **Pending; NO-GO** | C8.2 changes Panda C header. No target-native artifact, receipt or installed build proof. |
| Actual EPS response, independent physical CANCEL, HUD/mode cues, safety critical | **Pending physical review; NO-GO** | Offline tests cannot establish driver/vehicle response. |
| Independent exact-final-candidate safety reviewer, safety critical | **Pending** | Existing partial Qwen C4B text has `state: starting`, misquotes LKAS code, and is not final-candidate approval. Windows reviewer will run separately. |
| C8.1 full-image restoration rehearsal and optional settings preservation, logistics | **Owner previously waived; valid for this offline campaign** | Manual reinstall accepted, settings reset optional in [crosswalk](C4B_C81_ACCEPTANCE_CROSSWALK.md). This is not a safety or native-build waiver. |
| GUI Fast Update readiness, cosmetic/release logistics | **Historical only; no C8.2 install approval** | C8.1 changed `prebuilt.json` only; C8.2 changes native source, so its exemption is inapplicable. |
| Jetlink event tests, non-green baseline | **Open** | Candidate and original both 2 failed/5 passed earlier; no silent PASS. |

## Deliverables and next gate

Read [native gap matrix](C5_NATIVE_LIFECYCLE_GAP_MATRIX.md), [CAN2 evidence](C5_CAN2_FAULT_EVIDENCE_AND_ACTIONS.md), [source-only readiness](C6_SOURCE_ONLY_RELEASE_READINESS.md), [nonactuating Phase 5 draft](C6_PHASE5_NONACTUATING_ACCEPTANCE.md), and [independent handoff](C6_INDEPENDENT_REVIEW_HANDOFF.md). The next gate is independent review of this exact final source plus authentic target-native build/identity and separately authorized passive physical fault/standstill qualification. No Phase 5 completion, release, install or road claim is made.

**Final local commit SHA:** supplied in the final handoff message; the committed source tree itself is authoritative via `git rev-parse HEAD`. A commit cannot contain its own SHA without changing that SHA. No push or release tag.

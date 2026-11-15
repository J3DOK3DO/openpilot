# C8.2 Phase 2+3 combined offline engineering closure — 2026-11-15 UAE

**Verdict: OFFLINE_ONLY / DEVICE_INSTALL_NO_GO.** The focused host and native safety defect is repaired and bounded x86 tests pass. This is a local engineering checkpoint, not vehicle safety qualification, road certification, installation authority, or a release receipt. No physical CAN TX, device change, Panda flash, push, or merge occurred.

## Provenance and scope

- Only writable tree: `work_c82_phase23_20261115`, branch `accord11g-dom7-c8-2-phase23-safety-offline-20261115`. Starting HEAD `f004037b9117f3634ae657a179afdc570c10a892` had six uncommitted native/test files and this placeholder report. Parent C8.2 checkpoint `176364628268aa35b80f18e724bba52f957cea18`. Installed C8.1 SHA at campaign start `9d2da330f6539beb5afb67867b28491526c0e1bd`; previous Dom rollback `ab468b8ecd1baa3e63fb5436b69253213d892b5d`. Device unchanged.
- Read the Phase 0+1 report, initial combined execution trace, and copied C8.1 route findings. Logs are under `/tmp/c82_phase23_20261115/`. The older baseline mirror `/tmp/c82_full_x86_20261115` is untouched. The campaign mirror `/tmp/c82_phase23_20261115/x86_mirror` uses locally built x86 msgq, VisionIPC, params, C++ pandad bridge, and native Honda safety. Its older cached x86 acados dependency permits imports only; MPC and longitudinal behavior are not numerically qualified. No device binary was built or installed.
- The earlier trace ended with exit 124 from its time budget while the final lifecycle run was active. The completed log records 28 passed; the trace exit is not counted as a test result.

## Root cause and native correction

Before this patch, `honda_stock_aol_host_request()` recorded a host request but left the physical token intact after explicit zero withdrawal. With heartbeat engaged and RX healthy, a later nonzero host request could reuse that old grant. The baseline `native_before.log` fails at the internal token assertion after zero, even though exported permission was zero at the withdrawal instant.

`opendbc_repo/opendbc/safety/modes/honda_stock_aol.h:89-101` now clears token, pending grant, neutral gesture flags and session after an acknowledged zero request. `HONDA_STOCK_ACCORD11G` is reset and set only for Bosch safety params **80/81** at lines 25, 83 and 276. A pending physical grant survives the initial pandad zero-request handshake but grants no output until a fresh post-gesture nonzero request. Existing freshness, heartbeat, relay, invalid RX, MAIN, EPS, gear and physical gesture checks remain active. `safety.h:65-76` still passes zero into the policy hook; `honda.h:310-318` retains the native steering TX gate and limits. No Panda bypass, stock ACC path, steering limit or longitudinal production code changed.

Final scope review also restricted `HONDA_STOCK_REQUEST_SEEN` updates to nonzero requests outside the Accord withdrawal branch, preserving the original zero-request behavior for other Honda variants. Both focused suites passed again after that correction.

The test-only `safety_test_honda_stock_token()` in `opendbc_repo/opendbc/safety/tests/libsafety/safety.c:108-112` exposes token state to the host test library, not firmware. `test_honda_stock_aol.py:280-341` checks 80/81 token retirement, zero permission, rejected nonzero steering TX, and rejection of a later host request without a new physical edge; it also checks MAIN, EPS and expiry. Other Honda variants retain their prior zero-request behavior. Baseline `native_before.log`: **1 failed, 26 deselected** at stale token; patch `native_after_focused.log`: **1 passed, 26 deselected**. This is before/after host-built native TX proof, not physical CAN transmission.

## Real-loop simulation

`openpilot/starpilot/aol/tests/test_honda_recovery_lifecycle.py:66-535` exercises real Card, `SelfdriveD`, Controls, controller CAN packing, native Panda Honda safety hooks and the C++ pandad lifecycle bridge across 145 ticks. It decodes produced steering frames and checks safety TX acceptance, token, request, permission, host latch and events. `honda_selfdrive_step.py:7-29` now passes an actual `pandaStates` message into `SelfdriveD`. The early `interruptRateCan2` and `safetyRxChecksInvalid` injections propagate through that service; `controlsMismatch`, withdrawal and steering output are asserted. This validates simulated host fault response, **not** the cause of the historical CAN2 fault.

New Accord cases in `test_honda_canfd_lifecycle.py:31-47` cover physical CANCEL with and without an independent latch, full stop, stationary LKAS and early fault withdrawal; existing Reverse/fresh LKAS cases remain. In the independent CANCEL case, stock cruise and Panda `controlsAllowed` are false while a fresh gesture-backed lateral token/request/permission persist and simulated steering TX is accepted. In no-latch and withdrawal cases, steering request/torque are zero or native TX rejects a stale frame.

| Check and evidence log | Result |
|---|---|
| Native before/after: `native_before.log`, `native_after_focused.log` | Baseline **1 failed**, patch **1 passed**; later steering TX rejected. |
| Native Honda safety: `native_honda_final.log` | **33 passed**. |
| Explicit negative token: `native_negative_first.log` | **2 passed, 26 deselected**. |
| Stock Honda plus C8.2: `x86_stock_honda_final.log` | **365 passed**. |
| Full Honda native lifecycle: `x86_honda_lifecycle_final.log` | **28 passed**, including added Accord cases. |
| Selected Honda route regressions: `x86_honda_route_regressions_final.log` | **72 passed**. |
| Ruff: `ruff_final.log`; closure compileall and diff check | Ruff **all checks passed**; closure reruns of Ruff, `python3 -m compileall -q` on the four changed Python files and `git diff --check` also passed. |
| Jetlink event faults: `x86_jetlink_fault_final.log` | **2 failed, 5 passed**. Untouched earlier C8.2 baseline `x86_jetlink_fault_baseline.log` has the same two failed cases: `comm-43` raises `AttributeError: 'Sources' object has no attribute 'services'`; `radar-0` expects event 0 but sees `[25, 100]`. These remain failures. |

The x86 wrapper only redirects process-local Params/home paths to `/tmp` and removes the optional swaglog IPC handler for sandbox execution. It does not inject permission or bypass native TX. The fixture uses synthetic CAN frames and a host-built safety library; it cannot establish ECU timing, EPS torque behavior, bus wiring or physical fault behavior.

At closure, the 33 native Honda tests and all 28 lifecycle tests were rerun successfully. The campaign mirror's production safety source, native test hook and three lifecycle/helper Python files match this worktree byte-for-byte; its standalone safety test file differs, so the 33-case native rerun used this worktree directly. No broad suite was repeated.

## Historical C8.1 evidence and remaining gates

Read-only copied C8.1 route review (`c81_route_review.log` and `POST_SSH_RECOVERY_LOG_FINDINGS.md`) found 1,475 synchronized native `requested=0/allowed=0` and 2,023 `1/1` messages, zero synchronized `1/0` refusals in selected rlog windows, 21 LKAS presses and four CANCEL presses. CarParams reported AE 32 and `hondaBosch/80` after bootstrap. LKAS action 3 produced pause transitions. These are **C8.1 selected-window observations**, not C8.2 hardware qualification. The C8.1 CANCEL withdrawal where the independent latch was already false does not refute the C8.2 simulated independent CANCEL case.

**Vehicle installation and actuation remain blocked.** The C8.1 CAN2/OBD interruption cause, real `controlsMismatch`, short CANCEL behavior on the vehicle, source freshness at device timing and EPS/gear behavior require independent review. Stationary Drive denial is shown by C8.2 host checks and lifecycle simulation; both host checks share CarState and are not independent sensing. Native Panda has no separately verified standstill speed veto. A full stop clears the independent latch, so motion alone does not rearm it; effects on driver expectations after ordinary ACC stops also need review.

Phase 4 requires an engineer independent of earlier C8.2 implementation/reviews to verify the exact 80/81 token/session state machine, real pandad ordering and heartbeat, physical gesture/CANCEL semantics, CAN2 fault path, standstill behavior, UI mode indication, rollback and vehicle safety criteria before any separately authorized parked or live procedure. This report authorizes no ignition, steering command, device install, firmware change, setting change or road test.

# C8.2 Campaign 4 — response to separate GPT-6 source challenge

2026-11-15 Asia/Dubai. **Verdict: BLOCKED for Phase 4 closure.** The bounded offline source defect is reproduced on frozen `e54e9cc8c6e8dd7338618e1d22622fb97c6856dc` and repaired in this worktree; targeted candidate tests pass. Hardware state, independent human engineering review and physical standstill/CAN2 evidence remain unknown. Per the C4 close rule, the source change is **uncommitted**, device install is **NO-GO**, and no approval or release receipt is implied. GPT-6 provided an AI source challenge, not a human safety certification. Qwen produced no result and is not counted as approval.

## Native finding and red/green proof

The exact e54 production Honda safety source was compiled into a host `libsafety.so` with only the test-only flag accessor added to the harness. The final five C4 tests were run against that isolated library (`/tmp/c82_c4_exact_e54_red_final.log`): **2 failed, 3 passed, 28 deselected**. At 1.010 s, valid MAIN/EPS/gear in Park, inactive heartbeat, initial zero host mask and a physical LKAS edge produced `(flags, request, permission, TX) = (6, 0, 0, False)`: `TOKEN|PENDING`, no session and TX rejected. At 1.020 s, heartbeat became engaged and Drive was received with the LKAS button held. A new lateral request, without a new physical edge, produced `(578, 1, 1, True)` on e54. Flags 578 are `TOKEN|SESSION|DRIVE`; the pending flag had been consumed. The test frame was a nonzero `STEERING_CONTROL` on the configured TX bus and was accepted by the real native Honda TX hook. This is an **offline source defect**, not observed vehicle torque. The separate departure test found e54 retained `TOKEN|SESSION` (66) after shifting out of Drive. The initial pre-edit run also failed the Park test (`/tmp/c82_c4_baseline_red.log`).

`honda_stock_aol.h:208-211` previously granted on an LKAS edge without Drive; `:235-240` updated gear but left the token intact. `:142-158` only denied permission while non-Drive, so Drive could expose the latent token. `honda.h:310-318` then accepted nonzero steering when lateral permission was true. The healthy host clears its latch in non-Drive (`openpilot/starpilot/car/honda/stock_intent.py:38-50,111-120`), but native validation must withstand an unexpected host request.

The candidate requires Drive at the physical MAIN and LKAS grant sites (`honda_stock_aol.h:190-214`) for the `HONDA_STOCK_ACCORD11G` profile and retires token, pending and session when a validated gear frame reports non-Drive (`:227-241`). The profile flag is set only for Bosch params 80/81 (`:263-280`). A blocked MAIN transition consumes its neutral state, and a held LKAS level cannot replay on entering Drive. Other Honda profiles retain their previous grant semantics. No generic Honda TX, ACC/AEB, numerical bounds, watchdog, `controlsMismatch` or fault restriction was changed.

The same five C4 tests on the candidate passed (`/tmp/c82_c4_focused_final.log`): **5 passed, 28 deselected**. For both params 80/81 and sampled Park, Reverse, Neutral and unknown 0x191 values 0/1/2/3/15, the pre-Drive state was `(0, 0, 0, False)` and the Drive-entry state was `(576, 1, 0, False)`: `SESSION|DRIVE`, request 1, permission 0, native TX rejected; token and pending were absent. A session bit alone does not grant steering. The test also verifies an existing Drive token is retired on departure, and a held button cannot rearm; a new neutral-to-LKAS edge in Drive grants again. The flag accessor in `safety.c:113-117` exists only in the host test library.

## Bounded timing and scoping results

The Drive startup test (`test_honda_stock_aol.py:155-180`) shows a valid LKAS edge with heartbeat inactive and a zero pandad handshake remains pending, with permission 0 and TX rejected. A fresh post-gesture request after heartbeat engages gives `TOKEN|SESSION|DRIVE`, request/permission 1/1 and TX accepted. A later acknowledged zero retires the token; a nonzero request alone cannot rearm. This preserves a healthy Drive startup path, while a physical press before a validated Drive frame now requires another eligible gesture or normal ACC engagement in Drive.

The ordering test (`:213-254`) covers zero before and after a fresh LKAS edge in the same simulated tick, a fresh edge in the adjacent tick, heartbeat loss and return, MAIN off/on, EPS temporary 2/6 and invalid RX. A zero after an acknowledged edge revokes it; only a new physical transition can restore permission. EPS 2/6 denies TX while present; recovery can restore a still-current grant, matching the pre-existing temporary EPS policy. Heartbeat loss and invalid RX deny permission and do not rearm from a subsequent nonzero mask. The freshness test (`:255-283`) accepts at exactly 300,000 µs and denies at 300,001 µs after a refreshed RX stream. Bosch 16/17 retain their previous non-Drive pending-token behavior, explicitly delimiting this Accord-only change. These tests control synthetic frame order and time; they do not establish real CAN/USB interleavings or physical EPS behavior.

The previously existing all-gear test (`:712-727`) now expects params 80/81 to remain denied after a non-Drive excursion until a fresh LKAS edge. This assertion changed because the explicit new safety rule retires the token on leaving Drive. Other profiles keep their original return-to-Drive expectation.

## Actual test and check disposition

| Selection / evidence | Result |
|---|---|
| Exact e54 isolated native C4 tests, `/tmp/c82_c4_exact_e54_red_final.log` | **FAIL: 2 failed, 3 passed, 28 deselected**; Park and gear-departure defects reproduced. |
| Candidate C4 tests, `/tmp/c82_c4_focused_final.log` | **PASS: 5 passed, 28 deselected**. |
| Candidate stock AOL native file, `/tmp/c82_c4_native_all_final.log` | **PASS: 33 passed**. |
| Candidate Honda recovery/CAN-FD lifecycle, `/tmp/c82_c4_lifecycle_selected.log` | **PASS: 28 passed** with host built native safety and production C++ pandad bridge. |
| Affected concrete Honda safety and MVL stock tests, `/tmp/c82_c4_honda_stock_affected.log` | **PASS: 253 passed, 40 skipped, 204 deselected**. Skips remain skips. |
| First lifecycle invocation, `/tmp/c82_c4_lifecycle.log` | **FAIL: 7 failed, 28 passed** because collecting the imported `CurrentCaller` class separately bypassed its fixture environment; explicit intended 28-node selection passed afterward. |
| Ruff 0.16.7, Python compileall, `git diff --check` | **PASS** on changed Python and diff. System `ruff` command was absent; cached Ruff binary passed. |
| Vehicle/Panda/device and human independent gate | **BLOCKED/UNKNOWN**; none accessed or approved. |

The x86 mirror under `/tmp/c82_phase23_20261115/x86_mirror` received only the candidate native header, safety test hook and stock AOL test file for the lifecycle run. It compiles the unchanged production C++ negotiation bridge. Existing older acados x86 import support is not MPC numerical qualification. The earlier 72 route cases and unrelated GUI/MVL tuning were not rerun. Previous Jetlink 2-failed/5-passed evidence remains an open baseline failure, not a green suite.

## Changed files and driver expectation

- Production: `opendbc_repo/opendbc/safety/modes/honda_stock_aol.h` (Accord 80/81 Drive-bound grants and gear departure retirement).
- Test only: `opendbc_repo/opendbc/safety/tests/libsafety/safety.c` (native flag snapshot); `opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py` (five C4 tests and updated Accord gear expectation).
- Documents: this response, `C4_GATE_MATRIX.md`, and an appended note in `C4_CODEX_PRELIMINARY_SAFETY_CASE.md`. Four pre-existing untracked evidence Markdown files were preserved.

For Accord 11G, a MAIN or LKAS action taken before valid Drive is seen no longer creates a steering token. Returning from Park, Reverse, Neutral or unknown gear does not automatically resume independent steering; a new eligible physical LKAS/MAIN action or separately qualified normal ACC engagement in Drive is needed. Ordinary ACC and the host independent latch remain distinct. Driver display/expectation after CANCEL and a full stop still needs independent review.

## Remaining P0 physical blockers

Native independent lateral still has no separately qualified standstill speed veto (`honda_stock_aol.h:142-158`); host standstill guards share CarState. The visible Honda Panda TX hook does not establish a numerical torque/rate limit. Current vehicle CAN2/OBD topology, the cause of historical `interruptRateCan2` and real `controlsMismatch`, source timing, EPS/override response, physical CANCEL behavior, exact installed Panda/host identity and driver mode indication remain unmeasured here. The independent human engineering gate is **PENDING**. No live hardware, SSH, CAN TX, settings, firmware, push, merge or install was touched.

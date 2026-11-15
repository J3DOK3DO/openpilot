# C8.2 Campaign 4 — GPT-6 separate source challenge review
Date: 2026-11-15 UAE. Reviewed frozen C8.2 SHA e54e9cc8c6e8dd7338618e1d22622fb97c6856dc.
Reviewer: GPT-6 (separate from implementing Codex). This is **AI source review**, not independent human automotive safety certification. OpenCode/Qwen attempted on Windows; runner stalled with no response, and shared Ollama service was deliberately left running. Do **not** record Qwen PASS.

## Method and scope
Read directly from frozen worktree: opendbc_repo/opendbc/safety/modes/honda_stock_aol.h (1-270), honda.h (106-175,260-332); openpilot/starpilot/car/honda/stock_intent.py (1-120); honda/aol.py (75-133); runtime.py (190-272); source diff f004037b..e54e9cc8. Evidence from Phase2-3 test report and copied historical route is separately labeled prior engineer evidence, not re-executed here. No car, Panda, bus, firmware, Python or compiled C++ test was executed by this reviewer. Do not infer road capability.

## Findings for engineering response

### C4-P0-1: Native standstill guard not independently demonstrated
- In honda_stock_aol.h:142-159, permission requires MAIN, Drive, permitted EPS and controls_allowed/token, but does not check speed or standstill.
- Honda TX hook honda.h:310-318 checks only whether the nonzero steering command is permitted by lateral_controls_allowed; the inspected hook does not show numerical command magnitude/rate limits.
- Host independent-lateral protection exists in stock_intent.py:9-20 and 38-50 (and selfdrived/controlsd) but relies on CarState; not independent physical redundancy.
- **Disposition:** P0 vehicle hardware and architecture qualification blocker. Not evidence the tested host code sends torque at standstill; a source-level safety limitation. Do not assert Panda standstill veto exists. Require authoritative OEM/CAN speed source, validated safety policy and independent steering actuation review before changing any firmware or moving to gear-D tests.

### C4-P0-2: Physical token may survive an LKAS gesture issued while Park/Reverse — requires negative native reproduction
- honda_stock_aol.h:201-211 calls honda_stock_aol_grant() on a fresh physical LKAS button edge with acc_main_on, but does not explicitly require HONDA_STOCK_DRIVE at that point.
- honda_stock_aol.h:224-234 updates HONDA_STOCK_DRIVE based on gear without explicitly retiring the stored token when leaving Drive.
- The later permission gate (142-159) denies output in non-Drive; a pending grant may still exist, and host_request(0) retires only when SESSION and REQUEST_SEEN are both true (89-100). Under initial pending session, it is intentionally preserved for startup handshake.
- Stock_intent.py:38-50,111-120 clears host latch in non-Drive, so a healthy host should not request lateral after Park. But an independent native negative test should challenge whether a latent **physical** token can produce permission when Drive becomes true and a stale/new host request arrives within the pending window without a new physical edge.
- **Disposition:** P0 *challenge case*, not a proven exploit or observed torque. Reproduce in isolated Panda/native fixture at realistic timestamps. If pass-through is possible, consider narrow fail-closed native gear-token retirement that preserves actual startup behavior. Do not arbitrarily remove intended handshake or bypass native checks.

### C4-P1-3: Normal ACC engagement and separate independent LKAS intent remain behaviorally ambiguous
- honda_stock_aol.h:235-249 permits honda_stock_aol_grant() after normal engagement in Drive with healthy sources, including stock cruise rising edge. That is a physical ACC gesture, not necessarily a dedicated LKAS gesture.
- stock_intent.py:34 disables auto-main gesture translation when LKAS is mapped to AOL_TOGGLE(9), so user-requested 'ACC engagement from both OFF enables both' may not be represented by an independent host latch.
- honda.h:163-170 short CANCEL can retain masked lateral request if HONDA_STOCK_ENABLED; host physical_cancel_lateral_allowed (honda/aol.py:108-133) requires a preexisting lateral-active and native-acknowledged independent latch.
- **Disposition:** independent UX/behavior acceptance gap. Require before/after state matrix differentiating stock ACC+ordinary lateral from explicitly armed LKAS, and precise HMI feedback at short CANCEL and a full stop. No automatic independent latch from ordinary ACC without policy approval.

### C4-P1-4: Token retirement timing and source errors
- host_request(0) retires token only when SESSION and REQUEST_SEEN (honda_stock_aol.h:89-99). Special pending grant is intentionally preserved, but faults and stale host request expiry retire it in request_mask (116-140).
- Need bounded source-level race tests for host request=0 vs physical LKAS edge in same or next CAN/USB tick, heartbeat_engaged transition, MAIN off and EPS temporary 2/6. Native flag atomics do not imply transactional ordering across multiple flags.
- **Disposition:** P1 offline test expansion or independent external reviewer challenge. Preserve fail-closed policy and do not suppress CAN faults.

### C4-P0-5: CAN2/controlsMismatch physical cause unknown
- Prior C8.1 reports describe startup OBD mux CAN2 interrupt bursts and later selected route without the fault, but these are different sessions/configurations. Current vehicle topology, real EPS data validity, USB/panda firmware timing and the cause of actual controlsMismatch remain not directly measured in this review.
- **Disposition:** physical environment blocker. Do not classify simulation-only fault injection as resolution or disable Panda IRQ checks.

### C4-P1-6: Other-Honda/no-regression and provenance boundaries
- New HONDA_STOCK_ACCORD11G flag is selected by safety param80/81 (honda_stock_aol.h:263-275), not a generic Honda torque policy. Confirm only intended Accord variants map to these exact safety params in production CarParams.
- Older x86 acados module used as import-only dependency, not a numerically qualified current longitudinal controller. Preserve evidence distinction.
- Jetlink 2 failures existed in baseline; not a clear C8.2 regression but still not full suite green.
- **Disposition:** retain conditional offline gates; no numerical MPC or QCOM/device build claims.

## Review verdict
**PASS_WITH_BLOCKERS for source/evidence preparation only; independent Phase 4 approval NOT achieved. DEVICE_INSTALL_NO_GO.**
A strong separate challenge review of source is possible, but the required human/independent model engineering approval, cross-layer hardware safety evidence and CAN2 diagnosis are absent. In particular C4-P0-2 requires a native test, and C4-P0-1/C4-P0-5 require a separately authorized physical safety plan.

## Safe immediate action
Ask Codex to run P0-2 and P1-4 as narrowly targeted offline native negative tests using the existing C++ fixture, compare against e54e9cc8 without production changes first. If a real source bug is proven, implement a minimal Accord-only fail-closed candidate and regression test in this separate worktree, with no push/install. Then re-review and prepare a conditional Phase 4 matrix. Never run Claude parked Option A in D or change the installed C8.1 settings on this evidence.

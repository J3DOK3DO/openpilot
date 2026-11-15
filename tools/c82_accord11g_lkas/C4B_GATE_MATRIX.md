# C8.2 Campaign 4B — authorization and qualification gate matrix

Date: 2026-11-15 (UAE). **No road or vehicle-control authorization.**

| Gate | Status | Supporting evidence | Remaining mandatory requirement |
|---|---|---|---|
| C4B source preservation and lineage | **PASS** | Separate local-only branch based on `e54e9cc8` with SHA-256-verified preserved C4 patch; earlier C8.1/Phase23/C4 trees untouched | Final local SHA and no-push verified at checkpoint |
| C4B targeted native Panda token/gear safety | **PASS (offline)** | 33/33 fresh host tests; C4 prepatch TX acceptance and patched denial shown in prior red/green evidence | Later ARM/native firmware identity and genuine device acceptance |
| Targeted CAN2 evidence parser | **PASS (offline)** | 1/1 fresh test of sanitized historical timeline | Physical root cause and fault-free cold/warm startup |
| Full Card/selfdrived/Controls/Panda lifecycle | **REUSED PASS (offline)** | Exact equivalent C4 patched source previously passed 28/28; no new source change beyond verified C4 patch | Fresh exact build/fingerprint and hardware qualification before deployment |
| Cross-Honda regressions | **REUSED PASS (offline)** | 253 passed, 40 skipped, 204 deselected on same C4 patch; older host 365 passed | No new broad run necessary unless source changes |
| Jetlink event-fault cases | **BASELINE OPEN** | 2 failed and 5 passed both in C8.2 and untouched baseline | Separate issue owner resolution, not a current Panda patch regression |
| C8.1 owner rollback waiver | **DOCUMENTED LIMITED ACCEPTANCE** | Manual reinstallation; skip full-image restore rehearsal for offline/device-prep workflow | Rollback dry run if later separately required; NOT safety waiver |
| Phase 4 independent source/safety assessment | **PENDING / BLOCKED FOR FULL CLOSURE** | Codex implementer review + GPT-6 separate AI challenge; Windows Qwen not completed | Independent authoritative review of exact final C4B SHA, findings disposition |
| Phase 5 non-actuating hardware readiness | **DOCUMENTS PREPARED** | `C4_PHASE5_NONACTUATING_READINESS.md`, C4B crosswalk and fault triage | Comma reconnection, exact identities, passive hardware checks, no actuation |
| Panda standstill and stationary zero-torque | **P0 HARDWARE NO-GO** | Native permit gate and host shared-CarState veto only | Independent non-actuating/controlled hardware safety plan and evidence |
| CAN2 `interruptRateCan2` and `controlsMismatch` | **P0 PHYSICAL NO-GO** | Historical ELM327/0 interrupt/error storm, later C8.1 route distinct | Hardware topology, exact firmware, startup passive telemetry, qualified fault analysis |
| Native product/firmware build and exact install receipt | **NOT RUN / NO-GO** | C8.2 changes C header, unlike C8.1 GUI-only | Authentic ARM/Panda firmware and product build, receipt, independent release review |
| D-gear parked arming, steering actuation, public-road deployment | **NO-GO** | No explicit physical test authorization and unresolved critical risks | All earlier relevant gates, separate approval and controlled safety qualification |

**Current verdict: PASS_WITH_BLOCKERS for offline source candidate; PHASE4_APPROVAL_PENDING, PHASE5_HARDWARE_BLOCKED, C8.2_INSTALL_NO_GO.** Repeating already-passed unmodified suites would not resolve a missing physical or independent gate.

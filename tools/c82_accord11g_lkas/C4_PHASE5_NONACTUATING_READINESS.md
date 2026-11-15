# C8.2 Campaign 4 — Phase 5 nonactuating readiness design

2026-11-15 Asia/Dubai. **Checklist design only. Not an instruction to connect to the car or run a parked experiment now.** The frozen source is `e54e9cc8c6e8dd7338618e1d22622fb97c6856dc`; the installed C8.1 is a different revision. The separately commissioned OpenCode/Qwen review has not been reconciled. This checklist can establish document and telemetry readiness only. It cannot establish physical steering authorization, EPS acceptance, or standstill torque denial without a separately authorized hardware qualification.

## Boundary and roles

This phase permits offline review of existing files and, after a separate custody decision, a **telemetry-only** inspection of an ignition-OFF, physically isolated device on a bench. It has no ignition-on, READY, gear-D, LKAS-9 arming, live Panda/OBD query, CAN TX, firmware flash, settings change, or driving step. A device still installed in the vehicle is outside this checklist's telemetry boundary. Until a later authorization, work from already copied evidence only.

| Role | Required responsibility before a later nonactuating session |
|---|---|
| Safety lead, independent of implementation | Review exact source checksum, Qwen findings, hazard register and stop criteria; decide whether bench telemetry is allowed and record unresolved gates. |
| Operator | Keep device disconnected from vehicle/CAN; record the identity and data provenance of any read-only file or bench observation; stop on unexpected power, bus traffic or actuator connection. |
| Owner/custodian | Confirm the installed C8.1 remains intact, authorize any future device custody or bench handling separately, and retain rollback artifacts. |
| Recorder | Timestamp observations, hashes and tool versions; distinguish copied C8.1 route evidence from frozen C8.2 source or any later device state. |

## Nonactuating checklist

Each item needs an evidence reference, observer, timestamp, and PASS/FAIL/UNKNOWN. An UNKNOWN is not a pass. Do not turn this into a live procedure by filling gaps with vehicle actions.

1. **Scope and isolation:** record vehicle ignition OFF and no READY state from independent observation only if a later session is authorized. For bench telemetry, require physically isolated device, no OBD/panda/vehicle CAN attachment, no actuator path, and a documented power/data boundary. If isolation is uncertain, stop at offline file review.
2. **Frozen source:** verify branch `accord11g-dom7-c8-2-c4-independent-offline-20261115`, exact Git HEAD `e54e9cc8c6e8dd7338618e1d22622fb97c6856dc`, parent `f004037b9117f3634ae657a179afdc570c10a892`, clean source, and a content hash manifest of all native and host files under review. Compare any future candidate artifact against that source; never infer identity merely from a branch name.
3. **Installed and rollback identities:** from existing read-only custody records, distinguish installed C8.1 `9d2da330f6539beb5afb67867b28491526c0e1bd`, frozen C8.2 candidate, prior rollback `ab468b8ecd1baa3e63fb5436b69253213d892b5d`, Panda firmware identity, Panda safety mode/param and AE. Do not claim a Panda firmware identity from the host SHA. If a required identity is absent, mark UNKNOWN; do not access the live device in this phase.
4. **Model and CarParams:** confirm recorded `HONDA_ACCORD_11G` fingerprint source, expected firmware match and Hybrid/CAN-FD flags, transmission, `pcmCruise=true`, `openpilotLongitudinalControl=false`, `hondaBosch/80` or rigorously explained 81, AE 32, `minSteerSpeed`, and `steerAtStandstill`. Preserve the actual serialized CarParams and timestamp. A fixed/manual or fuzzy identity needs separate disposition; a copied C8.1 CarParams is historical evidence, not future C8.2 identity.
5. **Health and telemetry:** inventory available copied `pandaStates`, `aolSafetyWire`, `carState`, `aolIntentWire`, `aolAxisState`, `selfdriveState`, `carControl`, events and diagnostic logs. Check timestamp ordering, service validity, native serial/inventory match, request/permission synchronization, heartbeat and RX freshness, `interruptRateCan2`, `controlsMismatch`, EPS fault, and CAN2 error/IRQ counters where already recorded. Mark missing telemetry UNKNOWN. No CAN commands or synthetic live messages.
6. **Pending engineering:** reconcile Qwen assessment, 80/81 token/session state machine, CANCEL lease timing, full-stop loss of independent intent, temporary EPS recovery, brake/override policy, host restart, same-CarState standstill common cause, and exact native FW/build identity. Preserve the Jetlink 2-failed/5-passed baseline result as an open software issue. Record the older x86 acados import limitation.
7. **Storage and provenance:** verify copied rlog/qlog and checksum manifest are readable, timestamped and backed up; record available storage for any later authorized capture without deleting or overwriting existing evidence. Existing `device_readonly_20261114/ROUTE_LOG_SHA256SUMS.txt` and `/tmp/c82_phase23_20261115/*.log` are starting references. Separate raw source measurements from interpretations.
8. **Rollback plan:** identify the exact installed tree, Panda FW, settings snapshot and previously working recovery path from records; name a custodian and a trigger for reverting any future change. This is a plan, not a rollback execution. A future install needs a separately reviewed artifact and authority.
9. **Closure:** recorder marks every item PASS/FAIL/UNKNOWN, lists inaccessible measurements, and gets safety-lead review. This checklist can close only the nonactuating document/telemetry gate; it cannot close steering, brake, CAN2 physical health or public-road gates.

## Disposition of Claude Option A

The earlier `evidence/C8_2_INDEPENDENT_LATERAL_20261114/independent_review_20261114/parked_test/PARKED_TEST_PROCEDURE.md` and `OPERATOR_SHEET_OPTION_A.md` were prepared for installed C8.1. Their T1 changes LKAS mapping to 9 and powers the car to READY; T2 shifts to D; T3/T4 arm in stationary D; later steps use MAIN, gear, door and belt transitions. These are **actuating qualification actions**, despite the “parked” label. The procedure itself notes that Panda would accept steering torque if its single then-known host guard failed. Its additional claim of Panda numerical torque/rate limits is not supported by the visible Honda TX hook (`honda.h:310-318`); numerical limits are visible in the host Honda controller. Frozen C8.2 adds latch and selfdrived standstill guards, but both share CarState and there is no independently qualified Panda standstill veto. Moreover, the sheet's expected stationary D arm and P-to-D regrant conflict with `stock_intent.py:38-50,111-120`.

**Recommendation: defer/reject Option A for this campaign.** Its earlier settings-only authorization does not cover this frozen source or the current C4 prohibition. Reconsider only after Qwen reconciliation, an independent safety authority, a source-specific physical safety plan, instrumented abort criteria, rollback and explicit actuation authority. No part of T0–T11 is executed here.

## Separate risk-gated physical qualification outline (future decision only)

This is a list of evidence questions, not a procedure or commands:

- Independent reviewer signs off exact host/native/Panda artifacts, hazard analysis and telemetry fields, including startup and restart ordering.
- Establish healthy CAN2 and OBD topology under measured startup conditions; determine whether the historical error/IRQ burst recurs and whether a fault remains latched. Resolve any `controlsMismatch` without masking it.
- Measure EPS fault and driver-override response, CANCEL request/permission timing and expiry, MAIN/off, brake transitions, host restart and heartbeat loss, with native status and output observed together.
- Establish zero steering request and zero torque at stationary under all permitted states with a safety plan that treats CarState as a common-cause input. Native Panda currently lacks a separately qualified standstill veto.
- Verify that stock ACC state, independent lateral intent, native grant and actual steering output remain separate in telemetry and in the driver's mental model. Review gauge/HUD/LED indications and what the driver expects after CANCEL and a full stop.
- Review stop authority, independent observer, controlled environment, evidence custody and exact rollback before any physical qualification. A later physical protocol must be authored and approved separately; public-road use remains NO-GO.

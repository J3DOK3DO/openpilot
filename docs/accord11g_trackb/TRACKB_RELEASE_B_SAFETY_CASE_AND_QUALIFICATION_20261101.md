# Accord 11G Hybrid Release B: Tier 3 safety case, risk-acceptance annex and B5/B6 procedures (2026-11-01)

Target: 2025 US Honda Accord 11G Hybrid, `HONDA_ACCORD_11G`, Bosch-C / CAN-FD. Architecture under assessment: an
MVL-inspired (`mvl-boston/opendbc` `3fec9a41`) radar-disabled alpha-longitudinal design. Nothing here was executed on a
vehicle or bench; this document defines what would have to be proven.

## 1. Evidence classification of the seven MVL architecture findings

Classes: `OEM_AUTHENTICATED`, `TARGET_PASSIVE_OBSERVED`, `COMMUNITY_SOURCE_ONLY`, `SYNTHETIC_ONLY`, `UNKNOWN`.

| Finding | MVL assertion | Class | Software response this campaign |
| --- | --- | --- | --- |
| F1 ownership/relay inference | stock ACC alive from parsed `ACC_CONTROL`; relay open after camera silence **or 500 updates** | `COMMUNITY_SOURCE_ONLY`; target behaviour `UNKNOWN` | `source_evidence_contracts.classify_stream`/`RelayInference`: rejected ≠ silent, no update-count fallback (`SYNTHETIC_ONLY` tests) |
| F2 radar tick cadence | ticks from counters without an observed reference | `COMMUNITY_SOURCE_ONLY`; rates/DLC `UNKNOWN` | `TickReference`: no tick without a correctly sized fresh reference |
| F3 relay-fault forwarding | nominal forwarding claims | `COMMUNITY_SOURCE_ONLY`; Dom generic relay-fault test is host evidence | documentation: under a latched relay fault nothing is forwarded, so OEM ACC/CMBS frames do not reach the car |
| F4 shutdown restore | `deinit` "enable" request restores the radar | `COMMUNITY_SOURCE_ONLY`; ECU response `UNKNOWN` | `return_to_stock_established`: five stages, each needs target/OEM evidence |
| F5 startup fault suppression | `accFaulted` hidden for 10 s at start | `COMMUNITY_SOURCE_ONLY` | `startup_fault_record`/`record_hides_fault`: raw fault always reported |
| F6 DBC mux semantics | mux/sentinel pattern of lane/object frames | `COMMUNITY_SOURCE_ONLY` | none needed: self-consistency only, never protocol validation |
| F7 lane metadata ordering | lead lane metadata and path "in lockstep" | `COMMUNITY_SOURCE_ONLY` | `lane_metadata_consistent`: same current revision required |

No assertion is `OEM_AUTHENTICATED` or `TARGET_PASSIVE_OBSERVED`. The only target observations in this campaign are
read-only device facts (CarParams, Panda version string, AGNOS identity), none of which concern longitudinal command
ownership.

**Why MVL's code, or reports that it "works", do not prove recovery or priority on this Accord:** a community
implementation demonstrates that its authors' cars accepted its frames under the conditions they tried. It does not
establish (a) which ECU consumes `ACC_CONTROL`-class frames on a 2025 US Hybrid with its firmware, (b) behaviour on
loss of the replacement stream, (c) brake-module fault latching (MVL's own comments describe a `CRUISE_FAULT` latch
when its stream starts late), (d) whether the radar returns to service after an enable request, or (e) what happens
under a relay fault, where the Panda forwards nothing. Each of these is a safety-relevant failure path, and none has
target evidence.

## 2. Tier 3 safety case with factory CMBS/AEB/FCW unavailable

The owner accepts that a radar-disabled architecture loses factory CMBS, AEB and FCW. That acceptance records a
hazard; it does not mitigate one. The questions the safety case must answer, and the current answer from evidence:

| Question | Required for Tier 3 | Current state |
| --- | --- | --- |
| Who detects collision risk? | A qualified detector with defined coverage, latency and false-negative rate, replacing the OEM radar-based CMBS | **None qualified.** openpilot's model/radarless lead estimate and planner FCW are not an AEB system; with the radar silenced there is no radar track at all. Driver is the only backstop. |
| Who brakes in an emergency? | An independent emergency-braking path with authority, rate and reaction time at least as good as CMBS, or an equivalent argument | **None.** Any braking would come from the same openpilot command stream that is also the failure source. |
| Unintended acceleration/braking prevented by? | Independent interlock (Panda limits derived from B1 evidence, gas/brake exclusivity, rate and magnitude bounds, plausibility vs vehicle state) | Simulation contracts only (B2, B17, this campaign); no Panda long table exists, by design. |
| Driver override? | Brake and accelerator override measured on the target: latency, latching, no re-engagement | Simulation only (`plan_controller_sim`, `mvl_retained_sim`); stock path unchanged. Not measured. |
| Controller failure / loss of comms? | Defined safe state on process crash, msgq stall, Panda heartbeat loss, CAN bus-off, relay fault | Simulation withdraws; physical safe state **UNKNOWN**: with the radar disabled, stock ACC/CMBS do not automatically return (F4). |
| Stock brake system and ACC recover? | Measured return to OEM ACC and CMBS after every exit path, including ignition cycle, with DTC state recorded | **UNKNOWN**; MVL source documents a fault latch hazard. |
| External review | Independent functional-safety review (hazard analysis, FMEA, verification evidence), and applicable legal/roadworthiness review | Not performed. |

**Disposition: TIER_3_HOLD.** With CMBS/AEB/FCW removed and no qualified replacement detector or independent
emergency-braking path, the architecture cannot meet a defensible safety requirement for an operational
longitudinal release. This is a design-level blocker, not only a missing test.

## 3. Change-control annex (separate from the original requirements)

The original requirement set (`B0_HAZARD_AND_REQUIREMENTS.md`, register `B1-CMBS-AEB-PRECEDENCE`) requires factory
CMBS/AEB to be preserved. The owner's decision proposes an alternative. It is recorded here as a **proposed**
change, without altering or passing the original requirement.

| ID | Original requirement | Proposed alternative (owner) | Status | Conditions before it could replace the original |
| --- | --- | --- | --- | --- |
| CC-01 | Preserve OEM CMBS/AEB/FCW and their precedence | Accept their loss under a radar-disabled alpha-long design | PROPOSED, NOT APPROVED | qualified replacement detection + independent emergency braking (§2), independent safety review |
| CC-02 | Panda RELEASE-signed firmware on target | Accept DEBUG firmware for research | ACCEPTED FOR RESEARCH ONLY (DEV-PANDA-DEBUG-001) | RELEASE build + measured flash before any Tier 3 activation |
| CC-03 | Installed AGNOS raw identity = pinned image | Accept version-equal hash mismatch | ACCEPTED FOR RESEARCH ONLY (DEV-AGNOS-HASH-001) | independently reviewed identity before Tier 3 |

Severity of CC-01 if adopted without the conditions: loss of the vehicle's automatic collision mitigation while a
software controller holds longitudinal authority. Residual risk is unbounded by current evidence.

## 4. B5 — electrically isolated bench qualification (procedure for qualified personnel; not executed)

Purpose: verify the command path and every fault path **without a vehicle**, before any B6 activity.

1. **Setup:** target-equivalent comma and Panda (RELEASE-signed firmware built from the reviewed source, flash
   identity measured), a recorded bus simulator/harness emulating the 11G CAN-FD buses, an independent bus logger,
   and a hardware kill path that removes Panda power. No connection to a vehicle.
2. **Identity:** record source SHA, build manifest, Panda firmware SHA-256, AGNOS identity and Params; compare with
   the reviewed release manifest.
3. **Nominal:** for each permitted mode transition (off → armed → active → withdrawn → stock), verify that only
   B1-derived frames are emitted, at the specified rates, with correct counters and checksums.
4. **Fault injection (each repeated ≥ 30 times, results logged):** process crash/restart (cold-start barrier),
   msgq stall, stale/duplicate/out-of-order plans, Panda heartbeat loss, CAN bus-off and error-passive, relay fault,
   wrong-length and bad-checksum frames, simultaneous gas/brake requests, driver brake/accelerator override,
   ignition cycle mid-activation. Acceptance: emitted command stream stops within the specified bound, Panda
   rejects every out-of-table frame, no re-engagement without a fresh driver action, logged stock-restoration request.
5. **Negative TX sweep on target firmware:** every non-table ID/bus and every non-qualified safety word denied.
6. **Exit criteria:** zero unexplained frames, every injected fault reaches the defined safe state within bound,
   independent review of logs. Any failure stops the programme before B6.

## 5. B6 — independently supervised closed-course validation (procedure; not executed)

Purpose: verify vehicle behaviour after B1 evidence and B5 pass. Requires separate explicit authorization.

1. **Preconditions:** B1 gates PASS with authenticated evidence; B5 PASS and reviewed; insurance and site approval;
   independent safety observer; trained driver; documented abort procedure; the comma's longitudinal function
   enabled only for the session by a reviewed, auditable configuration.
2. **Site:** closed course, no public traffic, soft targets only for any lead-vehicle scenario, run-off space.
3. **Sequence (speed increments only after the previous step passes):** stationary arming/disarming; low-speed
   creep and stop; steady following of a soft target; target braking; driver brake override at each speed; driver
   accelerator override; cancel button; controller kill (hardware path) at each speed with measured deceleration
   and the car's state afterwards; ignition cycle and confirmation that stock ACC and CMBS return (with DTC scan).
4. **Measurements:** commanded vs measured acceleration, override latency, time to safe state, stock ACC/CMBS
   availability after every exit, any warning or DTC.
5. **Exit criteria:** every scenario within pre-registered bounds; no uncommanded acceleration or braking; stock
   systems restored after every exit; independent sign-off. Anything else keeps Tier 3 on HOLD.

## 6. Next concrete evidence needed for Tier 3

1. Authentic Honda service/electrical information for the 2025 US Accord Hybrid that identifies the consumer and
   integrity rules of longitudinal command frames, and CMBS/AEB arbitration (B1).
2. A replacement for CMBS/AEB/FCW, or an architecture that keeps them (CC-01), with an independent safety review.
3. A RELEASE-signed Panda build with a B1-derived table and a measured flash identity (B3).
4. B5 then B6, as above, each separately authorized.

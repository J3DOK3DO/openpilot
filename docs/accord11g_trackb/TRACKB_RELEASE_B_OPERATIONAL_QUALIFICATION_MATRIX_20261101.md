# Release B (operational custom Bosch-C longitudinal): qualification matrix — 2026-11-01

**Classification: SOURCE ENGINEERING COMPLETE (non-actuating scope) / PHYSICAL QUALIFICATION HOLD. Actuation: disabled; no path exists.**

The machine-readable twin is `RELEASE_B_EVIDENCE_REGISTER.json`, enforced by `tools/trackb_research/release_b_gate.py`. In the register every row is HOLD, because a PASS there needs an author, a distinct named independent reviewer, and evidence only of the kinds that row accepts (physical rows: exactly one OEM/target/bench/vehicle kind; B2 and B4-source accept several source/host kinds), resolving to an artifact with matching SHA-256 (identity rows bound to the measured hash). The "campaign result" column below records what was actually demonstrated.

## 1. Requirements → evidence

| ID | Requirement | Campaign result | Evidence (source) | Acceptance owner |
| --- | --- | --- | --- | --- |
| B1-OEM-COMMAND-OWNERSHIP | ECU owning ACC gas/brake, frame set, integrity, takeover/fault semantics | **HOLD** | None authenticated. MVL `3fec9a` DBC/safety are fork claims (`TRACKB_MVL_3FEC9A_COMMA_DOM_SOURCE_AUDIT_20261101.md` §3) | OEM-data holder + independent safety reviewer |
| B1-CMBS-AEB-PRECEDENCE | CMBS/AEB precedence over external requests | **HOLD** | MVL itself warns its path disables AEB; comma excludes Bosch CAN-FD long | Same |
| B1-CANFD-TOPOLOGY-ARBITRATION | Topology, ID ownership, relay segments, bus-off/recovery | **HOLD** | Source-only `CANFD_SOURCE_DICTIONARY.json` | Same |
| B1-OWNER-TRANSITION | Authority transfer keeping radar/CMBS; fail-safe return (FR-B0-05) | **HOLD** | No known mechanism | Same |
| B2-SUBORDINATE-CONTROLLER-CONTRACTS | Dom-plan-following fail-closed controller + authorization gate | **PASS (source/synthetic)** | `plan_controller_sim.py`, `release_b_gate.py`, `test_plan_controller_sim.py`, `test_release_b_gate.py`, `test_plan_snapshot_schema_contract.py`; host and ARM64 runs (final report) | Independent reviewer (this campaign: Codex) |
| B3-HOST-RELEASE-DENIAL | Host RELEASE libsafety denies long/UDS/radar-emulation; DEBUG positive controls; OEM forwarding preserved | **PASS (host library only)** | `test_accord11g_trackb_release_{denials,rejections_extended,sweep}.py`, `test_accord11g_trackb_mvl3fec9a_canfd.py` | Independent reviewer |
| B3-TARGET-PANDA-RELEASE-IDENTITY | Hash and provenance of flashed RELEASE firmware | **HOLD** | No Panda access | Device owner + reviewer |
| B4-SOURCE-BUILD-COMPATIBILITY | Reproducible build, ARM64 dependency compatibility | **PARTIAL** | ARM64 emulated tests pass; pinned AGNOS image hash = `agnos.json`; full ARM64 release build NOT_RUN | Build engineer |
| B4-INSTALLED-DEVICE-IDENTITY | Installed AGNOS/slot/Panda identity | **HOLD** | Device backups absent; no device access (`TRACKB_AGNOS_BACKUP_COMPATIBILITY_REPORT_20261101.md`) | Device owner |
| B5-ISOLATED-BENCH | Electrically isolated bench qualification | **NOT_RUN → HOLD** | Procedure §2; no bench, equipment or authorization | Bench lead + independent safety reviewer |
| B6-CONTROLLED-VEHICLE | Overseen vehicle validation | **NOT_RUN → HOLD** | Plan §3; requires B1–B5 first | Vehicle test director + independent safety oversight |
| R-INDEPENDENT-REVIEW | Review of the exact final design and claims | See final verdicts | Codex review record in final artifacts | Reviewer outside this session |

**No OEM, Panda-target, bench or vehicle qualification was performed in this campaign.**

## 2. B5 isolated-bench procedure (draft; not executed)

Preconditions: B1 evidence accepted; a reviewed Panda safety table that exists only on a bench branch; written authorization; and a bench with no vehicle connection. The bench consists of the comma device, the target Panda, and CAN-FD interfaces that simulate the camera, radar and powertrain segments, on an isolated supply with a hardware kill switch.

| Test | Stimulus | Pass criterion |
| --- | --- | --- |
| B5-1 Identity | Read Panda RELEASE firmware hash and AGNOS system hash | Both equal the register's qualified identity |
| B5-2 Default denial | Every non-stock safety word and experience, controls on/off | Zero frames outside the reviewed table reach any bus (logic-analyzer capture) |
| B5-3 AEB precedence | Simulated CMBS/AEB active during an abstract proposal | Proposal withdrawn within one plan period; OEM brake frames forwarded unmodified |
| B5-4 Driver override | Simulated brake, accelerator, cancel | Withdrawal within one control cycle; stock ACC state remains authoritative |
| B5-5 Staleness / ordering | Delayed, duplicated or reordered plan and observation frames | Withdrawal with the documented reason; no TX |
| B5-6 Bus faults | Bus-off, error-passive, relay fault, Panda reset, USB/SPI loss | Fail-safe relay state; stock path restored; no TX until fresh token |
| B5-7 Firmware mismatch | Flash a non-qualified build on the bench Panda only | Gate reports `target_identity_mismatch`; no TX |
| B5-8 Recovery | Fault → recovery → re-engagement | Retired tokens rejected; a fresh token is required |

## 3. B6 controlled-vehicle plan (draft; not executed)

Entry only after B1–B5 PASS and independent sign-off: closed course, safety driver plus independent observer, and data logging of all CAN-FD segments. Exit criteria: OEM CMBS/AEB activation is unaffected (staged target tests against the OEM-specified procedure); driver override is immediate at every speed band; there are zero unexpected frames; every fault in B5 is replicated with a fail-safe outcome. Historical C6-12/C7 drives are not accepted as evidence.

## 4. Remaining implementation for an operational Release B

After B1 only: a production Bosch-C actuator builder, a Panda safety table derived from authenticated evidence, and wiring of `GateRecord.proposal` into the Honda CarController behind the register. Each requires its own review and B3–B6 requalification. None is implemented, and none can be specified honestly without B1.

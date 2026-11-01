# Accord 11G unified Track A/B architecture: Release A isolation and the Release B subordinate controller — 2026-11-01

## 1. Operational path today (Release A = Track A, unchanged)

```
modeld → Dom longitudinal planner ──longitudinalPlan──► controlsd/LongControl ──CarControl──► Honda CarController
                                                                                     │  pcmCruise=True, openpilotLongitudinalControl=False
                                                                                     ▼
                                     stock LKAS (0xE4), LKAS_HUD (0x33D), SCM_BUTTONS (0x296) only
                                                                                     ▼
                         Panda hondaBosch, word 80/81 → HONDA_MVL_STOCK_TX_MSGS; RELEASE never selects the Bosch-long table
OEM ACC / CMBS / AEB ──── camera/radar frames forwarded bus 2→0 except the two replaced LKAS frames ────► powertrain
```

- Longitudinal authority: **OEM ACC** (`pcmCruise=True`). Dom plans, but the plan is not turned into gas/brake commands for this car.
- Track A behavior in Git ancestry (`5fa8b2ed8` and earlier): stock-MVL LKAS interruption/cancellation, 500-frame rearm, persistent counters, SCM button takeover with freshness gating, words 80/81, physical-brake handling. Production files are byte-identical to `d88e2918` (no production path changed on this branch).

## 2. Release B target architecture (subordinate, not yet operational)

```
Dom longitudinal planner (sole planner) ──longitudinalPlan──► PlanSnapshot (schema-bound: ordinals/types pinned)
                                                                    │
VehicleObservation (driver pedals, cancel, AEB/CMBS state, ─────────┤
stock ACC state, validity, engagement token)                        ▼
                                              PlanControllerSimulation  (fail-closed state machine; a_target only)
                                                                    │ shadow record (always computed, audit)
OwnershipEvidence (OEM protection observed intact) ─────────────────┤
TargetIdentity (Panda RELEASE hash, AGNOS system hash) ─────────────┤
RELEASE_B_EVIDENCE_REGISTER.json (B1–B6 + review) ──assess_register─┤
                                                                    ▼
                                         SubordinateReleaseBGate → proposal | None   (abstract record only)
                                                                    ┊
                                     (no path exists) ┊ future, separately qualified Bosch-C actuator builder + Panda table
```

Ownership rules this design enforces:

| Concern | Rule | Where enforced (today) |
| --- | --- | --- |
| Planner ownership | Dom planner is the only trajectory source; the subordinate consumes `a_target` and uses `should_stop` only to select abstract hold. | `plan_controller_sim.py` docstring and API; no planner code in research modules |
| Schema/version | `PlanSnapshot` fields map to `LongitudinalPlan` with pinned ordinals and types. | `test_plan_snapshot_schema_contract.py` |
| Freshness / ordering | Stale plan/observation, duplicate or out-of-order IDs, clock reversal and timestamp inconsistency withdraw. | `PlanControllerSimulation._state_reason`, `_input_reason` |
| FCW/AEB/CMBS precedence | `aeb_cmbs_state != clear` or plan `fcw` withdraws; OEM protection must be observed in the gate. | simulator + gate (`oem_protection_state_not_observed`) |
| Engagement | Stock ACC must be enabled; the engagement token is retired on any withdrawal and recovery needs a fresh token. | simulator token lifecycle |
| Driver override / cancel | Brake, accelerator or cancel withdraws. | simulator |
| Faults / recovery | Malformed input, invalid observation and contradictory standstill withdraw; `reset()` retires the token. | simulator |
| Authorization | No proposal unless every one of 12 register requirements is PASS with an author and a distinct independent reviewer, and evidence only of the kinds that requirement accepts (`REQUIRED_KINDS`: B1 `oem_authenticated`, target identities `target_measurement`, B5 `bench_record`, B6 `vehicle_record`; B2/B3-host/B4-source/review accept their listed source or host kinds). Each item must resolve to caller-supplied artifact bytes with matching SHA-256. Identity rows must bind `qualified_identity` to the `measured_sha256` in their evidence, and the runtime target must equal it. This is an integrity check, not authentication: fabricated artifacts would pass, so authenticity rests on the reviewer. | `release_b_gate.py`, `test_release_b_gate.py` |
| Auditability | Every step returns reason, plan ID and observation ID; the shadow record is kept even when the proposal is withheld. | `SimulationRecord`, `GateRecord` |
| Isolation | No tracked file outside `docs/` and `tools/trackb_research/` references `tools/trackb_research`. The scan reads the working tree **and** every index blob (so sparse-checkout files are covered), with no test-name exemption. Research modules import only the standard library and sibling research modules. | `test_architectural_isolation.py` |
| Panda | RELEASE denies Bosch-long, UDS and MVL CAN-FD-long/radar-emulation frames for Accord and all non-stock words; OEM forwarding is preserved. | `test_accord11g_trackb_release_*.py`, `test_accord11g_trackb_mvl3fec9a_canfd.py` |

What does **not** exist, by design: no CAN builder, no Panda TX entry, no Params, no service, no process, and no import from `openpilot/`, `opendbc_repo/opendbc/` or `panda/`. Release B cannot affect the vehicle from this branch even if the register were edited, because nothing in production reads the register or the gate.

## 3. Conditions to wire Release B (none met)

1. B1: authenticated OEM command ownership, an owner-transition mechanism that keeps radar/CMBS/AEB, and topology.
2. A new Panda safety table that is reviewed against that evidence, plus target RELEASE identity (B3).
3. Installed-device identity (B4), isolated bench (B5) and controlled vehicle validation (B6).
4. Independent review of the wired design.

Only then would a production actuator builder consume `GateRecord.proposal`; that change would be a new, separately reviewed release.

## 4. Requirements → tests traceability

| Requirement | Release | Tests (native host unless noted) |
| --- | --- | --- |
| FR-B0-01/02 stock ownership, no long authority | A | `test_accord11g_stock_ownership_v4.py`, `test_accord11g_trackb_no_long_authority.py` |
| Track A LKAS interruption / rearm / counters / parameters | A | `test_accord_mvl_stock.py`, `test_accord_mvl_interrupt_v4.py`, `test_accord_mvl_parameters.py` |
| Words 80/81 physical brake, cancel, SCM freshness, forwarding | A | `test_honda_mvl_stock.py` |
| FR-B0-03/04 parked audit | A | `scripts/tests/test_accord11g_trackb_parked_audit.py` |
| FR-B0-06 FCW fail-closed | B | `test_plan_controller_sim.py`, `test_release_b_gate.py` |
| FR-B0-07 schema binding | B | `test_plan_snapshot_schema_contract.py` |
| FR-B0-08 isolation (incl. sparse/index scan) | A/B | `test_architectural_isolation.py` |
| FR-B0-09 RELEASE denial | A/B | `test_accord11g_trackb_release_denials.py`, `…_rejections_extended.py`, `…_release_sweep.py`, `…_mvl3fec9a_canfd.py` |
| OEM forwarding preserved (CMBS/AEB/ACC frames reach powertrain) | A | `test_accord11g_trackb_mvl3fec9a_canfd.py` |
| Release B authorization / evidence integrity | B | `test_release_b_gate.py` |
| Ownership evidence, brake-hold, synthetic faults | B | `test_ownership_evidence_model.py`, `test_brake_hold_contract.py`, `test_shadow_synthetic.py` |
| CAN-FD source dictionary integrity | B | `test_canfd_dictionary.py` |
| FR-B0-05 owner transition | B | **UNVERIFIED**: blocked on B1 |

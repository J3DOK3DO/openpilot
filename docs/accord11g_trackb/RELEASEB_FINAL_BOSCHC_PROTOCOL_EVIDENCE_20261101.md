# Accord 11G Hybrid Release B — Bosch-C protocol and architecture evidence (Stage 2, 2026-11-01)

Scope: owner-authorized Stage 2 (offline protocol, architecture and patch engineering). No device access, CAN/UDS
transmission, Panda/AGNOS change or vehicle test was performed. MVL reference `mvl-boston/opendbc`
`sp-honda-dev-202608` @ `3fec9a41` (research only). The 189-path comparison and F1–F7 delta are reused, not repeated.

## Evidence classes

| Class | Meaning here |
| --- | --- |
| `OEM_AUTHENTICATED` | Honda-published document for the 2025 US Accord Hybrid. Only owner-manual (functional) text is available; no service, electrical or protocol material. |
| `TARGET_PASSIVE_OBSERVED` | Read from the owner's car in the earlier authorized read-only audit (CarParams, Panda/AGNOS identity, staged update). |
| `COMMUNITY_SOURCE_ONLY` | MVL, sunnypilot, comma or Dom source code, DBCs and comments. |
| `SYNTHETIC_ONLY` | Offline models and tests in this repository. |
| `UNKNOWN` | No evidence of any class. |

## Conclusions

| # | Question | Conclusion | Class |
| --- | --- | --- | --- |
| P1 | Who owns ACC commands in stock operation? | The factory stack owns longitudinal control. The candidate keeps `pcmCruise=True` and `openpilotLongitudinalControl=False` in every configuration (lock-off test). Which ECU emits the command (MRR radar vs camera) is not established for the target. | ownership by the stack: `TARGET_PASSIVE_OBSERVED` (CarParams); emitting ECU: `COMMUNITY_SOURCE_ONLY` |
| P2 | ACC and CMBS share the front sensor | Honda's 2025 Accord Hybrid owner manual says the front sensor supports both ACC and CMBS. | `OEM_AUTHENTICATED` (functional text only) |
| P3 | Bosch-C CAN-FD bus and ECU boundaries | Dom/MVL assign PT, radar, camera and LKAS logical buses. The physical harness, the ECU on each segment and the frame owners are unverified. | `COMMUNITY_SOURCE_ONLY` |
| P4 | Longitudinal command semantics (accel, gas, brake request, standstill) | MVL `create_acc_commands` packs `ACCEL_COMMAND`, `GAS_COMMAND`, `BRAKE_REQUEST` and standstill fields from a community DBC. Meaning, units, limits and ECU reaction on the target are unknown. | `COMMUNITY_SOURCE_ONLY` |
| P5 | Brake and acceleration request integrity (counter, checksum, rates) | MVL implements a community checksum offset for extended IDs (BC-024). No authenticated algorithm, rate or timeout. | `COMMUNITY_SOURCE_ONLY` |
| P6 | Driver override and safe disengagement | Policy layer: modelled numerically (DRV-005: brake or gas withdraws in the same step, without latching; fault latches until rearm evidence). Physical behaviour (pedal priority in the PCM/VSA under an external command) is unknown. | policy: `SYNTHETIC_ONLY`; vehicle: `UNKNOWN` |
| P7 | Failure detection and recovery | F1/F2/F5 contracts reject MVL's update-count shortcuts (silence vs rejection, tick without reference, suppressed startup fault). Target fault behaviour and DTC side effects are unknown. MVL comments report `CRUISE_FAULT` from takeover-stream latency. | contracts: `SYNTHETIC_ONLY`; target: `UNKNOWN`; MVL report: `COMMUNITY_SOURCE_ONLY` |
| P8 | Consequence of the MVL alpha-long design for CMBS/AEB/FCW | MVL disables the radar's ACC by diagnostics so it can author look-alike frames. With P2, disabling the shared sensor's function plausibly removes CMBS/AEB/FCW, which MVL itself documents (`interface.py:52`: "WARNING: THIS DISABLES AEB!"). The exact loss boundary (whether FCW alerts or partial braking remain) is unknown. | loss expected: `COMMUNITY_SOURCE_ONLY` + `OEM_AUTHENTICATED` (P2); exact boundary: `UNKNOWN` |
| P9 | Safe return to factory control | F4 contract requires physical evidence at all five stages (request, safety accept, ECU acknowledgement, stock stream resumed, fault cleared). None exist. MVL's restoration is a constructed request only. | `UNKNOWN` (contract `SYNTHETIC_ONLY`) |
| P10 | Is a CMBS-preserving architecture technically feasible? | Yes, as a design class: stock-ACC set-speed modulation, where the factory radar keeps ACC and CMBS and openpilot only changes the set speed with cruise buttons (the sunnypilot ICBM pattern). In Dom's Panda Honda TX hook (`honda.h` force-cancel rule), a `0x296` frame on the button bus, or on bus 2 under the stock-MVL word, is blocked when controls are not allowed unless its button field is CANCEL (2). While controls are allowed, that rule places no restriction on the button value. Address, bus, length and relay checks still apply. So no new TX allowlist entry would appear to be needed. This is a permission fact about the existing safety code, not validation of the proposed behaviour. Not implemented: it is still vehicle-facing transmission of new behaviour, outside this campaign. Its authority is bounded by stock ACC, so it cannot deliver MVL-style braking authority. | feasibility: `COMMUNITY_SOURCE_ONLY` + Dom safety source; target behaviour: `UNKNOWN` |
| P11 | Can MVL's radar-disable architecture be qualified from source plus tests? | No. B1 needs `oem_authenticated` evidence for all four gates. Source, DBCs and synthetic passes cannot authorize command authority. | — |

## F1–F7 status after this round

| Finding | Status |
| --- | --- |
| F1 silence vs ownership | Offline contract in place (`classify_stream`, `RelayInference`); target unknown |
| F2 radar timing without reference | Offline contract in place (`TickReference`); target unknown |
| F3 fault-state forwarding | Documentation qualification; generic relay-malfunction test already covers it |
| F4 restoration uncertainty | Offline contract in place (`return_to_stock_established`); 0/5 stages evidenced |
| F5 raw vs filtered startup fault | Offline contract in place (`startup_fault_record`, `record_hides_fault`) |
| F6 DBC multiplexing limits | Unchanged: community DBC; no authenticated semantics |
| F7 cached lane metadata | Offline contract in place (`lane_metadata_consistent`) |

## New Stage 2 engineering

1. **Numeric brake-policy model** (`tools/trackb_research/brake_policy_model.py`, 48 tests). It covers DRV-001/003/005–010 together:
   - hysteresis, immediate meaningful brake and debounced release;
   - no brake entry on a positive request;
   - driver override, a bounded low-speed integrator, relaxation and a fault latch with explicit rearm;
   - requested vs corrected separation, one-sided brake fade and a near-zero speed tolerance.

   A seeded 20-run property sweep asserts: brake and propulsion are never both non-zero, outputs are bounded, the fade rate holds, and results are deterministic. An equivalence test shows the selection equals Dom's native classic-Bosch `update_honda_bosch_braking`.

   Each of 10 hand-made mutants (one per guard) is caught. During development the model itself was found to let the integrator hold the brake on through a positive request while the release debounce ran. It was fixed so a positive request only lets the brake fade.
2. **EPS status characterization** (BC-013, 18 cases, real CAN-FD parser, with an ALT_RADAR contrast case). This is installed-Dom behaviour, pinned.
3. **Isolation coverage**: `source_evidence_contracts.py` (added last round) and the new model are now in the stdlib-only import check.
4. **B5/B6** are recorded as `OWNER_DEFERRED / NOT_EXECUTED` in the register. The status still blocks the gate.

## Evidence request (to close B1)

| Gate | Exact evidence needed | Acceptable source |
| --- | --- | --- |
| B1-OEM-COMMAND-OWNERSHIP | ECU that emits ACC commands on the 2025 US Accord Hybrid; message list, field definitions, units, limits, rates, timeouts and integrity | Honda Service Information (ServiceExpress) electrical/network sections, or an OEM-authorized protocol specification for the exact VIN range |
| B1-CMBS-AEB-PRECEDENCE | Whether CMBS braking stays available when the radar's ACC function is suppressed or another node commands; arbitration priority | OEM system description / diagnostic manual |
| B1-CANFD-TOPOLOGY-ARBITRATION | Harness diagram for the camera, radar, PT and gateway segments; where the comma harness sits | OEM electrical wiring diagram |
| B1-OWNER-TRANSITION | Defined, recoverable return of ACC to the factory owner after an external controller withdraws, with fault and DTC behaviour | OEM documentation, then B5 bench corroboration |

Supporting target evidence (Stage 1, deferred) should be passive captures only, with provenance. No diagnostic transmission or excitation.

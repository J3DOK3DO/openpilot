# Track B17 — MVL-inspired architecture hazard record (2026-11-01)

**Status: OWNED_RISK_ACKNOWLEDGEMENT — NOT QUALIFIED_PASS.**

Scope is a pure, offline simulation of retained research IDs for a 2025 US Honda Accord 11G Hybrid (Bosch-C/CAN-FD). It does not alter the stock ACC, steering, CMBS, AEB, FCW, Panda policy, diagnostics, or vehicle traffic. It is not an installation, command-ownership, or operational-release approval.

## Owner acknowledgement and source boundary

The owner explicitly accepts, as a proposed-design hazard, that the separate community MVL-inspired alpha-longitudinal architecture would be expected to lose CMBS, AEB, and FCW. The upstream reference is `mvl-boston/opendbc` `sp-honda-dev-202608` at `3fec9a418a659de31d7b1f494193161697a35071`: its `values.py:157-159` warns of the loss; `interface.py:405-430` and `carcontroller.py:629-650` describe radar silence, fault/DTC pressure, and replacement-stream timing; and `honda.h:594-702` exposes a DEBUG-gated CAN-FD-long table. These are community source claims, not authenticated Honda authority.

This acknowledgement is a risk record only. It does not establish safe command ownership, braking behavior, protocol validity, stock recovery, or authority to disable any feature. In particular it does not authorize copying UDS disable behavior, an allowlist, a diagnostic request, a replacement stream, or any actuation logic.

The earlier owner acknowledgements for DEBUG Panda and the AGNOS 19.8.1 raw-hash mismatch remain research deviations only. They are not technical qualification, release firmware identity, or evidence that a physical target is safe.

## Architecture consequences and hazards

| Hazard / consequence | Why it matters | Current handling |
| --- | --- | --- |
| Loss of CMBS/AEB/FCW | No factory collision warning or automatic emergency-braking guarantee remains in the proposed alpha-long arrangement. | Explicitly accepted only as a hazard; no feature is disabled by this work. B1 CMBS/AEB precedence remains HOLD. |
| Controlled-transition failure | A gap, stale state, duplicate event, or timing mismatch during ownership transition could leave conflicting, absent, or faulted behavior. | Offline models classify stale/duplicate/silent-transition observations as unknown or withdrawn. No transition is performed. |
| Degraded redundancy | Removing/silencing a stock sensing or owner path would remove a layer that normally contributes to collision mitigation. | No redundancy claim is made. The factory path remains untouched in the repository and on any vehicle. |
| Brake-controller fault latch | The community source describes fault/DTC pressure; a brake/controller fault can persist or require a service/restart sequence. | Synthetic fault/restart latches withdraw and require explicit test-only rearm; this is not a recovery proof. |
| Unknown stock ECU recovery | Recovery after a fault, bus loss, relay condition, restart, or source silence is not authenticated for this target. | B1 owner-transition and topology/arbitration gates stay HOLD; B5/B6 are not evaluated. |
| Availability and driver override | Driver brake/gas, cancel, stale evidence, and unavailable stock ACC can invalidate any proposed path. | Offline simulations immediately withdraw labels on driver inputs and faults. This is not an override-performance claim. |

## Deliberately non-operational B17 architecture

`tools/trackb_research/mvl_retained_sim.py` accepts only caller-created symbolic observations. The BC-009..012 model labels fresh source-only stock ownership, relay ambiguity, unknown AEB state, and observed silent-transition failure. The BC-020..024 model classifies the words `hud`, `tick`, `mux`, `lead`, and `checksum` as source-claim metadata only. It contains no frame/payload/identifier, packer, checksum calculation, or schedule.

The DRV model has only test-symbolic `target_value` and `corrected_value` fields to preserve the analytical distinction requested by the retained register. Its output is a research classification and an abstract path label. It has no torque, acceleration-sensor, pedal, gas-channel, brake-channel, ECU, or transport output. A numerical zero is an analytical result only and is never converted into permission to transmit.

## Gate status

All four B1 authority gates remain **HOLD**:

| Gate | Status | Unresolved requirement |
| --- | --- | --- |
| B1-OEM-COMMAND-OWNERSHIP | HOLD | Authenticated target ECU producer/consumer, integrity, limits, faults, and arbitration. |
| B1-CMBS-AEB-PRECEDENCE | HOLD | Frame-level documented precedence, including activation/clear and conflict behavior. |
| B1-CANFD-TOPOLOGY-ARBITRATION | HOLD | Target routing, ownership, timing, relay segments, and recovery. |
| B1-OWNER-TRANSITION | HOLD | An independently justified, fault-tolerant authority transition and recovery arrangement; the proposed MVL architecture does not preserve factory CMBS/AEB/FCW, and accepting that loss does not validate takeover or restore. |

`B5-ISOLATED-BENCH` and `B6-CONTROLLED-VEHICLE` are OUT_OF_SCOPE / NOT_EVALUATED, not waived. Operational readiness is **NOT_ESTABLISHED**.

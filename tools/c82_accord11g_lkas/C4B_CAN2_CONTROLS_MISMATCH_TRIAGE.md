# C8.2 C4B — CAN2 interrupt and controlsMismatch offline triage

Date: 2026-11-15, **historical recordings only**; Comma disconnected. Sources: `tools/diagnostics/accord11g_20261113/c7_plus/C7_PLUS_ELM327_CAN2_STARTUP.md`, sanitized `c2_timeline_summary.json`, `C8_1_DECISION.md`, and copied Nov 14 C8.1 route.

## Observed historical fault window

| Approx. route time | Panda mode | Observations |
|---:|---|---|
| 17.063 s | elm327/1 | CAN2 interrupt rate ~760/s, total errors 0 |
| 18.076 s | elm327/0 | receive errors 121; total errors 0 |
| 19.076 s | elm327/0 | total errors 6,470; receive error count 127 |
| 19.576 s | elm327/0 | first recorded `interruptRateCan2` active event |
| 20.076 s | elm327/0 | CAN2 IRQ ~17,862/s; total errors 25,706 |
| 21.005 s | elm327/0 | total errors 35,221; fault persists |
| 22.019 s | elm327/1 | total errors 35,235; fault persists |
| 29.176 s | startup | first recorded `controlsMismatch` |
| 30.026 s | hondaBosch/80 | errors remain 35,235; fault persists |

The error burst **precedes the selection of HondaBosch/80** and overlaps ELM327/0 OBD CAN2 discovery. The 16,000/s interrupt threshold remains a critical safety check. Timing correlation does **not** establish causality, physical wiring failure, bitrate mismatch, or a firmware defect.

## Existing safety-preserving response

C8.1 implemented strict Honda bus-0 identification with 4.5-s spaced retries and HOLD/MOCK for incomplete identification, avoiding the old OBD mux sweep for a matching Honda signature. It does not prove the electrical root cause is fixed. This code must remain fail-closed; do not re-enable CAN2 diagnostic transmissions, suppress `interruptRateCan2`, clear faults to force engagement, alter Panda bitrate/OBD mux or waive `controlsMismatch`.

The Nov 14 route (different recording) identifies `HONDA_ACCORD_11G`, AE32, `hondaBosch/80`; in selected decoded data it did not show a synchronized request/permission mismatch. That does not disprove the earlier startup fault; compare exact route and firmware identity before extrapolating.

## Offline hypotheses to investigate later (not verified facts)

- CAN2 OBD mux or harness pin/transceiver state during ELM327 param 0 startup.
- FDCAN2 error-interrupt storms, nominal/data-bit timing, bus termination, grounding or physical harness interaction.
- Mode transition and firmware timing; lingering Panda fault after switching back to normal mux.
- `controlsMismatch` resulting from earlier fault/host state mismatch rather than an independent steering-tuning defect.

## Hardware evidence required when available

Collect **passive, separately approved** logs with exact Comma/Panda firmware SHA, model/fingerprint, harness and Panda board revision, OBD-mux state, orientation, nominal/data CAN timing, FDCAN2 last-error/bus-off state, RX/error and IRQ deltas at one-second resolution through cold/warm startup. Correlate fault timestamps with `pandaStates`, `CarParams`, steering status and `selfdriveState`. Stop on active Panda safety fault, unexpected CAN2 traffic, invalid RX, or controlsMismatch. No CAN injection or bypass.

## Offline validation in Campaign 4B

The pre-existing focused evidence test `tools/diagnostics/accord11g_20261113/c7_plus/test_can2_evidence.py` was rerun successfully (**1 passed**). It validates sanitized evidence parsing; it does **not** validate live CAN electrical behavior.

**Disposition:** EXTERNAL/HARDWARE EVIDENCE REQUIRED. Cannot close physical CAN2 root cause or vehicle-control mismatch with software-only simulation.

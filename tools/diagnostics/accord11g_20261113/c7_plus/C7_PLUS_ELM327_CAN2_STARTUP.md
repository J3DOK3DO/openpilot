# C7+ ELM327 CAN2 startup trace — offline, 2026-11-13

Source: sanitized schema 3 `../c2_timeline_summary.json`, route 0 `windows` and first-event fields. Times are route monotonic seconds, approximate sampled states; a transition can occur between samples. No raw route was copied or device contacted.

| Time | Safety model/param | CAN2 observations |
|---:|---|---|
| 17.063 | elm327/1 | IRQ0 760/s, totalErrorCnt 0, no active fault |
| 18.076 | elm327/0 | receiveErrorCnt 121, error warning/passive, totalErrorCnt 0 |
| 19.076 | elm327/0 | totalErrorCnt 6,470; receiveErrorCnt 127 |
| 20.076 | elm327/0 | IRQ0 17,862/s, totalErrorCnt 25,706, `interruptRateCan2` active |
| 21.005 | elm327/0 | totalErrorCnt 35,221, fault active |
| 22.019 | elm327/1 | totalErrorCnt 35,235, receive error 0, fault remains active |
| 30.026 | hondaBosch/80 | totalErrorCnt still 35,235, fault remains active |

First active `interruptRateCan2` event is approximately 19.576 s; first `controlsMismatch` is approximately 29.176 s. The error burst coincides with the initial ELM327/0 OBD CAN2 discovery window and predates Honda safety selection. The Hybrid eligibility qualifier runs at the car profile layer and cannot remedy this earlier Panda fault. A sampled IRQ rate includes RX and error interrupt work; these samples do not establish wiring, nominal bitrate, data bitrate, pin mux, or error IRQ causality. `faultTemp` can persist after the instant rate falls; active fault fields establish the sampled fault state.

Source comparison: current `panda/board/main.c` and original C7 `e997a36ac2:panda/board/main.c` both choose `CAN_MODE_OBD_CAN2` for `SAFETY_ELM327` param 0, then call `can_init_all()`. Current Red board mode switches FDCAN2 pins/transceiver by mode and harness orientation. Current `panda/board/drivers/fdcan.h` maps FDCAN2 IT0 to `can_rx(1)` with the `CAN_INTERRUPT_RATE` fault registration; original C7 has the same handler/rate contract. Current H7 rate is 16,000/s; `can_common.h` defaults to 500 kbps nominal and 2 Mbps data (values stored in 100 bps units). The later power-save/reinit guards and tracking changes have no demonstrated correction for this burst. Original C7 F8 deferred `interruptRateCan2` qualification.

A separately authorized, parked-only evidence capture should record exact board, harness, and firmware identities; harness orientation and OBD mux state; configured and measured nominal/data timing; transceiver power state; CAN2 error-warning, passive, bus-off, last-error, receive-error and core-reset fields; and per-second IT0/IT1, RX, and error counter deltas through initial discovery. An electrical integrity and termination inspection by qualified personnel would help interpret those measurements. No CAN injection, safety-fault reset, watchdog change, bitrate change, or controller command is justified by this trace.

**Disposition: OFFLINE CANDIDATE / VEHICLE HOLD.** The CAN2 startup fault is unresolved. This is timing evidence, not a physical or native Card qualification.

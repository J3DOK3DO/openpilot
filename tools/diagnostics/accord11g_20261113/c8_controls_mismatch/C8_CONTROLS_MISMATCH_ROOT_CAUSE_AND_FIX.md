# C8: Accord 11G Hybrid (Bosch CAN-FD) `controlsMismatch`. Root cause and fix

> **Superseded in part by C8.1** (`../c8_1/C8_1_DECISION.md`): strict bus-0 FW query and fail-closed HOLD replace the C8 OBD fallback.

Date: 2026-11-13. Base: installed Dom `7e6d08187b`, plus diagnostic commits and Codex
`05300cf1e7` (Hybrid AOL qualifier) and `737a40d32` (LKAS queue guards).
Evidence: the 2026-11-12 route logs (83 segments, 3 routes), decoded offline.

## 1. Causal chain (all links observed in logs or source)

| # | Link | Evidence |
|---|------|----------|
| 1 | On every ignition, card runs the generic all-brand discovery and muxes Panda CAN2 onto the OBD port (`SAFETY_ELM327` param 0 → `CAN_MODE_OBD_CAN2`). | Logs: `Setting OBD multiplexing to True` on 3/3 routes; pandaStates `elm327/0` at about 18–21 s. `car_helpers.fingerprint()` final `else` branch. |
| 2 | Nothing answers on that OBD path. The VIN query retries and fails; no muxed FW request gets a response. | `vin query retry (1)/(2)`, `vin_rx_addr -1`, VIN `000…0`. Both FW responses (`fwdRadar` 0x18dab0f1, `fwdCamera` 0x18dab5f1) came from the **bus 0** request. |
| 3 | While muxed, CAN2 goes error-passive (REC 121→127, `bit0Error`, RX = 0) and accumulates about 35,000 protocol errors in about 3 s. | Route 0: 0 → 35,235. Route 1 (same boot): 35,235 → 70,778. Route 2 (fresh boot): about 35,438. **The burst recurred on all three recorded discovery starts (two in one Panda boot, one after a fresh boot).** |
| 4 | That burst drives the FDCAN2 IRQ rate right up to the 16,000/s watchdog. The peak sits near the limit. Three starts do not establish a failure probability. | Peaks: route 0 **17,862/s (tripped)**, route 2 **14,139/s (did not)**. |
| 5 | `FAULT_INTERRUPT_RATE_CAN_2` is latched: the Panda firmware never calls `fault_recovered()` for IRQ-rate faults. It clears only on a Panda reset (reboot). | `panda/board/drivers/interrupts.h:76`. `fault_recovered` is only used for the relay. Route 1 inherited route 0's fault without a reboot. |
| 6 | Dom 7 (from 2026-10-27, `5fc5709e4d`) turns any active Panda fault into `controlsMismatch` unless `_diagnostic_mask()` exempts it. The Honda exemption covers only `CLASSIC_BOSCH`/`RADARLESS`, **not `HONDA_ACCORD_11G`**. | `openpilot/starpilot/aol/panda_faults.py`, used at `selfdrived.py:516`, `card.py:1403` and `transport_pause.py:46/900`. The AOL native-receipt path is blocked as well. |
| 7 | C6-12 (road-tested LKG) had the same OBD-mux discovery, but upstream fault semantics: faults never raised `controlsMismatch`. The storm was probably present there too. C6-12 did not gate engagement on it, but a latched Panda safety fault is not thereby harmless. | C6-12 `selfdrived.py:653` and `car_helpers.py:279`. |

So the Hybrid AOL fix (`05300cf1e7`) was necessary, but it could never clear the mismatch: the fault happens
about 10 s **before** Honda safety is selected. Codex's conclusion that "the CAN2 cause is unresolved / hardware" was
too pessimistic. The trigger is a software discovery step that collects no identity evidence on this car.

## 2. Fix applied: Honda normal-bus discovery (root cause, no safety relaxation)

This is the same pattern the fork already uses for Ford/GM/Tesla/Volvo-Polestar. The Ford comment in `car_helpers.py`
already says that *"the unrelated all-brand OBD mux scan can produce a CAN2 error/interrupt storm"*.

* `opendbc/car/honda/discovery.py` (new). A passive layout probe: Honda PT/camera 0x14A/0x18F/0x17C/0x158 on buses 0 and 2,
  plus the 11G CAN-FD frames 0x601 (48 B) and 0x603 (32 B) on bus 1. All were present within 0.5 s of first CAN on 3/3 routes.
* `opendbc/car/ford/discovery.py`. `normal_bus_query_brand()` gains a `honda_probe`, checked last, in the same shared 120 ms passive window.
* `opendbc/car/car_helpers.py`. When the probe matches: mux stays **False**, VIN is queried on bus 0, and FW comes from
  `get_fw_versions(query_brand='honda', normal_bus_only=True)`. That drops only the OBD-muxed bus-1 requests, which got no answers.
  **Fail-safe:** unless the firmware matches exactly `{HONDA_ACCORD_11G}`, discovery falls back to the original OBD sweep.
  Other Hondas, or a device moved to another car, keep today's behaviour.

Unchanged: the Panda firmware, the 16,000/s watchdog, `panda_faults.py` and the `controlsMismatch` gating, safety words,
CarParams construction, and AOL qualification. A test asserts that `interruptRateCan2` still **blocks** for this CP.

## 3. Verification (host, offline)

* `honda/tests/test_accord11g_normal_discovery.py`: 59 passed. It is driven by the real recorded pre-query window,
  fingerprint frames and FW responses (`testdata/accord11g_startup_discovery.json`, no VIN). The tests check that:
  * the mux is never set True. (**Superseded by C8.1:** the claim "every TX is on bus 0" held only because `get_fw_versions` was mocked; the production filter still sent the bus-1 non-mux request.)
  * the CP equals the old OBD-sweep CP (fingerprint, flags incl. HYBRID|BOSCH_CANFD, safety configs, pcmCruise, delays);
  * unconfirmed or foreign FW falls back to the OBD sweep;
  * every layout defect (missing/length/bus/echo/contradiction) rejects the probe;
  * the fault policy stays blocking.
* Mutation check: removing the probe → 3 failures. Removing the fallback → 2 failures.
* Regression results are in `C8_VERIFICATION.md`.
* **Not verified:** native Card/pandad on device, and a real drive. See §5.

## 4. Assessment of Codex's work

| Item | Verdict |
|------|---------|
| Diagnostics C1/C2/C2A (timeline, counter correction) | Sound and useful. The corrected counters are what reveal the per-boot burst. |
| `05300cf1e7` Hybrid flag in `accord_mvl_stock.qualified()` | Correct and narrow. Safety word stays 80/81, stock ACC is still required. This is what fixed AOL. |
| `737a40d32` LKAS pulse-queue withdrawal guards | Acceptable. The AOL (`altExp 32`) path already sent no pulses with ACC off, so ACC-off lateral is not affected. Codex adapted the existing cadence test by adding `POWERTRAIN_DATA.ACC_STATUS`; the new contract is "button substitution only while PCM cruise is engaged". |
| "CAN2 fault is physical / unresolved" | Superseded. The trigger is the OBD-mux discovery step (§1). The physical reason the OBD path doesn't answer, and whether a comma power / OBD cable is connected, is still open, but it is no longer on the engagement path. |
| Missed by Codex | `_diagnostic_mask()` excludes the 11G, VIN-unknown defeats the CarParams cache, C6-12 never gated on faults, and the fork already had a fix pattern for this storm. |

## 5. Deploy and confirm (parked first)

1. Install a build containing `05300cf1e7`, `737a40d32` and this commit. These are pure-Python files, so no SCons rebuild is needed for them.
2. Parked, ignition on: in the new route, `Setting OBD multiplexing to True` must be **absent**, pandaStates must never show
   `elm327` param 0, CAN2 `totalErrorCnt` must stay flat during discovery, `fingerprinted` must show `HONDA_ACCORD_11G` with `source fw`,
   and `Honda normal-bus discovery unconfirmed` must be absent.
3. No `interruptRateCan2`, no `controlsMismatch`. Repeat across at least 5 cold boots and several warm starts. Any recurrence is a STOP; preserve the logs.
4. If step 2 shows the fallback line, the FW differed. Capture the `fingerprinted` log and extend the identity check; do not widen the exemption.

## 6. Optional fallback (not applied)

If a CAN2 IRQ fault still appears **after** this fix, the cause is on the drive bus, not discovery, and it must stay blocking.
Only if it can be shown to originate before Honda safety selection would one consider adding `HONDA_ACCORD_11G` to the Honda
branch of `_diagnostic_mask()`, matching the existing CLASSIC_BOSCH/RADARLESS exemption. Not recommended without new logs.

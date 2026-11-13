# Accord 11G Hybrid C7+ source recovery — 2026-11-13

**Disposition: OFFLINE CANDIDATE / VEHICLE HOLD.** Source baseline was `9b7ca0926b3a50fb68766c343d10de2956df8165` on the requested isolated branch; installed Dom remains `7e6d08187b17085729851c939047cd44088b36b8`. No device, CAN, firmware, Params, or GitHub operation was performed.

## Provenance and applicability

Status means comparison to installed `7e6d081` source, not evidence that hardware works. Dates are commit dates or document dates. Oct C7 and Nov MVL Campaign 7 are distinct.

| Source / date | Path or report | Candidate effect and evidence | Status |
|---|---|---|---|
| `e997a36ac2`, Oct 17; `83053b1782`, Oct 17 | `docs/c7/*`, Panda, Honda | Original C7 F8 merged mid-Oct Dom. F8.3/F9 reports 13 ARM64 components, host tests and Honda archive preparation; report explicitly deferred `interruptRateCan2` and withheld release. No tested CAN2 over-rate correction found. | UNVERIFIED for CAN2; NOT_APPLICABLE as drop-in fix |
| `48bd4c1d88`, Oct 14 | `docs/C7_ENGINEERING_BASELINE_2026-10-14.md` | Nine-stage C7 safety/release gate from C6-12; no driver patch for this failure. | NOT_APPLICABLE |
| `3e7b035b2d`, Nov 1 | `opendbc_repo/opendbc/car/honda/accord_mvl_stock.py`; Hybrid qualification tests | Adds only `HYBRID` to Accord's allowed detected flag mask. Historical tests cover words 80/81, native profile and negative flags. Not ancestor of installed Dom; current source still rejected actual flags 2180. Recreated with current tests. | MISSING_PROMISING → recovered offline candidate |
| `291ceea777`, Nov 1 | Accord investigation/report | Recorded actual Hybrid CP and absent AOL marker despite setting. Establishes diagnostic provenance, not a safety receipt. | PRESENT_EQUIVALENT as evidence only |
| `61323fdf0c` / `5fa8b2ed8c`, Oct 30–Nov 1 | `accord_mvl_stock.py`, interruption tests | Clears queued synthetic LKAS pulses on physical/control withdrawal. Installed file has a return guard for marked brake/cruise and ordinary control cancel but does **not** clear the queue; therefore not semantically equivalent. Further camera-button ownership tests and review needed before a separate change. | MISSING_PROMISING / HOLD, not included |
| `68f13877e4`, Nov 12 | `opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py` | EPS and driving-gear boundary test coverage only; ancestor of installed source. | PRESENT_EQUIVALENT |
| `2567a32f70`, Oct 28; `e0f8b7a118`, Nov 9 | `panda/board/drivers/fdcan.h` | Retain power-save state on CAN reinit/error recovery. Current source contains these guards. No measured causal link to route 0 spike. | PRESENT_EQUIVALENT; CAN2 effect UNVERIFIED |
| C7 F8 versus current, Oct–Nov | `panda/board/drivers/{fdcan,can_common}.h`, `stm32h7/llfdcan.h`, `stm32h7_config.h`, `boards/red.h`, `panda/python/__init__.py`, `openpilot/selfdrive/pandad` | C7 and current keep `FDCAN2_IT0 -> can_rx(1)`, 16,000/s registration, 500 kbps nominal / 2 Mbps data default and RX/error IT0 handling. Current has power-save and register/config tracking changes, but no evidence they suppress this observed excess. Red board pin mux and pandad OBD startup merit parked inspection. No safe one-line rate correction identified. | CAN2 MISSING ROOT CAUSE / UNSAFE_HOLD for runtime tuning |
| C6-12 `7b4db9a260`, Oct 6 | Panda IRQ/fault contract | Same 16,000/s rate/fault mapping in existing offline checker; historical road use does not qualify current Panda or explain spike. | PRESENT_EQUIVALENT contract; cause UNVERIFIED |
| Nov 8 MVL Campaign 7 | `/mnt/commadrive/MVL_C7_CODEX_PATCH_20261108`, `/mnt/commadrive/MVL_C7_CROSS_REVIEW_20261108` | Separate display/offline campaign and HOLD material. No identified CAN2 or Hybrid runtime correction for this checkout. | NOT_APPLICABLE |

This is a bounded inventory of named branches, changed driver files, and supplied reports, not an exhaustive audit of all Git objects or raw logs. Original C7's G01–G07 work had testing and quarantined safety work but no demonstrated correction for the November 12 CAN2 fault. Some remote Git blobs were unavailable locally; no network fetch was attempted.

## Exact recovered source change

`qualified(cp)` permits `HondaFlags.HYBRID` alongside the previously permitted detected flags. Its fingerprint, Honda brand, ordinary transmission, stock PCM cruise, no openpilot longitudinal, safety model `hondaBosch`, exact word `80 | ALT_BRAKE` (80/81), single safety config, and alternatives 0/32 remain unchanged. `stock_aol.qualified(marked_only=True)` still requires 32; `native_accepts_cp` still checks the exact native safety model/word. Neither the source edit nor tests set vehicle Params or manufacture a native lateral grant. Actual Card policy may add 32 only through its existing authorized lifecycle. The Hybrid flag's direct carstate effect is selecting `HYBRID_BRAKE_ERROR` instead of `STANDSTILL`.

The source diff is limited to one explanatory comment and the OR of `HondaFlags.HYBRID` in the allowed mask. Historical test logic was brought forward and extended for nonhybrid parity, bad CP fields, exact native model/word, brake withdrawal and LKAS button output. No Panda, safety word, steering actuation, longitudinal, IRQ, fallback or heartbeat source changed.

## CAN2 root cause and safety decision

The decoded route 0 has six raw samples above 16,000/s in two one-second buckets, peak 17,862/s, first active `interruptRateCan2` at 19.575839471 s and first sampled over-limit rate at 19.676046137 s. First `controlsMismatch` was around 29.175884571 s, and 2,603 mismatch event-message occurrences followed. Route 1 starts with active fault but no sampled over-limit rate; route 2 lacks the fault and enabled with stock ACC. `faultTemp` is sticky; only active faults establish current state. Existing `C2_FINDINGS.md` and `C2_TIMELINE.md` retain the bounded, read-only aggregation and timing caveats.

IT0 includes RX and error handling, so the rate alone cannot distinguish actual frame load from repeated error interrupts. Historical C7 does not resolve this. Changing bitrates, pin mux, IRQ clearing, startup safety mode, OBD mux, or the 16,000/s watchdog without bus/error evidence could mask or worsen a real electrical fault. No Panda runtime correction is justified in this branch. The active Panda fault and controls mismatch remain engagement blockers even if Hybrid eligibility is corrected.

The read-only `can2_evidence.py` projects the existing full-snapshot summary without re-decoding raw logs. Observed CAN1 counter deltas include route 0 RX 830,103 / errors 35,235 / core resets 5, route 1 RX 15,358 / errors 35,543 / resets 5, and route 2 RX 2,831,533 / errors 35,437 / resets 5. Route 2 has no active rate fault despite similar error-counter delta, so these aggregates alone do not establish repeated error IRQs as the spike cause. Counter epochs and route durations differ; this is not a normalized error-rate comparison.

Parked, separately authorized hardware evidence needed before any future release decision: exact Panda firmware and board/harness identities; CAN1/FDCAN2 physical mapping and OBD multiplex state; nominal/data timing and transceiver power state; sampled IT0/IT1 rate with RX count and error/bus-off/overflow deltas from startup; electrical integrity/termination and harness seating checked by qualified personnel; reproducibility with stock ACC on/off; native receipt and withdrawal traces, controlsMismatch and Panda active faults all clear under the unchanged safety rules. These are evidence requirements, not instructions to bypass a fault or transmit CAN.

## Secondary observations

The single route 2 `carOutput` `not_alive` event at 27.428 s has messages on both sides and running `card`; no persistent crash is established. UI 25–32 FPS warning is from UI render timing, not demonstrated camera/model loss. GNSS NACK/almanac errors are logged separately. No evidence connects these to FDCAN2 or justifies cherry-picking performance code. See `../C2_FINDINGS.md`.

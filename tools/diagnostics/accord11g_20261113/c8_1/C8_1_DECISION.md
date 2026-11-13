# C8.1: strict bus-0 identification and fail-closed hold. Evidence and GO/NO-GO

Date: 2026-11-13. Installed base: Dom `7e6d08187b`. Commit chain on branch `accord11g-dom7-c8-1-strict-bus0-hold-20261113`:

| Commit | Content |
|---|---|
| `05300cf1e7` | Hybrid flag admitted in the stock-MVL AOL qualifier (recovered AOL fix) |
| `737a40d32` | LKAS pulse-queue withdrawal guards (recovered) |
| `e95115dbf` | C8: passive Honda normal-bus signature, no OBD mux on match |
| `219b108ae` | C8.1: strict bus-0 FW query, IDENTIFIED / OTHER / HOLD |
| `161aaed65` | C8.1: independent-review fixes (spaced retries, hold ordering, attribution) |

The exact head of the installation artifact is in `evidence/C8_1_DEPLOY_20261113/IDENTITY.txt`.
This responds to `evidence/C8_INDEPENDENT_CHATGPT_ASSESSMENT_20261113.md`.

## 1. What changed

| Review gap | C8 | C8.1 |
|---|---|---|
| 1. Bus-1 FW query under normal wiring | `normal_bus_only=True` kept Honda `Request(bus=1, obd_multiplexing=False)` and **sent UDS on CAN2**. This is reproduced in a test against production code. | New kw-only `get_fw_versions(request_buses=frozenset({0}))`; its default `None` leaves every other caller unchanged. On the Honda-signature path every diagnostic TX is on **bus 0** and the mux is never touched. |
| 2. OBD fallback after incomplete FW | Anything other than exact `{11G}` re-ran the storm-producing OBD sweep. | Bus-0 attempts every 0.5 s until 4.5 s after discovery start (at least 2, at most 10), each logged as `honda_normal_bus_attempt`. Outcomes: **IDENTIFIED** (exact 11G); **OTHER** (only purely foreign FW evidence → original OBD sweep, unchanged for those cars); **HOLD** (missing, unknown, or any 11G evidence including an ambiguous `{11G, X}` → no mux, `car_fingerprint=None` → MOCK, no engagement). HOLD is applied after every automatic refinement. |

Why the 4.5 s deadline: the recorded replies came from the old sweep's bus-0 request about 2–4 s into discovery. A
back-to-back retry at about 1.6 s (the first C8.1 version) could HOLD a car whose ECUs were simply not awake yet (review M1).

Not changed: Panda firmware, the 16,000/s IRQ watchdog, `panda_faults.py`, `selfdrived`, `card.py`, `transport_pause`,
`controlsMismatch` gating, safety models and words, CarParams construction, AOL qualification. `git diff --name-only 737a40d32..HEAD`
lists no panda, safety, selfdrived or card files.

## 2. Test evidence (Ubuntu x86 host, offline, no device)

`honda/tests/test_accord11g_c8_1_transport.py` runs **production** `get_fw_versions` → `IsoTpParallelQuery` → `uds`, `get_vin`,
`get_present_ecus`, `get_fw_versions_ordered` and `get_car`. None of them is mocked. They run against a transport-level ISO-TP ECU
simulator: the recorded radar 0x18dab0f1 and camera 0x18dab5f1 answer `22 F1 81` on bus 0, with first frame / flow control /
consecutive frames and tester-present; ECUs can be late, silent, silent for N attempts, or not awake until time T. A virtual clock
advances 10 ms per receive.

| Area | Covered |
|---|---|
| Gap 1 | The C8 call shape sends on {0,1}; C8.1 sends on {0} with zero mux calls and returns the exact recorded FW. |
| Timing | First frame at 20/80 ms is answered, at 130/500 ms it times out (production 0.1 s). ECUs waking 2 s in → IDENTIFIED, with no mux, end to end. The pre-review back-to-back retry would have missed them (regression guard). A camera consistently 200 ms late → HOLD after the deadline. |
| Missing / mismatched ECUs | Radar silent, camera silent, both silent, unknown camera FW, ECUs waking after the deadline, mixed 11G radar + CR-V camera, ambiguous `{11G, CRV_6G}` → HOLD, bus 0 only, no sweep. |
| Fail-closed | A legacy-Honda CAN-fingerprint candidate under HOLD is still MOCK. An explicit `FINGERPRINT` or saved vehicle selection overrides HOLD (existing semantics) and still never muxes. |
| Cache | A MOCK cache and an 11G cache with VIN_UNKNOWN are never reused; fresh bus-0 identification runs. |
| Other Hondas / brands | CR-V 6G FW behind the same signature → OTHER → original sweep → `HONDA_CRV_6G`. Without the signature, the original OBD sweep is unchanged. |
| Passive window | The recorded window matches under the advancing clock. A signature split across batches matches. Completion after 120 ms is rejected. Malformed DLC is rejected. No CAN → bounded, no match. |
| Cross-brand | 11 non-empty GM/Hyundai/Volvo captures never match the Honda signature (the corpus is asserted non-vacuous). No earlier probe claims the Accord capture. |
| Safety policy | `interruptRateCan2` still blocks for the identified CP. |

Results:
* C8 + C8.1 modules: **118 passed**.
* Mutation checks, all caught:

  | Mutant | Failures |
  |---|---|
  | M1: no strict bus 0 | 21 |
  | M2: HOLD → OBD sweep | 13 |
  | M3: HOLD keeps the CAN-only identity | 1 |
  | M4: no retry | 15 |
  | M5: no OTHER | 3 |
  | M6: pre-review back-to-back retry | 3 |
  | M7: 11G evidence may sweep | 19 |
* Recovered AOL suites (Hybrid qualifier, interrupt v4, stock-MVL, stock AOL): **361 passed**. 24 Card cases were deselected (native `msgq`).
* Offline diagnostic suites (16 + 1): OK.
* Broad sweep (every brand discovery test, `ford/tests`, `car/tests` using car_helpers/fw_versions, all `honda/tests`, `-k 'not card'`):
  **196 failed / 5544 passed, identical node IDs to the pre-C8 baseline. 0 new failures.** The 196, plus 12 collection errors,
  need ARM-native `msgq` / `libparams_c.so`.
* `git diff --check`: clean.

## 3. Independent review (fresh-context reviewer on `219b108ae`)

No CRITICAL or HIGH findings.

| Finding | Disposition |
|---|---|
| M1: the retry ran about 2.5 s earlier than the recorded replies, so a cold ECU → HOLD/MOCK | **Fixed** in `161aaed65` (spaced retries to 4.5 s), with an end-to-end test and mutant M6. |
| M2: other Honda CAN-FD cars | Known FW → OTHER → unchanged outcome, about 1.5 s slower. Unknown FW → MOCK, the same as the installed build (no Honda legacy CAN fingerprints; fuzzy matching excludes camera/radar). If their ECUs answer only via OBD, they HOLD. **Accepted and documented:** no data exists for those cars here. |
| L1: a saved vehicle selection overrides HOLD | **Documented and tested.** These are existing forced-selection semantics, and the mux is still never used. With VehicleSelection = Auto, HOLD means MOCK. |
| L2: HOLD ran before the Bolt refinement | **Fixed**: HOLD is now applied last before the explicit overrides. |
| L3: one foreign reply flipped a real 11G to OTHER (sweep) | **Fixed**: OTHER only for purely foreign evidence. |
| L4: a MOCK boot resets learned parameters on the next boot via CarParamsPrevRoute | Existing behaviour for any MOCK boot, and not identity cache poisoning. **Documented.** |
| L5: test vacuity and missing cases | **Fixed**: non-vacuous corpus, plus the new cases above. |
| The cumulative diff also carries `05300cf1e7`/`737a40d32` (AOL) | These were reviewed earlier in C8 (assessment §4), not in this pass. Their limits are in §4.4 below. |

The reviewer also confirmed:
* `honda_hold` is defined on every path.
* The only `set_obd_multiplexing(True)` reachable after a Honda signature is in the OTHER branch.
* There is no startup deadline at risk: pandad waits on `FirmwareQueryDone` without a timeout, and the panda stays in ELM327 param 1 throughout.
* The passive probe is evaluated last.

## 4. Open evidence. These block release

1. **Target-native (comma four, ARM64):** Card/pandad, `msgq` and `libparams_c.so` paths are not executed. That is 24 Card cases plus 196 startup tests.
2. **Parked hardware:** there is no on-car run of C8 or C8.1. Real ECU wake time with the mux off, the passive window against the real
   card start, and discovery duration are all unverified.
3. **Physical CAN2 cause:** why the OBD-port path errors (wiring, termination, CAN-FD timing, harness) is unknown. C8.1 avoids the trigger; it does not explain it.
4. **Independent lateral with OEM ACC off:** `05300cf1e7`/`737a40d32` are offline-tested only. No logged sustained native AOL grant,
   Card intent, Panda permission and steering state exists, and a latched CAN2 fault would still block regardless.
5. **Other Honda CAN-FD cars** matching the signature are not exercised on real hardware (see M2).

## 5. Decision

| Scope | Decision |
|---|---|
| Release / road / public-road steering | **NO-GO.** Items 4.1–4.4 are open. |
| Offline source candidate (Gap 1, Gap 2, review findings) | **Complete.** All tests pass with no regressions, and Panda safety is untouched. |
| Next gate A: target-native, non-actuating | **READY.** Run the Honda/discovery/Card suites from this exact commit in a separate ARM64 checkout. Do not touch the live install. |
| Next gate B: parked, immobile diagnostic qualification | **Only after gate A passes.** Use the exact-commit procedure in the deploy README, then repeat cold and warm starts. **STOP on any of these:** `Setting OBD multiplexing to True`, `elm327` param 0, any bus-1 diagnostic TX during discovery, CAN2 `totalErrorCnt` rising during discovery, IRQ ≥ 16,000/s, any active fault, `Honda normal-bus identification hold`, a fingerprint other than `HONDA_ACCORD_11G` / `fw`, or `controlsMismatch`. Preserve the logs on any STOP. |
| Closed-course AOL with ACC off | **Only after gate B passes and a native safety review.** |

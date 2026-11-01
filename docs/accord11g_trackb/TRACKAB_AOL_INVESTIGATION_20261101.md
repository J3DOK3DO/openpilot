# Accord 11G Hybrid: Always On Lateral investigation (2026-11-01)

Symptom (owner): `AlwaysOnLateral=1` on installed Dom `5b0f81ca`, but AOL does not work.

## Status

| Item | Status |
| --- | --- |
| Root cause | **VERIFIED in source and reproduced synthetically**; consistent with the car's own recorded CarParams |
| Source correction | **REQUIRED and applied** (one line, `accord_mvl_stock.qualified`) |
| Offline tests | **PASSED** (new hybrid tests; full Card→controls→native→libsafety lifecycle for the hybrid) |
| Device / vehicle confirmation | **PENDING** (nothing installed; no drive performed) |

## Read-only evidence

- Params backup (private, 2026-11-01): `AlwaysOnLateral=1`, `PauseAOLOnBrake=0.0`, `DisengageOnAccelerator=0`.
- `CarParamsPersistent` and `CarParamsPrevRoute` (Dom `SPCACHE` envelope, status valid, decoded locally; VIN not read
  out): `HONDA_ACCORD_11G`, FW fingerprint, automatic, `hondaBosch` word 80, `pcmCruise=True`,
  `openpilotLongitudinalControl=False`, PID lateral, **flags `BOSCH|BOSCH_CANFD|HYBRID`**,
  **`alternativeExperience=0`**. With those CarParams: `accord_mvl_stock.qualified=False`,
  `stock_aol.qualified=False`.

## Authorization path (candidate source)

1. `card.py` → `aol_policy_for(CP)` → `starpilot/car/honda/aol.py:policy_for` → `stock_aol.qualified(CP)`.
2. `stock_aol.qualified` for `HONDA_ACCORD_11G` returns `accord_mvl_stock.qualified(CP)` (experience 32 is already
   enforced at its top when `marked_only=True`).
3. `accord_mvl_stock.qualified` rejected any flag outside the 11G config flags plus `BOSCH_ALT_BRAKE`,
   `BOSCH_EXT_HUD`, `HAS_BSM`. **`HYBRID` (set when `0x184 HYBRID_BRAKE_ERROR` is present) was missing.**
4. Result on the Hybrid: policy `intent_supported=False`, so `Card.aol_qualified=False`, `aol_card_intent=None`, no
   experience 32, no `honda_stock_aol` enable in Panda (it requires experience 32), no independent lateral.
5. The same qualifier gates `CarController.accord_mvl_stock`, so the Track A camera-button controller (BC-025/026)
   was also never instantiated on this car under installed Dom.

`HYBRID` only changes which message `carstate` reads for `accFaulted` (`HYBRID_BRAKE_ERROR` instead of
`STANDSTILL`); it changes no ownership, safety word or TX table. Every other Honda CAN-FD stock platform already
admits its hybrid variant (`test_canfd_stock_aol_parity.py`, `test_stock_aol.py`); the 11G was the exception.

## Correction

`opendbc_repo/opendbc/car/honda/accord_mvl_stock.py`: add `HondaFlags.HYBRID` to the admitted flag set. No Panda,
DBC, TX-table, safety-word or steering change.

## Tests

- `opendbc/car/honda/tests/test_accord11g_hybrid_aol_qualification.py` (13): device-equivalent hybrid CarParams
  qualify for words 80/81 in every alpha/release combination; Honda AOL policy adds experience 32 and the native
  receipt accepts word 80 only; `marked_only` still requires 32; `CarController.accord_mvl_stock` exists for the
  hybrid; passive/dashcam/notCar, other words, other flags and openpilot long are still rejected.
- `openpilot/starpilot/aol/tests/test_honda_canfd_lifecycle.py`: two new hybrid cases (words 80 and 81) through the
  real Card, controls, native C++ negotiation and libsafety: AOL latches, `latActive` with accepted torque TX while
  stock cruise is **off** (ticks 79/105/135), withdrawal on brake/fault/reverse.
- Mutation: removing `HYBRID` again fails 11 qualification tests and both lifecycle cases with
  `Card.aol_card_intent is None` (the field symptom).

## Track A interaction

`AccordMvlStock.update` returns nothing and clears a queued synthetic LKAS press whenever stock cruise is off, the
brake is pressed, `LKAS_READY` drops, controls disengage, or cancel/resume is requested. It only governs the
synthetic SCM_BUTTONS stream to the camera; STEERING_CONTROL is produced separately and continues during AOL with
stock cruise off (lifecycle ticks above). Before Track A the same function already returned nothing at experience 32
with cruise off, so AOL-only lateral behaviour is unchanged by Track A.

## Behaviour change to verify on the car

With the correction, the Hybrid gets for the first time under this Dom lineage: AOL (experience 32, Panda
`honda_stock_aol` for word 80/81) and the Track A camera-button takeover while engaged (synthetic LKAS press every
≥ 500 frames, driver LKAS press blocked). Both use only frames already allowed for word 80/81. They need an
owner-supervised check in a safe place: AOL engages with stock ACC off, brake/steer override and disengagement
behave as expected, and the stock LKAS indication is as expected.

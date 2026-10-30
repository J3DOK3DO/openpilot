# Honda Accord 11G — Dom 7.0 V4 Track A integration

**Pinned source:** `StarPilotHQ/StarPilot` Dom at `b64d7cf9e96ee6bb92122852e437d5488c14aa56` (2026-10-30).
**Scope:** US 2025 Honda Accord 11G Hybrid Bosch-C / CANFD, factory PCM ACC and lateral steering only.
**Classification:** INSTALLABLE SOURCE BRANCH CANDIDATE, NOT ROAD/PRODUCTION QUALIFIED.

## Implementation
The stock-MVL camera LKAS synthetic pulse queue in `opendbc_repo/opendbc/car/honda/accord_mvl_stock.py` now clears on braking, stock ACC disabled, LKAS_READY loss, control disabled, cancel or resume, including non-CAN-send frames. It retains the 500-frame cooldown. The existing integration fixture now includes physical `POWERTRAIN_DATA.ACC_STATUS` so the test checks camera message suppression following stock ACC withdrawal.

This is **not** a new Panda permission, gas/brake/radar/UDS actuator, AEB/CMBS change, or implementation of Track B custom longitudinal control.

## Reproduce the current native tests
Run from repository root on a Linux development host:

```bash
./dev pytest \
  opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_stock.py \
  opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_parameters.py \
  opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_interrupt_v4.py \
  opendbc_repo/opendbc/car/honda/tests/test_accord11g_stock_ownership_v4.py \
  opendbc_repo/opendbc/safety/tests/test_honda_mvl_stock.py \
  opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py \
  opendbc_repo/opendbc/safety/tests/test_release_build.py \
  opendbc_repo/opendbc/can/tests/test_packer_parser.py \
  openpilot/starpilot/flm/tests/test_controls_scheduling.py \
  openpilot/system/tests/test_logmessaged.py

./dev pytest \
  opendbc_repo/opendbc/safety/tests/test_honda.py \
  opendbc_repo/opendbc/safety/tests/test_honda_mvl_stock.py \
  opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py

./dev python scripts/accord11g_v4_release_safety_smoke.py
```

## Results — fresh Dom native testing, Ubuntu x86_64
- Current host SCons build: PASS.
- Expanded V4/native suite: **91 passed** (2 deprecation warnings).
- Native Honda safety suite: **269 passed, 244 native skips**.
- Independently compiled Panda RELEASE library, Honda stock tests: **19 passed**.
- Codex PRE-change review: REVISE (issues corrected).
- Separate post-change Codex review: refer to campaign review record.
- Raw evidence: `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/evidence/`.

No tests rely on historical C6-12/C7 driving logs, earlier gates, or old baselines.

## Boundaries
This topic branch is separate from the upstream Dom branch and is not the active comma installation. This is one stock-MVL code correction plus focused new tests, **not 84 executable patches**. Track B Bosch-C longitudinal is not implemented. Panda device firmware, actual ARM64/AGNOS runtime, OEM AEB/CMBS interaction, independent hardware-fault paths, protected bench and controlled vehicle qualification remain unverified. No driving/production authorization is implied by passing host tests.

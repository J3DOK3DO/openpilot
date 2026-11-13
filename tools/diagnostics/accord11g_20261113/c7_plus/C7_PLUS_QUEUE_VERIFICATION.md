# C7+ stock-MVL queue verification — 2026-11-13

**Disposition: OFFLINE CANDIDATE / VEHICLE HOLD.** Local branch `accord11g-dom7-c7plus-boschc-regression-20261113` began at `05300cf1e790cd9bc5d75b75aa9bbc9e0654a590`. No device, firmware, GPIO, physical CAN, controller steering, Params, installation, or push operation was performed.

The current controller calls `AccordMvlStock.update()` every frame when its exact qualified profile is present. Its only output here is an existing camera-bus `SCM_BUTTONS` message. Compared with historical `61323fdf0c` (`5fa8b2ed8c` equivalent), the present helper returned on marked brake/ACC withdrawal and general disable/cancel/resume, but retained pending LKAS pulses; ordinary experience 0 did not check physical brake/ACC. The port clears the queue and returns before the four-frame send gate on brake, physical ACC off, `LKAS_READY` false, controls disabled, cancel, or resume for both experiences. It preserves `last_lkas_button_frame` and the 500-frame rearm. The previously committed Hybrid flag qualifier, exact safety model/word restrictions, and output encoding are unchanged. This removes possible stale pulses and adds no actuation path.

Host commands and observed results, with cached `pycapnp`, `setproctitle`, `zstandard`, `tqdm`, and `pyzmq` imported read-only from `/home/jdkd/.cache/uv/archive-v0` via `PYTHONPATH`. The table abbreviates cache roots; the exact final host command follows it:

| Command | Output |
|---|---|
| `PYTHONPATH=<cached pycapnp,setproctitle>:opendbc_repo:. python3 -m pytest -q opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_interrupt_v4.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_hybrid_aol_qualification.py` | 44 passed before adding two last-send cooldown cases; rerun below includes them. |
| `python3 -m unittest discover -s tools/diagnostics/accord11g_20261113 -p 'test_*.py' -v` | 16 passed. |
| `python3 -m unittest discover -s tools/diagnostics/accord11g_20261113/c7_plus -p 'test_*.py' -v` | 1 passed. |
| `PYTHONPATH=<five cached package roots>:opendbc_repo:. python3 -m pytest -q opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_stock.py opendbc_repo/opendbc/car/honda/tests/test_stock_aol.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_hybrid_aol_qualification.py opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_interrupt_v4.py -k 'not card'` | 358 passed, 24 Card cases deselected, 1 failed before two last-send cooldown cases were added. |
| Same command with `-k 'not card and not test_real_parser_controller_camera_button_cadence_and_override_exclusion'` | 360 passed, 25 deselected after the two added cases. |

```sh
PYTHONPATH=/home/jdkd/.cache/uv/archive-v0/i7wuLLr-rrR7DuZ2:/home/jdkd/.cache/uv/archive-v0/u8AcTYoFC6uArKy3:/home/jdkd/.cache/uv/archive-v0/my2o4q-92WVATYjh:/home/jdkd/.cache/uv/archive-v0/9X2dEASLdGaf_etc:/home/jdkd/.cache/uv/archive-v0/L3-mW9Oqfz1zoGci:opendbc_repo:. python3 -m pytest -q opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_stock.py opendbc_repo/opendbc/car/honda/tests/test_stock_aol.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_hybrid_aol_qualification.py opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_interrupt_v4.py -k 'not card and not test_real_parser_controller_camera_button_cadence_and_override_exclusion'
# 360 passed, 25 deselected in 0.42s
```

The single failing old test supplies only camera HUD and SCM_BUTTONS parser messages, leaving physical `cruiseState.enabled` false while expecting camera button messages whenever `control.enabled` is true. That expectation conflicts with withdrawal on physical ACC off. The requested file scope excludes editing `test_accord_mvl_stock.py`; its failure is recorded, not hidden. Its other assertions are not a safety qualification. Earlier C7+ host runs reported 24 Card integration failures at import because the checked-in `msgq` binary is AArch64 on this x86_64 host. No native Card or Panda safety pass is claimed.

See `C7_PLUS_ELM327_CAN2_STARTUP.md` for the separate startup fault. Queue cleanup does not resolve the fault or `controlsMismatch`.

## Final historical test-fixture reconciliation

The prior run's single legacy-parser fixture failure was resolved by restoring precisely the
historical 61323fdf0c test-fixture correction in
opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_stock.py. The original fixture
fed only SCM_BUTTONS and LKAS_HUD, leaving physical cruiseState.enabled false while
expecting the camera button stream. The restored fixture supplies synthetic
POWERTRAIN_DATA.ACC_STATUS enabled only during the intended interval, asserts
the real parsed cruise state matches it, and expects camera button forwarding
only while physical ACC is enabled. No runtime code was weakened by this test correction.

Superseding host result: the same four Honda pytest modules with five cached
package roots and selector -k 'not card' returned 361 passed, 24 deselected,
0 failures, in 0.54s. The 24 Card integration cases remain unexecuted because
host x86_64 cannot load the ARM64 msgq binding. Separately, the 16 standard
offline diagnostics, the C7+ CAN2 diagnostic, and the C6-12/current Panda
interrupt/fault contract checker passed. This historical fixture correction is
not physical/native Card qualification.

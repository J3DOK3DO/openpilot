# C19 targeted checks and artifact audit

## Actual checks

| Check | Exit / result |
| --- | --- |
| `pytest` new C19 guard plus Honda stock host file without exclusions | exit 1: 324 passed, 27 failed because `setproctitle` or `msgq` is unavailable |
| Same files excluding `active_engagement_arms_without_raw_cruise` and `actual_card` | exit 0: **326 passed, 27 deselected**; includes synthetic Accord gear, standstill, invalid speed, fault, CANCEL and other-Honda cases |
| Selected native Honda safety tests: reverse/EPS/heartbeat, selected EPS or gear loss, pending grant request | exit 0: **3 passed, 25 deselected**; current unchanged native safety source |
| Python `compileall` on the three host files and new test; `git diff --check` | exit 0 |
| Initial native invocation before host `cffi` cache was supplied | exit 2: collection blocked by absent `cffi`; resolved for selected native tests with read-only host package cache |
| C18 unchanged-source evidence | Reused: 329 cross-brand passes with 3 `msgq` exclusions; 25 focused; 3 native. Not rerun or counted as fresh C19 results. |

Test environment: system Python 3.12 and pytest, `PYTHONPATH` set to read-only host package caches plus `opendbc_repo` and worktree. Tests use fabricated schema states and current-source native safety library. No device, CAN transmit, flash, road run or private route data.

## C8.1 install recipe and C19 artifacts

`prebuilt` exists and `prebuilt.json` contains schema 1 inventory digest `107546c7842de8dce572c6477797371a3668b3c43c9a406b0787905aafc8480c`. `tools/ci/check_prebuilt_receipt.py --revision HEAD` reports no matching build receipt for parent C18. The C19 protected-source changes also invalidate that digest. The receipt was not refreshed; a refreshed digest without a same-commit native build would misrepresent provenance.

`SConstruct` selects aarch64 Qualcomm device build and Panda SConscript. Existing ARM/Panda binaries and model pickle chunks in the checkout predate C19; their presence does not establish C19 provenance. Panda release signing requires `RELEASE` and `CERT`; only the debug private key and release public key are present. No release private certificate is available. The laptop QCOM import contract requires `.cache/qcom-artifact-package/manifest.json` plus six bound target artifacts, or native `/dev/kgsl-3d0`; neither manifest nor GPU device exists. `/usr/bin/arm-none-eabi-gcc` exists, but an isolated Panda debug compile is not an installable product build. Disk free was about 7.6 GiB (92% used), RAM available about 13 GiB. A bounded native product build was not attempted because the QCOM and signing prerequisites are absent and disk headroom is narrow. No C19 target binary, firmware signature, package or build receipt was produced.

Do not use the checkout's reused binaries as a C19 image or copy the C8.1 receipt. The receipt validator must pass against an actual exact-commit build before a device candidate exists.

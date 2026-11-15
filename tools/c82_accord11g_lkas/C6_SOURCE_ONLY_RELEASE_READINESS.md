# C6 source-only release readiness and reproducibility manifest

2026-11-15 Asia/Dubai. **NOT INSTALLABLE.** This checkout and the companion C5/C6 reports are a local source review package. No release receipt, `prebuilt.json`, native firmware image, Qualcomm binary, release tag, push or device artifact was produced.

## Identity and delta

| Identity | Exact value / use |
|---|---|
| Original Dom rollback | `ab468b8ecd1baa3e63fb5436b69253213d892b5d` (historical, not contacted) |
| Installed C8.1 | `9d2da330f6539beb5afb67867b28491526c0e1bd` (last verified identity, not refreshed) |
| C8.2 Phase 2–3 parent | `e54e9cc8c6e8dd7338618e1d22622fb97c6856dc` |
| Frozen C4B starting commit | `2fe2061228b2b55ddbe1bff8ccdf394194555f81`, branch `accord11g-dom7-c8-2-c5c6-offline-20261115`, initially clean |
| C5/C6 final | One local commit; see [combined report](C5C6_COMBINED_CODEX_REPORT.md) for final full SHA. No release tag. |

The C4B `honda_stock_aol.h` SHA-256 was `7b8d6b380cdd7d6191667fd1d420f3214a0b3d5b622dc249f0c8f9b67cffc244`; the original e54 header was `3df459d8e7c6ae91a421e3e180a8ef43e7dd875af5eaf5e924e7`. C5's final header is `44decb9c4a51953db8434dc54027559aadbdcb7194ae784df56f61de05462882`; its test file is `3779167586428b30d52bbcc9bd445e0d17ea54e74d6cd1a4eb2217953017a053`. The historical C4B patch hash `67ff8af9a2fdddf7c5ebff29d01a6ded486d282d8ff3e0a0596d08487caeab13` remains a **C4B evidence label**, not a hash of the new C5 diff. The complete new source/test patch is [C6_NATIVE_SOURCE_DIFF.patch](C6_NATIVE_SOURCE_DIFF.patch); reproduce with `git diff --unified=0 2fe2061228b2b55ddbe1bff8ccdf394194555f81 HEAD -- opendbc_repo/opendbc/safety/modes/honda_stock_aol.h opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py`. Final source/test diff SHA-256: `33c02c90206dda4aca7df7dc7f575e44f6a8e43cffedc700430c35673ebf12bd`.

## Evidence manifest

All new bounded logs are under `/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C8_2_C5C6_OFFLINE_20261115/`; prior C4B evidence was left unchanged. The preexisting partial Qwen files in that directory concern frozen C4B, have `state: starting`, and do **not** constitute final-candidate review or approval. Its P0 claim about neutral-gear LKAS contradicts the quoted Drive condition and the C4B native red/green evidence; treat as a challenge to verify, not a result.

| Log / SHA-256 | Command and exact result |
|---|---|
| `c82_c5_reconnect_red.log` `2aa1d705c0edc192e2823c06c2e95993f303479b1042d9e7d3cbdd6cd0704c24` | `python3 -m pytest -q -s opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py -k c5_reconnect_zero_after_pending_grant_retires_old_session` on unchanged frozen C4B production header after adding only the test: **1 failed, 33 deselected**; actual `(578,1,1,True)` versus required `(576,1,0,False)`. |
| `c82_c5_gear_red.log` `bc26e30ea5c3f375da9f5b65b85132ce82f2d40b832acf601490707d0746e86f` | `python3 -m pytest -q opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py -k c5_gear_return_new_grant_needs_post_drive_host_request` with the exact frozen C4B header restored temporarily: **1 failed, 34 deselected**; stale host mask produced permission/TX `(1,True)` before new request. The working header was restored immediately after the red run. |
| `c82_c5_native_final.log` `51bcff334591c2ae54f8fad0fd99346947381cf5152c1d17edfd153c1d61f527` | `python3 -m pytest -q opendbc_repo/opendbc/safety/tests/test_honda_stock_aol.py`: **35 passed** after both C5 fixes. Earlier `c82_c5_native_all.log` is an intermediate 34-pass result, retained with its original hash. |
| `c82_c5_lifecycle_final.log` `3177100f7bb6844d13d6a051bbac67ff34d266c72ebe1daa545db60e87aa9a8d` | `bash /tmp/c82_phase23_20261115/run_x86.sh openpilot/starpilot/aol/tests/test_honda_recovery_lifecycle.py::TestHondaCurrentCaller openpilot/starpilot/aol/tests/test_honda_canfd_lifecycle.py::TestHondaCanfdCaller`: **28 passed** with final header copied byte-for-byte into x86 mirror. Earlier `c82_c5_lifecycle.log` is intermediate. Cached older x86 acados is import-only. |
| `c82_c5_bus0.log` `5ced299b6a4be81e4713b23351bdb3843552f4f727a21ca4485563dfa967cf21` | `python3 -m pytest -q opendbc_repo/opendbc/car/honda/tests/test_accord11g_c8_1_transport.py -k 'strict_query or incomplete_identification_holds_closed or fault_policy_unchanged'`: **8 passed, 48 deselected**. |
| `c82_c5_ruff.log` `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` | Ruff on changed Python: **all checks passed**. `python3 -m py_compile` and `git diff --check`: **passed**. |

The host tests sourced the existing `C8_2_INDEPENDENT_LATERAL_20261114/tools/env.sh`, then prepended this checkout and `opendbc_repo` to `PYTHONPATH`; no build from `release_gui` was substituted. The lifecycle runner's mirror uses production C++ pandad and host-built Honda safety, but is not ARM/Qualcomm qualification. Reused and explicitly not rerun: C4B 33 native and 1 CAN2 parser; earlier same-policy 253 passed/40 skipped/204 deselected Honda selection; C8.1 118 discovery; baseline Jetlink **2 failed, 5 passed** on candidate and original. No statuses were converted to PASS.

## Future exact-commit package gates

The [C8.1 acceptance crosswalk](C4B_C81_ACCEPTANCE_CROSSWALK.md) accepts a skipped full-image restoration rehearsal and optional settings reset for this offline scope. Its GUI Fast Update condition was not road approval. C8.1 changed `prebuilt.json` only at release; C8.2 changes a Panda C header. Therefore a **future, separately authorized** candidate needs an authentic target-native Panda firmware build from its exact source commit, firmware identity and safety-mode/param verification, Qualcomm/product binaries from the same exact commit, dependency/build logs, hashes and packaging receipts, and independent review of all native source and host ingress. A C8.1/old Dom receipt cannot qualify this diff. No such artifact exists here; this source package must remain out of install tooling.

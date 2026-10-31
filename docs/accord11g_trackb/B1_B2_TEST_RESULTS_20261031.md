# B1/B2 primary-pass and independent-review-fix test results

## Reproducibility context

- Branch: `accord11g-dom7-trackb-b1-b2-simulation-20261031`
- Starting SHA: `82e053f56c18a814f1a98ea10e7b2b4057ed7d76`
- Host wrapper: `./dev`; Linux; Python 3.12.14; pytest 8.4.2; ruff from the checked native environment.
- No device, Panda USB/SPI, CAN, diagnostics, Params, network vehicle service, logs, or replays were accessed. The wrapper reported a benign `PWD`/shared-worktree warning during builds; all commands below exited successfully. The R2 token-lifecycle correction pass completed at 2026-10-31T08:45:41+04:00.

## Commands actually run

| Time window (Asia/Dubai, UTC+04:00) | Command | Result |
| --- | --- | --- |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `./dev pytest tools/trackb_research/tests/test_canfd_dictionary.py tools/trackb_research/tests/test_plan_controller_sim.py tools/trackb_research/tests/test_architectural_isolation.py tools/trackb_research/tests/test_shadow_synthetic.py` | 110 passed, 0 failed, 0 skipped (pytest execution 0.23 s). Includes permanent token retirement across recovery/reset, stable repeated accepted tokens, explicit silent-token-change withdrawal, huge-integer timestamp/target/vector/policy/vehicle input regressions, UInt64-shaped IDs, malformed-type faults, and dictionary/isolation checks. |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `./dev pytest opendbc_repo/opendbc/car/honda/tests/test_accord11g_stock_ownership_v4.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_trackb_no_long_authority.py opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_parameters.py opendbc_repo/opendbc/car/honda/tests/test_accord_mvl_stock.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_denials.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py scripts/tests/test_accord11g_trackb_parked_audit.py` | 53 passed, 0 failed, 0 skipped (pytest execution 4.27 s). |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `./dev python -m ruff check --no-cache tools/trackb_research/plan_controller_sim.py tools/trackb_research/extract_honda_canfd_dictionary.py tools/trackb_research/shadow_synthetic.py tools/trackb_research/tests/test_plan_controller_sim.py tools/trackb_research/tests/test_architectural_isolation.py tools/trackb_research/tests/test_canfd_dictionary.py tools/trackb_research/tests/test_shadow_synthetic.py` | `All checks passed!` |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `./dev python -m compileall -q tools/trackb_research/plan_controller_sim.py tools/trackb_research/extract_honda_canfd_dictionary.py tools/trackb_research/shadow_synthetic.py` | Completed successfully. |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `python3 tools/trackb_research/extract_honda_canfd_dictionary.py` piped to `diff -u docs/accord11g_trackb/CANFD_SOURCE_DICTIONARY.json -` | 0 diff lines; checked-in dictionary is deterministic. |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `rg -n 'trackb_research' openpilot opendbc_repo/opendbc panda --glob '!**/tests/**' --glob '*.{py,c,cc,cpp,h,hpp,sh,SConscript}'` | 0 production-source matches (expected `rg` no-match status); structural test also passed. |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `git diff --check` | 0 whitespace errors. |
| 2026-10-31T08:45 (R2 token-lifecycle correction) | `git status --short` | Only reviewable source/docs changes; no production-runtime, Panda safety, DBC source, firmware, device, binary, build, or cache artifact is in the diff. |

`pyproject.toml` exposes Ruff but no configured mypy/pyright tool. `./dev python -m compileall -q tools/trackb_research/plan_controller_sim.py tools/trackb_research/extract_honda_canfd_dictionary.py` also completed successfully in this pass.

## Limitations

These are host-source and synthetic results. They do not validate a target vehicle, ECU, DBC applicability, physical topology, CAN-FD timing, Panda firmware, OEM ACC/CMBS/AEB preservation, relay behavior, or custom longitudinal authority. Passing simulation tests is not vehicle authorization.

## Fresh post-Qwen remediation tests

Windows OpenCode v2.1.4 successfully used local Ollama Qwen3-Coder 30B with direct attached source and explicit EOF on stdin. Review evidence is saved externally to /mnt/commadrive/DOM7_TRACKB_OPENCODE_20261031/OPENCODE_QWEN3_ATTACHED_REVIEW.log. Qwen's output was advisory: each claimed issue was checked against current source before any correction.

The B2 synthetic source now guards against backwards decision-time movement between otherwise fresh observations and explicitly requires synthetically known enabled stock ACC state. On 2026-10-31 the checked-out current Dom native test runner passed **169 / 169 selected tests**, with 0 failed, and Ruff passed. The exact executed selected suite and output are recorded in /mnt/commadrive/DOM7_TRACKB_OPENCODE_20261031/B1B2_POST_QWEN_FRESH_NATIVE_TESTS.log; lint output in B1B2_POST_QWEN_RUFF.log; git diff --check passed.

No live driving service, firmware, Panda, CAN bus, physical device, OEM ACC, CMBS or AEB was tested or modified. B1 protocol authority remains STOP; B2 is non-actuating simulation only.

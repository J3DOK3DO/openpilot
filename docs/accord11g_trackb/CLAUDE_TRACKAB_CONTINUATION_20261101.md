# Claude Track A/B native-candidate campaign — continuation checkpoint (2026-11-01)

- Candidate worktree (sparse): `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/dom7-v4-trackab-native-candidate-20261101`
- Branch: `accord11g-dom7-trackab-native-candidate-20261101`, base = installed Dom `5b0f81caa120a6e48b41ba7b271b9afa61733205`
- Disposable full build tree: `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/dom7-v4-trackab-native-build-20261101` (detached at `4e3605e6`, rewritten by the build; never commit from it without review)
- Artifacts: `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/trackab-native-continuation-artifacts-20261101/`
- Private Params backup (not in Git): `/mnt/commadrive/DOM7_PRIVATE_DEVICE_BACKUPS_20261101/` (0700)
- MVL `sp-honda-dev-202608` resolved to `3fec9a41…` (== pinned) at 2026-11-01T08:00:58Z

## Done

1. Lineage: merge base `b64d7cf9`; Track A/B file set disjoint from Dom `b64d7cf9..5b0f81ca`; `cherry-pick -x` replay content-identical (`4e3605e6`). Installed car lacks Track A.
2. New current-branch tests: DEBUG/RELEASE parity (80/81), no radar UDS, Volvo probe vs Honda DBC, no SLC adoption, PID lateral selection.
3. MVL functional gap matrix (27 features) and 84-ID new-base disposition (12 drift IDs reviewed).
4. Device read-only audit, flashed Panda from swaglog (DEBUG), AGNOS slot full raw hash (≠ pinned hash_raw, ABI files identical), private Params backup, staged update `195b7000` found.
5. AGNOS backups: both equal to pinned 19.8.1 (`hash` and `hash_raw`); sysroot extracted for the build.
6. B0/B2 cold-start arming barrier; register B5/B6 `OUT_OF_SCOPE`, B3-target `FAIL`.
7. ARM64 build: first attempt hung in `uv sync` under qemu (futex wait); venv pre-populated with `UV_CONCURRENT_*=1`, official build re-run.

8. ARM64 build PASS (attempt 4, `BUILD_EXIT=0`, QCOM package from Dom-committed artifacts); rebuilt binaries
   byte-identical except Panda version strings, SymPy names, and stale `TryChubbsLaneCentering` key in installed Dom.
9. ARM64 tests on the built tree: 2101 passed, 247 skipped, 0 failed (the 3 `msgq` startup tests that failed in the previous campaign pass natively).
10. Packaging: branch tip keeps installed binaries (no receipt fabricated); rebuilt package kept locally.
11. Codex R1 APPROVE WITH FINDINGS → fixed.

12. Codex R2 APPROVE WITH FINDINGS → RUNPATH-aware ABI audit (0 unresolved), wording/log fixes.
13. Owner 34-ID conditional exclusion applied (84/34/50 registers, 0 dependency exceptions).
14. AOL root cause: `accord_mvl_stock.qualified` rejected `HYBRID` (device CarParams flags BOSCH|BOSCH_CANFD|HYBRID,
    experience 0). Fixed in `3e7b035b`; host 2749 passed / 0 failed; lifecycle hybrid cases host-only.

## Open / next

- Codex R3 on the AOL fix and scope docs; publish branch; record remote SHA.
- Owner: supervised on-car check of AOL and the Track A takeover after any install (procedure in
  `TRACKAB_RELEASE_A_INSTALL_AND_ROLLBACK_20261101.md`); note the staged `195b7000` update on the device.

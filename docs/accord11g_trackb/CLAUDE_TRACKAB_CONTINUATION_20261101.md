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

## Open / next

- Finish ARM64 build → `validate_artifacts`, compare rebuilt vs committed binaries, decide release packaging (receipt).
- Run the 3 `msgq` startup tests and the Track A/B set inside the ARM64 container against the built tree.
- Codex R1 → fix → R2 on final tree + artifacts; publish branch; final verdicts.

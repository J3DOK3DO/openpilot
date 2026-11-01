# Accord 11G Track A/B native candidate — final verdicts (2026-11-01)

Target: 2025 US Honda Accord 11G Hybrid, `HONDA_ACCORD_11G`, Bosch-C / CAN-FD (single configuration).
Classification of the published commit: **NON_PRODUCTION_ENGINEERING_CANDIDATE**. It is not an authorized on-road
release; Release B has no actuation path.

## Identity

| Item | Value |
| --- | --- |
| Branch | `J3DOK3DO/openpilot` `accord11g-dom7-trackab-native-candidate-20261101` (final SHA in the published report) |
| Base | installed Dom `5b0f81caa120a6e48b41ba7b271b9afa61733205` (ancestor of `Dom` `195b7000`) |
| Replayed series | `b64d7cf9..c944fce3` via `cherry-pick -x` (content-identical) |
| Production delta vs installed | `opendbc_repo/opendbc/car/honda/accord_mvl_stock.py` only (Track A) |
| Binaries | all 93 tracked binaries (55 AArch64 ELF + 38 Panda files) identical to installed Dom |
| MVL branch / pinned | `sp-honda-dev-202608` = `3fec9a418a659de31d7b1f494193161697a35071` = pinned (checked 08:00:58Z and 08:45:06Z) |

## Native ARM64 build (`scripts/laptop_device_build.sh build 4`)

- Tree: disposable full checkout of `4e3605e6` (later commits change only tests, docs and `tools/trackb_research`; no
  native input). Image `dom7-trackb-arm64:20261030` (this tree's Dockerfile, Cap'n Proto 1.0.1). Sysroot extracted
  from the pinned AGNOS 19.8.1 ext4 image.
- Attempts: (1) `uv sync` hung under qemu-user (futex wait) → venv pre-populated with serialized uv; (2) stopped at
  the QCOM model import: no `.cache/qcom-artifact-package` → package built from the five Dom-committed QCOM
  artifacts with `qcom_artifact_contract.py record` (source signature `db2ee948…`); (3) stopped externally at 71 %;
  (4) resumed with `COMMA_SCONS_SCRUB_MODE=none`: **`BUILD_EXIT=0`**, SCons 3640 s, `validate_artifacts` passed
  (static AArch64 and QCOM capture structure checks; runtime inference not verified), params registry validated,
  receipt written.
- Reproducibility vs committed binaries: everything rebuilt byte-identical except 50 tracked files:
  - 36 `panda/board/obj` files: the version string embeds the commit (`DEV-4e3605e6-Pa5919516-DEBUG`);
  - 6 locationd generated sources/libraries: randomized SymPy symbol names only;
  - `libcommon.a` and the six C++ programs linking it (pandad, camerad, bootlog, encoderd, loggerd, replay): the
    committed binaries still contain the Params key `TryChubbsLaneCentering`, which `a7f4ba8254` (an ancestor of
    installed Dom) removed from `params_keys.h`. **Installed Dom's committed native binaries are one Params key
    behind their own source.** No Accord path reads that key; recorded as a Dom provenance gap, not fixed here;
  - `prebuilt.json`.
- ELF/ABI: all 55 tracked ELF files are AArch64 with `/lib/ld-linux-aarch64.so.1`; every `DT_NEEDED` resolves in the
  pinned AGNOS image (system paths, the ffmpeg `RUNPATH` directory, PulseAudio plugin context).

## Packaging decision

| Option | Content | Receipt | Panda on install | Chosen |
| --- | --- | --- | --- | --- |
| A (branch tip) | candidate source + installed Dom's committed binaries and firmware | `prebuilt.json` inherited from `5b0f81ca` → **invalid** for this tree | no reflash expected (signature unchanged) | **yes** |
| B (local artifact) | candidate source + rebuilt binaries + new receipt `30fc9539…` | valid | reflash to `DEV-4e3605e6…-DEBUG` (`panda_h7.bin.signed` `33e02b46…`) | no (kept as `release/rebuilt_package/`, not pushed) |

Option A changes the least on the car: Python only, with the native code and Panda firmware the car already runs. No
receipt was fabricated, so StarPilot Fast Update will refuse this target; install with the comma installer or git
(`TRACKAB_RELEASE_A_INSTALL_AND_ROLLBACK_20261101.md`).

## Tests

| Run | Environment | Result |
| --- | --- | --- |
| Expanded Honda/Track A/B/Panda/AOL set on new base (pre-change) | host x86_64 | 2637 passed, 247 skipped, 0 failed |
| Same + all new tests, candidate `b2542f62` | host x86_64 | 2729 passed, 253 skipped, 0 failed |
| Track B after Codex R1 fixes | host x86_64 | 469 passed |
| Honda car + Track B + Accord safety + new tests, natively built tree | ARM64 container, real aarch64 `msgq` | 2100 passed, 247 skipped, 1 failed: isolation scan could not run `git` (worktree gitdir not mounted) |
| Rerun of that test + the 3 previously failing `test_actual_card_publication…` | ARM64, common gitdir mounted read-only | 6 passed; combined ARM64 2101 passed, 247 skipped, 0 failed |

Skips: 204 abstract base classes, 30 no regen message, 10 no second speed message, 2 gearbox absent, 1 classic-Bosch
RELEASE-only contract (default library is DEBUG; not an 11G path), 6 parameterized base classes (host only).

## Verdict table

| Gate | Verdict | Evidence |
| --- | --- | --- |
| Track A source compatibility with installed Dom | PASS | disjoint file sets; host and ARM64 runs |
| Track A stock-ACC / lateral non-regression | PASS (host + ARM64 software) | words 80/81, PID selection, no SLC adoption, no radar UDS, Track A tests |
| MVL function-level assessment | PASS (source scope) | 27-feature gap matrix; 0 production adoptions |
| 84-ID reconciliation on new base | PASS | 84/84 dispositioned; 12 Dom-drift IDs reviewed |
| B0 contracts | PASS (simulation) | cold-start barrier corrected after Codex R1 |
| B1 protocol/OEM ownership | HOLD | no authenticated OEM evidence |
| B2 subordinate controller | PASS (simulation only) | 469 Track B tests |
| B3 host Panda safety | PASS | RELEASE denials, DEBUG == RELEASE parity |
| B3 target Panda RELEASE identity | FAIL as specified | flashed firmware is DEBUG (swaglog) |
| B4 source/runtime | PASS for native build, ABI, isolation; HOLD for independently reviewed device identity | this file, device audit |
| B5 / B6 | OUT_OF_SCOPE / NOT_EVALUATED | owner scope change |
| AGNOS compatibility | PASS for measured ABI; full raw slot identity NOT ESTABLISHED | device audit |
| Panda compatibility | PASS (flashed signature prefix == committed firmware, unchanged by candidate); RELEASE firmware: NO | swaglog, parity test |
| ARM64 native build | PASS | `BUILD_EXIT=0` |
| Release packaging | PASS for option A as a git/installer install; Fast Update receipt NOT VALID | packaging section |
| Independent review | R1 APPROVE WITH FINDINGS (fixed); R2 see `review/` | |
| **Release A installation readiness** | **CONDITIONALLY READY (engineering)**: installable by the documented git/installer path with unchanged binaries and Panda firmware; not vehicle-validated in this campaign; owner decision required | |
| **Release B source engineering** | **COMPLETE for the non-actuating scope** | |
| **Release B operational authorization** | **NOT_ESTABLISHED** | B1 HOLD, B3-target FAIL, B5/B6 not evaluated |

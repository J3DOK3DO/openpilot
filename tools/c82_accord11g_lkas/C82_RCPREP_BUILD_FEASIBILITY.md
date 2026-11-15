# C8.2 RC prep: offline native build feasibility

2026-11-15 Asia/Dubai. Source parent: `38b51582deb2a75430b5f9c0dfec95e0f685449c` (parent `2fe2061228b2b55ddbe1bff8ccdf394194555f81`). This is a **source freeze with a bounded native debug build**, not a device release, install package, or road qualification. The later RC prep commit adds documentation only; its full SHA is intentionally outside the committed manifest.

## Inputs and toolchain

- Read the actual `C6_SOURCE_ONLY_RELEASE_READINESS.md`, `C5C6_COMBINED_CODEX_REPORT.md`, root `SConstruct`, `panda/SConstruct`, `panda/SConscript`, `tools/laptop_device_build/VERIFIED_QCOM_ARTIFACTS.md`, and the existing C8.1/RC build handoffs. The starting worktree was clean at the exact parent SHA. No broad host suites were rerun.
- Host `arm-none-eabi-gcc`/`objcopy`: present; GCC `13.2.1 20231009`. Cached `/mnt/commadrive/.venv-native15/bin/scons`: SCons `4.9.1`. Host Python lacks SCons, acados, capnproto, ffmpeg and json11, so root product `SConstruct` cannot be treated as ready.
- Cached `dom7-trackb-arm64:20261030` image booted offline (`--network none --read-only --cap-drop ALL`): AArch64 and `arm-none-eabi-gcc`/`aarch64-linux-gnu-gcc` exist; Python in that image also lacks SCons, acados, capnproto, ffmpeg and json11. Docker image inspection and this probe used no pull. `/AGNOS`, `/dev/kgsl-3d0`, `/opt/tici-sysroot`, and `.cache/qcom-artifact-package` are absent in this checkout/host. The six source-matched stock QCOM captures required by `VERIFIED_QCOM_ARTIFACTS.md` are unavailable. No full QCOM build was attempted.

## Exact bounded H7 compile

The following ran against copies of this worktree's `panda` and `opendbc_repo` under `/tmp/c82_rcprep_build`; the copied `panda/board/obj` was removed before SCons, so inherited binaries could not satisfy the target. `GIT_DIR` and `GIT_WORK_TREE` identified the original clean parent checkout for Panda's version generator. `PYTHONPATH` pointed to the copied opendbc source. No source worktree output was written.

```sh
mkdir -p /tmp/c82_rcprep_build
cp -a panda opendbc_repo /tmp/c82_rcprep_build/
rm -rf /tmp/c82_rcprep_build/panda/board/obj
cd /tmp/c82_rcprep_build/panda
export PYTHONPATH=/tmp/c82_rcprep_build/opendbc_repo
export PYTHONDONTWRITEBYTECODE=1
export GIT_DIR=/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/dom7-v4-isolated/.git/worktrees/work_c82_rcprep_20261115
export GIT_WORK_TREE=/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/work_c82_rcprep_20261115
export SCONS_CACHE=/tmp/c82_rcprep_build/scons_cache
timeout 150s /mnt/commadrive/.venv-native15/bin/scons -Q -j2 board/obj/panda_h7.bin.signed > /tmp/c82_rcprep_build/panda_h7_build.log 2>&1
```

**Exit 0 in 5.1 s.** The log shows ARM Cortex-M7 assembly, compile of production `panda/board/main.c` (which includes `opendbc/safety/safety.h`), ELF link, objcopy and debug signing. The copied final Honda header SHA-256 equals the source header: `44decb9c4a51953db8434dc54027559aadbdcb7194ae784df56f61de05462882`. The source and copied `panda/board/main.c` SHA-256 both equal `43be524884432b47064f4f29024d66883e51838d889d638ae98d35e52c4b44e3`. Generated header states `DEV-38b51582-Pf38f504f-DEBUG`. `arm-none-eabi-readelf -h` identifies `main.elf` as ARM ELF32 executable, EABI5, hard-float. Linker emitted a `.data` section type warning; it did not fail the link.

| Temporary output | SHA-256 | Meaning |
|---|---|---|
| `/tmp/c82_rcprep_build/panda/board/obj/panda_h7/main.elf` | `397d2eda81d2631ed72e8fb8f44a754418a756ec9cec1e5e747242bac60a1846` | Real H7 debug main ELF for the parent source, not a product receipt |
| `/tmp/c82_rcprep_build/panda/board/obj/panda_h7/main.bin` | `571e0a338c7d19f0dd355287657aa85b09fa85f59541baeb82de3feed607aa39` | Objcopy output, temporary only |
| `/tmp/c82_rcprep_build/panda/board/obj/panda_h7.bin.signed` | `71978f7f21b3c2435fc683fb86861bff543992f2421241b997722797ad5dcaf7` | Debug certificate output, **not** release firmware or install authorization |
| `/tmp/c82_rcprep_build/panda_h7_build.log` | `ee5877c1e7dea19ddcbc02ab679fa87681800fe22007163de6c97b31e687f612` | Full command and compiler log |

The temporary tree occupied 28 MB after this build, below the 1.5 GB `/tmp` cap. This one target does not build the F4, bootstub, body, or full Panda variant set. It does not test firmware on hardware. The existing tracked `panda/board/obj/version` says `DEV-de2df523-Pf38f504f-DEBUG`, and tracked H7 binary and AArch64 `pandad` have no exact C8.2 build provenance; they were not substituted for outputs.

## Receipt and product blockers

`python3 tools/ci/check_prebuilt_receipt.py --revision 38b51582deb2a75430b5f9c0dfec95e0f685449c` exited **1**: `Prebuilt release ... has no matching build receipt`. No `prebuilt.json` was created or changed. Root `SConstruct` detects `comma_arm64` only on AArch64 with `/AGNOS`, imports multiple native Python packages, and requires a complete target sysroot for cross building. The cached ARM container and target compiler alone do not meet those requirements. QCOM model captures require the matching six-artifact package or target GPU generation. **Qualcomm/product build: blocked, no product binaries. Release Panda build: blocked, no release certificate or exact final-commit qualification. Installable candidate: NO.**

Existing exact-parent evidence is reused: 35 Honda native host tests, 28 lifecycle host tests, 8 bus-0 tests (48 deselected), and Qwen source review `PASS_WITH_BLOCKERS`. The 4 Qwen claim-disposition tests are a subset of the 35. Jetlink baseline remains 2 failed/5 passed. None of these results converts the H7 debug compile or missing product build into hardware qualification.

# C8.2 C7 offline native build report

2026-11-15 UAE. Implementer: Codex. Entry was clean at `9d3f5c1db40c6e323f6b6f0c9b70aabfad2f2e22` on `accord11g-dom7-c8-2-c7-native-artifacts-offline-20261115`. C5/C6 safety source is `38b51582deb2a75430b5f9c0dfec95e0f685449c`. The final local documentation commit is resolved by `git rev-parse HEAD`; it cannot contain its own SHA. No vehicle, Panda, USB, network build download, flash, push, merge or installer was used.

## Real native attempts

Fresh `panda` and `opendbc_repo` copies were made in `/tmp/c82_c7_native_build_20261115`; inherited `panda/board/obj` was removed. `GIT_DIR` pointed to this checkout's Git worktree metadata, `GIT_WORK_TREE` to this checkout, `PYTHONPATH` to the copied opendbc, and `SCONS_CACHE` to the bounded `/tmp` tree. Host `arm-none-eabi-gcc` is 13.2.1 and SCons is 4.9.1. Command, with a 300 second timeout:

`/mnt/commadrive/.venv-native15/bin/scons -Q -j2 board/obj/panda_h7.bin.signed board/obj/bootstub.panda_h7.bin`

Exit **0**, about 5.5 seconds. It compiled `board/main.c` including current Honda safety, linked H7 main and bootstub, objcopied both, and debug-signed the main. Generated header: `DEV-9d3f5c1d-Pf38f504f-DEBUG`; flags contain `-DSTM32H7`, `-DSTM32H725xx`, `-DALLOW_DEBUG`, and Cortex-M7 hard float. Both ELFs are ARM ELF32 EABI5 hard float. Linker warned `.data` section type changed to PROGBITS; link succeeded. Source/copy Honda header SHA-256 is `44decb9c4a51953db8434dc54027559aadbdcb7194ae784df56f61de05462882`; `panda/board/main.c` SHA-256 is `43be524884432b47064f4f29024d66883e51838d889d638ae98d35e52c4b44e3` in both locations. Full log: `/tmp/c82_c7_native_build_20261115/h7_build.log`.

| Temporary H7 output | SHA-256 |
|---|---|
| `panda/board/obj/panda_h7/main.elf` | `08759f7ff0b9f395e721d1582566bae98751ef0c5b4b0225779fad5e0badf89f` |
| `panda/board/obj/panda_h7/main.bin` | `8be5ad7afef12ac06180ceaff57d46e5813cdae80f2d62393d61438cf08e383a` |
| `panda/board/obj/panda_h7.bin.signed` | `4157653d20a4e40fc304187708fb72530507608f453a2c729fb423b20e8d1f00` |
| `panda/board/obj/panda_h7/bootstub.elf` | `cc1a5dd9703dcc3d776c134d5da987245078e36d394f0f3091c14352b4f8cbba` |
| `panda/board/obj/bootstub.panda_h7.bin` | `e38c03d00bba5512fcc2c342d31c1c60248f38dbbcfdbbb3b1dac787bf822407` |

The standard H7 target is the relevant offline compile. SConscript also defines standard F4, H7 special variants, and body H7; none has a device identity justification here. `RELEASE=1 scons -n ...` exited **2** at `panda/SConscript:17`, requiring `CERT`. No owner release certificate was available or created. The `.signed` filename above denotes a **debug certificate** only. It is not installable release firmware.

Cached `dom7-trackb-arm64:20261030` ran `--network none --read-only --cap-drop ALL` with source read-only and `/tmp` output. AArch64 GCC 13.2.0 and Cap'n Proto 1.0.1 are present. Direct exact-source `test_aol_protocol.cc` compiled to an AArch64 executable and ran with exit **0**; `openpilot/common/params.cc` compiled to an AArch64 relocatable object with exit **0** after adding `openpilot/cereal/gen/cpp` to includes. The initial read-only container compile failed on compiler scratch permissions (134), then the first params attempt failed on a missing generated-header include path (1); the corrected bounded command passed. These are partial ARM64 outputs, not linked `pandad`, `libparams_c.so`, or product binaries. Their hashes are in the manifest and `arm64_compile_retry.log`.

The corrected container command used `--platform linux/arm64 --user 1000:1000 -w /out -e TMPDIR=/out`, read-only `/src` and writable `/out` mapped to `/tmp/c82_c7_native_build_20261115/arm64`. Inside it, the exact compiles were:

```sh
aarch64-linux-gnu-g++ -std=c++17 -O2 -I/src -I/src/openpilot -I/src/panda -I/src/opendbc_repo -I/src/msgq_repo /src/openpilot/selfdrive/pandad/tests/test_aol_protocol.cc -o /out/test_aol_protocol_arm64
/out/test_aol_protocol_arm64
aarch64-linux-gnu-g++ -std=c++17 -O2 -I/src -I/src/openpilot -I/src/openpilot/cereal/gen/cpp -I/src/panda -I/src/opendbc_repo -I/src/msgq_repo -c /src/openpilot/common/params.cc -o /out/params_arm64.o
```

The root product build cannot start in that container: no SCons, acados, capnproto Python, ffmpeg Python, or json11 Python; no `/AGNOS` or source-matched sysroot. `launch_env.sh` pins AGNOS `20.5.2`, which does not establish the disconnected device's actual AGNOS. No target GPU is present. The existing static `validate_artifacts.py .` exited **0**, but it examined inherited checkout AArch64/model outputs and explicitly does not prove runtime inference or fresh C8.2 build. `check_prebuilt_receipt.py --revision 9d3f5c1d...` exited **1**: no matching build receipt. `prebuilt` and `prebuilt.json` were not altered.

The `/tmp` tree was 28 MB at inspection; `/tmp` free 15 GB and commadrive free 4.7 GB. Exact logs and the independently copied evidence list are in `D/evidence/C8_2_C7_NATIVE_20261115`. **Verdict: authentic H7 debug main and bootstub compile PASS; release-signed Panda firmware BLOCKED; full Qualcomm native product build and receipt NO-GO; physical safety qualification NOT RUN.**

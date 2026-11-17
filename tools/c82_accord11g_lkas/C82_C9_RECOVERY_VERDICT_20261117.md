# C8.2 C9 evidence recovery verdict — 17 November 2026

**Offline engineering checkpoint only. Native product, device installation, and vehicle use: NO_GO.** Branch `accord11g-dom7-c8-2-c9-agnos2052-build-offline-20261115` entered at `58ef6e5fcea2d0d303855784e5f0dd58313941c4`. This recovery did not build a product or touch control code, models, firmware, prebuilt markers, or native release outputs.

## Source identity and recovered evidence

Repository `openpilot/system/hardware/tici/agnos.json` SHA-256 is `e69520f0c108606b552793551a848ee7702d8890f6786098f25299a81bb2023e`; its `system` JSON entry equals the preserved `/tmp/c82_c8_agnos2052_20261115/system_manifest.json` (SHA-256 `1dc67e499f7734f7d03535b0a98bf084cb39ddfb4b077625feddd2910d8e5d4a`). The available compressed system image is 548,950,436 bytes and independently hashed on 17 November to `990319694ce76972667458a5318f1e7d414d1895867fd5312dcbbf175a9dbf14`. The pinned sparse SHA-256 is `ec1b9569c784dd0be5d81eb613f59c1628baba3fd13f20ca7568c740a208c5c6`; pinned raw SHA-256 is `4f2aa50375915e52ea24ce069ccd92dcaf68d3fbd88959adc5f9e572457bdba2`. These latter two hashes and `/VERSION=20.5.2` were measured by the older C8 extraction record, **not** rerun today: raw image and marker are absent. The compressed hash connects today's bytes to that older record, subject to trust in the old extraction procedure. No independent installed-device version is known.

Small evidence recovered to `D/evidence/C8_2_C9_AGNOS2052_20261115`, where `D=/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113`: original C9 trace, original C8 download/extraction log and provenance, preserved C9 build and test logs, ABI comparison, and new read-only identity/ELF/receipt checks. `SHA256SUMS.txt` covers all evidence files except itself. Large images and binaries were not copied. The source trace ended after a timed-out session; missing C9 evidence files had never been written to that directory.

## Exact old build outcomes and fresh subset

The 15 November wrapper `/tmp/c82_c9_agnos2052_build_20261115/run_scons.sh` invoked `timeout -k 5 235s docker run ... --platform linux/arm64 --network none ... -e COMMA_BUILD_SYSROOT=/opt/tici-sysroot ... /work/.venv/bin/python3 -m SCons -Q -j2 --cache-disable TARGET`, with a **synthetic** `/AGNOS` marker and a staged source checkout at the entry SHA. Its commands and logs are preserved; these were **not rerun** during recovery.

| Old command | Exit | Supported conclusion |
|---|---:|---|
| `run_scons.sh preflight openpilot/selfdrive/pandad/pandad` | 0 | Dry-run recipe only. |
| `run_scons.sh build openpilot/selfdrive/pandad/pandad` | 124 | Timed out after some compilation; no `pandad` link. |
| `run_scons.sh build openpilot/selfdrive/pandad/tests/test_aol_protocol` | 2 | Initial test link failed: missing root loader path in temporary sysroot. |
| Same test command after temporary loader symlink repair | 0 | Selected test linked. |
| Offline loader invocation of selected test in networkless ARM64 container | 0 | `AOL_TEST_PASS`; dependencies resolved to selected sysroot. |
| `run_scons.sh build openpilot/selfdrive/pandad/pandad` incremental | 137 | Killed; still no completed `pandad` link. |

The preserved selected test is ELF64 AArch64 PIE, 555,672 bytes, modified 15 November 21:40:02 +04:00, SHA-256 `88e31c91320722a1cb2b41ffe86c0e2ee802b3499abc53c06e3768eab50804f2`, with interpreter `/lib/ld-linux-aarch64.so.1` and needed `libstdc++.so.6`, `libgcc_s.so.1`, and `libc.so.6`. The staged `pandad` is a tracked, inherited binary dated 15 November 21:00:10 +04:00, before the C9 attempts; it is **not** a fresh C9 product. The selected AOL test is a bounded link/run result, not a full product, GPU inference, or vehicle test.

## Checks, limitations, and gates

17 November rerun: parsed repository `system` manifest equals preserved manifest (exit 0); compressed image SHA-256 matches prior record (exit 0); selected sysroot path and symlink inspection plus `readelf` metadata completed; read-only `PYTHONDONTWRITEBYTECODE=1 python3 tools/ci/check_prebuilt_receipt.py --revision 58ef6e5fcea2d0d303855784e5f0dd58313941c4` exited **1**, no matching build receipt. The 15 November five cached QCOM contract log is `INPUT_CONTRACT_ONLY`; it was recovered but not rerun. `libOpenCL.so.1` and `CL/cl.h` remain absent from the extracted sysroot. The vendor path and root loader link are synthetic extraction/build repairs. The old 21-library comparison is selective and is not an installed-device ABI check.

Unresolved C8 prerequisites remain: complete native root product build and inventory against the actual final source, matched target runtime and GPU/OpenCL dependencies, target inference, release Panda certificate/signature, physical AGNOS/Panda identity, independent safety review, standstill CAN2 `controlsMismatch` qualification, and road acceptance. No device, CAN, SSH, Panda compile/flash, firmware installation, GPU inference, or vehicle test was performed here. The prebuilt receipt remains `NO_GO`. No independent reviewer or human approval is claimed.

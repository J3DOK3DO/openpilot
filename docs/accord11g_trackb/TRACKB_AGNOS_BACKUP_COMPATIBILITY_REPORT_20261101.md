# AGNOS backup compatibility report — 2026-11-01

## 1. Specified device backups: ABSENT (blocker)

| Expected path | Result |
| --- | --- |
| `/home/jdkd/AGNOS_20261014/` | **Directory does not exist** |
| `/home/jdkd/AGNOS_20261014/agnos_system.img` | absent |
| `/home/jdkd/AGNOS_20261014/agnos_system.ext4.img` | absent |

Per instruction, no Windows search or new transfer was attempted. A bounded local search (`/home/jdkd`, `/mnt/commadrive`, depth 4, `agnos_system*.img`) found no device backup. So none of the following could be produced: device-backup sizes or hashes, the raw/sparse/ext4 relationship between the two backups, or a backup-versus-pin comparison. **B4-INSTALLED-DEVICE-IDENTITY remains HOLD.**

## 2. Substitute evidence actually examined: the repository-pinned AGNOS release image

The image, sysroot and logs live outside this repository and cannot be reproduced from the worktree alone. The raw logs are in the campaign artifacts at `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/trackb-unified-final-artifacts-20261101/logs/` (`AGNOS_PINNED_IMAGE_HASH.log`, `ARM64_CONTAINER_TESTS.log`). Only the `agnos.json` pin and `AGNOS_VERSION` are verifiable from the tree.

An earlier offline workspace holds a downloaded AGNOS system image. It is a **release image**, not a backup of the user's device.

| Item | Value |
| --- | --- |
| File | `/home/jdkd/g06-agnos-offline-20261014/cache/agnos_system.img.xz` |
| Size | 1,051,332,800 bytes (xz) |
| SHA-256 (xz), before and after analysis | `83b15de115957e539d03b52e8ef6091775213355a9db574a0d97c843fb154d05` (unchanged) |
| Decompressed format | Android sparse image (magic `0xED26FF3A`, block 4096; prior conversion manifest: 8250 chunks, raw size 4,718,592,000) |
| SHA-256 of decompressed sparse stream | `9c753bdd90e6079b2cf525659d7523d0ebc0a375bd61e61cca628f1db3832cfd` |
| Repository pin `openpilot/common/hardware/comma/agnos.json` `system.hash` | `9c753bdd90e6079b2cf525659d7523d0ebc0a375bd61e61cca628f1db3832cfd`: **match** |
| Pin `hash_raw` / `ondevice_hash` | `98e15de0…6417da8` / `9625ec32…94f4e9` (not recomputed: requires unsparsing to disk; free space is 14 GB) |
| `launch_env.sh` AGNOS_VERSION | `19.8.1` |

The hashes were computed by streaming (`xz -dc | sha256sum`). Nothing was mounted, written or flashed. The pinned URL host is `files.firestar.link` (system30.img.xz); the download manifest records it as "not yet target approved".

## 3. ARM64 sysroot (previously extracted from that image; read-only inspection)

`/home/jdkd/g06-agnos-offline-20261014/sysroot` (2.1 GB) contains `lib/`, `usr/` and `system/vendor`, matching the `REQUIRED_DIRS` of `tools/laptop_device_build/extract_sysroot_from_agnos.py`.

| Dependency | Finding | Dom requirement |
| --- | --- | --- |
| Architecture / loader | `ld-linux-aarch64.so.1`, ELF 64-bit aarch64 | ARM64 device build |
| C library | Ubuntu GLIBC 2.39-0ubuntu8.9 | — |
| Python | 3.12 (`libpython3.12.so.1.0`, venv `python3.12`) | `pyproject.toml`: `>=3.12.3,<3.13` (patch level not determinable from the sysroot) |
| Panda USB | `libusb-1.0.so.0.4.0` | Panda USB transport |
| Messaging | `libzmq.so.5.2.5` | msgq/zmq fallback |
| GPU | `libOpenCL.so.1` | modeld |
| Crypto / compression | `libssl.so.3`, `libcrypto.so.3`, `libzstd 1.5.5`, `liblzma 5.4.5`, `libffi 8.1.4` | — |

Panda SPI and CAN-FD userspace are implemented in Dom source (`panda/`, `openpilot/selfdrive/pandad`); their kernel/driver side cannot be judged from a userspace sysroot.

## 4. Native ARM64 evidence produced this campaign

| Check | Result | Evidence class |
| --- | --- | --- |
| Track A/B, RELEASE-denial, MVL CAN-FD, 80/81 safety, parked-audit and isolation tests in `dom7-trackb-arm64:20261030` (QEMU user-mode, `--network none`), host libsafety compiled natively for aarch64 inside the container | **373 passed, 0 failed, 0 skipped** | Source/build compatibility |
| Whole-repo isolation scan under ARM64 | Passed. The prior failure (no `.git` in a plain copy) was a **fixture limitation**: the fixture now is a git repository force-adding exactly the 7932 checked-out tracked files | Fixture fix, not a source defect |
| Full Dom ARM64 SCons release build against this sysroot | **NOT_RUN** (multi-hour QEMU build; does not change any classification while installed-device evidence is absent) | — |

## 5. Separation of evidence

| Category | Status |
| --- | --- |
| Source/build compatibility | Partial PASS: emulated ARM64 tests pass; the full release build was not run |
| Pinned-image compatibility | PASS for identity: the image equals the repo pin; sysroot ABI is consistent with Dom's Python/USB/ZMQ/OpenCL needs |
| Installed-device compatibility | **HOLD**: no device backup, no device access. A matching release image does not show what is installed |

## 6. Required to close B4 on the real device (read-only, separately authorized)

1. Device architecture, active slot, `/VERSION` and the AGNOS system partition hash (compare to `ondevice_hash` `9625ec32…`).
2. Panda firmware version and signature/hash. Panda MCU type.
3. `/data/openpilot` branch and commit, plus a Params backup (known-good rollback point).
4. Re-supply the device backups at `/home/jdkd/AGNOS_20261014/` if a backup comparison is still wanted.

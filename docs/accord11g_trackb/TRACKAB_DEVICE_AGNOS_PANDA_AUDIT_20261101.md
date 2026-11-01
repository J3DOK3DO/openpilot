# Accord 11G: read-only comma, AGNOS image and Panda identity audit (2026-11-01)

Scope: passive inspection only. No device writes, no Params change, no OTA/install, no Panda interrogation over USB,
no CAN/UDS transmission. Identifiers that could identify the owner (dongle ID, Panda serial, Params values) are
deliberately omitted from this published report.

## Connection

`ssh comma` → `comma@192.168.0.133:22`, `StrictHostKeyChecking=yes`, `BatchMode=yes`. Live ED25519 key
`SHA256:ZpPv3Fpwa0QjhtOoLFC4PatWfsa1LLzR6PxwQuvm0TY` matches the existing `known_hosts` entry. No SSH configuration
was changed in this campaign.

## Device state (2026-11-01T08:03Z–08:30Z)

| Item | Observation | Command (read-only) |
| --- | --- | --- |
| Host / arch | `comma-8896cc0a`, `aarch64`, kernel 4.9.103, Ubuntu 24.04.5 | `hostname; uname -m` |
| AGNOS | `/VERSION` = `19.8.1`; boot slot `_a` (`androidboot.slot_suffix`) | `cat /VERSION; /proc/cmdline` |
| openpilot | `/data/openpilot` branch `Dom`, HEAD `5b0f81ca…`, clean; `prebuilt` marker present | `git rev-parse`, `git status` |
| Updater | origin `StarPilotHQ/openpilot` `Dom`; **finalized staged update `195b7000`**, `UpdateAvailable=1`, `UpdaterState=idle` | `git -C /data/safe_staging/finalized rev-parse HEAD`; param files read |
| Rollback anchors | `ORIG_HEAD` = `5b0f81ca`; reflog shows prior Dom resets; `c944fce3`, `5fa8b2ed8`, `195b7000` objects present | `git reflog`, `git cat-file -t` |
| Storage | `/data` 89 GB, 48 GB free; `/` 4.3 GB, 272 MB free (94 %), mounted `ro` | `df -h`, `/proc/mounts` |
| Process state | offroad (`IsOffroad`), manager/pandad/controlsd/card/selfdrived/plannerd running | `pgrep -fc` |
| Params | `/data/params/d → d_tmp`, 264 files, 1.2 MB | `ls`, `du` |

### Active AGNOS system slot

- Full read-only hash of `system_a` over the image size (4,718,592,000 bytes, same method as Dom
  `agnos.py::get_raw_hash`): `f5bf56a979e1170e2c86ffc561db537eb808a272630d6074a0d60b61bf314935` (81 s, `nice`/`ionice`).
- This is **not** `agnos.json` `hash_raw` `98e15de07c39…`. The 64-byte updater marker at offset 4,718,592,000 is all
  zeros on both slots, so Dom's non-full `verify_partition` check would also not confirm the slot.
- Same ext4 UUID `d40b046a-6bad-4cd0-ab3f-331d909517c0` and the same last-write time as the pinned image; mount count
  4 (image: 1), later last-mount time, and a 117-block difference in the free-block counter. 17/17 ABI-critical files
  are byte-identical to the pinned image: `ld-linux-aarch64.so.1`, glibc `libc.so.6` (2.39), `libstdc++.so.6.0.33`,
  `python3.12`, `libpython3.12.so.1.0`, `libusb-1.0.so.0.4.0`, `libzmq.so.5.2.5`, `libOpenCL.so.1`, `libssl.so.3`,
  `libcrypto.so.3`, `libbz2`, `libz`, `libffi`, Adreno `libGLESv2`/`libEGL`, `/VERSION`.
- Verdict: **content-compatible with pinned AGNOS 19.8.1 for every measured ABI file; full raw identity not
  established** (consistent with mount-metadata writes; not proven).

### Panda

- Measured from the device's own swaglog (pandad `connected` line, written by Dom at every Panda connect), not by
  talking to the Panda: under installed `5b0f81ca` the flashed firmware reported
  `DEV-6f2ca2c4-Pa5919516-DEBUG`, signature prefix `510ed0d6c7a8d322`, expected `510ed0d6c7a8d322`.
- Locally, the last 128 bytes of the committed `panda/board/obj/panda_h7.bin.signed` (SHA-256 `425f7a34…`) begin
  `510ed0d6c7a8d322`. The candidate does not change `panda/`, so installing it should not trigger a reflash.
- The flashed build is **DEBUG** (`ALLOW_DEBUG`, debug signing key), as every Dom build recorded in these logs has
  been. Only a 64-bit signature prefix is logged; the full flashed-image hash is not measured.
- Host evidence for this firmware type: `test_accord11g_debug_release_parity.py` (DEBUG and RELEASE libsafety give
  identical TX and forwarding for words 80/81; `allOutput` exists only in DEBUG).

### Params backup (private)

A complete owner-only copy (`tar` of `/data/params/d`, SHA-256 `4a05ef9f…`) is stored outside Git in a 0700 host
directory. 263 of 264 files match device-side SHA-256 sums; the exception is `LastAthenaPingTime`, which athena
rewrites continuously. Values are not reproduced here.

## Local AGNOS backups (`/home/jdkd/AGNOS_20261014/`, opened read-only)

| File | Size | Format | SHA-256 |
| --- | --- | --- | --- |
| `agnos_system.img` | 3,972,387,664 | Android sparse v1.0, 4096-byte blocks, 1,152,000 blocks, 8,250 chunks | `9c753bdd90e6079b2cf525659d7523d0ebc0a375bd61e61cca628f1db3832cfd` = `agnos.json` `hash` |
| (streamed sparse expansion) | 4,718,592,000 | raw ext4 | `98e15de07c39a19b5fa17c96a67e66d4362f9ebaf7827b640f4127e3b6417da8` = `agnos.json` `hash_raw` |
| `agnos_system.ext4.img` | 4,718,592,000 | ext4, UUID `d40b046a-…` | `98e15de07c39…` (identical to the expansion) |

Both backups are the same filesystem: the exact pinned AGNOS 19.8.1 system image named by the candidate's
`openpilot/system/hardware/tici/agnos.json` (`launch_env.sh` `AGNOS_VERSION=19.8.1`). File size and mtime were
unchanged before and after hashing. A sysroot was extracted from the ext4 image into the disposable build tree
(`libc`, `libzmq`, `libusb`, `libOpenCL` hashes match the device). The earlier finding that these backups were
missing is obsolete.

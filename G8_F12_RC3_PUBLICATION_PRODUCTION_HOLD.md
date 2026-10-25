# G8-F12 RC3 — Production-intended engineering qualification branch

**Branch:** `release/g8-f12-rc3-production-qualification-hold`
**Source parent:** `7ac485a19e1e5bd9bd53cc139e45cd607262055f`
**Vehicle:** Honda Accord 11th Generation only
**Disposition:** **ENGINEERING REFERENCE / PRODUCTION HOLD — NOT AN INSTALLER**

This branch is the independent publication/reference copy for RC3 release qualification. It contains the Honda-only RC2 driving components, source-built AArch64 binaries, model reconstruction pieces, offline test machinery and immutable references to the source/model digests. **The launch script deliberately exits with code 78 before loading the manager, Panda, CAN or any other hardware service. Do not remove or bypass this guard.** The 126,302,979-byte driving model is intentionally represented by three tracked chunks and its SHA-256 rather than a >100MB Git blob.

## Important: AGNOS A/B is not application A/B

On the comma, `boot_a/system_a` and `boot_b/system_b` are *operating-system slots*. `abctl --set_active` changes the boot selection and AGNOS updater operations write operating-system partitions. The openpilot application is an independent writable checkout under `/data/openpilot`. Installing this repo into the inactive AGNOS slot would not safely install an alternate openpilot release. The app updater uses /data-based staged overlay activation and presently lacks independently trusted recovery from unexpected power loss or failed startup. The current boot slot A must remain unchanged in this campaign.

## Verified offline evidence (exact RC3 source baseline)

- Honda-only source isolation: reviewed by independent Codex Sol High.
- Source-built AArch64 native artifacts: 14; four generated localization C++ files.
- Full driving model SHA-256: `27969d9da00f74ba0c1f56de575665121a967528753500cd2f809b61664e0e3f`.
- New Honda-only `pandad` AArch64 ELF SHA-256: `6fec6261fae4a84de75ef16f6fa604df01cd66f56e6ccea596fdfd890698d671`.
- Offline suite: Ubuntu 444 pass/1 skip, ARM64/QEMU 444 pass/1 skip.
- Compiled host Honda Panda C-safety suite: 369 pass/267 skip; no physical Panda behavior tested.
- Boot contract model: 39 simulations pass, **not a trusted OS supervisor**.
- Installed AGNOS 19.8.1 forensic comparison: 4487/4500 MiB raw matches pinned; all 13 differing windows reconciled to ext4 metadata/journal and two background image files. OEM root of trust, active dm-verity and enforcing SELinux not established.

## Mandatory physical release gates still HOLD

1. Independently establish an authenticated OS boot/root trust policy, actual signed image/vendor chain and permission/xattr/metadata security assessment. Raw byte similarity is not secure-boot authentication.
2. Implement a protected health authority **outside mutable /data/openpilot**, validate healthy manager/model/Panda state over a bounded probation interval, and demonstrate power-failure, bootloop and true A/B rollback on a sacrificial comma.
3. Prepare a **different** signed, recoverable candidate and verify complete native Python, NumPy, model, system dependencies and actual off-road startup on controlled hardware.
4. Independently validate Honda Panda/CAN hardware fail-safe and disengagement, and obtain qualified release authorization. Owner acceptance of scope exceptions for R2/R4 or unrelated Toyota functionality cannot substitute for physical Honda safety evidence.

This branch is public engineering evidence, not a safe-to-drive release, **not an installation URL** and **not a production tag**. It must not install or flash the comma, modify boot partitions, engage CAN actuation or replace the existing functional application. Any future production branch must be based on separately reviewed signed source, measured hardware evidence and a fully tested rollback route.

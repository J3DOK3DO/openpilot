# C8 combined offline build closure report

2026-11-15 Asia/Dubai. Codex implementer, source entry `0bdc95e610d4e8766438cbc7b0de2035247adcdd` on `accord11g-dom7-c8-2-c8-build-closure-offline-20261115`. C8.2 Panda steering source is the unchanged C5/C6 fix from `38b51582deb2a75430b5f9c0dfec95e0f685449c`; this campaign changed documentation only. Resolve the final local C8 commit by `git rev-parse HEAD` after commit; this report cannot embed its own commit SHA.

## Result

| Decision | Status | Evidence |
|---|---|---|
| Exact-source ARM64 subset | **PASS_BOUNDED_ARM64** | New msgq native objects/archive/test ELF compiled and ran 20/20 tests; ELF SHA and commands in [build attempts](C82_C8_ARM64_BUILD_ATTEMPTS.md). |
| Exact 20.5.2 product dependency | **FAIL_DEPENDENCY** | Manifest requires raw system hash `4f2aa503…`; bounded caches hold 19.8.1 and 19.9, with differing measured/provenance hashes. See [ABI audit](C82_C8_ENVIRONMENT_AND_AGNOS_ABI_AUDIT.md). |
| QCOM five-target input consistency | **PASS_INPUT_CONTRACT_ONLY** | All five were freshly reverified against current source; no package imported or regenerated. See [matrix](C82_C8_QCOM_PRODUCT_RECEIPT_MATRIX.md). |
| Full native product and receipt | **NO_GO** | No 20.5.2 sysroot, full build, release Panda certificate, target runtime/inference proof or matching `prebuilt.json`; exact entry receipt checker exited 1. |
| Independent safety review and physical qualification | **HUMAN_SAFETY_PENDING; HARDWARE_PHYSICAL_NO_GO** | No exact-final-commit C8 reviewer verdict and no device connection. See [later hardware handoff](C82_C8_LATER_HARDWARE_QUALIFICATION.md). |

The old 19.8.1 sysroots agree byte-for-byte on 19 measured present ABI files, proving only consistency between those old copies. A cached TrackAB venv and a cached nanobind package let root SCons perform a **generic AArch64 read-only dry run** of `msgq_repo/msgq/test_runner`. Neither the dry run nor C7's H7 DEBUG compile closes target AGNOS ABI, whole-product build or firmware release gates. Disk stayed above the stop thresholds; `/tmp/c82_c8_native_20261115` was under 1 MB at inspection, persistent log copies under 100 MB.

## Carried evidence and waivers

C5/C6's exact native Honda suite passed 35, lifecycle suite passed 28, and C8.1 selected strict bus-0/HOLD suite passed 8 with 48 deselected. C7 already built an H7 DEBUG main/bootstub and AArch64 AOL test/Params object. Those source paths did not change here, so repeating them would add no evidence. The Jetlink event baseline is 2 failed/5 passed and remains open. Broad GUI/restore, model inference, full product compilation, firmware release signing, physical standstill, CAN2/controlsMismatch diagnosis and device identity checks were skipped because prerequisites or authorization are absent; none is silently treated as passed. C8.1 owner waivers cover redundant GUI and restoration rehearsal logistics only. They do not waive native, Panda, independent safety or physical gates.

## Handoff

The reviewer packet is this report, the four companion C8 documents, `C82_C8_BUILD_MANIFEST.json`, small command logs and ABI hashes in `D/evidence/C8_2_C8_OFFLINE_20261115`, and the exact post-commit SHA supplied by the orchestrator. Challenge old sysroot provenance, the diagnostic root dry run, QCOM producer trust, inherited product artifacts, receipt failure, Honda 80/81 TX handover and CAN2/controlsMismatch. A separately created **preliminary** Qwen text in that evidence directory predates the final C8 commit and relies mainly on C7; it is excluded from Codex's manifest and cannot serve as final review. Qwen2.5-Coder/OpenCode on Windows will review separately after freeze; exact-final-commit reviewer status is **pending**, not authored by Codex. Next engineering step is trusted offline acquisition and hash verification of the exact pinned image, then isolated target-native build and independent review. This source-only C8 candidate is neither an install package nor a road release.

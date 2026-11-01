# Claude Track A/B unified campaign — continuation checkpoint

Kept here (not repo root) so the whole-repository isolation scan's `docs/` allowance covers it.

- Worktree: `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/dom7-v4-trackb-mandatory-final-20261101`
- Branch: `accord11g-dom7-trackb-unified-integration-20261101`, started from `d88e2918021908b260bc0d4c427277037bfd1019`
- Final artifacts: `/mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/trackb-unified-final-artifacts-20261101/`

## Completed

1. Baseline verified: HEAD `d88e2918`, clean, Track A `5fa8b2ed8` in ancestry. `opendbc_repo/` and `panda/` are vendored (no submodules).
2. Three-way audit: MVL `3fec9a41` (629 tree entries / 553 blobs), comma `1bce882c` (513 / 455), Dom `d88e2918`. 189 relevant paths classified, 0 NOT_REVIEWED. Inventory: `TRACKB_MVL_3FEC9A_SOURCE_INVENTORY_20261101.tsv`.
3. 84-ID: all 84 dispositioned; 0 mandatory missing implementations. The "55/29" split is the patch-kit matrix scope, not the ledger `track_B_status` (60/24); 15 IDs differ, all covered. Matrix: `TRACKB_84_ID_DISPOSITION_MATRIX_20261101.tsv`.
4. 244 skips classified: 204 abstract base classes, 30 no regen message, 10 no second speed message; none mandatory.
5. New non-actuating work: `test_accord11g_trackb_mvl3fec9a_canfd.py` (23 tests), `tools/trackb_research/release_b_gate.py` + `test_release_b_gate.py`, `RELEASE_B_EVIDENCE_REGISTER.json` (all 12 requirements HOLD).
6. AGNOS: `/home/jdkd/AGNOS_20261014/` **absent**. Pinned release image `/home/jdkd/g06-agnos-offline-20261014/cache/agnos_system.img.xz` sparse SHA-256 = agnos.json `9c753bdd…3832cfd`; sysroot glibc 2.39 / Python 3.12 / libusb-1.0.

7. Sparse-checkout defect fixed: the whole-repo isolation scan now also reads every index blob (1,287 skip-worktree files were unscanned), with no test-name exemption.
8. ARM64 (QEMU, `dom7-trackb-arm64:20261030`, git-backed fixture): all pass, 0 skipped. Host consolidated set: 2003 passed / 246 skipped (all classified).
9. Codex independent review: R1 REJECT → fixed; R2 APPROVE WITH FINDINGS → P3 doc fixed.

## Release status

- Release A: publishable non-production engineering candidate; installation candidate NOT established (gates 4/5 HOLD; ARM64 release build and packaging NOT_RUN).
- Release B: ENGINEERING COMPLETE / PHYSICAL QUALIFICATION HOLD (B1, B3-target, B4-device, B5, B6 HOLD). No actuation path exists.

## Next (needs the user or a device)

Read-only device audit (AGNOS hash/slot, Panda firmware, current commit + Params backup), then the B1 OEM evidence. Optionally a full ARM64 release build. See `TRACKB_DUAL_RELEASE_FINAL_VERDICTS_20261101.md`.

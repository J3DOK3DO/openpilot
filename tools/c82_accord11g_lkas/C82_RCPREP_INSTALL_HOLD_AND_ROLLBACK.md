# C8.2 RC prep installation hold and rollback identity

2026-11-15 Asia/Dubai. **HOLD: source review candidate only. No installation, device connection, USB use, Panda flash, CAN TX, actuation or road test is authorized by this packet.** The RC prep branch begins at `38b51582deb2a75430b5f9c0dfec95e0f685449c`; its later commit is documentation only. It has no valid C8.2 prebuilt receipt or qualified product binaries.

## Known identities from retained records

| Role | Exact Git identity | State |
|---|---|---|
| C8.1 last verified installed release and intended **manual reinstall rollback** | `9d2da330f6539beb5afb67867b28491526c0e1bd`, branch `accord11g-dom7-c8-1-gui-release-20261113` | Historical installed identity; device was not checked again in this campaign |
| Original Dom fallback | `ab468b8ecd1baa3e63fb5436b69253213d892b5d` | Historical fallback only; not a substitute for verified C8.1 |
| C8.2 frozen vehicle-control source parent | `38b51582deb2a75430b5f9c0dfec95e0f685449c` | Offline parent of this RC prep worktree; never installed |

The C8.1 GUI release report records its previous ref as Dom `ab468b8` and its release branch at `9d2da330`. The C4B crosswalk records the owner's acceptance of **manual reinstall** as rollback, waiver of a full-image restoration rehearsal for the offline campaign, and possible settings reset. Those logistics choices do not certify C8.2 safety or prove that a future recovery will work. No manual reinstall is performed or instructed now. A future custodian must independently confirm the source, matching image, settings implications, installation method and recovery access before any separately authorized change.

## Hold and future prerequisites

The receipt check for the frozen parent exited 1 with no matching build receipt. The source checkout also contains inherited `panda/board/obj/version` (`DEV-de2df523-Pf38f504f-DEBUG`), older signed Panda bytes and an AArch64 `pandad`; none proves a C8.2 target build. The `/tmp` H7 **debug** main build is a feasibility artifact, not an installable firmware release. Do not use this branch, those inherited binaries, or the debug image for a manual install.

Before a separately approved installation could be considered, the exact reviewed final source commit needs a real target Panda release firmware build and safety-mode/param identity, a complete Qualcomm/product build from matching inputs, validated receipts and artifact hashes, and independent human safety review. Independent standstill steering protection, CAN2 interrupt/`controlsMismatch` diagnosis, EPS/CANCEL behavior, driver cues, and a controlled nonactuating-first physical qualification plan remain open. The owner may continue to skip Comma-based checks **in this offline preparation**; that does not make the current candidate ready for vehicle use. A later installation decision must be made separately after these gates are closed.

If a future authorized change fails qualification, the intended rollback identity is the last verified C8.1 commit above, by manual reinstall under a separate approved recovery plan. The original Dom SHA remains a fallback reference. Record actual device and firmware identity at that future time; do not infer it from this packet.

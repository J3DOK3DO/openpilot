# G8-F12 RC1 — Engineering publication only / NO INSTALL

**This GitHub branch is deliberately NON-RUNNABLE.** It is not a production release, not an installer URL, and is not safe for vehicle use. The root launcher exits with code 78 before hardware initialization or boot-success calls. Do not remove the guard or point a comma installer at this branch.

## Publication scope

- Base source commit: 65d045a2a3df3eb6915618567be8fb61c6b08353
- Frozen offline Stage4A: 14 current-source-built AArch64 ELF outputs, four regenerated localization source files, and a SHA256-verified driving model reconstructed offline from three existing source-controlled chunks.
- GitHub branch contains the 14 ELF outputs and four regenerated sources, but does not store the reconstructed 126 MB driving model as a Git blob. The three original source-controlled chunks remain unchanged; the exact model SHA256 is recorded in the publication manifest.
- Full offline snapshot and 6,725-file manifest were previously verified on Ubuntu and Windows; this branch differs because of the fail-closed launcher and omission of the assembled model.
- This branch must not become the default branch or production installation branch. Do not target this branch with an automated release, firmware flash or updater workflow.

## Tests and known defects

- Ubuntu: 431 passed, one skipped. ARM64/QEMU: 431 passed, one skipped. Five native extension imports, localization, eight H3 and four acados load checks, and non-actuating Panda loader resolution passed offline.
- Active comma AGNOS 19.8.1 boot image bytes matched pinned manifest; active system image bytes failed its manifest hash. Trusted system-image signing, verified boot and recovery remain unqualified.
- Base launcher has premature abctl --set_success before trusted application health. It is protected in this publication by an unconditional abort and is NOT fixed for production. Stage3 offline alternative also lacks a qualified trusted supervisor.
- Twelve inherited H3/acados vendor binaries lack fresh source provenance; valid import/load and byte parity do not replace source attestation.
- R2 Panda/SPI and R4 driving-control findings are user-accepted project-scope exceptions, NOT successful engineering tests or physical vehicle safety qualification.
- No deployment, Panda firmware flash, boot-slot change, CAN actuation, physical recovery testing, production release signing, release tag or driving qualification was performed.

## Mandatory Stage 4B release gate

Resolve system-image authenticity mismatch, qualify trusted boot-success and A/B rollback, complete inherited vendor provenance and physical hardware safety tests, obtain independent approval, then build a DIFFERENT signed deployable release. This branch remains NO INSTALL. Do not publish an installation URL for this branch.

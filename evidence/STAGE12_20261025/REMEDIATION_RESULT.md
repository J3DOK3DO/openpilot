# Stage 2 post-review remediation and final disposition

Date: 2026-10-25. **NON-DEPLOYABLE HOST-ONLY MODEL. Not an installer.**

The independent reviewer found 4 MAJOR concerns and several MINOR items. A later Codex remediation attempt hit an account usage limit before editing. Narrow offline patches were then applied to the new prototype and tested on both host and ARM64/QEMU. This amendment is not an independent re-review or production safety approval.

## Locally implemented and tested
- **Health agreement:** The signed independent health observation must have the same exact measurement digest as the envelope submitted to the protected mock authority. The protected authority still separately checks its signature. Mismatch moves the journal to HOLD.
- **Revoked cached grant:** A repeated identical cached launcher-observation request now re-reads the protected policy epoch, generation and recovery identity and protected attempt count. A canceled or changed protected trial triggers HOLD, never returns the old decision.
- **Journal and path hardening:** Rebind loaded OS/device/recovery identities to instance-pinned values; detect coordinated OS/gate changes; reject a symlinked host journal directory, unsafe directory ownership/mode and unsafe lock files.
- **Four additional negative tests:** independent/protected health mismatch, cached grant revocation, coordinated OS-journal tamper and symlinked journal root.

## Unresolved MAJOR findings and safety restrictions
- **Full hardware-bound launch context:** The retained protected authority BootGrant still lacks a single verifiable signed boot/OS/device/physical-gate/snapshot context. A production F6-style consumed grant integrated with protected immutable policy is required.
- **Journal trust:** A local writable canonical journal is not rollback- or replay-resistant. Some coordinated gate/trial/request edits remain potentially plausible unless re-authorized against immutable external authority. No host-only patch can substitute for protected storage and signed snapshots.
- **System integration:** No OS-resident protected supervisor, secure verified boot/key custody, hardware restart/rollback, Panda/Honda physical qualification or actual RC3 process start is implemented or claimed.
- **Code assurance:** The separate independent review applies to the initial model; the manual remediation has unit/regression evidence but needs follow-up independent review before any software approval.
- **Planner:** The unchanged RC3 exact Git-path allowlist rejects the engineering worktree. It was not relaxed. No release package approval can be inferred from isolated unit suites.

## Test results, clearly scoped
- Focused supervisor, readiness and prior contract tests: **67 passed, 0 skipped, 0 failed** on Ubuntu and ARM64/QEMU.
- Integration-isolated release-tool tests (excluding only the two planner-dependent modules): **511 passed, 1 skipped, 0 failed** on Ubuntu and ARM64/QEMU.
- Entire unchanged suite: **542 passed, 1 skipped, 21 setup errors** on Ubuntu, due to the unchanged package planner.
- Frozen launcher guard is unchanged and exits 78; active comma remains untouched. All installation, OS slot switching, Panda/CAN operation, device actuation and road use are unauthorized.

## Next independent prerequisites
Externally audited protected F6-style signed grant, hardware-backed storage and device resident recovery, physical bench evidence, repeat full integration test against an accepted release-planner policy, and independent reviewer signoff. Preserve HOLD until all pass.

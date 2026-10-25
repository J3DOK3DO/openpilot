# G8-F12 RC3 supervisor and hardware-evidence handoff

## Binding and disposition

- Frozen Honda RC3 commit: `bbb771a2fadf5af96f532e798846ba8171483e50`
- Frozen Honda RC3 tree: `fcd3142e877a165911a677f9361c6594f3eecf6b`
- Engineering commit inspected: `93cf96efd6b026854464b9aa505f01ad3c45b4a2`
- Engineering tree inspected: `a9a481ad44848c2708ef7c1bc45b24fcf3fcd48a`
- Platform string required by the gate: `HONDA_ACCORD_11G`
- Launcher guard remains exit 78.
- Current disposition: **HOLD; no physical evidence supplied**.

`RC3_HARDWARE_READINESS_GATECARD.json` is the canonical no-evidence result produced by the gate logic. Owner authorization and risk acceptance were not inferred from the engineering prompt and are false in that gatecard. Even if present in a future manifest, those fields only report context and have no effect on technical completion.

## New engineering artifacts

`tools/g8_release/rc3_hardware_readiness_gate.py` is stdlib-only, offline, verification-only code. It enforces canonical JSON, strict exact-key schemas, duplicate-key rejection, safe relative paths, non-symlink descriptor traversal, bounded stable reads, per-artifact and aggregate size caps, SHA256 descriptors, freshness, exact source/tree/platform/hardware bindings, exact gate/contract source hashes, unique evidence files, an externally pinned trust policy, separate operator/reviewer identities and organizations, Ed25519 signatures, and signed monotone progression records. There is no signing function or external-operation interface.

`tools/g8_release/rc3_supervisor_contract.py` is a NON-DEPLOYABLE design contract and observation-only state model. It reuses the existing `ProtectedAuthority` calls for authorization, durable attempt consumption, authenticated health, cancellation, and transactional promotion. It returns no launcher path, does not emit systemd unit text, and cannot start or install anything.

## Reuse of existing mechanisms

- `g8_protected_authority.py`: exact protected trial/attempt/health/promotion authority protocol; its file-backed implementation remains a host mock, not hardware.
- `g8_f6_early_boot_boundary.py`: required future verified-OS/immutable-snapshot boundary and consumed authorization interface; not instantiated here.
- `g8_slot_supervisor.py`: existing sealed-slot/tree verification and recovery invariants; not installed or invoked as an on-device service.
- `rc3_package_planner.py`, `rc3_external_trust.py`, and `rc3_host_staging.py`: retained as guarded frozen-inventory and host-simulation mechanisms. Their caller-supplied synthetic trust cannot qualify production.

## Open binding requirements

Future physical evidence must bind every signed observation to the frozen and engineering identities above, the signed-package digest, exact comma and Panda identity hashes, AGNOS/bootloader versions, `HONDA_ACCORD_11G`, a fresh qualification ID/run nonce, and the monotone predecessor. The evidence root must contain unique raw artifacts for all seven groups listed in `LAB_QUALIFICATION_PLAN.md`.

The attester trust-policy SHA256 must arrive through an independent channel. Both operator and reviewer keys must have physical-qualification purpose, separate identities and organizations, and independence from owner and developer. The gate validates signatures and bindings but lab governance must establish the truth of those key-policy claims and chain of custody.

## Handoff decision

Do not install, flash, modify a boot slot, call `abctl`, launch openpilot, connect Panda/CAN, or actuate. Proceed only with the isolated lab plan. On any missing, stale, replayed, malformed, mismatched, symlinked, oversized, digest-invalid, signature-invalid, or non-independent record, retain HOLD.

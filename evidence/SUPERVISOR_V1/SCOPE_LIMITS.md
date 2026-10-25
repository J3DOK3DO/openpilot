# Scope and limits

## Performed

- Read the existing protected-authority, early-boot boundary, slot supervisor, RC3 host staging, external trust, package planner, pertinent tests, and prior handoff prompt.
- Added an offline canonical evidence verifier with strict schemas, duplicate-key rejection, bounded descriptor-relative reads, `openat`/`O_NOFOLLOW` path handling, stable-file checks, SHA256 verification, source/tree and hardware bindings, freshness, Ed25519 operator/reviewer attestations, and signed monotone progression bindings.
- Added a non-deployable OS-resident supervisor design contract and observation-only state model using the existing `g8_protected_authority.ProtectedAuthority` interface.
- Added adversarial synthetic tests and ran the complete host release suite.

## Not performed and not claimed

- No hardware-backed boot-chain, verified-boot, antirollback, RPMB, secure-element, or bootloader measurement.
- No proof that a supervisor is installed in verified OS storage outside `/data/openpilot`.
- No AGNOS/systemd integration, SELinux validation, hostile-device writer test, actual block-storage durability test, application execution, or OS boot-success marking.
- No signed reproducible release package from a production release authority.
- No native ARM64 startup, model execution, or pandad observation on comma hardware.
- No physical power-cut, bootloop, forced-failure, retry, rollback, or recovery experiment.
- No Honda Accord 11G Panda/CAN bench work: fail-silent, watchdog, disengagement, allowlist, and heartbeat behavior remain unmeasured.
- No independent physical-lab operator or reviewer evidence and no independently provisioned trust-policy digest.
- No production, installation, boot-operation, vehicle, or road-use approval.

## Trust boundary limits

The gate can prove that bytes match descriptors and that signed observation payloads verify under keys in the exact externally pinned trust policy. It cannot prove that a named organization is genuinely independent, that a private key was well controlled, or that a log originated from physical equipment unless the trust-policy provisioning and lab chain of custody establish those facts. Owner authorization and risk acceptance are context fields only; they never satisfy a technical requirement.

The existing protected authority and early-boot adapters are ordinary-file host mocks marked simulated/non-deployable. Passing their tests is not evidence of protected storage, real early boot, atomic power-loss durability, or hardware antirollback.

The service contract is design data, not unit-file text. No `ExecStart` or executable implementation is provided.

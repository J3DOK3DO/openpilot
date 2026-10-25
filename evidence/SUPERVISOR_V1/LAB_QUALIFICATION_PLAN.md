# Non-actuating path to physical qualification

All work remains HOLD until every irreducible record below is captured on the bound hardware and reviewed under an independently pinned attester policy. Owner approval may authorize the lab to proceed but cannot replace observations.

## Safe lab boundaries

1. Use an isolated reproducible-build lab to produce and independently verify the signed package. Keep signing credentials and the attester trust-policy pin outside the application source and evidence bundle.
2. Use a comma hardware security/boot lab with the device disconnected from a vehicle. Physically neutralize CAN transmission and instrument power, boot console, storage, and verified-boot state.
3. Use a programmable-power fault lab for bootloop, abrupt power-cut, partial-write, exhausted-retry, forced startup/model/pandad failure, and recovery measurements. Preserve raw instrument logs and the exact fault matrix.
4. Only after the no-CAN device work passes, use a non-vehicle Honda 11G bench with a harness/load simulator, monitored bus, independent emergency isolation, trained operator, and independent reviewer. Do not use a public road or a movable vehicle for qualification.

## Required evidence groups

- `boot_trust_antirollback`: pinned boot-chain measurement and a demonstrated downgrade/rollback rejection.
- `os_resident_supervisor`: measured placement in verified OS storage outside writable `/data/openpilot`, plus isolation and service-sandbox tests.
- `authenticated_trial_recovery`: authenticated authority/health exchanges and transactional attempt, rollback, and promotion tests across real restarts.
- `signed_reproducible_package`: signature-chain verification and independent byte-for-byte reproducible-build comparison bound to the source/package digest.
- `native_arm64_neutral_can`: observed ARM64 startup, model execution, and pandad startup while CAN transmission is physically neutralized.
- `physical_failure_recovery`: complete bootloop, power-cut, forced-failure, and recovery matrices on the bound comma hardware.
- `honda11g_panda_can_bench`: observed fail-silent, watchdog, disengagement, allowlist, heartbeat, and safety-summary results on the isolated Honda 11G bench.

Each group needs unique raw artifacts; one file cannot satisfy two checks. Its signed payload binds the qualification ID, fresh run nonce, monotone predecessor, frozen and engineering source identities, signed-package digest, exact comma/Panda identities, platform, observation window, operator key, and reviewer key. Operator and reviewer must have distinct identities and organizations and both must be independent of owner and developer under the externally pinned trust policy.

## Decision sequence

1. Capture artifacts create-only and retain chain-of-custody originals.
2. Build canonical requirement payloads and obtain operator then independent-reviewer Ed25519 signatures.
3. Run the offline gate against a separately pinned trust-policy SHA256.
4. Treat any parse, path, digest, signature, identity, freshness, replay, or requirement error as HOLD.
5. Even a complete physical gatecard does not authorize action: it reports `EVIDENCE_COMPLETE_AWAIT_EXTERNAL_RELEASE_DECISION`, keeps production/install/boot/road fields false, and records an external-decision hold.
6. Installation or boot-slot work requires a later explicitly scoped run, a separate release decision, and its own safety procedure. This host run grants no such capability.

# G8-F12 RC3 Honda — Stage 3 physical qualification handoff (not authorization)

State: HOLD. Stages 1 and 2 in this worktree are static ABI inspection and **non-deployable host-only supervisor simulation**. There is no installed OS-resident supervisor or protected authority, no signed production package, and no Honda physical safety approval. The staged comma archive must remain inert.

## Preconditions before even beginning bench tests
1. Independently verify Honda Accord 11G Panda firmware/source combination, supported safety mode, allowed CAN topology and physical relay/isolation capability with a qualified bench operator. Tests must use a dedicated isolated bench rig or disconnected vehicle controls—not public roads or an actively controlling Panda.
2. Provision independently maintained trust anchors/key custody, signed candidate manifest and hardware-backed verified boot; lock down OS-resident supervisor and rollback-resistant monotonic storage (e.g. independently evaluated TEE/RPMB design); confirm actual enforcement rather than relying on mutable /data or SELinux permissive.
3. Document protected recovery app identity and how a known-good existing release is recovered without confusing AGNOS OS slot _b with openpilot app rollback. Obtain a tested physical recovery procedure and human technician present.
4. Verify electrical safety, device health, power/thermal limits, test instruments and reliable external logging. Define normal shutdown and emergency disconnection criteria before stimulating failures.
5. Sign test-plan approval by test operator and **separate** independent safety reviewer, and preserve unedited raw measurement data with source, hardware revision and UTC timestamps.

## Required tests (no physical testing performed by this campaign)
- Verified OS trust and anti-rollback: prove source identity, key rotation/revocation, kernel/OS measurement, non-writable early-boot policy, immutable app snapshot and signed health authority.
- Native runtime off-road and non-actuating: demonstrate manager/model/pandad startup, process health and clean exit **with Panda/CAN transmit electrically prevented** and receipt binding verified; log load failures and missing libraries.
- Power-loss and recovery: failure before/during/after durable attempt charge, failed health, forced crash, interrupted copy/rename, full data filesystem, corrupted metadata, stale/forged health, stuck restart/boot loop, repeated reboot. Show bounded retries and automatic return to a known-good app across actual power removal.
- Honda 11G Panda CAN safety: safety hooks for supported Panda firmware, transmit allowlist/denylist, heartbeat loss, watchdog expiry, speed/driver override/disengagement, controller output limits, CAN bus faults, explicit NO ACTUATION when supervisor unqualified.
- Long-form endurance/thermal and regression only after preceding non-actuating safety checks; no road operation before independent signoff.
- Separate reviewer assessment of signed test reports and evidence, explicit PASS/HOLD per item, production sign key governance and operator recovery drill.

## Stop conditions and release criteria
Any unknown host-to-Panda behavior, missing protected storage or recovery, inconsistent signature/health binding, fault-test failure, unverifiable rollback, missing CAN disengagement, or independent review refusal = HOLD. Owner risk acceptance alone never transforms a missing technical result into PASS.
No commands in this handoff activate the device, Panda, CAN or AGNOS alternate boot slot. Do not rename or move the staged archive into /data/openpilot.

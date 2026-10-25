# G8-F12 RC3 Honda — Stage 2B, Stage 2C and Stage 3A handoff

**Disposition:** Stage 2B offline verification prototype tested; Stage 2C protected-supervisor interface documented, real OS integration HOLD; Stage 3A comma read-only preflight performed and recorded. No device actuation, flashing, installation, AGNOS boot switch or RC3 startup. Not production deployable.

## Stage 2B

- Implemented a NONDEPLOYABLE host-only signed full-context verifier using the maintained cryptography Ed25519 public-key implementation.
- Enforces strict canonical JSON, duplicate-key rejection, test-trust domain separation, source commit, manifest, pinned app/recovery snapshot hashes, OS slot and boot identity, Panda/comma identity hash, gate receipt, nonce, monotonic sequence and trial attempt.
- **Real trust is unresolved:** the public key, policy and epoch floor remain supplied by the calling test. Re-signing or replaying the same record under attacker-controlled test trust cannot grant actual boot approval; this code explicitly returns no process/install/boot/Panda/CAN/road authority.
- Older stage2 host model and known source-level review limitations still apply. This new module does not patch or replace g8_protected_authority.BootGrant and does not implement protected launch authorization.
- Unit tests include wrong platform/OS/boot/rootfs/app/recovery/Panda/CAN gate fields, altered source and signature, wrong signing key, stale epoch, replay, invalid/noncanonical JSON, duplicate keys and impermissible runtime operation.

## Stage 2C

- Detailed integration contract in STAGE2C_PROTECTED_SUPERVISOR_INTEGRATION_CONTRACT.md specifies independently verified boot/rootfs, OS-resident supervisor outside mutable /data, protected monotonic retry/health authority, immutable known-good application fallback and Panda hardware isolation.
- No OS service, systemd unit, hardware key custody, TEE/RPMB authority or rollback supervisor was installed or activated. Root read-only alone is not verified boot. Existing AGNOS system A/B slots cannot substitute for openpilot application rollback.
- Thus actual Stage2C integration acceptance criteria have NOT passed; real supervisor implementation/testing remains a hard HOLD.

## Stage 3A

- Read-only native comma inventory confirms AGNOS 19.8.1, AArch64, original openpilot commit, unchanged RC3 inert source archive and OS slot _a. Root filesystem ext4 mounted read-only; shared /data ext4 read-write; SELinux kernel boot setting permissive.
- No visible /dev/tee*, /dev/tpm*, or *rpmb* device nodes; these observations do NOT prove the hardware lacks such a capability. No secure boot or hardware-backed key authority was independently verified.
- No Honda/Panda physical bench CAN testing, power-cut recovery, startup or off-road native model runtime tests were attempted.
- Stage3A is a safe **inventory result only**, not physical safety qualification.

## Tests

- Ubuntu and ARM64/QEMU focused signed context + old supervisor/readiness tests: **113 passed, 0 failed/skipped** in each environment.
- Ubuntu and ARM64/QEMU broader regression excluding 2 planner-dependent modules: **557 passed, 1 skipped, 0 failed/errors** in each environment.
- Full unmodified Ubuntu release-tool suite: **588 passed, 1 skipped, 21 setup errors**. All 21 are from the original RC3 package planner refusing non-allowlisted engineering changes; its integrity guard has not been weakened.
- Separate Codex Sol High independent security review **was attempted but unavailable due to usage limit**. This is not an independent software/safety signoff.

## Remaining mandatory acceptance criteria

1. Independently assessed hardware-rooted signing/secure boot and a complete signed consumed-launch grant bound to OS, device, recovery, physical safety gate and immutable source/artifact measurements.
2. Actual protected monotonic state, OS-resident supervisor and power-loss-tested rollback to a signed known-good application outside attacker-writable storage.
3. Native ARM64/AGNOS runtime tests on a controlled device with Panda/CAN electrically isolated, followed by Honda Accord 11G physical CAN safety bench and independent signoff.
4. Revised signed production manifest and release planner policy reconciliation through an independently authorized engineering change (not suppressing the existing strict rejection).
5. Complete separate software-security reviewer acceptance and physical Honda/Panda reviewer acceptance.

**No production installer, boot-slot-switch approval, device runtime activation or road-use permission arises from this campaign.**

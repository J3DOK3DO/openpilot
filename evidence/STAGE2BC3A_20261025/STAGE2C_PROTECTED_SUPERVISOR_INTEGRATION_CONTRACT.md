# RC3 Stage 2C — protected OS-resident supervisor integration contract

**Engineering design only: no installable unit, no ExecStart, no daemon, no activation.**

## Trust and execution boundaries

- AGNOS 19.8.1 on comma: root was observed read-only ext4, /data ext4 read-write, SELinux in permissive mode. Rootfs authenticity has not been independently proven. A read-only filesystem is not a cryptographic boot trust chain.
- AGNOS OS A/B slots (_a and _b) are distinct from openpilot application candidates on shared /data. OS-slot switching cannot substitute for verified application rollback.
- A device-resident recovery authority must live *outside candidate-controlled writable application storage*, in independently verified/immutable storage, before any candidate startup. Neither a /data folder nor a host temp-file journal meets this requirement.
- A vetted crypto verifier must authenticate a production release policy, signatures, revocation, source/build provenance, immutable application snapshot, Honda Panda firmware identity, boot/rootfs digest, device identity, accepted gate result, startup nonce, trial epoch and bounded retry grant.
- Monotonic generation, epoch, retries and health decisions must be durable under tested physical power loss and hostile candidate tampering. TEE/RPMB or equivalent authority needs separately assessed hardware evidence. If absent, fail closed.
- Independently qualified, immutable fallback application identity and tested physical recovery procedures are prerequisites. Do not confuse an AGNOS system boot slot with an app rollback slot.
- A distinct protected health authority must attest the same measured startup identity/epoch/nonce as the granted attempt. Timeouts, mismatches, replay, inconsistent counters and unsigned owner overrides reject authorization.
- Panda/CAN access must default physically isolated and non-actuating until independent Honda Accord 11G bench approval. Process health does not certify vehicle safety.

## Required ordering (design, not an executable procedure)

1. Verify OEM bootchain/root integrity and independently pinned trust anchors.
2. Establish protected OS supervisor outside mutable candidate application, with credible enforcement despite observed permissive SELinux.
3. Verify source, artifacts and a signed immutable candidate snapshot using vetted cryptography and a protected rollback-resistant policy.
4. Consume exactly one monotonic attempt before execution; issue an externally attested, exact-context, single-use launch grant.
5. Start any process only in a controlled isolated bench with CAN physically unable to actuate; validate authenticated startup-health receipts.
6. On failed health or interrupted durable state, select a separately signed known-good application and prove recovery.
7. Promote or release only after independent hardware recovery, Honda/Panda safety, release signing and software signoff.

## Evidence required

- Hardware-rooted verified boot, signing key governance and immutable supervisor code authority.
- Protected monotonic data store, testable retry budgets and fault injection across real power removal.
- Actual OS-resident implementation, verified ordering/access boundaries, known-good application recovery and signed production release.
- Native comma runtime compatibility, electrically isolated Panda/CAN safety tests, watchdog/disengagement, human reviewer.
- Release-planner integration without weakening its existing exact allowlist; recorded full regression acceptance.

## Device findings 25 October 2026

Stage 3A read-only inspection: OS _a; AGNOS 19.8.1; active app and inert archive unchanged; read-only root, writable /data, SELinux permissive. No exposed TEE/TPM/RPMB nodes were seen. Their absence is NOT evidence that the hardware cannot support protected trust. Protected supervisor identity, key custody, measured startup and physical rollback are unknown.

Stage 2B prototype rc3_stage2bc_context.py uses caller-supplied test trust and mock monotonic floor and returns no runtime permissions; it cannot be installed or promoted to a production authority.

**Disposition: Stage 2B offline design verified but hardware anchoring HOLD; Stage 2C implementation HOLD; Stage 3A read-only inventory completed; Stage 3B physical bench not started; Stage 4 install blocked.**

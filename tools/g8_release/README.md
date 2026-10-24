# C7 G8 host-only manifest and recovery reference — NOT FOR DEPLOYMENT

This reference implementation is for offline tests and secure-design review.
It is not integrated into AGNOS startup, does not authorize installing on comma,
and does not provide vehicle/Panda/CAN actuation or road-test approval.

The manifest verifier uses Ed25519 and fails closed on untrusted/dev-only keys
by default. The slot supervisor requires an independent, caller-pinned trust
policy and approved source commit, stores a signed manifest per slot, and
checks the signature, source policy, slot metadata, complete tree hashes and
launcher before stage/activation/boot/recovery/rollback. Passing a fake
verifier callback is no longer a supported authorization method.

**Test signing keys are disposable, generated in memory, and marked
SIMULATED_TEST_TRUST; they are not production-release credentials.**

Remaining unproven properties: secure production key provisioning, external
hardware-backed anti-rollback state, early-boot supervisor placement outside
replaceable application storage, hostile concurrent-writer TOCTOU, atomic disk
durability after actual power cut, real ENOSPC, SELinux, AGNOS 19.8.1 device
loader and storage layout, true system health acknowledgment and independent
on-device rollback. G4-G7 technical safety requirements are still deferred.

Full G8 installation/rollback, Panda/CAN and road deployment: HOLD.

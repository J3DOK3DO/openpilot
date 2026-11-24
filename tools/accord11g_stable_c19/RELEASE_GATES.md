# C19 release gates

**Source integration: GO for independent scoped engineering review.** A source-only engineering prerelease can be prepared by the separate publisher only after that review passes; it must say `NO INSTALL / NO ROAD USE` and identify the Panda gap. This worktree has not been pushed or tagged.

**Parked-device install candidate: NO-GO.** Require independent integration and native tests of the C8.2 Panda token/Drive/host-zero safeguards, full relevant Honda and other-vehicle safety regression, genuine C19 exact-commit aarch64/QCOM product build, matching `prebuilt.json` receipt, correct Panda release signing identity, installed Panda/AGNOS identity, and non-actuating parked checks of watchdog, RX invalidity, EPS limits, CAN2 and controlsMismatch. Missing host `msgq`/`libparams_c.so` tests are still open and cannot be called passes.

**Driving: NO-GO.** Require actual vehicle functional-safety qualification, fault diagnosis and controlled physical validation after the parked gates. Earlier C8.1 road routes do not qualify C19. Manual reinstall rollback may replace a full-image restoration rehearsal only as a rollback method; it is not evidence that this software is safe. No device or road tests were performed.

The separate reviewer/publisher owns public publication. Protected `stable`, Dom and C18 remain untouched.

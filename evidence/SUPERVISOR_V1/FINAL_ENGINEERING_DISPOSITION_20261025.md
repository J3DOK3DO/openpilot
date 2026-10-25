# G8-F12 RC3 supervisor qualification: final engineering disposition

**HOLD — NON-INSTALLABLE ENGINEERING ONLY.** No device installation, OS boot-slot change, Panda/CAN activity or road-use authorization. Owner permission to proceed once independently qualified is recorded, but technical qualification is not complete.

## Verified host / simulated architecture tests

- Ubuntu release and supervisor suite: **531 passed, 1 skipped, 0 failures/errors**.
- ARM64/QEMU identical suite: **531 passed, 1 skipped, 0 failures/errors**.
- Honda-specific Panda safety **source-unit tests** in isolated ARM64/QEMU: **369 passed, 267 skipped, 0 failures/errors**. Source tests are **not physical hardware or vehicle qualification**.
- Corrected QEMU runner mounted Git common directory as read-only and used executable ephemeral /tmp; the first QEMU attempt with missing common Git metadata/noexec /tmp is a harness failure and is retained separately, not release evidence.
- Frozen baseline source tree and fail-closed exit-78 launcher were not altered.

## Outstanding critical gates

1. Hardware-backed verified boot/antirollback and separately trusted signing/attestation authority.
2. OS-resident application supervisor with protected state outside the writable app and authenticated bounded probation, with verified safe fallback. Current supervisor is a **non-deployable contract/model**, not an OS-installed protection.
3. Real controlled power-cut, bootloop, failed startup and recoverability tests on sacrificial comma hardware.
4. Native off-road model/manager/pandad startup on comma with demonstrably neutralized CAN.
5. Physical Honda Accord 11G Panda/CAN safety bench tests with operator and independent safety reviewer.
6. Independent security signoff. The attempted additional model review did not produce a completed report. The new readiness-gate module currently implements Ed25519 in pure Python; replace with an independently maintained/verified cryptographic implementation before production trust decisions.

## Evidence locations and traceability

- Machine gatecard: `FINAL_ENGINEERING_GATECARD_20261025.json` (SHA-256 `43cb6a04a1ff7e969da69dbc6d1c2a90d2f2f2e59e99d9a2298989ac404eb123`).
- Host JUnit: `/mnt/commadrive/g8-f12-rc3-supervisor-independent-tests-20261025/HOST_SUPERVISOR_FINAL.xml` (SHA-256 `6666936f42ff6d9526838b23b799b47a0cb53bbfd31aaee5bc6a659adbdeb8f1`).
- ARM64 QEMU JUnit: `/mnt/commadrive/g8-f12-rc3-supervisor-independent-tests-20261025/QEMU_SUPERVISOR_CORRECTED.xml` (SHA-256 `a60a85b268922a057553aadf0dcb403eb02bc9f57d5335466ef888ec29f053c6`).
- Honda source test log: `/mnt/commadrive/g8-f12-rc3-honda-safety-qemu-20261025/HONDA_QEMU_BUILD_AND_TEST.log` (SHA-256 `83c9028f4dfaed505ff2fc160c92d4fc77b4a3fc2350083b955c57637a064a6d`).

**Not an installer. Do not select AGNOS inactive boot slot or activate RC3 from this branch.**

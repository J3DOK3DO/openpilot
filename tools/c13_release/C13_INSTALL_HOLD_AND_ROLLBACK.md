# C13 — installation hold, explicit deferrals, recovery identity

**Status: HOLD / NO-GO.** This source-only pre-release is not approved for installation on the Comma 4, Panda firmware flashing, CAN transmission, custom steering/ACC actuation, or public-road evaluation.

## Decision record

The owner authorized C13 release-candidate **preparation** and accepted deferring fresh Qualcomm GPU execution and physical CAN2/`controlsMismatch` diagnosis during offline engineering. Those are **schedule deferrals, not successful safety tests or permanent release waivers**. They remain blockers for a later vehicle-operational release decision.

The current source-only preparation uses the already compiled code identity `586da6b91ffb43e2a1e114072104b694d3c8a2b3`, not an assumed installed code/firmware identity. No Panda safety logic was relaxed, and no actuation or device connection is part of C13.

## Historical recovery reference (not verified on device today)

- Last historically identified C8.1 GUI branch: `accord11g-dom7-c8-1-gui-release-20261113`.
- Historical C8.1 SHA: `9d2da330f6539beb5afb67867b28491526c0e1bd`.
- Historical original Dom fallback SHA: `ab468b8ecd1baa3e63fb5436b69253213d892b5d`.

The owner previously accepted **manual reinstallation** as the recovery approach, with possible loss of settings. This document does not attest that either image, installation method, or recovery access is currently available or validated. Do not attempt to install this C13 branch or use the historical identities as evidence of current device state.

## Conditions before a separate installation decision

1. Independent source and safety review using complete exact source, Panda CAN safety configuration, and fail-closed fault handling, with documented corrections and targeted regression tests.
2. Proven target Panda firmware identity and matching source/release build, installed AGNOS compatibility, and an authenticated **same-commit** prebuilt product receipt.
3. Actual Qualcomm producer/runtime and model-inference compatibility evidence on qualified isolated target hardware, not just cached input hashes.
4. Parked/isolated verification of CAN2 interrupt behavior, `controlsMismatch`, stock versus modified lateral/ACC authority, explicit EPS and driver-button behavior, alerts and fail-safe state. No on-road custom-steering tests while unresolved.
5. Reconfirm earlier install/rollback branch and exact commit, accessibility and recovery procedure, and decide whether to proceed **in a separate explicit safety release approval**.

Stop on unexplained safety mismatch, Panda refusal, unknown firmware identity, unexpected CAN transmission, or loss of fallback controls. Never bypass Panda protections to pass a release gate.

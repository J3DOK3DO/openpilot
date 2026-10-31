# Track B B0--B6 qualification status

## Current scope pin

This primary pass starts at `82e053f56c18a814f1a98ea10e7b2b4057ed7d76` on branch `accord11g-dom7-trackb-b1-b2-simulation-20261031`. It uses only current-native source/tests and new synthetic tests for qualification. Historical commit `7b4db9a26010ba9899eef242d3ca49b33cbcca9c` and recovery artifacts are reference evidence only; C6-12/C7 logs, replays, old tests, and old safety baselines are excluded from qualification.

| Gate | Required evidence | This pass | Status | Blocking evidence |
| --- | --- | --- | --- | --- |
| B0 | Non-actuating scope, hazards, reviewed acceptance record | Existing B0 hazard record plus this source-only boundary | PARTIAL | No target/device review. |
| B1 | Authoritative Bosch-C CAN-FD ownership, protocol, AEB/CMBS/fault semantics | Source inventory, official function pages, and unresolved-authority report | **PARTIAL / STOP** | OEM service architecture and independently reviewed target-specific non-actuating evidence. |
| B2 | Isolated downstream simulation of an authoritative plan contract | New stdlib synthetic abstract controller; it creates no planner or actuation | PARTIAL | No authoritative plant/controller/fault oracle; simulation is not vehicle authorization. |
| B3 active | Authorized active authority/safety case | No implementation or authorization attempted | **HOLD** | Explicit B3 authorization plus B1/B2 evidence, target firmware/device and independent review. |
| B4 | Authorized parked non-actuating verification | No device/vehicle access in this pass | HOLD | Separate authorization and target evidence. |
| B5 | Controlled later-stage test evidence | Not attempted | **HOLD** | B1--B4 completion and separate authorization. |
| B6 | Release/operational authorization | Not attempted | **HOLD** | B1--B5 completion and release approval. |

Current source retains `pcmCruise=True` and excludes Bosch CAN-FD alpha longitudinal (`interface.py:51-58`). That is a source-policy boundary, not an OEM or physical qualification. No status above authorizes custom longitudinal control, radar modification, diagnostics, Panda changes, or driving.

# C7 engineering baseline — 14 October 2026
Status: OFFLINE SOURCE BASELINE ONLY. NOT DEVICE QUALIFIED. NOT ROAD APPROVED.

- Direct parent: frozen road-tested C6-12 source `7b4db9a26010ba9899eef242d3ca49b33cbcca9c`.
- No C6-13A/B source merge or capture observer imported.
- All existing Accord11G steering, Honda braking, stop-hold, vision nonurgent confirmation, and following logic unchanged.
- StarPilot Dom public tip inspected: `b220a37f4bd119e402225a7aa16a7cd84878d0af` (three commits after `83f914fc`).
- MVL Boston Honda source public tip inspected: `66598eda130dde70fbf84278215adabd174afe36` (three commits after `cb0f8eb4`).
- MVL opendbc new pointer: `cf46117420f283b3e38241c00d728a191aa9fccc` (six commits after `0fbd1d50`).
- Do not auto-import Dom MPC terminal constraint changes, Panda SPI transport or firmware, arbitrary other-car actuator calibrations, or MVL Honda onroad-cycle handback.
- P0 interruptRateCan2 is user-deferred from engineering analysis and remains a separate unresolved safety issue; no safety checks bypassed.
- C7-0 exit: exact tracked source/tree identity versus C6-12, clean worktree, basic static checks and a working host-native x86 test harness before any functional changes.
- C7-1: conditional small, independent upstream patch groups with vehicle-scope guard tests.
- C7-2: only reproducible C6-12 comfort defects with RED/GREEN tests; no blanket gain/headway/brake-offset tweaks.
- C7-3: integrated host replay, native solver+CAN qualification and independent review.
- C7-4: separately approved parked qualification and controlled release.
C6-13 captured-state diagnostic tooling remains in its isolated legacy branch and is not required to alter C7 controller timing.

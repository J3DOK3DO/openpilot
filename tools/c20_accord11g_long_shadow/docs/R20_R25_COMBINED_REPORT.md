# C20 R20–R25 combined engineering report — 2026-11-28 UAE

## Result

The C20 worktree started at `519a981b72fc0ba1bf0a029904628990086b9f37`. Frozen C19 remains `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`. This campaign adds one manually launched, read-only product diagnostic using the **same C19 `LongitudinalMpc` Python source** (SHA-256 `3e2689f6c6366f98b2bfcfc1946074766585ed1e353a6fa22f9054934828d1ee`). C20 and frozen C19 `LongitudinalPlanner` also match by SHA-256 `5d78f335aa20f0490bb743dfc6a069317fda2eca3f6e7a5bc574578fdf3c8a7d`, but the full planner is **NOT_EXECUTED** in C20 shadow. No native product solve was run in this campaign.

Path A consists of read-only source, diagnostic admission, gate and packaging preflight. Path B1 is the same diagnostic's native MPC adapter: it subscribes to `carState`, `radarState`, `modelV2`, `controlsState`, `deviceState` and `carParams`; it validates receiver and source monotonic clocks, exact Accord 11G identity, stock ACC ownership, engaged factory cruise, driver override, stock AEB/FCW, radar faults, lead presence and restart floor. Then it calls the product `LongitudinalMpc.set_cur_state()` and `update()` without publishing a message. It ignores `modelV2` lead trajectories numerically; the model message is an admission signal only. Output is a small allowlisted JSON diagnostic with a hypothetical first predicted acceleration. This is **not** a full longitudinal plan or vehicle response. Any invalid cycle clears the MPC instance; native failure clears it and reports no execution. Import and CLI startup never load native MPC before admission. CLI requires `--shadow-only`, has a bounded number of polling cycles, and is absent from `process_config.py`, params, UI and controller paths.

The existing Honda interface leaves `alphaLongitudinalAvailable` false for Bosch CAN-FD and `pcmCruise` true when openpilot longitudinal control is false. Accord 11G remains under factory ACC. Existing Card/AOL, LKAS and controls mismatch logic was inspected and untouched; this diagnostic cannot repair or qualify those vehicle issues. No changes were made to `carcontroller`, Panda, opendbc safety, engagement, or carControl publication.

## Evidence classification

| Item | Current classification |
| --- | --- |
| R19 frozen C19 x86 Python MPC | Historical genuine Cython/ACADOS numerical execution, 24 synthetic cycles; nonnumerical import stand-ins disclosed in R19 receipt. This does not establish current product loop execution. |
| C20 product MPC | Source-integrated read-only adapter; **NOT_EXECUTED** on current product inputs or on AArch64. Synthetic unit double validates isolation only. |
| C20 full LongitudinalPlanner | **NOT_EXECUTED**; would require complete same-cycle planner state, model trajectories and controls messages. No bridge to command publication is planned here. |
| Recorded exact-vehicle replay | **NOT_RUN**; no authenticated same-cycle route admitted. |
| Product AArch64 build | **BLOCKED** on host: no AArch64 compiler or `scons`; QCOM package and compiled driving/DM models absent. Existing AArch64 solver ELF is not proof of a current product build. |
| Device, HIL, physical, road | **NOT_RUN / UNVERIFIED**. Path B2 active control **NO_GO**. |

## Checks and remaining gates

`r25_gate.py` emits deterministic named path statuses and checks exact starting ancestry, frozen C19 revision and cleanliness, source command-path audit, current git cleanliness, product prebuilt receipt and native dependency preflight. Dirty source is `PENDING_COMMIT`; historical logs never satisfy current acceptance. `r25_package.py` requires a clean exact commit after this work, an exact protected-inventory prebuilt receipt, AArch64 solver artifacts, compiled product models and a separate exact-commit SCons build receipt matching artifact hashes. It can then create a bounded committed-source tar with an adjacent digest record, classified only `OFFLINE_PACKAGE_UNVERIFIED_INSTALLATION`. An installer and on-device acceptance remain independent gates. The present candidate manifest is blocked; no archive was built.

Acceptance includes the existing 95 R19 research tests, eleven explicit synthetic R25 isolation/gate tests (including a 2 Hz `deviceState` cadence regression and an isolated synthetic-MPC smoke test), native receipt verification, command-path static audit, gate/package negative preflight and `git diff --check`. The old R19 research-only scope audit correctly rejects C20's deliberate product file; its historical receipt test fixtures explicitly restore the former branch/scope while exercising receipt tampering. These tests do not reclassify R19 into product evidence.

Independent review handoff after the host commits: Codex xhigh should inspect exact native source/ABI, admission and output privacy, failure reset, no publication path, packaging receipt and current build provenance. Windows Qwen should review the same final diff and gate/manifest, and distinguish Windows static review from Linux x86 and AArch64 execution. Both should report known exclusions: full planner, authenticated vehicle replay, QCOM build, device installation, radar/Panda safety, LKAS/AOL mismatch resolution and physical qualification. No reviewer signoff is assumed.

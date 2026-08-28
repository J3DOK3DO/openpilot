# Accord 11G latest-DOM integration candidate

This document defines the protected Honda Accord 11G replay on the pinned StarPilot DOM base, its upstream boundaries, and its repeatable verification gates. It does not authorize deployment or replace controlled on-road validation.

## Platform boundary

- Vehicle: Honda Accord 11G.
- Architecture: Honda Bosch C CAN-FD.
- Harness: `bosch_c`.
- Safety extension: `BOSCH_CANFD_MVL` where enabled by the Accord configuration.
- The hand-written Bosch-A radar DBC and Bosch-A object decoder are not the Accord 11G path.

## Pinned upstream snapshot

| Source | Pinned reference | Integration treatment |
| --- | --- | --- |
| StarPilot `Dom` | `227b5cf82ac7ace1e86d5a568c3fb2a0b5d95b2f` (`gpu`) | Git base |
| MVL openpilot `sp-honda-dev-202608` | `66ad9fac65f577940a9cbbe269104fb8177f2f76` | Review/specification reference; not merged wholesale |
| OpenDBC pinned by MVL openpilot | `8901198e59d5c58a8ddc9b80e9f48f11478465e8` | MVL-aligned reference |
| Latest MVL OpenDBC branch observed during replay | `27b4808af3d36f6e59555df07dcc11a002a2b6b8` | Recorded only; not merged because it is ahead of MVL openpilot's gitlink |

The clean runtime checkpoint is `39733a035068e74e321dc4a2db408662aabe268d`. The Accord driving checkpoint is `a9b496c83270111602676458e30f8287a1eff367`; the Accord diagnostic checkpoint is `83d1762b7355c66690b12a6c6c0bb2789bfbcd99`.

## Protected integration manifest

| Patch | Commit | Binary diff SHA-256 | Scope |
| --- | --- | --- | --- |
| DOM-ACCORD-05 | `d7747872fe50faff106381ec9f1b55559b659ea8` | `6f45b1307be12d7b2aea72c9f2defb775f851f834c1a0e3b064d79abb83a73d6` | Isolated MVL longitudinal stack |
| DOM-ACCORD-06 | `0b4af9504ed38877d2c6528c75fb14b0f984a386` | `044f54f6d91feba4c1a5beae77d3724c00704329c4d434103abc1bf5a666133a` | Isolated MVL radar lead policy |
| DOM-ACCORD-07 | `643879a879a222714b6e4580231f2bd9ddf4d15e` | `3ee6dc3cbf5636107f666bf57675abe259cc1801cd829fb6b35d88729132f025` | Adapted isolated MVL lateral model and delay behavior |
| DOM-ACCORD-08/10 | `620db5f1904b2227555b0e9413469bc98a151a9f` | `bc6ae6b96dc79fadc762e34910657fa6dc0264ca37de9ad8ae6038b45a5895fb` | Fixed Accord 11G PID gains |
| DOM-ACCORD-13 | `c7ff6f79faf5cd3942ccb934d8a0a6e01d313a6b` | `749436fc853c7197db7f6bd2ec81c553761a11b418cc2d2b28c75273c539cc20` | LKAS HUD state-change pulse |
| DOM-ACCORD-14 | `01fa130fb4b729603cae54df7873f6515a419d28` | `3d4452c4fa0e51ced7b29cec218249cfd4ac777563fabf4ee24c2a7a75820ca3` | Asynchronous learned gas/wind persistence |
| DOM-ACCORD-15 | `a9b496c83270111602676458e30f8287a1eff367` | `779d7bf03dd94d15e2cb642ea58b3923ee8e76546d332469ea2a504c68102fb9` | Disable parameter learning in reverse |
| DOM-ACCORD-OBS-01 | `83d1762b7355c66690b12a6c6c0bb2789bfbcd99` | `f25572e0a921856177b7c0689b32daa4d83d99da6bab310b708ac4e2ba173fc1` | Bounded Accord-only CAN-valid diagnostics |
| DOM-UPSTREAM-FIX | `39733a035068e74e321dc4a2db408662aabe268d` | `d9d6fc2479e4d4a95b288fd3d00c5a88e9d08dbd8811180fa27816f13e7d578e` | Restore the missing Toyota torque-controller enum import in the pinned DOM base |

ACCORD-07 was adapted during replay. Non-Accord vehicles retain latest DOM's generic twitch guard and general v16 action conversion. Accord mode uses its isolated takeoff guard and MVL curvature helper, then bypasses the generic turn-hold policy through the preserved `mvl_accord_raw_curvature` path. The helper and latest DOM conversion are currently mathematically identical.

## Verified host build and regression

Verification was performed in a detached x86-64 worktree created from the integration source. A full `uv sync --frozen --all-extras --all-groups`, SCons clean, and cache-disabled full build completed before tests. Critical Python extensions were checked as x86-64 to prevent stale ARM artifacts from being loaded.

Observed results:

- OpenDBC parser tests: 20 passed.
- Honda tests: 24 passed.
- MVL Accord longitudinal: 28 passed.
- MVL Accord radar: 39 passed.
- MVL Accord lateral: 74 passed.
- Full lateral-control suite: 170 passed.
- Locationd: 10 passed, 1 skipped, 12 subtests passed.
- Total: 365 tests passed, 12 subtests passed, 1 skipped.

Run protected history verification from a clean descendant of the runtime checkpoint:

```bash
tools/accord11g/verify_release.sh
```

Run regression only in an x86-64 verification worktree that has already completed the clean full build:

```bash
tools/accord11g/verify_release.sh --run-tests
```

The verifier refuses to run tests if the required native extensions are missing or are not x86-64.

## Host-native clean build procedure

Never rebuild x86 test artifacts in the deployment worktree. Use a detached verification worktree so tracked ARM artifacts in the deployment source remain untouched.

```bash
uv sync --frozen --all-extras --all-groups
uv run scons -u -c
uv run scons -u --cache-disable -j"$(nproc)"
```

Before testing, verify at least `msgq_repo/msgq/ipc_pyx.so`, `common/transformations/transformations.so`, `common/params_pyx.so`, the longitudinal acados solver, and `rednose_repo/rednose/helpers/ekf_sym_pyx.so` report `x86-64` with `file`.

Generated native outputs in the detached verification worktree are intentional. Do not stage or commit them.

## DBC generation and idempotence

Run only from a clean committed worktree. The generator deletes and recreates every `_generated.dbc` before rebuilding it.

```bash
test -z "$(git status --porcelain)"
uv run python opendbc_repo/opendbc/dbc/generator/generator.py
git diff --exit-code -- opendbc_repo/opendbc/dbc
uv run python opendbc_repo/opendbc/dbc/generator/generator.py
git diff --exit-code -- opendbc_repo/opendbc/dbc
```

Both diff checks must be empty. Inspect unexpected output; do not discard it blindly.

## Panda clean build and signing

Use a disposable clean worktree because SCons updates generated Panda outputs.

```bash
uv run scons -u --cache-disable -j"$(nproc)" panda/board/obj/panda_h7.bin.signed
file panda/board/obj/panda_h7.bin.signed
sha256sum panda/board/obj/panda_h7.bin.signed panda/board/obj/version
```

`panda/scripts/make_release.sh` requires the protected private release certificate. Never substitute, copy, or expose a release certificate. A developer-signed artifact is not an official release artifact.

## Release checklist

- [ ] Protected commit parents and binary diff hashes match this manifest.
- [ ] Full clean x86-64 build and architecture audit pass.
- [ ] All listed regression suites pass.
- [ ] DBC generation is idempotent if a DBC source or generated DBC changed.
- [ ] Panda H7 clean build passes if Panda, safety, or firmware changed.
- [ ] No unreviewed safety, forwarding, parser-validity, controller-output, or timing change is present.
- [ ] Deployment branch, source tree, device artifact, and Panda hashes are recorded.
- [ ] Static/off-road validation passes on the intended device.
- [ ] Controlled on-road validation is completed before normal use.

## Controlled validation checklist

- [ ] Accord 11G fingerprints as Bosch C CAN-FD with the intended harness and safety flags.
- [ ] Boot completes without DTCs, persistent CPU/GPU overload, or diagnostic flooding.
- [ ] Engage, disengage, cancel, brake, gas override, and driver steering takeover behave normally.
- [ ] Accord PID gains stay fixed while other Honda gain scaling remains unchanged.
- [ ] Low-speed takeoff curvature is stable and the latest DOM generic guard remains correct for non-Accord vehicles.
- [ ] Lane centering and learned lateral delay remain stable; reverse does not update parameter learners.
- [ ] Lead acquisition, cut-in/out, stopped lead, and radar handover remain stable.
- [ ] LKAS HUD state transitions do not flicker or latch incorrectly.
- [ ] B/regen, standstill, resume, and low-speed operation match the intended configuration.
- [ ] Force Stop fast-approach and adjacent-stop behavior are explicitly exercised.
- [ ] Route identifiers, logs, source SHA, Panda version, and anomalies are recorded.

## Known limitations and deferred review

- The latest-DOM base includes `Force Stop: Fast Approach` and its adjacent-stop radar change. ACCORD-05 isolates the Accord planner/MPC law, but shared vCruise/radar behavior still requires controlled validation.
- The four later DOM commits after Force Stop (`PiP orientation`, `the morrow`, `build`, and `gpu` in the observed range) were inherited through the base rather than individually ported.
- MVL openpilot and the latest MVL OpenDBC branch are not aligned. The newer OpenDBC actuator-delay commit was not imported.
- Automated tests do not establish on-road safety or compatibility with every vehicle firmware revision.
- This latest-DOM branch has completed host build/regression, but has not yet completed device boot or a full controlled drive test.
- ACCORD-OBS-01 is falling-edge-only, bounded to eight offenders, and intentionally does not alter parser validity, safety, forwarding, output, or timing.
- ACCORD-06 contains one known blank line at EOF; verification accepts only that exact historical report.
- Full-file Ruff debt remains in protected upstream/custom files. The verifier excludes only the recorded files while hashes and runtime regression cover them.
- Official Panda release signing is unavailable without the protected private certificate.

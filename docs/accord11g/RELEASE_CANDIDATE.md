# Accord 11G DOM release candidate

This document defines the protected Accord 11G replay stack, repeatable verification, and release gates. It is documentation only; it does not authorize deployment or replace controlled on-road validation.

## Platform boundary

- Vehicle: Honda Accord 11G.
- Architecture: Honda Bosch C CAN-FD.
- Harness: `bosch_c`.
- Safety extension: `BOSCH_CANFD_MVL` where enabled by the Accord configuration.
- The hand-written Bosch-A radar DBC and Bosch-A object decoder are not the Accord 11G path.

## Protected references

The replay begins at protected base `b7393ad04a7b692dda95240fbe4bba3af156b926` (`gniht`, parent `1da30086765a6d500ff0d61a8e02ec21db01d12d`). The driving checkpoint is `a16bd673f84f6570b51cd14ce2f6964ae2957502`; the diagnostic checkpoint is `2ca2ef43bd5bb7159e02d1f94d0fc467d58e77e7`.

| Patch | Commit | Binary diff SHA-256 | Scope |
| --- | --- | --- | --- |
| DOM-ACCORD-05 | `94161bc09cc7927a0ed7e2dae50d9bbcbaad6b98` | `26ed1ecc8f1d1c527806940f8a8a02ccfdece00731f0050fd04312a541132564` | Isolated MVL longitudinal stack |
| DOM-ACCORD-06 | `917527727478d3079901706b580aa0e3800d359e` | `a602b3057437fb794f60e8e11dd6a3df18e1009110e55c98a9c2f242e49cac8f` | Isolated MVL radar lead policy |
| DOM-ACCORD-07 | `690b3e073c9ab3f7097af072c934aa3b3b6bd5c4` | `53be74854855c0f007313d5c9d946d427cd4d06a53c8a96e5ce0faf1a3694ca3` | Isolated MVL lateral model and delay behavior |
| DOM-ACCORD-08/10 | `00db2fcf9cead3fdd46bc501d15bf4e5d866d9ba` | `44483f4ae16a4a246529bdfce8591f2c5a78f60438d898172b10bf4a525a5511` | Fixed Accord 11G PID gains |
| DOM-ACCORD-13 | `00ebd3aead3e451c64c7a362b3c8911e490ab242` | `749436fc853c7197db7f6bd2ec81c553761a11b418cc2d2b28c75273c539cc20` | LKAS HUD state-change pulse |
| DOM-ACCORD-14 | `8e79ba1b358e4a669ca975276035ec3c455032aa` | `3d4452c4fa0e51ced7b29cec218249cfd4ac777563fabf4ee24c2a7a75820ca3` | Asynchronous learned gas/wind persistence |
| DOM-ACCORD-15 | `a16bd673f84f6570b51cd14ce2f6964ae2957502` | `779d7bf03dd94d15e2cb642ea58b3923ee8e76546d332469ea2a504c68102fb9` | Disable parameter learning in reverse |
| DOM-ACCORD-OBS-01 | `2ca2ef43bd5bb7159e02d1f94d0fc467d58e77e7` | `f25572e0a921856177b7c0689b32daa4d83d99da6bab310b708ac4e2ba173fc1` | Bounded Accord-only CAN-valid diagnostics |

The manifest starts at the protected replay base. Features already present in that base are not reconstructed as separate commits here.

## Monitored upstream references

These are review references, not release dependencies. Fetch and verify them again before any port.

| Source | Observed reference | Status |
| --- | --- | --- |
| StarPilot | `a497c0f8` | No newly selected driving change |
| StarPilot `Dom` | `5882bd23bafd690a3d601d7ec7a4be5b34a7c9fe` | `Force Stop: Fast Approach`; classify `ADAPT` |
| MVL openpilot | `66ad9fac` (reported pointer `8901198e`) | No newly selected driving change |
| MVL opendbc | `27b4808a` | Already reviewed reference |

Do not replay the Force Stop commit wholesale. Its generic longitudinal-planner/MPC changes overlap the validated ACCORD-05 envelope. Review the vCruise reduction-only constraint separately, and review the adjacent-lane stopped-vehicle suppression as a separate radar/Force Stop patch. Each requires its own branch, tests, and controlled validation.

## Environment and automated regression

Create the locked environment once:

```bash
uv sync --frozen --all-extras --all-groups
```

Verify protected history and hashes without running tests:

```bash
tools/accord11g/verify_release.sh
```

Run the patch-specific regression suite:

```bash
tools/accord11g/verify_release.sh --run-tests
```

The script covers the three isolated MVL control tests, full lateral-control tests, parser/Honda tests, and locationd regression excluding `read_saved_params`.

## DBC generation and idempotence

Run this only from a clean committed worktree. The generator deletes and recreates every `_generated.dbc` before rebuilding it.

```bash
test -z "$(git status --porcelain)"
uv run python opendbc_repo/opendbc/dbc/generator/generator.py
git diff --exit-code -- opendbc_repo/opendbc/dbc
uv run python opendbc_repo/opendbc/dbc/generator/generator.py
git diff --exit-code -- opendbc_repo/opendbc/dbc
```

Both diff checks must be empty. If either produces a diff, inspect it; do not discard generated output blindly. `honda_bosch_a_radar.dbc` is explicitly hand-written and is not generated or used by Accord 11G.

## Panda clean build and signing

Build in a clean checkout because SCons updates generated artifacts such as `panda/board/obj/gitversion.h` and `panda/board/obj/version`.

Developer H7 build:

```bash
uv run scons -u --cache-disable -j"$(nproc)" panda/board/obj/panda_h7.bin.signed
file panda/board/obj/panda_h7.bin.signed
sha256sum panda/board/obj/panda_h7.bin.signed panda/board/obj/version
```

`panda/scripts/make_release.sh` is not a general developer command. It requires the private certificate at `/home/batman/xx/pandaextra/certs/release`, cleans the Panda build, deletes `board/obj/*`, rebuilds, and packages signed binaries. Never substitute or copy a release certificate. A developer-signed artifact is not an official release artifact.

## Release checklist

- [ ] `tools/accord11g/verify_release.sh` passes on a clean descendant of the diagnostic checkpoint.
- [ ] `tools/accord11g/verify_release.sh --run-tests` passes.
- [ ] Commit SHAs and binary diff hashes match the manifest.
- [ ] DBC idempotence passes if any DBC source or generated DBC changed.
- [ ] Panda H7 clean build passes if Panda, safety, or firmware changed.
- [ ] The intended device build reports the expected Git/Panda versions.
- [ ] No unreviewed safety, forwarding, CAN-validity, controller-output, or timing change is present.
- [ ] Deployment branch and device artifact hashes are recorded.
- [ ] Off-road and controlled-road validation are completed before normal use.

## On-road validation checklist

Perform static/off-road checks first, then use a controlled route with a safety driver ready to disengage.

- [ ] Accord 11G fingerprints correctly as Bosch C CAN-FD with the expected harness and safety flags.
- [ ] No startup CAN diagnostic flood occurs; a valid-to-invalid transition logs at most eight sorted offenders with an omitted count.
- [ ] Engage, disengage, cancel, brake, and driver-steering takeover behave normally.
- [ ] Accord PID gains remain fixed while other Honda gain scaling remains unchanged.
- [ ] Lane centering and learned lateral delay remain stable; reverse driving does not update parameter learners.
- [ ] Lead acquisition, cut-in/cut-out, stopped lead, and radar handover remain stable.
- [ ] Longitudinal approach and stopping behavior stay inside the validated ACCORD-05 envelope.
- [ ] LKAS HUD lane/state transitions do not flicker or remain latched incorrectly.
- [ ] B/regen gear behavior, standstill, resume, and low-speed operation match the approved configuration.
- [ ] Save route identifiers, logs, software SHAs, Panda version, and observed anomalies.

## Known limitations

- Automated tests do not establish on-road safety or compatibility with every vehicle firmware revision.
- ACCORD-OBS-01 intentionally stays silent during startup-invalid state and logs only after a parser has first become valid.
- ACCORD-OBS-01 reports at most eight offenders per event and does not change parser validity, safety, forwarding, controller output, or timing.
- Protected ACCORD-06 contains one known blank line at EOF in `test_mvl_accord_radar.py`; verification accepts only that exact historical exception.
- Full-file Ruff excludes `controlsd.py`, `latcontrol_pid.py`, and `modeld.py` because the protected versions contain known style debt; immutable hashes and regression tests still cover them.
- Official Panda release signing is unavailable without the protected private certificate.
- The Force Stop fast-approach and adjacent-stop changes remain deferred `ADAPT` candidates and are not part of this release stack.

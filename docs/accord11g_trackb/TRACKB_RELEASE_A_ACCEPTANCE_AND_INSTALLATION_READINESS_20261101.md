# Release A (stock-ACC-preserving Track A/B engineering candidate): acceptance and installation readiness — 2026-11-01

**Classification: NON-PRODUCTION ENGINEERING CANDIDATE.** It is not a comma installation candidate: installation gates 4 and 5 need device evidence that this offline campaign cannot obtain.

## 1. Source integrity

- Branch `accord11g-dom7-trackb-unified-integration-20261101` from `d88e2918021908b260bc0d4c427277037bfd1019`. Track A `5fa8b2ed8` is an ancestor.
- Production paths (`openpilot/`, `opendbc_repo/opendbc/car|safety|dbc|can`, `panda/`, `starpilot/`, `system/`, `scripts/` excluding tests, launchers, `SConstruct`) are byte-identical to `d88e2918`. This branch changes only docs, `tools/trackb_research/`, and test files (verify: `git diff --stat d88e2918 HEAD`).
- Track A invariants are preserved and pinned by tests: `pcmCruise=True`, no openpilot longitudinal or alpha long for 11G, words 80/81, LKAS interruption, 500-frame rearm, counters, SCM freshness forwarding, steering profile 12789.

## 2. Installation-candidate gates

| # | Gate | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Native ARM64 release build and dependencies | **PARTIAL**: ARM64 emulated tests pass; the full ARM64 SCons release build was not run | Final report §tests; AGNOS report §4 |
| 2 | Packaging, manifest, commit identity, binaries reproducible | **NOT_RUN** (`tools/release/build_release.sh` builds and packages a release tree; not executed) | — |
| 3 | Track A / Honda safety regressions; mandatory skips reviewed | **PASS (host)**: see the final report for counts; skips are abstract base classes or platform features Honda lacks (regen message, second speed message, gearbox message on platforms without one) | Final report |
| 4 | Target hardware, installed AGNOS and Panda firmware compatibility from read-only device evidence | **HOLD**: no device access; the specified backups are absent | AGNOS report |
| 5 | Known-good installation, configuration and recovery preserved | **HOLD**: current device branch/commit and Params backup not recorded | §3 |
| 6 | Independent final review of the exact candidate | See `TRACKB_DUAL_RELEASE_FINAL_VERDICTS_20261101.md` | Codex record |
| 7 | No unqualified longitudinal, radar-control or diagnostic TX enabled | **PASS (source/host)**: no production change; RELEASE-denial and forwarding tests | Tests listed in the architecture doc §4 |

## 3. Installation preparation and rollback (for a later, separately authorized install; nothing is installed here)

1. Parked and offroad. Record the device's current `/data/openpilot` remote/branch/commit, the AGNOS version and system hash, the Panda firmware version, and a Params backup. Confirm the known-good commit is fetchable.
2. Run the B4 parked audit (`B4_PARKED_PROCEDURE.md`, `scripts/accord11g_trackb_parked_audit.py`) against the published commit SHA.
3. Install by switching the checkout to the reviewed commit. This branch adds no Params, services, firmware or boot changes. Do not flash Panda or AGNOS.
4. Rollback: switch back to the recorded known-good commit while parked, reboot, and rerun the parked audit. No data migration is involved.
5. Abort criteria: any AGNOS/Panda identity mismatch against the recorded values, any new CAN TX ID, or any change in stock ACC/CMBS/AEB behavior. Roll back immediately.

## 4. Publication

Allowed as a non-production engineering branch once its source/review gates pass (final verdicts). A GitHub push is not deployment approval.

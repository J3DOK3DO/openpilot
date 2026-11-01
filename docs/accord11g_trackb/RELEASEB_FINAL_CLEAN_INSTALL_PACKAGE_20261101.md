# Accord 11G Hybrid Release B — clean-install engineering candidate (2026-11-01)

**Status: engineering candidate, not installed, not vehicle-qualified for longitudinal control.** It is the Release
B source with every safely activatable feature on and every unqualified longitudinal mechanism off. Fresh
installation is the owner's packaging preference. It is not evidence of compatibility or safety.

## Identity

| Item | Value |
| --- | --- |
| Branch | `J3DOK3DO/openpilot` `accord11g-dom7-releaseb-cleaninstall-candidate-20261101` (frozen once published: later work goes to a new branch, so an installed device never auto-updates to unreviewed commits) |
| Commit and tree | recorded in the final handoff and evidence register (a commit cannot name its own SHA) |
| Parent | `bc5c79b5` (Tier 2 candidate) → `12021bdc` → `bc1eea1a` → installed Dom `5b0f81ca` |
| Production delta vs installed Dom | one Python file, `opendbc/car/honda/accord_mvl_stock.py` (Track A + HYBRID admission). Everything else added is tests, docs and `tools/trackb_research/`, which no runtime file imports (isolation tests). |
| Native binaries | all 93 committed binaries byte-identical to installed Dom `5b0f81ca`; ARM64 build passed at commit `4e3605e6`; the only later production change is the pure-Python `accord_mvl_stock.py`, whose final bytes were ARM64-tested (19/19 lifecycle, hash-bound) |
| Panda firmware | committed `panda/board/obj` identical to installed Dom; DEBUG build, expected signature `510ed0d6c7a8d322` (DEV-PANDA-DEBUG-001, owner-accepted research deviation, **not** a RELEASE qualification) |
| Panda safety | `hondaBosch` with words 80 (no alt brake) / 81 (alt brake); no `BOSCH_LONG` bit in any configuration |
| AGNOS | requires 19.8.1, the version installed Dom targets. Device raw-partition hash ≠ pinned image (DEV-AGNOS-HASH-001, accepted for research). The ABI files match. |
| Fast Update | not supported. No exact-tree `prebuilt.json` receipt exists, and none was fabricated. Install by comma installer or git only. |

## Behaviour on the car

| Feature | State | Effect vs installed Dom |
| --- | --- | --- |
| Stock PCM ACC, set speed, following, stop-and-go | active (factory) | unchanged |
| Factory CMBS / AEB / FCW | active (factory; radar not disabled, no radar UDS) | unchanged |
| openpilot lateral (PID, limits, EPS fault classification) | active | unchanged |

"Active and qualified for defined scope" in the 50-ID matrix means software qualification only. The behaviour equals the in-service installed build and is verified by host/ARM64 tests. None of those 13 rows is a target measurement, except the BC-002 identity observation.

| AOL (lateral with stock ACC off) on the Hybrid | **active** | **new on the Hybrid**: the HYBRID qualifier fix admits it |
| Track A camera-button takeover / LKAS pulse | **active** while engaged | **new on the Hybrid**; cancels a queued synthetic press on brake, PCM off, `LKAS_READY` low, disengage, cancel or resume |
| openpilot / alpha longitudinal, MVL radar-disable, custom gas/brake | **off, unreachable** | none: no configuration, preference or branch type enables it (lock-off test) |
| Track B research (policy model, evidence contracts, gate) | not shipped to runtime | none |

The two new Hybrid behaviours need a supervised on-car check before normal use (procedure below).

## Prerequisites for the deferred deployment stage (Stage 1, not done here)

A fresh install does **not** remove these:

1. Confirm the device's current HEAD and whether staged Dom `195b7000` was applied (`UpdateAvailable=1` was last seen 2026-11-01).
2. Confirm `cat /VERSION` = `19.8.1`, with ≥ 2 GB free on `/data`.
3. Verify the private Params backup and its checksum. A comma installer reinstall keeps `/data/params`, but the backup is the recovery source.
4. Confirm the Panda will not be reflashed. The candidate ships the same firmware. Any reflash on first boot means a mismatch: stop and roll back.
5. Record the recovery path before installing: reinstall `installer.comma.ai/StarPilotHQ/Dom`, or `git checkout` of `5b0f81ca`.

## Install (procedure only, not executed)

- Clean install: on the device, uninstall, then enter the custom installer URL `installer.comma.ai/J3DOK3DO/accord11g-dom7-releaseb-cleaninstall-candidate-20261101`. This makes a fresh clone of `/data/openpilot`; Params are kept.
- Post-install checks:
  - HEAD equals the published SHA and `git status --porcelain` is empty.
  - The pandad swaglog shows `signature 510ed0d6c7a8d322, expected 510ed0d6c7a8d322`.
- Supervised onroad check in a safe location:
  - stock ACC engages and cancels as before;
  - lateral engages;
  - AOL latches with stock ACC off;
  - brake, steering override and disengagement withdraw it;
  - the LKAS takeover behaves as described.

  On any anomaly, disengage and roll back.
- Rollback: reinstall Dom (`installer.comma.ai/StarPilotHQ/Dom`), or check out `5b0f81ca` with git and reboot. Restore Params from the private backup only if a setting changed.

## B0–B6 status

| Stage | Offline (software) work | Technical safety qualification | Physical |
| --- | --- | --- | --- |
| B0 hazards and requirements | complete | — | — |
| B1 OEM authority (4 gates) | source and evidence research complete | **HOLD, 0/4** (no authenticated OEM protocol) | — |
| B2 subordinate controller contracts | complete: simulators, F1–F7 contracts, numeric DRV policy model | synthetic only | — |
| B3 Panda | host release-denial tests pass | target RELEASE identity **FAIL** (DEBUG firmware) | — |
| B4 build and device identity | source/build compatible (ARM64 build, ABI audit) | installed identity **HOLD** (AGNOS raw hash) | — |
| B5 isolated bench | procedure written | — | **OWNER_DEFERRED / NOT_EXECUTED** |
| B6 controlled vehicle | procedure written | — | **OWNER_DEFERRED / NOT_EXECUTED** |

## Still required before custom Bosch-C longitudinal can be enabled

1. B1 4/4 with authenticated OEM evidence (see `RELEASEB_FINAL_BOSCHC_PROTOCOL_EVIDENCE_20261101.md`).
2. Either a CMBS-preserving architecture (for example stock-ACC set-speed modulation), or a qualified replacement collision detector with an independent emergency-braking path, plus an independent functional-safety review approving CC-01 or its replacement.
3. A target-specific controller design and calibration replacing the synthetic DRV bounds.
4. A RELEASE Panda build with a TX table derived from B1, flashed and measured under separate authorization.
5. An AGNOS identity review.
6. B5 bench, then B6 closed-course qualification, by qualified personnel.
7. Legal and roadworthiness review.

Owner acceptance and software test results do not substitute for any of these.

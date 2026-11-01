# Accord 11G: installed Dom vs. Track A/B lineage reconciliation (2026-11-01)

Target: 2025 US Honda Accord 11th Gen Hybrid, `HONDA_ACCORD_11G`, Honda Bosch-C / CAN-FD (one target configuration).

## Commits

| Role | SHA | Evidence |
| --- | --- | --- |
| Installed on comma | `5b0f81caa120a6e48b41ba7b271b9afa61733205` | `ssh comma` read-only, 2026-11-01T08:03Z: branch `Dom`, clean |
| Provenance | ancestor of `J3DOK3DO/openpilot` and `StarPilotHQ/openpilot` `Dom` = `195b7000aab3…` | `git merge-base --is-ancestor`, `git ls-remote` |
| Merge base with Track A/B | `b64d7cf9e96ee6bb92122852e437d5488c14aa56` | `git merge-base 5b0f81ca c944fce3` (also for `d88e2918`, `5fa8b2ed8`) |
| Track A milestone | `5fa8b2ed8c4b…` (1 commit on `b64d7cf9`) | |
| Previous Release A candidate | `c944fce3930f…` (9 commits on `b64d7cf9`) | |
| Selected base | **installed Dom `5b0f81ca`** | provenance verified; preferred by the campaign brief |
| Candidate branch | `accord11g-dom7-trackab-native-candidate-20261101` | `git cherry-pick -x b64d7cf9..c944fce3` onto `5b0f81ca`, then new commits |

`b64d7cf9..5b0f81ca` is 132 Dom commits (647 files); `b64d7cf9..c944fce3` is 9 commits (56 files). The two file sets
are **disjoint**, the cherry-pick applied without conflict, and `git diff b64d7cf9 c944fce3` equals
`git diff 5b0f81ca 4e3605e6` byte for byte (index lines excluded).

## What actually differs on the Accord path

- `accord_mvl_stock.py`: installed blob `e5249457` is the merge-base blob, so the installed car **lacks** the Track A
  fix `5fa8b2ed8` (cancel a partially queued synthetic LKAS press on brake / PCM off / LKAS_READY low / disengage /
  cancel / resume). Track A is the only Honda production-source change in the candidate.
- No file under `opendbc_repo/opendbc/car/honda/`, `safety/modes/honda*.h`, `safety/safety.h`, the Honda DBCs,
  `opendbc/can/`, `car.capnp`, `log.capnp`, or Panda **source** changed between `b64d7cf9` and `5b0f81ca`. The 19
  tracked files that name `HONDA_ACCORD_11G` at installed Dom (21 in the candidate, with two Track A tests) are
  unchanged by Dom in that range.
- Panda **artifacts** did change: 36 committed `panda/board/obj` files were rebuilt (version
  `DEV-b3b96ade-Pa5919516-DEBUG` → `DEV-6f2ca2c4-Pa5919516-DEBUG`) and `panda/tests/libpanda/libpanda.so` was
  replaced, with no Panda or Honda safety source change. The candidate keeps the installed `5b0f81ca` artifacts.
- Shared Dom changes reachable from the Accord path, each reviewed; the new current-branch tests pin the inner gate
  named in the right-hand column:

| Dom change (`b64d7cf9..5b0f81ca`) | Accord effect | Test |
| --- | --- | --- |
| `car_helpers.py` Volvo normal-bus probe | none: no Honda CAN-FD DBC address is in the 16-pair layout | `test_accord11g_installed_dom_discovery.py` |
| `card.py` SLC engagement adoption (caller) + `cruise.py` `initialize_v_cruise` | inert twice: `card.py:848` requires `openpilotLongitudinalControl` before computing a target, and `initialize_v_cruise` discards any target without it | `test_accord11g_installed_dom_cruise.py` covers the inner `VCruiseHelper` gate only (passes a target with `openpilotLongitudinalControl=False`); the outer `Card` gate is source-reviewed, not tested |
| `controller_selection.py` generic torque policy, all platforms in `KNOWN_POLICIES` | PID lateral keeps the standard controller; a saved Accord entry is ignored | `test_accord11g_installed_dom_lateral_selection.py` |
| `long_mpc.py` / `longitudinal_planner.py` `extra_stopped_gap_m` | planner only; stock ACC owns actuation | Track B schema contract tests |
| `selfdrived.py` radarFault / longitudinal-only events | generic; no Honda branch | existing Dom tests |
| `custom.capnp` `engagementAdopt @12` | additive enum | `test_plan_snapshot_schema_contract.py` |
| Committed Panda firmware artifacts rebuilt (no source change), `DEV-6f2ca2c4-Pa5919516-DEBUG` | DEBUG build; host libsafety DEBUG == RELEASE for words 80/81 | `test_accord11g_debug_release_parity.py` |

Pending device update: `5b0f81ca..195b7000` (8 commits, 46 files) is already finalized in `/data/safe_staging` with
`UpdateAvailable=1`. It touches only `card.py` (Ford-only `observe_controller_can`), `selfdrived.py` (Ford AOL
expiry) and tests/CI, no `panda/` and no file in the candidate's delta. It still lacks Track A.

## Migration manifest (Track A/B content onto installed Dom)

| Item | Decision | Basis |
| --- | --- | --- |
| Track A `accord_mvl_stock.py` withdrawal cancellation + tests (`5fa8b2ed8`) | NEEDS_ADAPTATION → applied unchanged | Dom never touched the file; 2637-test host run passes |
| Track B research modules `tools/trackb_research/*` | ALREADY_PRESENT in lineage → replayed | no production import (isolation scan) |
| Track B safety denial tests (`test_accord11g_trackb_*`) | REQUIRES_TEST → pass on new base | host run |
| Parked audit / smoke scripts | replayed | `test_accord11g_trackb_parked_audit.py` |
| Docs and B0–B4 registers | replayed, then updated for the new base | this directory |
| MVL alpha-long, radar UDS disable, CAN-FD long TX table, radar emulation | REJECTED (`UNQUALIFIED_TX_REJECTED`) | `TRACKAB_MVL_FUNCTIONAL_GAP_MATRIX_20261101.tsv` |
| MVL LKAS HUD lane changes, ICBM button spoofing | REJECTED for Release A (`OPTIONAL_TUNING_RESEARCH`) | same |
| Old C6-12 patches, historical logs | not applied, not used as acceptance | campaign rule |
| Installed-car FW versions, live bus recordings | UNKNOWN | not read in this campaign |

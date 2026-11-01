# Three-way source audit: MVL `3fec9a` / commaai `1bce882c` / Dom `d88e2918` — 2026-11-01

Machine-readable inventory: `TRACKB_MVL_3FEC9A_SOURCE_INVENTORY_20261101.tsv` (one row per path, with blob SHAs for all three trees, pairwise relation, `git diff --numstat` per pair, disposition, track, 84-ID linkage, tests). 84-ID linkage: `TRACKB_84_ID_DISPOSITION_MATRIX_20261101.tsv`.

## 1. Inputs and roles

| Ref | Repository / commit | Role | Verified identity |
| --- | --- | --- | --- |
| A | `mvl-boston/opendbc` `3fec9a418a659de31d7b1f494193161697a35071` | Read-only research evidence | Commit `2026-10-25T23:45:53-04:00` (= `03:45:53Z`), "Set Honda STEER_MAX per platform torque limits"; 629 tree entries (`ls-tree -r -t`), 553 blobs |
| B | `commaai/opendbc` `1bce882c6330f8cc591f368f415ae5fa241ae225` | Read-only upstream comparison | 513 tree entries, 455 blobs |
| C | `J3DOK3DO/openpilot` `d88e2918021908b260bc0d4c427277037bfd1019`, prefix `opendbc_repo/` | Authoritative implementation | Vendored (no submodule); clean |

Fetched by exact SHA (`git fetch --depth 1 --filter=blob:none <sha>`). The MVL branch name was not used. No external source is treated as OEM authorization, calibration or proof of safety.

## 2. Method

A deterministic script (`three_way_audit.py`, copied to the final artifacts) selects every path matching the Honda car, SunnyPilot Honda, Honda DBC generator, Honda safety mode, shared safety headers, `can/parser.py`, `car.capnp` and the Honda safety/release tests in any of the three trees. It then follows MVL Python `opendbc.*` imports transitively. Result: **189 paths**. All of them are classified. Paths the selection does not reach are out of scope: other brands' DBC/safety/car code that no Honda module imports.

| Relation (189 paths) | SAME | DIFF | only one side | both absent |
| --- | --- | --- | --- | --- |
| MVL vs comma | 62 | 49 | 37 MVL-only | 41 (Dom-only) |
| MVL vs Dom | 51 | 62 | 76 one-sided | — |
| comma vs Dom | 54 | 57 | 43 Dom-only | 35 (MVL-only) |

Dispositions: `NOT_APPLICABLE` 113, `ALREADY_IN_DOM` 52, `RELEVANT_SOURCE_ONLY` 13, `PROHIBITED_UNQUALIFIED_TX` 7, `SUPERSEDED` 3, `REQUIRES_TARGET_EVIDENCE` 1, `NOT_REVIEWED` 0. Adopted into Dom production source: **none**. Adopted as tests: one negative safety test (§5).

## 3. Release-critical findings (verified at the exact blobs)

| # | Area | MVL `3fec9a` | commaai `1bce882c` | Dom `d88e2918` | Disposition |
| --- | --- | --- | --- | --- | --- |
| 1 | `values.py` 11G steering | `HONDA_ACCORD_11G` grouped at `STEER_MAX = 12789` (l.58-60) | not present at that value | 12789 via `parameter_profiles.py:7` (Track A, commit `cf21c9729`); pinned by `test_accord_mvl_parameters.py` | Value already in Dom; the MVL value is **not** additional validation. Physical torque qualification is not established by this audit. |
| 2 | `interface.py` ownership | `alphaLongitudinalAvailable = True`, `openpilotLongitudinalControl = alpha_long`, `pcmCruise = not …` for Bosch incl. CAN-FD (l.44-56, comment "THIS DISABLES AEB!"); radar communication-control and DTC clearing (l.398-420) | Bosch CAN-FD excluded from alpha long (l.48-53) | Excluded like comma (l.53-58); `pcmCruise=True` for 11G; `BOSCH_CANFD_MVL` (64) flag | `PROHIBITED_UNQUALIFIED_TX`. Not ported. Pinned by `test_accord11g_trackb_no_long_authority.py`, `test_accord11g_stock_ownership_v4.py`. |
| 3 | `carcontroller.py` / `hondacan.py` / `hud_objects.py` / `lane_path.py` | +1265 / +147 lines vs comma: CAN-FD radar-disable diagnostics, radar message simulation/replacement, conditional custom gas/brake | absent | absent | `PROHIBITED_UNQUALIFIED_TX`. |
| 4 | `safety/modes/honda.h` | `HONDA_CANFD_LONG_TX_MSGS` (0x1DF/0x1EF/0x30C/0x18DAB0F1 bus 0, 0x310 and 29-bit 0x6CD5558/9, 0xF31AA52/5C, 0x1A45AA4E on bus 0 and 2), selected by Bosch-long on CAN-FD; fwd hook blocks radar UDS responses 0x18DAF1B0 | CAN-FD stock table only | No CAN-FD long table. 80/81 → `HONDA_MVL_STOCK_TX_MSGS` (0xE4, 0x296 b0/b2, 0x33D); other CAN-FD words with bit 64 → empty table. The Honda fwd hook adds only the 0x296 bus 0→2 block under fresh buttons; the generic relay check additionally withholds the relay-checked TX addresses 0xE4/0x33D on bus 2→0 (`safety.h` `safety_fwd_hook`) | `PROHIBITED_UNQUALIFIED_TX`; adopted only as **negative tests** (§5). |
| 5 | `safety/tests/test_honda.py` | stock CAN-FD and Bosch CAN-FD long classes (l.878-904) | stock only | stock + Dom classes | Long class presumes enabled TX and is not ported. |
| 6 | `honda_common_canfd.dbc` | blob `4c19ed96…` (+68 lines: RADAR_REFERENCE 929, RADAR_HUD_CANFD 784, LANE_PATH, HUD_OBJECTS, RADAR_LEAD/LEAD2, BOSCH_SUPPLEMENTAL_CANFD, tick references) | blob `cd7efe7b…` | **equals comma** `cd7efe7b…` | `RELEVANT_SOURCE_ONLY`. Not substituted. "Factory log" comments are unverified fork claims. |
| 7 | SunnyPilot Honda layer | `carstate_ext`, `eps_mod`, `fingerprints_ext`, `gas_interceptor`, `icbm`, `mads`, `values_ext`, tests | absent | absent | `mads` superseded by Dom AOL; `icbm` (SCM button set-speed spoofing) prohibited; `gas_interceptor`/`eps_mod` not applicable to a Bosch-C stock car; `fingerprints_ext` has no 11G entry. |
| 8 | Firmware identity | Source library only | — | — | No inference about flashed Panda firmware (B3-target HOLD). |

Smaller deltas: `_steering_control_d_ext.dbc` (same bits 23|16, named `STEER_CONTROL_ACTIVE` in MVL vs `STEER_APPLIED` in Dom; no Dom code reads it); `_bosch_2018.dbc` (MVL documents the `AMBIENT_LIGHT_MAYBE` echo in SCM_BUTTONS; Dom `hondacan.py:233` already echoes it); `_community.dbc` (pedal signal renames); `car.capnp` (MVL mass-normalized CarParams refactor); `can/parser.py` (validity-latch handling; ND-003/004 stay REWORK/DEFER).

## 4. Answers to the mandated questions

- **Is any MVL change mandatory for the Accord?** No. Every Accord-relevant MVL difference either already exists in Dom (12789 steering profile, SCM_BUTTONS byte echo, 0x296 freshness forwarding) or adds an unqualified control, radar-emulation or diagnostic path.
- **Does Dom's CAN-FD DBC match MVL?** No, it matches pinned commaai. This is unchanged.
- **Does Dom permit any MVL CAN-FD long/diagnostic frame?** No, in RELEASE for every CAN-FD word, and also in DEBUG for every non-radarless CAN-FD word (§5).
- **Does Dom suppress OEM camera/radar traffic?** For words 80/81 the Panda withholds only the two relay-checked LKAS frames it replaces (0xE4, 0x33D) from bus 2→0. Every other 11-bit camera-side address, including the ACC/AEB/HUD examples, is forwarded. Bus 0→2 forwards every 11-bit address and 0x18DAF1B0 when buttons are not fresh (§5).

## 5. Adopted change (test-only) and evidence

`opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_mvl3fec9a_canfd.py` (23 tests, host libsafety):

1. RELEASE: every CAN-FD word (all 256 values with bit 16) × experiences {0, 32, 1, 2, 16} denies all MVL CAN-FD-long-only frames.
2. DEBUG: the same for every non-radarless CAN-FD word, which shows Dom has no CAN-FD long table even with `ALLOW_DEBUG` and the Bosch-long bit. Positive control: DEBUG still admits Bosch-long 0x1DF on bus 1 for word 2.
3. Words 80/81, experiences 0/32, controls on/off: the exact set of bus 2→0 blocked 11-bit addresses is {0xE4, 0x33D}; MVL radar-emulation IDs forward.
4. Words 80/81: no bus 0→2 11-bit block in the initial state, and 0x18DAF1B0 forwards (MVL's radar-disable forwarding block not adopted).

These are host-library results, not flashed-firmware results.

## 6. Limits

Lines in MVL files were read where they bear on the findings above. The 113 `NOT_APPLICABLE` rows are classified by rule (other platform, Dom-only, transitive non-Honda helper), not by line-by-line reading. GitHub source analysis says nothing about the user's car's ECUs, bus routing, AEB behavior or installed firmware.

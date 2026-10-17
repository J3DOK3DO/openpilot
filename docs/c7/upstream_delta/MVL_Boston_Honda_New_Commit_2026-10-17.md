# MVL Boston — New Honda Lateral Parameters Since C7 Baseline

**Assessment:** 17 October 2026 (Asia/Dubai) | **Disposition:** P2, review-only — no live tuning.
**Repo:** [mvl-boston/openpilot — sp-honda-dev-202608](https://github.com/mvl-boston/openpilot/tree/sp-honda-dev-202608)
**Last source head assessed on 14 October:** `66598eda130dde70fbf84278215adabd174afe36`.
**Current source head:** `cb15c04e918b759688cb354b1bbc9b3c5a47a65c`.

## One new upstream commit

[cb15c04e — Additional Honda lateral gain and shape parameters](https://github.com/mvl-boston/openpilot/commit/cb15c04e918b759688cb354b1bbc9b3c5a47a65c) (15 October US Eastern time) changes only `openpilot/common/params_keys.h`: **21 added lines, no deleted lines**. No steering controller, actual lateral calibration, CAN, Panda firmware or vehicle output source was changed by this commit.

| Registry family | New persistent FLOAT keys | Count |
|---|---|---:|
| Honda lateral gain | `HondaLatGain05Params`, `HondaLatGain10Params`, `HondaLatGain15Params`, `HondaLatGain20Params`, `HondaLatGain30Params`, `HondaLatGain40Params`, `HondaLatGain50Params`, `HondaLatGain60Params`, `HondaLatGain70Params` | 9 |
| Honda lateral shape | `HondaLatShape10Params`, `HondaLatShape15Params`, `HondaLatShape20Params`, `HondaLatShape25Params`, `HondaLatShape30Params` | 5 |
| Honda lateral wire | `HondaLatWire50Params`, `HondaLatWire60Params`, `HondaLatWire70Params`, `HondaLatWire80Params`, `HondaLatWire90Params`, `HondaLatWire100Params` | 6 |
| Honda lateral ceiling | `HondaLatCeilingParams` | 1 |
| **Total** | | **21** |

**What this proves:** additional identifiers can be stored as persistent floating-point Params. It does **not** supply a consumer, default, validation range, interpolation unit, control equation or measured improvement. Sample upstream searches returned registry declarations only for the new representative identifiers. Do not infer that numeric suffixes describe physical speed/gain units without the consuming implementation.

## Accord 11G / C6-12 / C7 recommendation

**No immediate port.** Before any lateral-tuning trial, obtain actual reading/writing code, validated defaults/limits, Accord 11G EPS and carFingerprint applicability, steering-torque/lat-accel safety constraints, and real low-speed oscillation/corner evidence. Key registration alone cannot fix ping-pong or justify modifying C6-12. The refreshed C7-from-Dom candidate intentionally **does not add these unused keys**.

## OpEndBC

The MVL superproject points its `opendbc_repo` Git submodule to `cf46117420f283b3e38241c00d728a191aa9fccc` at both the old and new source heads. This is the same pinned dependency revision from our 14 October audit: **zero new pinned opendbc commits in this comparison**.

## Relation to the Dom-34 assessment

The 21 registered keys are an **additional MVL P2 item**, not one of Dom's 34 commits. Retain the original five Dom P1 investigations: MPC terminal constraints, stop/lead, Params cache migration, Panda SPI/CAN and SLC/CSC/schema behavior. The present MVL commit is not a new safety or performance fix and should not be cherry-picked into a deployment branch.

**Controls:** read-only Git source inspection; no vehicle/Params/CAN operation, no C6-12 change, no C7 deployed change.

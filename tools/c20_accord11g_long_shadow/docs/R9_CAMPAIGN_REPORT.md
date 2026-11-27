# R9 combined offline engineering report — 2026-11-27 UAE

## Scope and decision

All changes are research-only under `tools/c20_accord11g_long_shadow/`, starting from branch `c20-r9-native-readiness-rlog-schema-shadow-rc-20261127` at `fad3b1697644cc8bf7d8262a13644173825e1063`. C19 stable baseline `a32dcc0a6e62a4e2a15d9ac4425424e598313c98` remains unchanged. No vehicle, CAN, Panda, controller, launch, or road operation was performed. **Active Alpha Long and road release: NO_GO.** The accepted CMBS/FCW/AEB research risk in `risk_acceptance.md` does not qualify any active configuration.

## R9-1: raw evidence census

`rawlog_census.py` requires the four exact R8 SHA-256 values and verifies complete zstd frames. It reads only four fixed historical paths, rejects symlinks, missing files, changed bytes, altered hashes and unsupported decoder summaries. Total compressed input: **47,107,060 bytes**. All four digest and frame checks passed. The pinned hashes are in `fixtures/r9_decoded_summary.json` and the R8 report. No raw bytes are copied into Git or the archive.

An isolated, read-only probe used cached `pycapnp 2.1.0`, `zstandard 0.25.0`, and `Event.read_multiple_bytes` with the historical checkout's schema. It emitted only service counts, first/last `logMonoTime`, and decoder exception counts. The old schema checkout is `1d998a73ceb3c177c463e85f207ae081c6b55e03`; exact `log.capnp`, `car.capnp`, and `custom.capnp` hashes are in the summary. These hashes bind the **schema used to read local bytes**, not the recorder's software, ECU firmware, DBC, route custody, or current Accord identity. The September Candidate-1 source `d49c5ff` and OpenDBC tree `d5967a1` are distinct historical references; neither is a verified match to C19 or the present vehicle. Current authenticated exact-car routes: **zero**.

| Segment | Compressed bytes | Last decoded log time (ns) | modelV2 | carState | radarState | controlsState | selfdriveState | carControl | carParams | longitudinalPlan | sendcan |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 11,282,740 | 393,051,080,005 | 1,200 | 5,973 | 1,200 | 5,973 | 5,973 | 5,973 | 2 | 1,200 | 5,973 |
| 6 | 13,628,533 | 453,053,266,076 | 1,200 | 5,974 | 1,200 | 5,974 | 5,974 | 5,974 | 1 | 1,200 | 5,974 |
| 105 | 11,079,674 | 6,393,172,697,716 | 1,200 | 5,972 | 1,200 | 5,973 | 5,972 | 5,973 | 1 | 1,200 | 5,972 |
| 106 | 11,116,113 | 6,453,163,931,444 | 1,200 | 5,970 | 1,200 | 5,973 | 5,971 | 5,973 | 1 | 1,200 | 5,970 |
| **Total** | **47,107,060** | — | **4,800** | **23,889** | **4,800** | **23,893** | **23,890** | **23,893** | **5** | **4,800** | **23,889** |

Each segment's minimum decoded time is `31,421,886,966 ns`, an initialization event. The last times above are segment maxima. The probe encountered zero undecodable events. `rawlog_census.py` marks counts `UNPARSED` unless the separately collected, digest-bound summary is supplied; a valid frame alone cannot establish service presence. The summary is reproducible but not independently signed.

## R9-2: genuine C19 MPC feasibility

`native_preflight.py` now emits a dependency graph and dynamic ELF `NEEDED` entries. On this x86_64 host, the generated Cython solver and five generated libraries are AArch64. The solver needs `libacados_ocp_solver_long.so` and `libc.so.6`; the local solver runpath includes `$ORIGIN`. Normal host Python has NumPy but lacks SciPy, CasADi, and Cap'n Proto. Cached Cap'n Proto used for the probe is a separate read-only analysis capability, not a C19 runtime environment. **No solver cycle was run or claimed.** No acados or product build was attempted.

The C19 `longitudinal_planner.py` reads `carState`, `radarState`, `modelV2`, `controlsState`, `selfdriveState`, `carControl`, `vehicleParameters`, CP, model lead history and planner state. `long_mpc.py` checks model/radar/car source timestamps, radar model association and model receipt time. The historical rlogs contain schema-readable messages for seven named services in every segment; they do not record the receiver's per-service receipt times, a C19 exact-source binding, authenticated drive reset boundaries or a current vehicle reference. `message_readiness` therefore reports `BLOCKED_RECEIPT_AND_EXACT_SOURCE_PROVENANCE`. `native_gap.py` now checks explicit driver override, lead-history source/receipt clocks, drive IDs, reset transitions and optional expected vehicle identity. A complete JSON inventory remains `SCHEMA_PRESENT_EXECUTION_UNVERIFIED`, never native execution.

## R9-3: source-aligned historical attribution

`historical_attribution.py` first validates every CSV row with R8's pinned event, segment and causal timestamp rules, then summarizes only qualifying rows. Alignment is to decoded `sendcan` publication with older-or-equal source holds. `aEgo` is a measured estimate on its own older timestamp; same-row differences do **not** establish command-response lag or actuator calibration. The historical CSVs contain 1,433 / 690 / 1,122 qualifying rows and 407 / 214 / 62 rows with a negative LongControl-to-CAN boundary delta below −0.02 m/s². No checked source timestamp is future. Across the three windows, all five source hold-age series have **zero** rows older than 200 ms.

| Event | Plan hold p50/max (ms) | CarControl hold p50/max (ms) | carState hold p50/max (ms) | Radar hold p50/max (ms) | Gas→brake / brake→gas | Standstill + brake rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LS001 | 23.9701 / 55.5639 | 7.0306 / 13.6184 | 1.3669 / 17.6021 | 24.7061 / 57.9555 | 2 / 2 | 237 |
| LS003 | 25.0691 / 55.6079 | 6.9774 / 8.9791 | 1.4025 / 1.8931 | 25.3474 / 55.8171 | 3 / 3 | 0 |
| LS004 | 23.8984 / 61.6041 | 6.9883 / 18.3273 | 1.3410 / 1.8561 | 25.5123 / 65.8817 | 0 / 1 | 847 |

The CLI also reports p90/p99 and plan-to-LongControl, LongControl-to-CAN, and CAN-to-measured same-row differences. The validated minimum issued CAN values remain −2.300 / −0.670 / −2.000 m/s²; measured `aEgo` minima remain −1.486 / −1.050 / −1.516 m/s², on their own timestamps. These are historical Candidate-1 measurements, not C19 replay or a brake tuning target. Fault tests cover duplicate clocks, wrong segment, missing/future provenance, stale lead history, reset misuse and vehicle mismatch.

## R9-4: inert shadow contract

`serialize_observation` is a disabled-by-default pure function returning canonical immutable JSON **bytes**. It requires source, receipt and cycle clocks; a 200 ms maximum source age; a lowercase SHA-256; explicit drive/cycle/reset continuity; and finite measured acceleration. It accepts `SIMULATED` or `HISTORICAL_UNVERIFIED`. The `CURRENT_VERIFIED` label fails closed because this package has no independent authentication authority. Stale, future, missing, bad digest, reset and identity faults emit only `FAILED_INPUT`, with no measurement. The earlier `observe` formatter remains for R8 compatibility and is historical-unverified only. Neither API emits commands, frames or hooks.

## Gate matrix and review prerequisites

| Gate | R9 state |
| --- | --- |
| R1 | Four physical historical segments integrity-checked and schema-read; zero authenticated current exact-car routes. |
| R2 | Native C19 execution blocked by architecture, dependencies, receipt clocks and exact-source provenance. |
| R3 | Source-aligned historical attribution and synthetic scenarios only; no C19 solver execution. |
| R4 | Owner's CMBS/FCW/AEB loss risk accepted for research; active safety case unresolved. |
| R5 | Inert offline serialized advisory contract; no runtime integration. |
| R6 | ARM64 hardware/build receipt pending. |
| R7 | Research candidate pending exact commit, deterministic archive, rollback and independent reproduction. |
| R8 | HIL, closed-course, legal/insurance and independent qualification pending. |
| A1–A5 | Radar/camera ownership, CAN2/relay recovery, Panda/brake policy, override/fault behavior, and road/legal release all unverified. |

Independent review needs current exact-car route custody and firmware/software/DBC binding; synchronized source and **receipt** clocks; same-cycle C19 planner state and lead history; an isolated architecture-matched solver receipt; then separate HIL and controlled qualification. The risk acceptance is not authorization for any active work. Stock C19 and safety functions remain installed and untouched.

## Verification and release state

On 2026-11-27, `python3 -m unittest discover -s tools/c20_accord11g_long_shadow/tests -q` passed **47 tests** (including the previous R8 cases); the raw census CLI, native preflight CLI, source gate and `git diff --check` passed. Source audit reported only research paths since the C19 baseline. This report is a working-tree research candidate until an exact Git commit is made. `bundle.py` must build a deterministic research-only archive **after** that commit from a clean tree; no raw logs enter it. No GitHub push or vehicle installation was done. See `r9_walkthrough.md` for bounded reproduction commands.

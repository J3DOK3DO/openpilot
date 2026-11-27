# R8 historical evidence and inert shadow decision — 2026-11-27

## Source chain and custody limits

Read-only originals are under `/home/jdkd/AI_Workspace/projects/accord11g-starpilot/c2-low-speed-causal-20260914_202004/`. The September Candidate-1 audit names source commit `d49c5ff167bfa2fc3e4c7a626dd8cd3404cd060b`, OpenDBC tree `d5967a1fc00912edde415105973e2a93224ec423`, and an original route archive. Its extraction script uses local `LogReader`, four rlog segments, and a native monotonic route origin of `31374859675 ns`. It chooses the latest plan/control/state/radar publication **at or before** each decoded `sendcan` `ACC_CONTROL` publication. Its CSVs are derived, not original signed recordings. We independently hashed the local bytes and validated the scalar clocks, deltas and event counts; we did not authenticate the upstream archive, vehicle, firmware, DBC or extraction environment. No VIN or location is included here.

| Read-only file | SHA-256 |
| --- | --- |
| `FULL_RATE_LOW_SPEED_CAUSAL_AUDIT.md` | `07e0cbef3bb248274c616a6d10edb7ac236ba5b36a9d9f48a6c65ce63cab9431` |
| `extract_full_rate.py` | `5932b5ec8d53503da9b8600e4bdbfdf0a88d85090da791c2ad7cb4052ca5e74b` |
| `LS001_FULL_RATE.csv` | `554e2eb396b53ce78dca8a04091dc798ad9d27f56691dc38431c19c3380c0f74` |
| `LS003_FULL_RATE.csv` | `3ee6c209182537879c4a0635b11ed9e18f3dfd43bd5702e0767c2c1958118165` |
| `LS004_FULL_RATE.csv` | `5f70252d49eece5adab15ba79329200b247328c1afdff1948823fc4c9c823aa4` |
| route segment 5 `rlog.zst` | `495800114585f060007efa56472622125182b064834528511fb5576b0c95b435` |
| route segment 6 `rlog.zst` | `1646f143bc0a90bac360c0db329e302b022808a5f4c7ff70aa6f5f92b095355a` |
| route segment 105 `rlog.zst` | `1fba3eb1e1b37e217ab387b430073ad3a62672763e0d139325372ffc4a28135f` |
| route segment 106 `rlog.zst` | `d4d8c4c368557e920c52f1484f307aa2859876f4e168d4396df264c40a5a0202` |

The three CSVs contain 1,881 / 1,139 / 1,571 total rows and 1,433 / 690 / 1,122 qualifying rows. Their first and last `logMonoTime` values are respectively `6358294048980–6396071171101`, `6387290386573–6410153782189`, and `373750519231–405291721251 ns`. Each row checks the route-time transform and nonfuture source hold stamps. Units: monotonic `ns`, human route seconds, speed `m/s`, acceleration `m/s²`, hold age `ms`; `GAS_COMMAND` is a decoded raw integer with `-30000` as the extraction's no-gas sentinel, and `BRAKE_REQUEST` is a bit. The script's `gas_force_coordinate` is a copy of requested acceleration; hill/wind terms are not recorded. A filtered `vEgo` of −0.0025 m/s near standstill occurs in LS001, so the validator permits small negative sensor noise down to −0.5 m/s while rejecting larger negative speed.

## Measured versus requested observations

`longitudinalPlan.aTarget` is a historical planner request, `carControl.actuators.accel` a historical LongControl output, `ACC_CONTROL.ACCEL_COMMAND` a decoded issued CAN value, and `carState.aEgo` a measured response estimate. The first three are not measured deceleration. Sample-boundary differences are descriptive and do not imply an actuator calibration.

| Event | Planner min | LongControl min | Issued CAN min | Measured aEgo min | CAN minus LongControl < −0.02 rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| LS001 | −1.667 | −2.001 | −2.300 | −1.486 | 407 |
| LS003 | −0.492 | −0.492 | −0.670 | −1.050 | 214 |
| LS004 | −1.417 | −2.001 | −2.000 | −1.516 | 62 |

All accelerations in m/s². The September audit's event counts and minima are reproduced by the streaming CSV reader. The matched LS004 CAN minimum has plan −0.186, LongControl −2.001, CAN −2.000, so the deep plan-to-CAN gap is upstream of the final Honda boundary at that instant. The 62 boundary rows are a separate earlier transient. LS001 has both a stopping-state LongControl surplus and a direct negative final-boundary surplus; LS003 is primarily the latter at its command minimum. LS001 and LS003 each have 2 and 3 gas-to-brake transitions; LS004 has none in the qualifying window. LS004 records 847 standstill rows with brake requested, but this is historical command persistence, not proof of stationary holding force or C19 behavior. Measured response extrema occur on their own timestamps; no future-aligning them with command minima is allowed.

## Native same-cycle gap

`native_gap.py` reports **FAIL_MISSING_REQUIRED_INPUTS** for each scalar CSV. The CSV has several carState/radarState/carControl scalars and message timestamps, but lacks the complete serialized C19 messages, full `modelV2` trajectories, `controlsState`, `vehicleParameters`, `selfdriveState`, `CP`, model/lead history, drive reset boundaries, exact current firmware/software/DBC binding and independent custody reference. It cannot be relabeled as a C19 MPC replay fixture. The C19 `LongitudinalMpc` imports `openpilot.cereal.log`, CasADi, and its generated acados solver. This host is x86_64, the checked solver and five generated libraries are AArch64, and host Python lacks CasADi and CapNP; no solver was executed or installed. The September Candidate-1 source and C19 source are distinct revisions with no demonstrated exact-vehicle equivalence.

## Shadow interface and fault boundary

`shadow_advisory.observe(HistoricalSample, ShadowConfig)` is a stateless pure formatter. Configuration defaults disabled. Enabled output is labeled `HISTORICAL_UNVERIFIED`, carries only the measured aEgo and decoded historical CAN value with the source digest, and says `autonomous_braking: false`. Invalid time, nonfinite numeric values or malformed digest return `FAILED_INPUT`. It has no process import, transport, CAN frame, CarParams, Panda, actuator value, runtime hook or persisted setting. The recursive AST source audit rejects forbidden imports, dynamic imports, control bindings, symlinks and out-of-scope Git changes. That audit is a research source gate, not a runtime safety proof.

Any later qualified runtime interface would need a separate design, authorization and implementation: read-only receipt of versioned, independently authenticated observations; exact source/receipt clocks and validity; explicit stale/fault state; bounded telemetry schema; zero authority to publish control, CAN or diagnostics; separate process and hardware isolation review. No C19 launch path is wired here.

## Release and independent review gate

R1: four historical raw segments, three derived windows, **zero authenticated current exact-car routes**. R2: native C19 execution blocked. R3: deterministic behavioral synthetic suite plus historical Candidate-1 measured attribution; no C19 replay equivalence. R4: owner CMBS/FCW/AEB loss risk accepted for research only; active safety case unresolved. R5: offline inert shadow formatter and source gate pass; no production integration. R6: ARM64 build/receipt pending. R7: commit-pinned offline research archive can be generated and verified after commit; rollback and independent reproduction pending. R8: HIL, closed-course, legal/insurance and independent qualification pending.

A1 radar/camera ownership and stock ACC/AEB coexistence; A2 CAN2/relay startup and recovery; A3 Panda policy and brake command failure; A4 override, timeout, lead validity and fault behavior; A5 road release/legal/insurance: **all unverified**. HIL readiness requires exact hardware and firmware inventory, synchronized source and receipt timestamps, isolated no-actuation replay harness, independent fault injections and a reviewed expected behavior matrix. Parking/closed-course prerequisites include stock ACC recovery, driver override, loss-of-sensor and emergency-stop checks under a separate authorized safety plan. No road actuation or installer qualification follows from this archive. Active longitudinal control remains **NO-GO**; stock ACC and CMBS/FCW remain unsuppressed by C20.

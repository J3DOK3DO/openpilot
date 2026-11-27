# C20 Accord 11G long shadow: offline research

This package reads local JSON, computes descriptive acceleration references, and prints JSON metrics. It imports only Python's standard library and its own modules. It has no CAN, UDS, Panda, controller, device, scheduler, or runtime integration. The calculations are **not** actuator commands or proof of braking. Stock ACC and C19 code are untouched.

## Run

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/c20_accord11g_long_shadow/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.replay tools/c20_accord11g_long_shadow/fixtures/synthetic_trace.json --synthetic
```

The fixture is invented and always emits `SIMULATED`. A recording requires a manifest, a separately authenticated reference record, and its canonical SHA-256 obtained independently:

```sh
python3 -m tools.c20_accord11g_long_shadow.replay TRACE.json \
  --manifest MANIFEST.json --trusted-reference REFERENCE.json \
  --reference-sha256 EXPECTED_REFERENCE_SHA256
```

The reference must bind the exact route ID, trace SHA-256, software SHA, DBC SHA, vehicle identity, fingerprint, radar/camera/brake firmware, timestamps and units. A locally fabricated matching reference is not independent evidence. Even a matching digest is labeled `REFERENCE_MATCH_UNVERIFIED` because this program cannot authenticate its issuer or vehicle custody. The example manifest contains `UNVERIFIED` placeholders and is intentionally inadmissible.

## Input contract

The trace is a JSON array of rows. Each row needs `t_ns` (monotonic nanoseconds), `v_ego`, `a_ego`, `v_cruise`, `raw_accel` (m/s, m/s² as appropriate), `pitch` (radians), boolean `gas_pressed`, `brake_pressed`, `stock_aeb`, and `lead`. `signal_t_ns` must give separate source timestamps for each of those eight non-lead signals, each no older than 200 ms. `lead` is `null` or an object with `track_id`, `t_ns`, `valid`, `radar`, `distance` (m), `speed` (m/s), and `confidence` in [0,1]. A present lead must be no older than 200 ms. Row gaps may not exceed 500 ms. A real trace with missing fields is rejected rather than interpolated. `raw_accel` is a recorded/descriptive acceleration demand signal, not a CAN output.

The manifest schema is shown in `fixtures/example_manifest.json`. Hash fields use lowercase 64 digit SHA-256 hex. The exact vehicle descriptor is Honda Accord 2024 Hybrid Touring, US-spec import. `HONDA_ACCORD_11G` is required; CR-V/Pilot 4G traces cannot be relabeled. The manifest must give actual ECU firmware strings, route ID, software and DBC hashes, first/last timestamp, units, and a SHA-256 of the exact trace bytes. No VIN, user identity, device identity, or location is required.

## Interpretation

The two strategies are `c19_behavioral` and `c6_behavioral`. Both are simplified references driven by **the same** input rows. Neither runs the C19 MPC/native solver, C6's full planner, a stock ACC controller, or the MVL controller. Headway is observed lead distance divided by observed ego speed. Acceleration error compares reference demand with the supplied descriptive `raw_accel`; jerk is the derivative of the reference demand, not measured vehicle jerk. Hold, transition, override, freshness, TTC and failure reasons are counts or per-row labels. The braking floor is only a numerical reference rule, not evidence of AEB or driver-brake preservation. The response fields compare the MVL planner's scalar pitch coast expression and a wind table from its Honda controller; the wind table and learned gas/wind factors are not validated Accord calibrations. `mvl_factor_reference` is a bounded counterfactual, omitting controller saturation, PID, and history. A measured improvement cannot be inferred from any of these metrics.

## 2026-11-27 campaign additions

`inventory.py` hashes bounded local raw logs and metadata without inferring vehicle identity. `native_preflight.py` checks the actual compiled C19 solver architecture and imports without loading it. `scenarios.py` runs deterministic static/closing lead, cut-in, phantom, override/AEB observation, radar-loss, grade and stop/go cases. `release_gate.py` audits research source scope and emits active-control `NO_GO`. See [risk_acceptance.md](docs/risk_acceptance.md) and [release_recipe.md](docs/release_recipe.md). No runtime hook or actuator path is present.

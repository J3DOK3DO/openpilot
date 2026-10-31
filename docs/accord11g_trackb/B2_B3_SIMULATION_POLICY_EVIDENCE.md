# B2/B3 limited simulation and host-policy evidence

## B2: synthetic analysis only

`tools/trackb_research/shadow_synthetic.py` remains a standalone Python standard-library-only eligibility helper. It is not imported by any live openpilot process and contains no CAN, Panda, UDS, Params, network, file-write, vehicle, or command output path. Its immutable synthetic `Observation` has caller-supplied monotonic acquisition/decision timestamps, validity, AEB/CMBS state, driver inputs, explicit engagement token, conflict state, optional synthetic lead presence, and latency. Its only result is `eligible_for_analysis` or `withdrawn/unknown` plus a reason.

`tools/trackb_research/plan_controller_sim.py` is a separate standard-library-only, non-actuating downstream simulation. `PlanSnapshot` deliberately mirrors only the relevant published-plan shape: model/plan monotonic identities, publication time, `a_target`, `should_stop`, `allow_brake`, `allow_throttle`, `has_lead`, plan source, and speed/acceleration/jerk vectors. `VehicleObservation` is synthetic driver/vehicle state. Dom `a_target` is the sole acceleration-magnitude input: the simulator does not compute a speed, trajectory, lead response, or replacement plan. Dom `shouldStop` is an existing plan mode signal used only to select abstract downstream standstill-hold behavior; it is not a second planner or an acceleration-magnitude input. The simulator emits only `SimulationRecord(mode, acceleration_request, reason, identities)` where the hold selection and acceleration field are abstract, non-actuating, and have no physical or encoded meaning. Its symbolic envelope and expiry values are test-owned, explicitly not vehicle calibration or OEM requirements.

It fails closed for stale/invalid/nonfinite/timestamp-inconsistent data, including oversized integer inputs; empty or unequal plan-vector lengths; duplicate or out-of-order inputs; driver brake/accelerator/cancel; contradictory state; active/unknown AEB/CMBS; and throttle/brake denials. Synthetic float-valued fields are bounded before calling `math.isfinite`; monotonic identifiers are separately constrained to positive UInt64-shaped values. Every withdrawal retires the last accepted token and any valid token on the fault record; retired tokens remain rejected for simulator lifetime, including after recovery. Within an active logical session the accepted token is stable, and a silent token change withdraws explicitly. `reset()` clears ordering identifiers only, retains retired tokens, and after prior acceptance requires a new, never-retired token. `test_architectural_isolation.py` proves no `tools.trackb_research` reference occurs in production `openpilot`, `opendbc`, or `panda` source and parses the simulator imports to restrict them to the standard library. This is a structural test-only boundary, not a vehicle claim.

`ExpiryPolicy.stale_after` is intentionally passed by a test. It is a symbolic synthetic contract parameter, not a chosen vehicle target or control requirement. The tests cover `T_stale−ε`, `T_stale`, and `T_stale+ε`; malformed objects/lists; nonblank-stripped IDs/tokens; actual boolean flags; optional lead `bool|None`; AEB string type; nonfinite and huge numeric inputs across timestamps, plan vectors, policy values, vehicle values, and monotonic IDs; negative-zero behavior; duplicates; atomic ordering; driver/AEB faults; retirement across multiple faults/resets; stable repeated tokens; silent token changes; and recovery only with a new, never-retired token. Recovery is an in-memory simulator-state transition and provides no vehicle authority.

This is not the B2 longitudinal controller, planner, vehicle simulator, protocol decoder, calibration, or acceptance oracle. It provides no acceleration, gas, brake, torque, CAN encoding, or production authority.

## B3: RELEASE host-source negative evidence only

`opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py` calls the existing `libsafety_py._build_libsafety(release=True)` and `make_CANPacket` API. It tests Honda words 80/81, alternative experiences 0/32, and controls allowed true/false against the enumerated generic Bosch-long bus-1 table entries: `0xE4`/5, `0x1DF`/8, `0x1EF`/8, `0x1FA`/8, `0x30C`/8, `0x33D`/5 and /8, `0x33DA`/5, `0x33DB`/8, and `0x39F`/8, plus a syntactically valid UDS tester-present single frame. All enumerated probes must be denied. These generic examples are deliberately not asserted to be 11G protocol; configurations outside the listed stock words/experiences are not generalized.

This test does not access a CAN device, compile/flash Panda firmware, alter an allowlist, transmit, or establish a target Panda RELEASE authorization. It is a regression guard for the current host source policy only. If a native RELEASE build cannot be supported, the correct result is a documented blocker; no allowlist or policy weakening is allowed.

## Commands to execute in Dom's native host wrapper

The following are commands for evidence collection; this document does not claim they have run.

```sh
./dev pytest tools/trackb_research/tests/test_shadow_synthetic.py
./dev pytest tools/trackb_research/tests/test_plan_controller_sim.py tools/trackb_research/tests/test_architectural_isolation.py tools/trackb_research/tests/test_canfd_dictionary.py
./dev pytest opendbc_repo/opendbc/car/honda/tests/test_accord11g_stock_ownership_v4.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_trackb_no_long_authority.py
./dev pytest opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_denials.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py
./dev python -m ruff check --no-cache tools/trackb_research/plan_controller_sim.py tools/trackb_research/shadow_synthetic.py tools/trackb_research/tests/test_plan_controller_sim.py tools/trackb_research/tests/test_shadow_synthetic.py tools/trackb_research/tests/test_architectural_isolation.py tools/trackb_research/tests/test_canfd_dictionary.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py
```

Passing host tests would remain limited test evidence. B1 is not complete, B2 has no controller, and B3 has no actual Panda RELEASE firmware authorization.

## B2 downstream synthetic research model

The added PlanControllerSimulation in tools/trackb_research/plan_controller_sim.py consumes a synthetic already-published Dom a_target and synthetic vehicle observations. Its output acceleration_request is a bounded **abstract test record only**, not a vehicle command; no CAN, UDS, Panda, Params or live OpenPilot service imports are present. The now-monotonic comparison preserves a last accepted decision-clock boundary across reset; a separately supplied required synthetic boolean stock_acc_enabled withdraws on disabled or unknown/malformed input. No factory ACC ownership or custom longitudinal authority has been physically established. Current post-Qwen selected native suite: 169 PASS. B1 and the actual custom longitudinal controller remain unqualified.

# B2/B3 limited simulation and host-policy evidence

## B2: synthetic analysis only

`tools/trackb_research/shadow_synthetic.py` is a standalone Python standard-library-only module. It is not imported by any live openpilot process and contains no CAN, Panda, UDS, Params, network, file-write, vehicle, or command output path. Its immutable synthetic `Observation` has caller-supplied monotonic acquisition/decision timestamps, validity, AEB/CMBS state, driver inputs, explicit engagement token, conflict state, optional synthetic lead presence, and latency. Its only result is `eligible_for_analysis` or `withdrawn/unknown` plus a reason.

`ExpiryPolicy.stale_after` is intentionally passed by a test. It is a symbolic synthetic contract parameter, not a chosen vehicle target or control requirement. The tests cover `T_stale−ε`, `T_stale`, and `T_stale+ε`; malformed objects/lists, nonblank-stripped IDs/tokens, actual boolean flags, optional lead `bool|None`, AEB string type, nonfinite and huge numeric inputs, negative-zero behavior, immutability, duplicates, atomic ordering, driver/AEB faults, and recovery only after a fresh monotonic observation with a new non-poisoned token. That recovery is an in-memory logical state transition; this harness makes no initial or later physical-driver-handback claim.

This is not the B2 longitudinal controller, planner, vehicle simulator, protocol decoder, calibration, or acceptance oracle. It provides no acceleration, gas, brake, torque, CAN encoding, or production authority.

## B3: RELEASE host-source negative evidence only

`opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py` calls the existing `libsafety_py._build_libsafety(release=True)` and `make_CANPacket` API. It tests Honda words 80/81, alternative experiences 0/32, and controls allowed true/false against the enumerated generic Bosch-long bus-1 table entries: `0xE4`/5, `0x1DF`/8, `0x1EF`/8, `0x1FA`/8, `0x30C`/8, `0x33D`/5 and /8, `0x33DA`/5, `0x33DB`/8, and `0x39F`/8, plus a syntactically valid UDS tester-present single frame. All enumerated probes must be denied. These generic examples are deliberately not asserted to be 11G protocol; configurations outside the listed stock words/experiences are not generalized.

This test does not access a CAN device, compile/flash Panda firmware, alter an allowlist, transmit, or establish a target Panda RELEASE authorization. It is a regression guard for the current host source policy only. If a native RELEASE build cannot be supported, the correct result is a documented blocker; no allowlist or policy weakening is allowed.

## Commands to execute in Dom's native host wrapper

The following are commands for evidence collection; this document does not claim they have run.

```sh
./dev pytest tools/trackb_research/tests/test_shadow_synthetic.py
./dev pytest opendbc_repo/opendbc/car/honda/tests/test_accord11g_stock_ownership_v4.py opendbc_repo/opendbc/car/honda/tests/test_accord11g_trackb_no_long_authority.py
./dev pytest opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_denials.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py
./dev python -m ruff check tools/trackb_research/shadow_synthetic.py tools/trackb_research/tests/test_shadow_synthetic.py opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_rejections_extended.py
```

Passing host tests would remain limited test evidence. B1 is not complete, B2 has no controller, and B3 has no actual Panda RELEASE firmware authorization.

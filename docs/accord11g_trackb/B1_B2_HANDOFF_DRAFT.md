# B1/B2 source-only research engineering handoff

- Branch: `accord11g-dom7-trackb-b1-b2-simulation-20261031`
- Starting SHA: `82e053f56c18a814f1a98ea10e7b2b4057ed7d76`
- This document identifies the reviewed parent SHA; final GitHub publication identity is recorded separately in the release handoff.

## Delivered review set

- B1 source-only protocol specification, exact-classification evidence matrix, OEM authority/unresolved report, and deterministic current DBC dictionary.
- B2 `PlanControllerSimulation`: standard-library-only synthetic downstream state machine that accepts plan/observation snapshots and emits abstract non-actuating records. Dom `a_target` is the sole acceleration-magnitude input; Dom `shouldStop` only selects abstract downstream standstill-hold behavior and is not a second planner. It does not create a planner, use runtime imports, encode CAN, or alter production code. Existing `ShadowEligibility` was unchanged.
- New deterministic tests for plan/observation staleness, validity, bounded huge numeric inputs, UInt64-shaped IDs, ordering, malformed records, tokens retired for simulator lifetime, stable active-session tokens, multiple-fault/reset recovery, stop/standstill mode selection, driver override, AEB/CMBS unknown/active, gate denials, isolation, and dictionary reproducibility.
- R2 correction validation: 116/116 B1/B2 and shadow synthetic tests plus 53/53 selected Honda/RELEASE/parked-audit tests passed; Ruff, compile, deterministic dictionary, production-isolation, and whitespace checks passed. Qwen3-Coder reviewed actual source attachments; advisory findings were independently adjudicated. The final native rerun passed.
- Updated B0--B6 matrix: B1 is **PARTIAL / STOP**; B3 remains active at its **HOLD** boundary; B4, B5, and B6 are **HOLD** in this no-device pass.

Changed files are the B1/B2 documents and data under `docs/accord11g_trackb/`, plus `tools/trackb_research/plan_controller_sim.py`, `extract_honda_canfd_dictionary.py`, and their three tests. No production runtime, Panda safety source, CarParams selection, DBC production definition, manager service, firmware, or actuation path changed.

See [test results](B1_B2_TEST_RESULTS_20261031.md) for commands and exact pass counts.

## Outstanding evidence

B1 still needs authoritative OEM electrical/service architecture and independently reviewed non-actuating target-specific evidence for ECU inventory/ownership, CAN-FD topology and protocol, AEB/CMBS/ACC priority, diagnostics, fault and recovery. B3/B4/B5/B6 require their respective separate authorizations and evidence. This pass provides no vehicle or release authorization.

## Subsequent Qwen-informed source delta

A synthetic factory-ACC state field is now required by VehicleObservation. The research simulator withdraws on factory ACC disabled or malformed state and explicitly refuses backwards decision-clock movement across steps and reset. This changes synthetic research only; no live vehicle runtime, Panda policy, CAN, or device.

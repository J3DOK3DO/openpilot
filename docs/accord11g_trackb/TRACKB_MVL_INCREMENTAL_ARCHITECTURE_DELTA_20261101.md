# Accord 11G Bosch-C — incremental MVL architecture delta (2026-11-01)

**Analysis method:** Codex gpt-6-astra/max source investigation, gracefully interrupted and continued in the **same session** with gpt-6-luna/medium at the owner’s request to reduce usage. Findings are source-derived only. No implementation, tests, or target qualification occurred in this analysis.

**Source pins:** [MVL opendbc 3fec9a](https://github.com/mvl-boston/opendbc/tree/3fec9a418a659de31d7b1f494193161697a35071) · [Dom Track B17 1d810b7](https://github.com/J3DOK3DO/openpilot/tree/1d810b741586034aa90a8490fb3d922e3b7a7198)

## 1. Executive delta

**Seven incremental source findings** add detail to the existing analysis. They concern how MVL infers source silence and relay state, how its radar tick and lane metadata are generated, how Panda forwarding changes after a relay fault, and what its shutdown and startup-fault paths establish. These are code-level observations, not evidence about the US 2025 Accord Hybrid’s actual buses, ECUs, message meanings, installed firmware, or safety behavior.

The pinned source is MVL `3fec9a418a659de31d7b1f494193161697a35071` (“M” below); the reviewed Dom source is `1d810b741586034aa90a8490fb3d922e3b7a7198` (“D”). The new findings do not qualify alpha-longitudinal control or establish safe return to factory ACC. **All four B1 gates remain HOLD; B3/B4 remain unqualified and B5/B6 unevaluated.** No tests were run for this assessment.

## 2. Baseline reuse and duplicate exclusions

I treated the following records as established baseline and did not reproduce their inventories, parameter results, or passed tests:

- [Three-way MVL/comma/Dom source audit](TRACKB_MVL_3FEC9A_COMMA_DOM_SOURCE_AUDIT_20261101.md)
- [L01–L10 / G01–G14 crosswalk](TRACKAB_MVL_FUNCTIONAL_GAP_MATRIX_20261101.tsv)
- [B1 source/OEM evidence matrix](B1_CURRENT_SOURCE_OEM_EVIDENCE_MATRIX.md), [protocol research specification](B1_PROTOCOL_RESEARCH_SPEC.md), and [B1 continuation](TRACKB_B1_RESEARCH_CONTINUATION_20261101.md)
- [B17 hazard record](TRACKB_B17_MVL_HAZARD_AND_ARCHITECTURE_20261101.md), [17-ID simulation matrix](TRACKB_B17_RETAINED_PATCH_SIMULATION_MATRIX_20261101.tsv), and [integration handoff](TRACKB_B17_INTEGRATION_HANDOFF_20261101.md)
- [Owner-accepted research deviations](TRACKB_B1_OWNER_ACCEPTED_DEVIATIONS_20261101.md)

The reported offline test pass and independent review are reused as prior history; neither was rerun. In particular, the safety-denial tests establish a host-library policy result for selected source configurations. They do not demonstrate that a faulted operational takeover safely restores factory ACC or retains CMBS/AEB/FCW. Owner acceptance of the proposed architecture’s expected CMBS/AEB/FCW loss remains a hazard acknowledgement, not a safe-operation finding.

## 3. Architecture pathways and target applicability

The “M” references below are relative to `opendbc/` in the pinned MVL worktree. “D” references are relative to `opendbc_repo/` in the reviewed Dom worktree. Source confirms code behavior only.

| Pathway | Source observation and 11G relevance |
|---|---|
| Platform, config, and bus routing | M `opendbc/car/honda/values.py:172–178, 215–221` selects the Bosch-C/CAN-FD platform and shared DBC for the Accord family. M `hondacan.py:6–40` assigns CAN-FD PT, radar, camera, and LKAS logical buses. These are software labels, not observed US 2025 Hybrid wiring. D `interface.py:51–59` keeps CAN-FD alpha long unavailable and factory PCM cruise selected. The existing hybrid qualification issue is excluded. |
| CarState ownership inputs | M `carstate.py:360–378` infers stock ACC and relay state from successfully parsed message history and an update counter. D `carstate.py:225–227, 250–267` also selects camera-side LKAS HUD for the exact Accord 11G, while D `interface.py:219–225` permits alternate-brake configuration for a CAN-FD fingerprint. Neither establishes target-frame semantics. |
| Radar-disabled hypothetical | M `interface.py:405–430`, `carcontroller.py:629–705, 1177–1183`, and `honda.h:392–408, 594–615` describe deferred radar diagnostics, look-alike traffic, and an expanded CAN-FD-long table. These are hypothetical community architecture paths. Their timing, ECU ownership, and return-to-stock behavior have not been authenticated for the target. |
| Panda nominal and fault forwarding | M `honda.h:729–749` contains Honda-specific forwarding blocks. The generic safety hook at `safety.h:340–360` also blocks all forwarding when relay malfunction is latched. Thus nominal forwarding claims do not describe the relay-fault path. |
| DBC and generated metadata | M `honda_common_canfd.dbc:9–72` declares radar-reference/tick messages, muxed lane/object records, counters, and checksum fields. M `hondacan.py:345–362` implements the community checksum offset. These are source definitions and algorithms, not proof of target authentication, bus ownership, DLC, rate, or checksum protocol. |
| SunnyPilot extensions | The pinned `carstate_ext.py:25–33` has a camera-speed-limit path, but its enable flag is derived from a PT fingerprint in M `interface.py:323–325`; the extension chooses PT for platforms outside its CAN-FD/radarless sets. That path may be relevant only if the 11G flag and routing conditions hold; target applicability is unverified. ICBM button spoofing in `icbm.py:17–39` changes stock set speed and is outside this assessment’s control scope. MADS is superseded by Dom AOL for this target (existing crosswalk L08); modified EPS and Nidec/hybrid additions do not establish an applicable 11G control path. |

## 4. New verified source findings

### F1 — Parsed-message silence and relay-open labels can be inferred from missing data
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P1 research
**Sources:** M `opendbc/car/honda/carstate.py:360–378`; parser `opendbc/can/parser.py:38–82, 214–251`.

`stock_acc_alive` is based on whether `ACC_CONTROL` appears in `vl_all`, then becomes false after four update cycles without an accepted entry. The relay label becomes true after five cycles without accepted camera `STEERING_CONTROL` once seen, **or after 500 CAN-FD state updates**. This code does not separately establish whether the bus was silent, the message was invalid, the stream was otherwise unhealthy, or the relay physically opened. The 500-update fallback does not require camera silence.

**Effect:** An inferred source transition is not confirmation of vehicle ownership or a real relay transition. A non-actuating regression should distinguish missing messages from malformed/rejected messages and test continuous camera-steering observations through the 500-update fallback. Relevant IDs: **BC-009, BC-010, BC-012**. No real CAN transmission is appropriate.

### F2 — Radar tick pulses have no “reference observed” prerequisite
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P2 research
**Sources:** M `carstate.py:76–84, 313–358, 427–435`; DBC `honda_common_canfd.dbc:64–72`; consumer `carcontroller.py:662–705`.

The tick counters initialize at zero. When no tick reference is found in the current `vl_all` window, the counters increment and set one-shot Boolean pulses at fixed counts. The tick DBC records use `IGNORE` fields and declare message sizes of 32, 6, and 16 bytes, but the parser’s generic signal decoder does not enforce the DBC message size for each accepted frame. The code therefore derives cadence events from update counts without first proving a reference stream was observed or remained fresh.

**Effect:** DBC names, nominal sizes, counters, and parser freshness behavior do not authenticate those references or their timing. Add source-only parser fixtures for absent, stale, wrong-length, and valid-reference cases; assert that “no reference observed” remains distinct from a measured tick. Relevant IDs: **BC-011, BC-020–023**.

### F3 — The normal forwarding sweep omits the global relay-fault outcome
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P1 research
**Sources:** M `opendbc/safety/safety.h:340–360`; `opendbc/safety/modes/honda.h:729–749`; existing Dom test `opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_mvl3fec9a_canfd.py:76–97`; generic relay test `opendbc_repo/opendbc/safety/tests/common.py:1083–1100`.

In a nominal configuration, the target denial test verifies selected forwarding behavior, including the static blocks and the radar-diagnostic address. In a relay-malfunction state, the generic forwarding hook returns blocked for every message. The generic test already checks that behavior, so this is a **documentation qualification**, not a request to duplicate it.

**Effect:** Nominal forwarding assertions do not establish delivery of OEM ACC/CMBS traffic under a latched relay fault. Any takeover safety claim would need a fault-path argument; no source-only denial sweep can prove safe recovery or physical braking behavior. Relevant IDs: **BC-010, BC-012**.

### F4 — The shutdown helper does not establish successful ECU restoration
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P1 research
**Sources:** M `opendbc/car/honda/interface.py:405–430, 433–436`; `opendbc/car/honda/carcontroller.py:629–652`; Panda allowlist `opendbc/safety/modes/honda.h:392–408`.

The hypothetical deinit path reuses `init` with an enable-communication request. The reviewed CAN-FD safety hook accepts only the documented diagnostic-session and disable-communication request forms, while the car-side code shown does not establish an accepted enable request, ECU acknowledgement, resumed ACC stream, or fault-free factory ownership afterward. This identifies an unproven path; it does not establish whether some external safety-mode transition changes the result.

**Effect:** Calling a source helper “enable” is not proof that stock service resumed or that the transition is safe. A documentation-only lifecycle table should distinguish request construction, Panda acceptance, ECU response, stock-message resumption, and fault clearance as separate unknowns. Relevant IDs: **BC-012 and DRV-007**. BC-016’s explicit re-enable is outside the retained 17-ID set and is not revived here.

### F5 — Startup fault suppression changes status, not the underlying evidence
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P3 research
**Sources:** M `carstate.py:66–67, 271–281`.

For Bosch longitudinal mode, an ACC fault observed before the initial ten-second timer expires is returned as `accFaulted = False` while `cruiseState.available = False`. The timer is one-time: once it expires, the code marks startup fault clearing complete. This is an availability gate, not proof that a raw fault cleared or that the system recovered.

**Effect:** A synthetic test should retain separate fields for raw fault, reported fault, availability, and elapsed startup interval. It should assert both the startup suppression case and the post-window persistent-fault case. Relevant ID: **DRV-007**. This source detail does not establish that this fault is present on the target.

### F6 — DBC mux annotations do not become parser-level semantic checks
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P3 research
**Sources:** M `opendbc/dbc/generator/honda/honda_common_canfd.dbc:21–56`; `opendbc/can/dbc.py:148–198`; `opendbc/car/honda/lane_path.py:119–129`; `opendbc/car/honda/hondacan.py:270–313`.

The DBC describes muxed lane/object signals, but the parser stores signal layouts rather than enforcing the source’s mux-bank sequencing rules. The application code manually maps mux values to point groups and creates idle/object values. A pack/parse round trip can therefore show that the source encodes itself consistently without proving that the mux, sentinel, or counter pattern matches an OEM target.

**Effect:** Documentation or synthetic-only assertions should verify the code’s own mux-to-slot and sentinel mapping, and explicitly label the result “source self-consistency,” not protocol validation. Relevant IDs: **BC-022–024**; the existing audit already covers checksum claims and their lack of OEM authority.

### F7 — Lane-count metadata reads cached lane state
**Classification:** `NEW_VERIFIED_SOURCE_GAP` · **Priority:** P2 research
**Sources:** M `carcontroller.py:692–705, 1313–1328`; `hondacan.py:316–342`.

The 5 Hz lead metadata uses `self.dash_lane`, while lane state is refreshed in a separate 50 Hz branch later in the controller update. Thus a coincident update can construct lead lane-count/line metadata from the prior cached lane snapshot and lane-path data from the current update. The source comments claim lockstep, but this call ordering permits a one-update separation in the host model.

**Effect:** A non-actuating synthetic ordering test can tag cached lane revisions and assert whether the intended metadata and path share a revision, including coincident and missed tick cases. This tests source consistency only, not whether the vehicle’s dash uses these fields as claimed. Relevant IDs: **BC-022, BC-023**.

## 5. Unverified hypotheses and evidence limits

| Candidate | Classification | Why source cannot close it |
|---|---|---|
| Radar silence, relay state, message owner, and bus topology on a US 2025 Accord Hybrid | `UNVERIFIED_HYPOTHESIS` | MVL logical bus labels and parser counters are not passive target observations or OEM wiring documentation. |
| Radar tick meanings, rates, freshness, DLC rules, checksum boundary, and counter semantics | `UNVERIFIED_HYPOTHESIS` | A DBC and packer can encode a community interpretation; neither establishes Honda’s protocol for this year/region/platform. |
| CMBS/AEB/FCW precedence, fault latch duration, override behavior, and factory ACC recovery | `UNVERIFIED_HYPOTHESIS` | Community comments and owner-manual function descriptions do not authenticate frame-level priority, timing, or recovery. |
| SunnyPilot camera-message flag and actual 11G camera/PT routing | `UNVERIFIED_HYPOTHESIS` | The source condition and consumer bus are readable, but no target fingerprint or passive capture establishes whether the enabling message is present on either bus. |
| Whether synthetic model lead entries denote distinct physical vehicles | `UNVERIFIED_HYPOTHESIS` | MVL’s `hud_objects.py:190–198, 281–307` applies spatial-separation rules to model horizons; that does not identify separate real objects. |

## 6. Retained 17-ID mapping: new research only

| IDs | Incremental action |
|---|---|
| **BC-009, BC-010, BC-012** | Add the F1 distinction between parsed-message absence, relay inference, and physical ownership. |
| **BC-011, BC-020–023** | Add F2 absent/stale/reference cases and F7 lane-snapshot ordering as metadata-only assertions. |
| **BC-024** | No new checksum finding. Keep the existing classification as an unauthenticated source claim. |
| **DRV-007** | Add F4 lifecycle-stage distinction and F5 raw/reported startup-fault assertions. |
| **DRV-001, DRV-003, DRV-005, DRV-006, DRV-008, DRV-009, DRV-010** | No incremental MVL source finding identified beyond the existing B17 matrix. |

These additions are test or documentation requirements only. They do not request physical gas/brake transmission.

## 7. Prioritized non-actuating backlog

1. **P1 — Ownership inference contract:** document and simulate absent versus invalid ACC frames, continuing camera frames, and the 500-update fallback; never label these outcomes as measured relay state.
2. **P1 — Fault-path forwarding note:** extend the architecture record with the global relay-malfunction forwarding consequence. Reuse the generic relay test result; do not duplicate it.
3. **P1 — Lifecycle evidence table:** distinguish shutdown request, safety acceptance, ECU response, stock stream resumption, and fault clearance. Acceptance criterion: no source-level statement equates a constructed enable request with safe return to stock.
4. **P2 — Tick and lane-metadata cases:** synthetic tests for no reference, stale/wrong-length references, missed ticks, and lane revision mismatch. Assert only source-level classification and consistency.
5. **P3 — Startup-fault status case:** separately assert raw fault, reported fault, cruise availability, and timer state.
6. **P3 — DBC semantic note:** record mux tests as self-consistency checks, with no OEM protocol or target-validity claim.

All regression assertions must use synthetic inputs and must not emit real CAN or UDS traffic.

## 8. Source ledger and readiness statement

The findings above were verified by reading the pinned MVL sources at SHA `3fec9a418a659de31d7b1f494193161697a35071` and, where cited, Dom sources at SHA `1d810b741586034aa90a8490fb3d922e3b7a7198`. No vehicle access, diagnostics, source edits, or tests were performed in this continuation.

The four B1 gates remain **HOLD**: OEM command ownership, CMBS/AEB precedence, CAN-FD topology/arbitration, and owner transition. B3/B4 target qualification remains **HOLD**; B5/B6 remain **OUT_OF_SCOPE / NOT_EVALUATED**. The DEBUG Panda and AGNOS hash difference remain research-only owner-accepted deviations. **Production and operational readiness are not established.**

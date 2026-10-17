# C7 — Final MVL 66ad → Current 288-Commit Engineering Reconciliation

**Dated 17 October 2026 — read-only source audit, release HOLD.**

## Executive result

Historical MVL reference: `66ad9fac65f577940a9cbbe269104fb8177f2f76`. Current MVL source: `cb15c04e918b759688cb354b1bbc9b3c5a47a65c`. True common ancestor: `718db8c62eff6002c46770ec8e71ad18694189d7`. These are **divergent histories**, not a simple linear 139-commit fast-forward.

**Decision:** we identified and source-classified **all 288 records**. None meets the evidence requirements for an immediate *production* port to Honda Accord 11G C7. DEFER means potentially useful but requires explicit source-level applicability and testing. EXCLUDE means do not integrate this particular upstream commit directly; this includes divergent history, Nidec-only code and compiled firmware output. These are affirmative current decisions, not claims of verified vehicle performance.

| Git source range | Records | PORT approved | DEFER | EXCLUDE |
|---|---:|---:|---:|---:|
| Current MVL main (new since historical reference) | 139 | 0 | 94 | 45 |
| Historical-only divergent MVL main | 26 | 0 | 0 | 26 |
| Nested opendbc old→new | 116 | 0 | 63 | 53 |
| Nested Panda old→new | 7 | 0 | 0 | 7 |
| **Total** | **288** | **0** | **157** | **131** |

The source ledger was checked against actual Git objects, first-parent diff paths, changed code excerpts and source patch IDs; not merely commit titles. Both protected C6-12 and C7 remain clean. No code was imported, built for deployment, flashed or transmitted over CAN.

## Dependency provenance

| Revision stream | Historic pin | Current pinned revision | Verified relationship |
|---|---|---|---|
| MVL main | 66ad9fac65f5 | cb15c04e918b | 26 historical-side-only, 139 current-side-only |
| opendbc_repo | 8901198e59d5 | cf46117420f2 | 116 newer commits, none left-only |
| Panda | ea5a83a956d6 | 74a0adced421 | seven newer commits, none left-only |

The opendbc pin is a **Git submodule source dependency**; it is not a separate set of changes in the main MVL commit sequence. Panda similarly consists of nested commits affecting **a net three-file packed health ABI update**: board/health.h, board/main_comms.h, and python/__init__.py. Merge/revert/re-sync events in those seven commits must not be counted as seven distinct new firmware features.

## Repeated patch detection

Stable Git patch-ID reconciliation found 28 groups of equivalent patches among 56 commit records. **21 of those groups pair current and historical MVL commits**, showing cherry-pick/repeated source changes under different SHAs. There was 1 empty change record. Patch-ID equivalence is not proof that a change survived unchanged at the final tree head.

## Critical Accord 11G source facts

The MVL final opendbc interface explicitly identifies HONDA_ACCORD_11G and uses HondaFlags.BOSCH_CANFD. Therefore, blanket exclusion of changes titled for other Honda vehicles is unreliable when generic Bosch code is touched. However, the current MVL controller uses gasalpha, brake_pid, last_applied_brake and a different targetaccel/gas-force control sequence.

Protected C6-12 and the Dom-refreshed C7 retain **update_accord_bosch_braking**, mvl_accord_mode fingerprint gating and **mvl_radar_owned = mvl_accord_mode and canfd_relay_open and not stock_acc_alive**. These are material differences, so MVL Bosch braking cannot be safely cherry-picked onto C7 without same-input 50 Hz CAN/stop/jerk/lead/radar-ownership tests.

### High-value DEFER investigations (not ports)

| Engineering focus | Source commit(s) actually involved | Recommendation / evidence required |
|---|---|---|
| Bosch low-speed brake PID and stopping ramp | [`314b3f16e1`](https://github.com/mvl-boston/opendbc/commit/314b3f16e14093db50648fc0dd2415de96babb19), [`83bf1f7295`](https://github.com/mvl-boston/opendbc/commit/83bf1f7295876c71b02baca839a37ff02e2f3c4f), [`7269d573e8`](https://github.com/mvl-boston/opendbc/commit/7269d573e86e76dbf49e77cc5f971cdfa66751d4), [`09b693c075`](https://github.com/mvl-boston/opendbc/commit/09b693c075336a93ec101c1bafecef6a862bfc17), [`ff6a1aa225`](https://github.com/mvl-boston/opendbc/commit/ff6a1aa2253efd47563f6213be9407b49fffeee5) | DEFER; test actual Accord command bytes and gas/brake non-overlap, standstill release/hold, jerk and actuator feedback |
| GasAlpha and learning | [`794b346b9d`](https://github.com/mvl-boston/opendbc/commit/794b346b9d7af65b09a658711788c28ef6c32876), [`50285f66ee`](https://github.com/mvl-boston/opendbc/commit/50285f66ee479f0b25c3d248e4103d9799767617), [`657358074e`](https://github.com/mvl-boston/opendbc/commit/657358074e3934cec954e8a448d11d23f808abde) | DEFER; check 11G parameter names, learning persistence, grade/creep, numerics and bounds; never import constants from a different law |
| Steering-status and lane/path gains | [`d2db7e8d41`](https://github.com/mvl-boston/opendbc/commit/d2db7e8d4100a4627bc8cd4cdfbb18691b0225b7), [`170dbffb08`](https://github.com/mvl-boston/opendbc/commit/170dbffb08a075b20848a35cdc81fd4ed5d38b57), [`49e0bfd21a`](https://github.com/mvl-boston/opendbc/commit/49e0bfd21a844d4e8ed54007eafad0906e1ece99), [`98591cbbaf`](https://github.com/mvl-boston/opendbc/commit/98591cbbafa9bbd261c24b395a772103a793559e) | DEFER; actual EPS torque/status and CAN checksum byte parity, confidence and low-speed stabilizer replay |
| Honda safety | [`866bab83d3`](https://github.com/mvl-boston/opendbc/commit/866bab83d3004ae17fcd7207fd03950f42480c34), [`ef5ebd5ef1`](https://github.com/mvl-boston/opendbc/commit/ef5ebd5ef1f64940a9344caea1a53e6faf51d29d) | DEFER; safetyParam and RX/TX whitelist including noOutput, signed Panda/firmware compatibility |
| Confidence-gated lane centering | [`401bbc3cfe`](https://github.com/mvl-boston/openpilot/commit/401bbc3cfe8e7ef3e51460830fa927f2c895c511) | DEFER; actual controlsd/lane_centering model confidence and driver override vs C6-12 |
| Honda MADS all-speed | [`465f734f34`](https://github.com/mvl-boston/openpilot/commit/465f734f3408a0418321f8c74711556c4ca3e6e6) | DEFER; engagement state transition and lateral/longitudinal safety policy |
| New Honda Params lateral key definitions | [`cb15c04e91`](https://github.com/mvl-boston/openpilot/commit/cb15c04e918b759688cb354b1bbc9b3c5a47a65c) | DEFER; 21 FLOAT keys registered but no consumer/valid range in this new commit, not real tuning |
| Nidec/interceptor or RLX/Integra-only changes | [`d61a8a1c65`](https://github.com/mvl-boston/opendbc/commit/d61a8a1c65b937c9c0701d1091a8b60b8bcc7222), [`193f909b91`](https://github.com/mvl-boston/opendbc/commit/193f909b91ee22db84996429b0e192cc2ad07794), [`2f6d001e02`](https://github.com/mvl-boston/opendbc/commit/2f6d001e0290a04ed888e61cffa7aa2c7b8cf05a) | EXCLUDE direct port for known Bosch CANFD 11G absent proved shared applicability |

## Corrections to previous feature-to-commit attributions

### 1. HD-04 CANFD radar handover cited 8ad8ada
e9c19408 (pre-audit opendbc history) introduces relevant radar/disable_ecc and controller code; 8ad8ada only updates Honda UI settings and does not implement handover

**Actual reference SHA(s):** `e9c19408`, `8ad8ada771`. **Disposition:** DEFER / CRITICAL.
**Required tests:** Require C6-12 vs MVL final CANFD radar ownership/relay state parity, matched Panda safety, no competing transmitters

### 2. HD-08 model/settings references 401bbc,465f,9621031 as model selector
401bbc is confidence-gated lane centering in controlsd; 465f is Honda all-speed MADS in sunnypilot/mads; 9621031 is Params key registration; none is model selector/cache implementation

**Actual reference SHA(s):** `401bbc3cfe`, `465f734f34`, `9621031a00`. **Disposition:** DEFER / HIGH.
**Required tests:** Handle lane centering, MADS and persistent key schema in separate feature gates; do not import a model platform from these commits

### 3. HD-03 ACC_HUD generic scope cites 215186dc as general HUD
215186dc only imports CAR and handles Acura Integra COMPUTER_BRAKE_ASSIST in hondacan.py

**Actual reference SHA(s):** `215186dc74`. **Disposition:** EXCLUDE / LOW.
**Required tests:** Do not attribute this Integra code to Accord11G HUD or Bosch ACC_CONTROL behavior

### 4. Honda registry new 21 keys current cb15c04e
Current branch includes an additional post-Oct14 params_keys.h-only commit; no control readers implemented in that commit

**Actual reference SHA(s):** `cb15c04e91`. **Disposition:** DEFER / LOW.
**Required tests:** Do not adopt gain/shape/wire keys as active steering tune absent consumer, validation limits and EPS fingerprint

### 5. Panda seven commit records imply seven independent firmware improvements
Seven commits traverse merge/sync and reverts of largely the same board health ABI change; the final net delta comprises three paths: board/health.h, board/main_comms.h, python/__init__.py

**Actual reference SHA(s):** `ea5a83a956`, `74a0adced4`. **Disposition:** DEFER / CRITICAL.
**Required tests:** Review final net packed ABI, not naive additive per-commit features; no firmware cherry-pick

For the radar case specifically, the actual pre-range opendbc implementation is **e9c19408**; the previously cited **8ad8ada771** changed Honda UI settings, not canfd_relay_open or stock_acc_alive controller handover. The prior lane centering 401bbc3, MADS 465f734 and Params keys 9621031 are three distinct features, not a model selector. The 215186dc change is Acura Integra brake assist, not generic Accord HUD.

## Clear actions before C7 can take any MVL change

1. Extract proposed features into **separate offline candidate patches** after identifying a final-source consumer and precise Honda11G dispatch; no batch upstream imports.
2. Use source-consistent F8 ARM64/Cereal/Params/Acados builds and same-input Honda logged CAR/Panda safety values. Old or unrelated prebuilt objects are not valid qualifications.
3. Test individual Bosch braking and radar handover changes with the frozen C6-12 control law, startup handoff, lead-loss, low-speed stop, gas/brake overlap and body CAN byte parity.
4. Qualify actual Panda flashed firmware provenance, health ABI, tx/rx rules, driver override and noOutput before any physical testing. Distinguish this MVL health ABI delta from newer Dom SPI/CAN sequence changes.
5. Retain the independent **39 historical G02 patch dispositions**, 72 AOL skipped tests, owner signoff and physical rollback as separate OPEN gates. This static commit audit does not close them.

## Audit boundary

All 288 source commits have a per-SHA PORT/DEFER/EXCLUDE decision, changed paths, code excerpts, exact patch hash and required acceptance criterion in the accompanying ledger. This is **complete source-history reconciliation**, not 288 build/test passes or actual driving-safety certification. The decision to defer may be revised only through focused evidence. No immediate ports, no C6-12/C7 edits, no device use.

**RELEASE: HOLD / NO-GO.**

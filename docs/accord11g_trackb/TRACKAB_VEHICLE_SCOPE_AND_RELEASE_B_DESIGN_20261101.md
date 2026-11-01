# Accord 11G: unified vehicle scope, RX/TX separation and Release B source design (2026-11-01)

## 1. One target configuration

| Identifier | Meaning | Source of truth in the candidate |
| --- | --- | --- |
| `HONDA_ACCORD_11G` | platform: 2023–26 Accord / Accord Hybrid (2025 US Hybrid is the owner's car) | `values.py:218-224` (`HondaBoschCANFDPlatformConfig`, mass 3477 lb, wheelbase 2.83, steerRatio 16.7, c2f 0.39) |
| Bosch-C | control-system / harness architecture (camera-side LKAS, OEM radar ACC, relay on camera bus) | `values.py` `HondaFlags.BOSCH | BOSCH_CANFD`; `fingerprints.py` 4 camera / 1 radar FW |
| Honda CAN-FD | network; `honda_common_canfd_generated` DBC, powertrain on bus 0 | `values.py:176`; `honda.h` `HONDA_PARAM_BOSCH_CANFD = 16` |
| Safety word | `hondaBosch` 80 (`BOSCH_CANFD_MVL` 64 + `BOSCH_CANFD` 16), 81 with `ALT_BRAKE` | `interface.py:233-237`; `test_accord11g_trackb_no_long_authority.py` |
| Longitudinal owner | OEM radar / PCM (`pcmCruise=True`, `openpilotLongitudinalControl=False`, `alphaLongitudinalAvailable=False`) | `interface.py:56-58` |
| Lateral | PID (kf 3.5e-5, kp 0.115, ki 0.052, delay 0.3 s), STEER_MAX 12789 linear, 100 Hz STEERING_CONTROL | `interface.py:124-132`, `parameter_profiles.py:7` |
| Camera button takeover | `AccordMvlStock` (qualified only for this exact CP) | `accord_mvl_stock.py` |
| Always-on lateral | Dom AOL (`stock_aol.py`, `honda_stock_aol.h` words 80/81 with experience 32) | Dom tests |

Release A and Release B share this single configuration. There is no second Bosch-C fingerprint, flag set, service
owner or Panda policy. Other platforms (MDX/Passport/Pilot share `STEER_MAX=12789` in MVL; Civic/CR-V/Nidec/radarless)
are reference only; nothing is inherited from them. Not established for the owner's car: the FW versions actually
present, the live bus map and ECU ownership.

## 2. RX / simulated proposal / TX-permitted / TX-rejected (words 80/81, RELEASE and the shipped DEBUG build)

| Class | Frames (bus) | Evidence |
| --- | --- | --- |
| RX (Dom parses) | Honda CAN-FD DBC messages in `honda_common_canfd_generated` incl. `ACC_CONTROL` (stockAeb), `STEERING_CONTROL` from camera, `SCM_BUTTONS`, `LKAS_HUD`, brake/gas/speed | `carstate.py`, Panda RX checks |
| RX reference only (MVL claims, not in Dom DBC) | `RADAR_REFERENCE` 0x3A1, tick references 0x710/0x730/0x750, `RADAR_HUD_CANFD` 0x310 | gap matrix G05/G13; semantics fork-inferred |
| Simulated proposal (never transmitted) | `SimulationRecord(mode, acceleration_request)` from `plan_controller_sim.py`, wrapped by `release_b_gate.py` | `test_architectural_isolation.py` (no runtime import) |
| TX permitted | `0xE4` STEERING_CONTROL b0 (relay-checked), `0x296` SCM_BUTTONS b0 and b2, `0x33D` LKAS_HUD b0 (relay-checked) — only with controls allowed | `test_accord11g_debug_release_parity.py::test_stock_word_tx_profile_is_the_dom_mvl_stock_table` |
| TX rejected | `0x1DF` ACC_CONTROL, `0x1EF`, `0x1FA`, `0x30C`, `0x39F`, UDS `0x18DAB0F1` (both tester-present forms), radar emulation `0x310`, `0x6CD5558/9`, `0xF31AA52/C`, `0x1A45AA4E` on every bus; every non-stock word and experience | `test_accord11g_trackb_release_*`, `test_accord11g_trackb_mvl3fec9a_canfd.py`, parity test |
| Forwarding | camera→PT withholds only relay-checked `0xE4`/`0x33D`; PT→camera forwards everything incl. radar UDS replies | `test_release_stock_words_forward_*` |
| Car-side UDS | none: `CarInterface.init/deinit` never reach `disable_ecu` for 11G | `test_accord11g_no_radar_uds.py` |

## 3. B0 deterministic fail-safe contract (simulation)

| Condition | Result (`PlanControllerSimulation`) |
| --- | --- |
| malformed plan/observation/policy, non-finite numbers, bad ids | withdraw, retire current token |
| duplicate/out-of-order plan or observation, decision clock reversal | withdraw |
| stale plan / stale observation | withdraw |
| invalid or contradictory observation | withdraw |
| stock ACC disengaged, driver brake/accelerator, cancel | withdraw, retire token |
| AEB/CMBS not clear, plan FCW | withdraw, retire token |
| brake/throttle not allowed by the Dom plan | withdraw |
| engagement token missing/retired/changed without recovery | withdraw |
| **process/service restart (new instance)** | withdraw until a current, valid disengaged state is observed; tokens seen before arming are retired (new this campaign) |
| reset | ordering cleared, token retired, new token required |
| Release B evidence register not fully PASS | proposal suppressed (gate), shadow kept for audit |
| firmware/AGNOS identity mismatch | gate requires `qualified_identity` bound to measured SHA-256 |

The only magnitude input is the Dom plan's `a_target`. The output has no physical meaning and no code path sends
it to `carcontroller`, the packer or the Panda.

## 4. B1–B4 status for this campaign

| Stage | Status | Reason |
| --- | --- | --- |
| B0 contracts | COMPLETE (simulation scope) | table above; cold-start gap closed |
| B1 protocol/ownership | HOLD | MVL source documents fork behaviour, not OEM authority; RX reference frames are inferred |
| B2 subordinate controller | COMPLETE (simulation only) | 468 Track B tests |
| B3 host Panda | COMPLETE (host) | RELEASE denials + DEBUG parity |
| B3 target Panda | FAIL as specified | flashed firmware is a DEBUG build (log-derived) |
| B4 source/runtime | see final verdicts | ARM64 build against pinned AGNOS sysroot; isolation scan |
| B5 bench / B6 vehicle | OUT_OF_SCOPE / NOT_EVALUATED | owner scope change; still blocking |

## 5. Source-only design for an operational Bosch-C longitudinal (not implemented, not authorized)

What would have to exist, in this order, before any custom longitudinal frame could be sent on this car:

1. B1 authenticated evidence: which ECU consumes `ACC_CONTROL`-class commands on the 2025 US Accord Hybrid, how
   CMBS/AEB keeps precedence, and an OEM-supported owner transition that does **not** disable the radar (MVL's UDS
   disable is rejected; its own comments record a `CRUISE_FAULT` latch when the replacement stream starts late).
2. A Panda table derived from B1 (not from MVL), RELEASE-built and signed, with its flashed identity measured.
3. A `carcontroller` consumer that takes only the gated proposal, re-checks every B0 condition at send time, and
   falls back to stock ACC on any withdrawal.
4. B5 and B6 with objective acceptance criteria.

Until then Release B stays `NOT_ESTABLISHED`: the words "operational custom longitudinal", "production-ready
braking/acceleration" and "vehicle-qualified" do not apply.

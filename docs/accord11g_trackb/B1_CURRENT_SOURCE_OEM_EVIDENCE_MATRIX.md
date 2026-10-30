# B1 current-source and OEM evidence matrix — STOP

## Scope pin and reading rule

This is a source-only research record for commit `b088da2780e3a168193bfc1ce62e5df811a69867` on branch `accord11g-dom7-trackb-b1-b4-discovery-20261030` (parent `5fa8b2ed8c4b397e1235a3acae0bb4030b35a804`). It does not use historical C6–12/C7 logs, replay fixtures, gate criteria, or previous safety baselines. It does not assert an installed artifact, a connected vehicle, a CAN capture, or a Panda result.

“Source statement” below means only what this checkout's code selects. It is not a reverse-engineered ECU/control protocol. “OEM statement” below is restricted to the linked 2025 US Accord Hybrid owner's-manual functions; it is not a bus or arbitration specification.

The current comma source status for Bosch-C/11G is **stock longitudinal**: `pcmCruise=True` and no selected openpilot longitudinal control. This is a source-policy fact, not an OEM qualification.

| Topic | Exact pin / source | What it establishes | What it does **not** establish |
| --- | --- | --- | --- |
| 11G platform selection | `opendbc_repo/opendbc/car/honda/values.py:175-183, 216-222` | `HONDA_ACCORD_11G` uses `HondaBoschCANFDPlatformConfig` and the generated CAN-FD DBC name. | That the generated/imported records are decoded or applicable to US 2025 Hybrid ECU traffic. |
| Current source-longitudinal choice | `opendbc_repo/opendbc/car/honda/interface.py:51-59` | Bosch CAN-FD forces `alphaLongitudinalAvailable=False`; therefore alpha request does not select openpilot longitudinal and `pcmCruise=True`. | OEM authorization, target hardware state, or factory ECU ownership. |
| Current stock-MVL word | `opendbc_repo/opendbc/car/honda/interface.py:219-221`; `opendbc_repo/opendbc/car/honda/accord_mvl_stock.py:6-13` | The current source's Accord 11G helper qualifies only its stock boundary: Honda Bosch word 80, or 81 with alternate brake, PCM cruise, and no openpilot longitudinal. | That “MVL” is a Honda-defined control protocol or that a community implementation is qualified. |
| Safety source selection | `opendbc_repo/opendbc/safety/modes/honda.h:424-449, 514-557` | In this source, 80/81 with experiences 0/32 takes `HONDA_MVL_STOCK_TX_MSGS`; generic Bosch-long interpretation is conditional on `ALLOW_DEBUG` and its table. | A flashed Panda RELEASE result or an 11G command format. **Generic Bosch IDs are not an 11G longitudinal protocol.** |
| Source parser AEB field | `opendbc_repo/opendbc/car/honda/carstate.py:212`; generated-record closure under `opendbc_repo/opendbc/dbc/generator/` | A repository representation derives `stockAeb` from generic `ACC_CONTROL`. | Correct 2025 Hybrid signal semantics, CMBS/AEB state ownership, freshness, or fault behavior. |
| Source RELEASE host boundary | `opendbc_repo/opendbc/safety/tests/libsafety/libsafety_py.py:11-35`; `test_accord11g_trackb_release_denials.py:11-38` | A local host library can be compiled with `release=True`, which omits `ALLOW_DEBUG`, and tested for denial. | Panda firmware hash, target architecture, flashing, wiring, forwarding, or vehicle behavior. |

## Official 2025 US Accord Hybrid manual functions

Honda's official [Adaptive Cruise Control manual section](https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-520366.html) describes the ACC function and states that it shares its radar sensor with CMBS. Honda's official [Collision Mitigation Braking System™ section](https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-519694.html) describes CMBS alerts and braking assistance for potential collisions. These are function-level OEM statements only. They support a shared-radar safety-ownership concern, not any conclusion about CAN frames, ECU arbitration, control authority, or replacement of ACC/CMBS/AEB.

Detailed service information may require a Honda Service Information System (SIS) subscription. No SIS access is claimed here.

## Status and missing authoritative evidence

The comma/open-source `accord_mvl_stock.py` naming and adjacent community source are experimental, non-authoritative, and **not qualified** as OEM evidence. No reverse-engineered implementation in this checkout is treated as a protocol specification.

Missing authoritative evidence includes, at minimum:

- US 2025 Accord Hybrid ECU inventory and the ownership/arbitration relationship among ACC, braking, CMBS, AEB, radar, camera, gateway, and EPS.
- Target-specific bus topology, CAN/CAN-FD framing, identifiers, payload meanings, timing, counters, integrity, freshness, fault, disable, and recovery rules.
- Authoritative meaning and precedence of CMBS/AEB, pedestrian, driver-brake, accelerator, cancel, ACC-main, and diagnostic states.
- Confirmation that the generic generated DBC/import closure matches this trim/year; no materialized target-specific authoritative DBC is present.
- Target Panda RELEASE binary identity and source-to-firmware provenance.

Required acceptance evidence before B1 can move: legally obtained authoritative OEM service material (SIS if required) and independently reviewed, non-actuating, target-specific evidence tying ECU owners, bus/frame semantics, safety state precedence, fault/recovery behavior, and the exact trim/year together. It must separately demonstrate that factory ACC and CMBS/AEB remain OEM-owned. No generic Bosch identifier, host test, source parser, or community MVL code can substitute.

## B1 conclusion

**B1 STOP.** The above is partial source-policy and manual-function evidence, not authoritative 2025 US Accord Hybrid control-protocol qualification. B2 is limited to the synthetic harness described separately; B3 remains host-source denial testing only.

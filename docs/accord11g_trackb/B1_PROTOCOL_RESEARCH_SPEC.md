# B1 Honda Bosch-C protocol research specification — source-only STOP

## Scope and evidence rule

This record is pinned to current commit `82e053f56c18a814f1a98ea10e7b2b4057ed7d76`. It is for the requested US 2025 Honda Accord 11th Gen Hybrid only as a research target; it does **not** validate a vehicle, trim, ECU, bus, firmware, harness, or Panda. No logs, replays, devices, diagnostics, vehicle communication, Params, telemetry, or physical observations were used. Consequently, there are no `PHYSICALLY_OBSERVED` findings in this package.

The historical commit `7b4db9a26010ba9899eef242d3ca49b33cbcca9c` and the supplied recovery directory are reference evidence only. They identify previous source hypotheses and unsafe authority paths; they are not protocol authority, qualification evidence, or a baseline for tests. Current-source facts take precedence where they differ.

## Reconciled current versus historical source result

| Subject | Current pinned source | Historical reference | Reconciliation / allowed conclusion |
| --- | --- | --- | --- |
| Platform/DBC selection | `values.py:175-180,218-224` selects `HondaBoschCANFDPlatformConfig` with `honda_common_canfd_generated`. | Historical `values.py:197-204` selected a materially expanded CAN-FD DBC. | Current source is generic DBC closure only; neither proves target applicability. |
| Longitudinal owner | `interface.py:51-58` makes CAN-FD alpha longitudinal unavailable and retains `pcmCruise=True`. | Historical `interface.py:59-64` selected openpilot longitudinal when alpha was requested. | Do not port historical behavior. Current source is stock-longitudinal policy, not OEM authority proof. |
| Safety/RELEASE posture | `safety/modes/honda.h:424-578` chooses stock CAN-FD/MVL tables for words 80/81; generic Bosch long is inside `ALLOW_DEBUG` at 514-520. | Historical safety code had CAN-FD MVL-long plus diagnostics (`honda.h:403-426`) under debug. | Old allowlists are forbidden candidates for negative research only; no current TX allowlist is added. |
| ECU strings | Current `fingerprints.py:1178-1187` lists radar and camera strings. | Same family of source strings. | Source inventory only, never installed-ECU confirmation. |
| AEB/CMBS | Current code has generic `stockAeb` parser logic (`carstate.py:212-217`) but no target proof. | Historical candidates included `CMBS_ENABLED_MAYBE`. | Names and parser conditions are hypotheses, not state/priority/ownership proof. |

## Source-verified inventory and dictionary

“Verified” in this section means exactly present in source, **not** verified on the target.

- ECU fingerprint candidates: current `fingerprints.py:1178-1187` contains only `fwdRadar` request address `0x18DAB0F1` with `8S302-30A-A040`, and `fwdCamera` request address `0x18DAB5F1` with `8S102-30A-A050`, `-A060`, `-A070`, and `-A080`. These 29-bit diagnostic request identifiers and strings are `SOURCE_DERIVED_HYPOTHESIS`; they neither identify installed ECUs nor authorize diagnostics.
- Current generic DBC closure: [CANFD_SOURCE_DICTIONARY.json](CANFD_SOURCE_DICTIONARY.json) deterministically records all 50 current imported DBC records and all 412 source-defined signals: identifier format, DLC, DBC producer label, candidate-bus limitation, named counter/checksum fields, scale/offset/bit layout, source reference, and missing rate/consumer status. It was generated using `python3 tools/trackb_research/extract_honda_canfd_dictionary.py --output docs/accord11g_trackb/CANFD_SOURCE_DICTIONARY.json`. The DBC import closure is `honda_common_canfd.dbc:1-7`; topology is explicitly not represented by DBC records. `hondacan.py:239-254` provides a source checksum implementation, not target integrity-algorithm validation.
- Current source bus mapping: `hondacan.py:5-45` labels legacy logical buses and maps CAN-FD through `pt=offset`, `radar=offset+1`, `camera=offset+2`. This is a software mapping, not a physical 2025 topology observation.
- Historical Accord-specific candidates: `honda_common_canfd.dbc:9-71` at the historical commit defines 10 candidates: `0x3A1`/8 `RADAR_REFERENCE`; `0x310`/8 `RADAR_HUD_CANFD`; extended `0x6CD5558`/8 `LANE_PATH`; extended `0x6CD5559`/8 `HUD_OBJECTS`; extended `0xF31AA52`/8 `RADAR_LEAD2`; extended `0xF31AA5C`/8 `RADAR_LEAD`; extended `0x1A45AA4E`/8 `BOSCH_SUPPLEMENTAL_CANFD`; `0x710`/32, `0x730`/6, and `0x750`/16 tick-reference records. Their listed layouts, 2-bit counter and low-nibble checksum fields are historical source hypotheses only. `CMBS_ENABLED_MAYBE`, `LEAD_DISTANCE_MAYBE`, and `TARGET_SPEED_MAYBE` explicitly remain unresolved labels. Historical `hondacan.py:335-350` adds a special extended-ID checksum adjustment; that is implementation behavior, not OEM algorithm evidence. Historical `carstate.py:278-328` contains timing/relay inferences, not measured timing facts.
- Generic Bosch versus Accord-specific: generic current imported messages such as `ACC_CONTROL` (`0x1DF`) are not Accord-11G claims. The historical 10-record list is Accord-specific only in historical source naming, still `SOURCE_DERIVED_HYPOTHESIS`. Neither set may be used as a target decoder, transmitter, owner/arbitration claim, or CAN-FD rate specification.

## Current-source protocol/authority boundary

Current `interface.py:51-58` warns radar disable affects AEB and explicitly leaves Bosch CAN-FD radar disable as TODO; it keeps stock cruise. Current `accord_mvl_stock.py:6-14` limits the stock helper to the narrowly shaped source policy (Honda Bosch, stock PCM cruise, no openpilot longitudinal, safety words 80/81). `safety/modes/honda.h:454-480` lists the current stock/CAN-FD source TX tables, and `safety.h:303-325` applies a whitelist/hook model. These are software-policy facts only. They do not identify physical producers, consumers, relay state, ECU ownership, arbitration, timing, firmware identity, or a target command protocol.

## Required B1 evidence before any advancement

Legally obtained authoritative service/electrical material and independently reviewed target-specific, non-actuating evidence must establish the exact trim/year ECU inventory; topology and CAN/CAN-FD framing; identifier/DLC/rate/counter/integrity definitions; ACC/CMBS/AEB/brake/powertrain/radar/camera priority; diagnostics/session recovery; faults; and evidence that OEM emergency functions remain OEM-owned. Until then **B1 is PARTIAL / STOP**, never qualified.

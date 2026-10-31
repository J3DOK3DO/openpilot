# B1 evidence matrix — source-only STOP

Each material finding has exactly one classification. `PHYSICALLY_OBSERVED` is intentionally absent: no new physical evidence exists.

| Finding | Classification | Exact evidence / boundary |
| --- | --- | --- |
| Current 11G platform chooses Bosch CAN-FD config and generic DBC | SOURCE_DERIVED_HYPOTHESIS | `values.py:175-180,218-224`; selection is not target traffic validation. |
| Current 11G source retains PCM cruise and does not select openpilot longitudinal | SOURCE_DERIVED_HYPOTHESIS | `interface.py:51-58`; code policy, not OEM ownership proof. |
| Current helper accepts only source stock words 80/81 conditions | SOURCE_DERIVED_HYPOTHESIS | `accord_mvl_stock.py:6-14`; words are source configuration, not Honda protocol. |
| Current safety source contains stock CAN-FD TX tables and debug-gated generic Bosch long | SOURCE_DERIVED_HYPOTHESIS | `safety/modes/honda.h:424-578`; host source is not target Panda RELEASE proof. |
| Current radar/camera fingerprint strings and request IDs exist in source | SOURCE_DERIVED_HYPOTHESIS | `fingerprints.py:1178-1187`; no installed ECU was queried. |
| The 50-message current DBC closure exists with source bit layouts | SOURCE_DERIVED_HYPOTHESIS | [CANFD_SOURCE_DICTIONARY.json](CANFD_SOURCE_DICTIONARY.json); generic DBC is not target-specific. |
| Honda owner manual says ACC uses a radar sensor shared with CMBS | OEM_CONFIRMED | Official ACC page: <https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-520366.html>; function statement only. |
| Honda owner manual describes CMBS alerts/braking assistance | OEM_CONFIRMED | Official CMBS page: <https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-519694.html>; function statement only. |
| Honda owner manual gives radar-sensor limitations/care guidance | OEM_CONFIRMED | Official radar page: <https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-393311.html>; no architecture inference. |
| Honda owner manual describes Honda Sensing functions/limitations | OEM_CONFIRMED | Official Honda Sensing page: <https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-519533.html>; no protocol inference. |
| Historical `RADAR_HUD_CANFD` and extended candidate layouts existed | SOURCE_DERIVED_HYPOTHESIS | Historical `7b4db9a:.../honda_common_canfd.dbc:9-71`; reference only. |
| Historical checksum and relay/tick timing logic represented target behavior | UNVERIFIED | Historical code is implementation evidence only; no target capture or OEM spec. |
| Current generic `stockAeb` parser represents CMBS/AEB state on target | UNVERIFIED | `carstate.py:212-217`; semantic/freshness/priority mapping absent. |
| Radar, camera, PCM, brake/VSA, relay, and ECU arbitration ownership | UNVERIFIED | No authoritative service architecture or physical evidence. |
| CAN-FD buses, IDs, payload semantics, rates, integrity, faults/recovery | UNVERIFIED | No target-specific authoritative or physical evidence. |
| Target Panda RELEASE identity/source-to-firmware provenance | UNVERIFIED | No target firmware/device evidence; historical ELF is DEBUG reference only. |

**B1 status: PARTIAL / STOP.** OEM function statements and source inventory do not qualify architecture or authority.

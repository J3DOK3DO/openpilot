# B1 OEM ACC/AEB/CMBS authority and unresolved-evidence report

The official function-level pages are: [ACC with Low Speed Follow](https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-520366.html), [CMBS](https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-519694.html), [radar sensor](https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-393311.html), and [Honda Sensing](https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-519533.html). They establish driver-facing functions only. They do **not** establish a bus, identifier, ECU owner, brake command, arbitration rule, radar-disable behavior, diagnostic service, fault response, or recovery process.

| Area | What is known here | What remains unresolved / required evidence |
| --- | --- | --- |
| ACC / radar / camera | OEM function pages describe ACC, CMBS and radar-function context. Current source retains stock cruise (`interface.py:51-58`). | Which ECU owns ACC, uses camera/radar inputs, transmits which frames, and arbitration with CMBS/AEB. |
| AEB / CMBS | Current generic parser names `stockAeb`; historical DBC labels include `CMBS_ENABLED_MAYBE`. | Exact activation, priority, persistence, driver notification, pedestrian logic, sensor degradation, and handback behavior. |
| Powertrain / brake / ABS / VSA | Current DBC source labels messages `PCM`, `VSA`, and brake-related fields. | Target ECU inventory, producer/consumer binding, brake/regen/ABS/VSA authority and precedence. |
| Relay / gateway | Current safety source has relay-malfunction mechanisms; historical code inferred relay state from frame absence. | Physical relay/gateway topology, electrical state, forwarding and failure behavior. Frame absence is not proof. |
| Diagnostics | Historical code described extended-session/communication-control traffic; current code permits only narrow source-policy forms. | OEM authorization, session state, security access, watchdogs, ACK/NRC, timeout, reset, restore, and safety consequences. No diagnostic traffic was sent. |
| Fault/recovery | B2 contains synthetic fail-closed tests only. | OEM requirements for stale data, ECU reset, sensor fault, brake fault, cancel/main/pedal override, and recovery arbitration. |
| Panda / firmware | Current host tests can compile a local RELEASE-mode library. | Target device identity, firmware provenance, hardware behavior, wiring and actual deny/forwarding behavior. |

The current source comment that radar disable affects AEB (`interface.py:51-56`) is a material safety warning, not architecture proof. No component in this pass changed radar, CMBS, AEB, diagnostics, firmware, safety policy, or runtime behavior. **B1 remains STOP pending OEM and independently reviewed target-specific evidence.**

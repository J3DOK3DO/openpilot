# B0 hazard and functional requirements

## Scope and authority

This branch adds only documentation, tests and a manually invoked diagnostic; it adds no CAN/UDS/USB/Panda/Params control path or manager service and changes no vehicle-control/safety sources. Existing Track A software can still perform lateral steering and ordinary Panda communications; this new audit does not stop or alter that behavior. `CarInterface.get_params` is inspected and tested as a source contract only.

| Item | Hazard / requirement | Current source anchor | Owner before / after | Evidence state | Independent reviewer |
| --- | --- | --- | --- | --- | --- |
| H-01 | An unintended longitudinal owner could command propulsion or braking. Track B shall not acquire longitudinal authority. | `opendbc_repo/opendbc/car/honda/interface.py` Bosch-CANFD branch | Factory ACC/PCM / factory ACC/PCM | Source-boundary test required; no target proof | Unassigned |
| H-02 | Disabling/interfering with radar could degrade AEB/CMBS. AEB/CMBS shall remain OEM-owned and untouched. | `interface.py` warning that radar disable disables AEB; no Track B radar change | OEM radar/CMBS / OEM radar/CMBS | OEM ownership unverified | Unassigned |
| H-03 | A stale, absent, or contradictory observation could be treated as valid. Unknown evidence shall fail closed for qualification. | Parked audit reports `UNKNOWN`, never PASS, until an externally copied published GitHub `--expected-head` matches local git HEAD; also for unavailable/incomplete git/proc, non-aarch64 host, or missing AGNOS version marker | No Track B owner / no Track B owner | Source-only | Unassigned |
| H-04 | Process observation could expose personal or vehicle data. Audit shall read numeric `/proc/*/comm` only and report booleans, never cmdline, CAN, routes, telemetry, VIN, or Params. | `scripts/accord11g_trackb_parked_audit.py` | N/A / N/A | Native synthetic test | Unassigned |
| H-05 | An audit could be misrepresented as driving validation. Outputs shall state audit completeness only and never readiness to drive. | audit `operational_claim` | N/A / N/A | Source-only | Unassigned |

## Functional requirements and transition rules

| ID | Requirement | Pass evidence | Current state | Independent reviewer |
| --- | --- | --- | --- | --- |
| FR-B0-01 | With either alpha flag and either release mode, 11G Bosch-C CarParams retain `pcmCruise=true`, `openpilotLongitudinalControl=false`, and `alphaLongitudinalAvailable=false`. | New native parameterized test | PASS (source regression only) | Unassigned |
| FR-B0-02 | The stock safety selection is Honda Bosch with word 80, or 81 only when the current alternate-brake detection is present. | New native parameterized test | PASS (source regression only) | Unassigned |
| FR-B0-03 | Missing/unsafe source is FAIL; absent/nonmatching external release pin, unavailable/incomplete git/proc, modified tracked files, non-aarch64 host, or missing AGNOS marker is UNKNOWN, never PASS. The published GitHub SHA must be copied externally, never computed locally as the trust source. | Synthetic audit tests | PASS (audit behavior only) | Unassigned |
| FR-B0-04 | Audit default operation writes no file; explicit output is mode 0600. | Synthetic audit tests | PASS (audit behavior only) | Unassigned |
| FR-B0-05 | Any later owner transition must have separate authoritative OEM, protocol, RELEASE, target, and independent-review evidence. | Future B1--B6 package | UNVERIFIED | Unassigned |

No timing value is invented here. Fault expiry is deliberately qualitative: a missing source is a failure, unavailable collection is unknown, and any future authority or fault-expiry behavior must be specified from authoritative target evidence before a timed requirement is accepted. Recovery is likewise limited to a fresh parked audit after the cause is corrected; it does not re-enable, reset, or command any vehicle component.

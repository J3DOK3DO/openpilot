# Track B B0--B4 qualification status

## Source and scope pin

This preparation is pinned to source commit `b088da2780e3a168193bfc1ce62e5df811a69867` on branch `accord11g-dom7-trackb-b1-b4-discovery-20261030`; its immediate parent is the prior Track A commit `5fa8b2ed8c4b397e1235a3acae0bb4030b35a804`. It evaluates only the current DOM-native source and the new tests introduced for this request. No C6--12, C7, historical logs, historical tests, or prior safety baselines are evidence.

The target named by the request is US 2025 Honda Accord 11th Gen Hybrid Bosch-C CAN FD. This is a source-preparation status, not a vehicle qualification or readiness claim.

| Gate | Requirement/evidence needed | Current source evidence | Status | Blocker / independent review |
| --- | --- | --- | --- | --- |
| B0 | Defined nonactuating scope, hazards, owners, and independently reviewable acceptance record | This document; `B0_HAZARD_AND_REQUIREMENTS.md`; read-only audit and native source-boundary test | UNVERIFIED | No parked target/device evidence; no ARM64/AGNOS target sysroot |
| B1 | Authoritative Bosch-C CAN FD ownership, bus/message, AEB/CMBS, and fault semantics evidence | `interface.py` makes CANFD `alphaLongitudinalAvailable` false; `carstate.py` exposes stock AEB only for the current data path | UNVERIFIED | Bosch CANFD is excluded from alpha longitudinal; no authoritative OEM radar/AEB ownership or protocol capture/evidence |
| B2 | Simulation-only planner acceptance against an authoritative, nonactuating contract | New B2 synthetic analytical harness checks only eligibility plus reason; it has no planner, command, or physical-handback assertion | UNVERIFIED | No authoritative input/output contract or fault/recovery oracle; B2 must remain simulation-only |
| B3 | RELEASE-native negative tests prove no unauthorized longitudinal path and preserve stock emergency authority | Source gates Bosch long under `ALLOW_DEBUG`; CarParams test asserts 80/81; host RELEASE tests enumerate generic Bosch-long bus-1 examples | UNVERIFIED | Host deny tests are not actual Panda firmware or vehicle safety proof. Target RELEASE identity, physical denial, and OEM AEB/CMBS compatibility remain unverified |
| B4 | Parked-only, source/host diagnostic run with a reviewable result and no actuation path | `scripts/accord11g_trackb_parked_audit.py` is stdlib-only/read-only; it requires an externally copied published GitHub commit SHA and procedure constrains use | UNVERIFIED | No actual parked-device result or published release pin; host audit cannot establish vehicle, Panda, OEM radar, AEB, or CMBS behavior |

Known source facts are not completion evidence. `opendbc_repo/opendbc/car/honda/interface.py` sets Bosch CANFD `alphaLongitudinalAvailable` false and derives `openpilotLongitudinalControl` from it. `opendbc_repo/opendbc/safety/modes/honda.h` places Bosch-long interpretation behind `ALLOW_DEBUG`; its CANFD handling is source policy, not target RELEASE evidence. The currently selected stock words for this 11G path are 80 and 81 in `accord_mvl_stock.py`.

Accordingly, B0--B4 cannot be claimed completed. B5/B6 cannot be skipped: their separate acceptance evidence, approval, and any authorized later-stage work remain required after these blocked gates are independently reviewed.

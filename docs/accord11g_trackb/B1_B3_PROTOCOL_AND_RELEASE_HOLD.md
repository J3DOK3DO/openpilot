# B1--B3 protocol and RELEASE hold

## What current source establishes

`opendbc_repo/opendbc/car/honda/values.py` identifies `HONDA_ACCORD_11G` as a Bosch CAN FD platform. In `interface.py`, Bosch CAN FD makes `alphaLongitudinalAvailable` false; `openpilotLongitudinalControl` therefore remains false even when alpha is requested. The current 11G stock qualification helper is `accord_mvl_stock.py`, where source words 80/81 represent the current stock boundary. The new `test_accord11g_trackb_no_long_authority.py` covers both alpha selections, both release selections, and both current brake-detection cases.

`opendbc_repo/opendbc/safety/modes/honda.h` is the current native Honda safety source used by the repository safety build; `opendbc_repo/opendbc/safety/safety.h` registers the Honda Bosch hooks. Its Bosch-long interpretation is guarded by `ALLOW_DEBUG`. This preparation neither changes that source nor asserts that an installed Panda RELEASE artifact has any new authorization. Exact tx identifiers, bypasses, custom gas/brake messages, and UDS are intentionally absent from this document and this implementation.

## B1 evidence gaps (hold)

The repository does not provide authoritative, target-specific evidence for the 2025 US Accord Hybrid Bosch-C CAN FD bus topology, OEM radar ownership, ACC/CMBS/AEB ownership, message semantics, counters/checksums, fault behavior, or recovery behavior. Current source parsing is not that evidence. B1 remains UNVERIFIED until separately authorized, parked, nonactuating, confidentiality-controlled evidence is independently reviewed.

## B2 simulation-only hold

No Track B planner, longitudinal model, simulator, oracle, or drive trace is implemented. A future B2 package must remain simulation-only and must define its input source, expected output, invalid/stale-data behavior, fault-expiry semantics, recovery criteria, and independent review. It may not treat source-only CarParams or a parked audit as a planner acceptance oracle.

## B3 RELEASE negative-test hold

A new host-native test, `opendbc_repo/opendbc/safety/tests/test_accord11g_trackb_release_denials.py`, compiles a RELEASE libsafety library without `ALLOW_DEBUG` and verifies explicit disallowed TX under Honda safety parameters 80/81 and alternative experiences 0/32 (4 tests passed). This is a SOURCE/host denial result, not a permission to transmit or a physical Panda firmware qualification. B3 still requires identified target RELEASE firmware and negative tests across selection, invalid/expired data, cancellation, recovery and configuration boundaries. The existing native source exposes `ALLOW_DEBUG` as a material distinction; no result in this package proves target Panda RELEASE behavior. Any future test must preserve OEM AEB/CMBS and factory ACC, must not change safety allowlists, and must not manufacture a pass from an unavailable target or build environment.

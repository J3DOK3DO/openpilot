# Track B B1 — Owner-accepted device deviations (2026-11-01)

Status: **OWNER-ACCEPTED RESEARCH DEVIATIONS**, not independent technical PASS and not approval to activate longitudinal control.

Target: US 2025 Honda Accord 11G Hybrid, Bosch-C/CAN-FD, AGNOS 19.8.1, published Track A/B engineering candidate `bc1eea1a7ab460cdf5fd9a367f57495c12fa2af7`.

## Owner authorization (explicit)

The owner authorizes continued **B1 source research, passive evidence review, non-actuating simulation, and independent software review** while accepting the following two differences from prior evidence goals.

| ID | Owner-accepted condition | Existing verified observations | Effect of acceptance | Remains unverified |
| --- | --- | --- | --- | --- |
| DEV-PANDA-DEBUG-001 | Installed Panda firmware is a **DEBUG** rather than RELEASE build | Read-only swaglog reports `DEV-6f2ca2c4-Pa5919516-DEBUG`, prefix `510ed0d6c7a8d322` matching expected; existing stock words 80/81 host DEBUG/RELEASE parity tests pass | Do not block B1 research or offline controller simulation merely due to DEBUG designation; record `OWNER_ACCEPTED_DEVIATION` separately | Complete flashed image, target execution and every enabled debug capability; acceptance is not safety equivalence or new CAN/TX authority |
| DEV-AGNOS-HASH-001 | Active AGNOS partition's raw hash differs from pinned image **provided installed AGNOS version is the same** | Read-only `/VERSION=19.8.1`; active `system_a` SHA-256 `f5bf56a979e1170e2c86ffc561db537eb808a272630d6074a0d60b61bf314935` vs pinned `98e15de0...`; 17/17 measured ABI-critical files identical; differences consistent with ext4 mount metadata | Do not block B1 research or offline software tests merely due to whole-partition hash mismatch when version and relevant compatibility checks match | Exact raw image identity, unmeasured files, future update/slot identity; same version alone does not establish binary equivalence |

## Boundaries

1. These approvals are **owner risk acceptance**, not technical evidence. Keep the original `B3-TARGET-PANDA-RELEASE-IDENTITY` and `B4-INSTALLED-DEVICE-IDENTITY` gate measurements visible in the authoritative evidence register; add an overlay rather than silently marking those gates PASS.
2. No Panda flashing, AGNOS flashing, slot/Params changes, diagnostics, CAN or UDS transmissions, firmware bypasses, new TX allowlists, or longitudinal actuator commands are authorized by these deviations.
3. The current installed device and Claude-published Track A engineering branch must remain untouched.
4. B1 command ownership, OEM CMBS/AEB precedence, CAN-FD physical topology, and owner transition remain `HOLD_UNVERIFIED` until independently corroborated authoritative target-specific evidence exists.
5. B5/B6 remain out of scope and operational Release B remains `NOT_ESTABLISHED`.
6. For every finding include evidence classification: `HONDA_OFFICIAL_FUNCTIONAL`, `SOURCE_DERIVED`, `THIRD_PARTY_HYPOTHESIS`, `TARGET_PASSIVE_OBSERVED`, `AUTHENTICATED_OEM_PROTOCOL`, or `UNVERIFIED`. The first four cannot automatically prove command authority.

## Sources

- `TRACKAB_DEVICE_AGNOS_PANDA_AUDIT_20261101.md`
- `TRACKAB_FINAL_VERDICTS_20261101.md`
- `TRACKAB_VEHICLE_SCOPE_AND_RELEASE_B_DESIGN_20261101.md`
- `RELEASE_B_EVIDENCE_REGISTER.json`
- `TRACKAB_OWNER_SCOPE_RECONCILIATION_20261101.md`
- Honda 2025 Accord Hybrid ACC manual: https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-520366.html
- Honda 2025 Accord Hybrid CMBS manual: https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-519694.html

Owner acceptance applies to the present **research continuation**, not to a future production safety certification.

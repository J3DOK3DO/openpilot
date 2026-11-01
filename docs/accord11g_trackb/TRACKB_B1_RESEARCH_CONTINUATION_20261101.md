# Track B B1 — Research continuation after Claude / Qwen handoff (2026-11-01)

**Classification:** NON-ACTUATING SOURCE/EVIDENCE RESEARCH; no OEM protocol authorization, no physical longitudinal authority.

## Identity and references

- Target: US 2025 Honda Accord Hybrid, 11th generation, Bosch-C/CAN-FD, `HONDA_ACCORD_11G`.
- Parent source: published `J3DOK3DO/openpilot` candidate `bc1eea1a7ab460cdf5fd9a367f57495c12fa2af7`. Preserve it, the known-good branch and the installed comma.
- Follow-on branch: `accord11g-dom7-trackb-b1-qwen-research-20261101` (research documentation; not an install target).
- Canonical Claude output: `TRACKAB_FINAL_VERDICTS_20261101.md`, `TRACKAB_VEHICLE_SCOPE_AND_RELEASE_B_DESIGN_20261101.md`, `RELEASE_B_EVIDENCE_REGISTER.json`, `B1_CURRENT_SOURCE_OEM_EVIDENCE_MATRIX.md`, `B1_PROTOCOL_RESEARCH_SPEC.md`, `TRACKB_MVL_3FEC9A_COMMA_DOM_SOURCE_AUDIT_20261101.md`.
- Owner deviations: [TRACKB_B1_OWNER_ACCEPTED_DEVIATIONS_20261101.md](TRACKB_B1_OWNER_ACCEPTED_DEVIATIONS_20261101.md). DEBUG Panda and AGNOS raw-hash mismatch accepted for non-actuating engineering, not evidence of safe actuation.

## B1 four required authority determinations

| B1 gate | Established facts | Missing proof / criterion | Current disposition |
| --- | --- | --- | --- |
| OEM command owner | Current source selects stock PCM/ACC (`pcmCruise=True`, `openpilotLongitudinalControl=False`); Honda's owner manual describes ACC. | Authenticated, target-specific ECU producer/consumer identities; command-status frames and integrity; gas/brake authority, limits, faults and arbitration. Generic Bosch/MVL frames cannot substitute. | **HOLD — NO AUTHENTICATED OEM PROTOCOL** |
| CMBS/AEB precedence | Honda 2025 Accord Hybrid manual says ACC and CMBS share the radar sensor; CMBS can warn and apply braking. Current source avoids radar disable. | Verified command-priority and conflict arbitration, fail-safe transitions and brake override for all relevant modes while radar/CMBS stays active. | **HOLD — FUNCTIONAL OEM TEXT ONLY** |
| CAN-FD topology/arbitration | `hondacan.py` defines logical bus offsets; source-derived DBC closure has 50 records/412 signals; source tests define current stock words 80/81. | Exact target harness routing, ECU addresses, bus frame ownership/rates, checksum/counters and physical forwarding; safe recovery on bus loss. | **HOLD — SOURCE ONLY** |
| Owner transition | Current branch keeps custom long disabled and does not disable radar. Community source warns takeover stream latency may cause `CRUISE_FAULT`. | OEM-approved arbitration/transition with CMBS preserved, deterministic return to stock ACC, and independent physical evidence. | **HOLD — NO SAFE TRANSITION PROVEN** |

## The 17 retained future operational patch IDs

| IDs | Research-only action permitted now | Engineering stage still blocked |
| --- | --- | --- |
| BC-009, BC-010, BC-011, BC-012 | Map stock owner and relay hypothesis, timing/DBC ambiguity, and parser negative cases from source; tag all inferred IDs unverified. | Any real owner change or radar/relay manipulation. |
| BC-020, BC-021, BC-022, BC-023, BC-024 | Inventory historical generated frames and checksum claims as hypotheses; document source provenance and missing OEM validation. | Radar emulation, injected CAN-FD frames, TX whitelist expansion. |
| DRV-001, DRV-003, DRV-005, DRV-006, DRV-007, DRV-008, DRV-009, DRV-010 | Define non-actuating controller simulation requirements for brake/gas exclusion, saturation, rate limits, fault withdrawal and synthetic boundaries. | Implementation or activation of physical gas/brake commands before B1 is proven. |

Existing B0 fail-closed and B2 simulation can remain in place; no change to stock ACC, CMBS/AEB, Panda safety policy or Track A is justified by this phase.

## Independent evidence chain needed for each B1 row

1. Legally obtained authoritative Honda service/electrical material or OEM-authorized protocol specification matching exact year, region, hybrid variant, ECU and firmware. A public owner manual is **functional-only** evidence.
2. Independently corroborated passive target observations, with source hash, ECU inventory, non-identifying hardware/firmware references, capture provenance, and frame integrity/rates. No diagnostic transmission or active excitation.
3. An explicit proof of OEM radar/CMBS/AEB priority and safe behavior on loss of command owner/heartbeat, stale plans, conflicting pedal requests and service restart.
4. Independent reviewer challenge of assumptions and source-to-evidence traceability. Unidentified frame meaning, unknown bus topology or inferred command semantics remain HOLD.
5. Only after these facts are qualified can any future design for operational longitudinal control be considered. B5/B6 stay outside this effort.

## Public Honda facts (functional evidence, not protocol authentication)

- 2025 Accord Hybrid ACC with Low Speed Follow: https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-520366.html
- 2025 Accord Hybrid CMBS: https://techinfo.honda.com/rjanisis/pubs/OM/AH/A30B2525IOM/enu/details/131245047-519694.html
- 2025 Accord Hybrid front camera supports both ACC and CMBS: https://techinfo.honda.com/rjanisis/pubs/om/ah/a30b2525iom/enu/details/131245047-320307.html
- Comma's Bosch-C vehicle support entry describes the 2023–2026 Accord Hybrid with stock ACC, not authenticated custom longitudinal takeover: https://www.comma.ai/vehicles

## Handoff deliverables to complete

- Source claim ledger with exact paths/line references and source SHA.
- Four-row B1 evidence matrix with provenance, missing facts, accepted evidence class and named independent reviewer.
- Independent Qwen source-analysis report (if inference runner succeeds), then Codex challenge of any new technical claims.
- Owner deviation overlay kept separate from authoritative evidence-gate PASS/FAIL/HOLD statuses.
- No source controller changes or production publication until B1 authority criteria are met.

**Current B1 acceptance:** 0/4 authenticated protocol gates passed. This is not 0% research performed: source reconnaissance and simulations exist, but operational authority is unverified.

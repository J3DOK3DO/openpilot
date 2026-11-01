# Accord 11G: owner-approved 34-ID conditional exclusion — reconciliation (2026-11-01)

Authority: owner scope files `scope/OWNER_SCOPE_MANIFEST_20261101.json` (overlay SHA-256 `c457983c…`, verified),
`TRACKAB_84_OWNER_APPROVED_SCOPE_OVERLAY_20261101.tsv`, `OWNER_APPROVED_34_EXCLUSIONS_DEPENDENCY_NOTES_20261101.md`.
They decide scope; the dependency findings below are this campaign's own source review, not taken from them.

Files (this directory):

| File | Rows |
| --- | --- |
| `TRACKAB_84_ID_MASTER_OWNER_SCOPE_20261101.tsv` | 84 (all IDs kept; historical disposition preserved as a separate field) |
| `TRACKAB_34_ID_CONDITIONAL_EXCLUSION_REGISTER_20261101.tsv` | 34 |
| `TRACKAB_50_ID_RETAINED_DEVELOPMENT_REGISTER_20261101.tsv` | 50 |
| `TRACKAB_34_ID_DEPENDENCY_EXCEPTION_MATRIX_20261101.tsv` | 34 (one row per excluded ID) |

## Before / after

| | Before | After |
| --- | --- | --- |
| Inventory | 84 | 84 (unchanged) |
| Current development scope | 84 | **50** |
| Owner-excluded (conditional) | 0 | 34 (group A 6, B 14, C 14) |
| Counted as newly implemented because of the exclusion | — | 0 |

## Dependency assessment (source level)

Method per excluded ID: the ledger target and intent; the retained IDs sharing files (owner overlay); symbol search
and callers in the candidate tree; shared state/schemas; Honda CAN-FD parsing and controller paths; Panda TX and
forwarding; Track A/B interfaces; and the tests that pin the native behaviour.

| Classification | Count | IDs |
| --- | --- | --- |
| `EXCLUDED_NATIVE_DOM_FUNCTIONALITY_PRESERVED` | 14 | ND-001, ND-005, ND-007, ND-008, ND-014, ND-016, BC-018, ND-003, ND-004, ND-011, DRV-021, DRV-022, DRV-023, DRV-027 |
| `EXCLUDED_NO_NEW_IMPLEMENTATION` | 10 | BC-015, BC-016, BC-017, BC-019, BC-033, DRV-032, DRV-033, ND-002, ND-009, ND-017 |
| `EXCLUDED_SUPERSEDED_BY_DOM` | 10 | DRV-018, DRV-019, DRV-020, DRV-024, DRV-025, DRV-026, DRV-028, DRV-029, DRV-030, DRV-031 |
| `CONDITIONAL_DEPENDENCY_EXCEPTION` | 0 | — |
| `UNRESOLVED_DEPENDENCY_REQUIRES_EVIDENCE` | 0 | — |

Points the owner asked to check:

- **BC-018 vs BC-025/BC-026:** the retained items and Honda stock AOL depend on the native stock-ownership qualifier
  `accord_mvl_stock.qualified` (pcmCruise, no openpilot long, hondaBosch 80/81, flag set), not on MVL's radar-liveness
  gating. The qualifier is protected. This campaign corrected it to admit `HYBRID` (AOL investigation); that is a
  fix to retained functionality, not an implementation of BC-018.
- **ND-003/ND-004 vs parser:** checksum/counter failures still block updates, timeouts and `can_valid` are unchanged.
  Only retained BC-012 (silent-transition parsing, no code, needs radar silence which is rejected) would latently
  need a prior-valid latch if it were ever implemented. Recorded as latent, not a current exception.
- **DRV-020–023:** `LeadTakeoff.step`, `Lead.identity`, `lead_behavior.inside_gap_cap`, `LeadApproach._target` are
  native and protected; only historical extensions are excluded. `lead_behavior.py` has no lift state to remove.
- **DRV-027:** `lead_approach.project` fails closed on SubMaster valid/alive, carState `canValid`/`canTimeout` and
  pedals; protected (B0 relies on Dom plan validity).
- **DRV-028–031:** no Accord-specific planner code exists; ND-006/ND-010 observation and snapshot fields are native
  (`test_plan_snapshot_schema_contract.py`). For the 11G the PCM owns set speed (`test_accord11g_installed_dom_cruise.py`).
- **ND-007/ND-008:** the AOL diagnosis used the existing `aolAxisState`, `aolSafetyWire`, Card intent and carOutput;
  no redundant schema fields were added.
- **ND-016:** `logmessaged.py` applies one 2 MiB pre-publish guard to both `logMessage` and `errorLogMessage`; it is
  shared with retained ND-015 and protected.

No existing function was removed.

## Retained 50 by state

| State | Count |
| --- | --- |
| Existing native implementation | 13 |
| New implementation, implemented but unqualified (BC-025, BC-026, Track A) | 2 |
| Implemented (native) but unqualified | 11 |
| Pending evidence (OEM/physical) | 7 |
| Operational qualification requirement (Track B, not in production by design) | 17 |

## Requirements that genuinely block software completion

None for Track A source/host/ARM64 software. Everything still open is evidence or physical: B1 OEM ownership
(BC-002, BC-007, BC-028, BC-032 and the 17 Track B operational items), Release-signed Panda firmware (B3-target),
an independently reviewed device identity (B4), and B5/B6 (out of scope).

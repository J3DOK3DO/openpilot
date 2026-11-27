# C20 offline research candidate and active-control gate

## Reproduce without device access

From the C20 worktree root, use `PYTHONDONTWRITEBYTECODE=1` and run:

```sh
python3 -m unittest discover -s tools/c20_accord11g_long_shadow/tests -v
python3 -m tools.c20_accord11g_long_shadow.scenarios
python3 -m tools.c20_accord11g_long_shadow.native_preflight
python3 -m tools.c20_accord11g_long_shadow.release_gate
python3 tools/ci/check_prebuilt_receipt.py --revision a32dcc0a6e62a4e2a15d9ac4425424e598313c98
```

The native preflight must say `executed_solver: false` until an actual compatible acados solver is run in an isolated offline environment. The current AArch64 solver cannot run on the x86_64 host; CasADi is absent. An identical-cycle native fixture must include carState, radarState, modelV2 trajectories and timestamps, controlsState, vehicleParameters, CP, cruise target, personality, all planner state and reset boundaries. The simplified JSON trace cannot substitute for those inputs. An ARM64 build or device hardware trial was not attempted.

The queued field-level contract is [native_cycle_schema.json](../fixtures/native_cycle_schema.json). It is deliberately incomplete data, never a solver input claim. The baseline C19 prebuilt receipt check passed for `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`; that receipt does not cover the new research commit.

For route inventory, pass explicit bounded evidence roots to `python3 -m tools.c20_accord11g_long_shadow.inventory ROOT --max-files 100 --max-dirs 100`. Both limits are independent, count examined entries/directories, and cap traversal even for empty trees. Review `truncated` and `truncation_reason`; a truncated inventory is incomplete. Hashes and metadata field names derive from one stable file snapshot and are for local custody only. A route is admitted for recorded behavioral replay only with exact vehicle/firmware/software/DBC binding and an externally authenticated reference digest. A caller-created `authenticated: true` record is not independent proof. Route extraction from compressed logs and exact-cycle native fixture generation remain pending.

## Release checklist

| Gate | Required state | Current state |
| --- | --- | --- |
| R1 evidence | Verified exact-car raw route, metadata, firmware, software and DBC | BLOCKED: four older raw segments, zero verified exact-car routes |
| R2 C19 MPC | Native solver on identical-cycle synthetic and then admitted recorded inputs | BLOCKED: architecture and dependency |
| R3 comparisons | Deterministic bounded adversarial synthetic suite, then recorded validation | PARTIAL: synthetic behavioral references only |
| R4 safety | Owner risk record and independently qualified safety architecture | PARTIAL: risk recorded, active safety case NO-GO |
| R5 shadow | Offline inert research package and source audit | PARTIAL: offline package only, no product runtime integration |
| R6 build | Reproducible ARM64 build and artifact receipt | PENDING: baseline C19 receipt verified; C20 build not run |
| R7 candidate | Independent reproduction, rollback demonstration and release signoff | PENDING; research candidate only |
| R8 independent qualification | Closed-course, HIL, legal/insurance and release review | NOT STARTED |
| A1–A5 actuation | Radar/camera ownership; CAN2 startup; Panda/brake; override/faults; regulatory/insurance | ALL NOT VERIFIED |

`release_gate.py` audits research source imports, forbidden send-style attributes and changed-file scope, then emits a fail-closed matrix. It is a research integration guard, not an automotive safety verifier. Its current `NO_GO` for active Alpha Long and road deployment cannot be overridden by this package. The branch and exact C20 commit identity must be recorded after commit. Rollback is **NOT VERIFIED**; the C19 baseline commit alone does not demonstrate device rollback.

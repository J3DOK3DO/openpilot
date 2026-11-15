# C6 Phase 5 nonactuating acceptance draft

2026-11-15 Asia/Dubai. **Documentation only; no Phase 5 execution or approval.** The Comma and Panda remained disconnected. This campaign authorizes no ignition/engine, D gear, LKAS=9 arming, CAN TX, OBD request, firmware flash, steering actuation or road test. Claude Option A is not approved here. Physical safety gates stay **NO-GO** after offline PASS.

## Entry checklist for a later, separately approved campaign

| Gate | Required evidence before any install or vehicle interaction | Current state |
|---|---|---|
| Source and independent safety review | Independent reviewer inspects exact final commit, full Honda native diff, C5 red/green test, pandad USB/heartbeat/session path, host CarState and stop logic; findings disposed in writing | **PENDING**. Codex implementer review is not independent approval. Preexisting partial Qwen C4B text is neither final-candidate nor completed review. |
| Native build and identity | Authentic target-native Panda firmware and Qualcomm/product builds from exact reviewed commit, reproducible hashes and packaging receipt; verify installed firmware before any control assessment | **MISSING**. C8.1 GUI-only no-rebuild precedent cannot apply. |
| Independent standstill and torque safety | Independent native/physical evidence for zero steering authority at standstill and torque/rate bounds, plus EPS response and abort behavior | **MISSING**. Current host low-speed checks share CarState ([stock_intent.py:9](../../openpilot/starpilot/car/honda/stock_intent.py#L9), [selfdrived.py:1861](../../openpilot/selfdrive/selfdrived/selfdrived.py#L1861)); Honda native TX code checks permission for nonzero steering but does not establish a separate numerical torque bound ([honda.h:310](../../opendbc_repo/opendbc/safety/modes/honda.h#L310)). No new speed-CAN policy is inferred. |
| Fault root cause and passive cold/warm startup | Exact Panda/host build identity, harness/OBD topology, CAN2 IRQ/error counters, mux state, bus-0 query and HOLD behavior, `controlsMismatch` disposition on same boot | **MISSING**. Historical ELM327/0 storm and later C8.1 route differ; see [CAN2 evidence](C5_CAN2_FAULT_EVIDENCE_AND_ACTIONS.md). |
| Driver and physical controls | Independently observed HUD/mode cues, short CANCEL versus full MAIN OFF, EPS 2/6 and source-loss behavior, physical stop path | **MISSING**. Software simulations only. |
| Owner logistics | Manual reinstall rollback and optional settings reset from C8.1 crosswalk | **WAIVED only for full-image rehearsal/settings preservation**; no safety or native-build waiver. |

## Abort matrix for a future passive observation only

| Observation | Required action in that later plan |
|---|---|
| Unexpected firmware/SHA, Panda safety model/param other than qualified HondaBosch/80 or 81, mismatched owner/session, invalid native status | Stop qualification; preserve logs; no engagement. |
| OBD mux enabled on matched 11G signature, bus-1 diagnostic TX, ELM327/0, Honda HOLD with unexpected fingerprint | Stop and preserve discovery trace; do not force an identity. |
| CAN2 errors rise, IRQ reaches 16,000/s, `interruptRateCan2`, any active Panda fault or invalid RX | Stop; preserve counters, exact timestamps and firmware identity; do not reset fault to continue. |
| `controlsMismatch`, native/request/permission disagreement, unexpected steering command, EPS 2/6 mismatch or stale host state | Stop; preserve synchronized Card/SelfdriveD/Controls/pandad/Panda state. |
| Missing independent stationary torque protection, unexplained HUD/CANCEL/MAIN behavior | Keep Phase 5 and all actuation NO-GO; do not use an offline demo as physical qualification. |

## Passive command examples for copied logs only

These commands are **examples to put in a later approved data-capture procedure**, not commands run in C5/C6. They inspect already copied text/JSON files and produce no CAN traffic:

```bash
rg -n 'Setting OBD multiplexing|honda_normal_bus_attempt|Honda normal-bus identification hold|fingerprinted' <copied-card-log>
rg -n 'interruptRateCan2|controlsMismatch|safetyRxChecksInvalid|aolSafetyWire' <copied-event-log>
sha256sum <copied-log> <exact-native-build-manifest>
```

No copied current-device log or native-build manifest exists in this campaign. Future captures should be timestamp synchronized and passive, with the owner explicitly authorizing the physical setting and qualified safety personnel defining stop controls. A passive clean trace would be prerequisite evidence, not steering approval.

# C19 selective C8.2 source integration

Parent: `d146252ba988fb892155fef5ce71ab389908ccb1` (C18 R3). Reference C8.1: `9d2da330f6539beb5afb67867b28491526c0e1bd`. Reference C8.2: `20c86ebef9023845af0f62a946125700f7d51ce7`. Compared the actual C8.1..C8.2 diff with this worktree; no whole-file cherry-pick.

| C8.2 area | C19 disposition | Reason |
| --- | --- | --- |
| `selfdrived.py` stationary AOL inhibit | Adapted to current `_decide_aol_axes` | Accord 11G independent lateral veto at standstill or `vEgo <= max(0.3, minSteerSpeed)`; ordinary lateral remains owned by current state machine. |
| Honda `stock_intent.py` and `aol.py` | Adapted | Exact Drive only; P/N/R, unknown and other non-Drive gears clear latch and neutral history. Return to Drive needs release then fresh gesture. Full engagement cannot pre-arm while ineligible. Non-finite, negative or malformed speed/threshold fail closed. Cruise unavailable and fault guard runs after CANCEL actions. |
| Panda `honda_stock_aol.h` | **Not imported** | C8.2 adds an Accord flag, token retirement on zero host mask, Drive-only physical grant, and gear-transition host-mask reset. Current stable has newer atomic flag storage and native authorization logic. No independently validated C19 native integration of those changes and matching full tests was completed. Existing Panda still permits a latent token in some C8.2 cases, so installation is blocked. |
| Native C8.2 Honda tests and `libsafety/safety.c` test accessor | Not imported | They assert the omitted Panda behavior; claiming those tests on unchanged C19 native code would be false. Selected existing native tests ran on the current source. |
| C8.2 Honda host lifecycle and build-gate docs | Compared, selectively represented here | Current stable caller, selfdrive and product-build context have diverged. No route recording was restored. |

C18 R1-R3 discovery remains unedited: one-seed bounded passive observation, fail-closed bus-0 Honda firmware selection, and no generic CAN2 OBD scan for a plausible Accord. No Panda interrupt watchdog, `safetyRxChecksInvalid`, EPS limit, authorization flag, force ACK, Bosch-C alpha-long, stock ACC, radar, AEB or other-vehicle source was changed.

The C8.2 native gap includes physical CANCEL/RESUME and pending-grant edge ordering. The host guard does not establish native token retirement. Source is suitable for independent scoped review only, not a Panda safety acceptance claim.

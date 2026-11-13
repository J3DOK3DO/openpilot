# Accord 11G offline AOL eligibility matrix

This matrix reads the **current** checkout only. `aol_matrix.py` is a conservative, non-actuating triage of the recorded profile. It cannot issue a grant and does not model every native condition.

| Gate | Current source | Dom 7 evidence | Decision |
|---|---|---|---|
| Vehicle and stock profile | `opendbc_repo/opendbc/car/honda/stock_aol.py:52-84`; `accord_mvl_stock.py:6-14` | Accord 11G, Bosch 80, flags 2180, PCM cruise true, OP long false | Profile fits the recorded stock configuration; transmission and passive fields require explicit check to prove full `qualified()` result |
| Saved preference and valid settings | `openpilot/starpilot/aol/intent.py:51-83` | `AlwaysOnLateral=1` saved | Preference alone is not a request or grant; pause and button settings are not established by the aggregate |
| Marked independent profile | `openpilot/starpilot/car/honda/aol.py:37-52,62-80`; `stock_aol.py:52-58` | `alternativeExperience=0` in recorded CP | **Fails marked-only gate** (`32` required). No native independent session is proven |
| Physical LKAS and MAIN intent | `opendbc_repo/opendbc/car/honda/carstate.py:73-76,209-210,234-237`; `openpilot/starpilot/aol/intent.py:296-416` | Route 2 has 39 LKAS press/release pairs; stock ACC active with lateral | Button telemetry shows input, not its mapped AOL action, latch, or native acknowledgment |
| Fresh state and temporary restriction | `stock_aol.py:120-139`; `openpilot/starpilot/car/honda/aol.py:108-132` | No complete native proof trace exported | Unknown: valid fresh state, gear/fault restriction and session freshness |
| Native profile, inventory, session, lateral grant | `openpilot/starpilot/aol/runtime.py:78-108,262`; `openpilot/starpilot/car/honda/aol.py:62-80,108-132` | No matching proof in provided aggregate; marked CP absent | Unknown at each native gate; cannot infer a grant |
| Panda health | `openpilot/selfdrive/selfdrived/selfdrived.py:500-517` | Route 0/1 active `interruptRateCan2` and controls mismatch | Blocking fault explains unavailable controls independent of AOL preference |

Route 2's four lateral-active/stock-ACC-false samples occur near transitions and do not show a sustained independent session. `pcmCruise=true` means the ordinary engagement path follows stock ACC status (`carstate.py:209-210`). Camera LKAS button substitution in current `accord_mvl_stock.py:17-44` and C6-12 `carcontroller.py:729-750` is a HUD/SCM behavior, not a native lateral grant.

The C6-12 tree at `7b4db9a` contains Accord-specific PID tuning (`opendbc_repo/opendbc/car/honda/interface.py:95-99`), brake/standstill code and LKAS camera button substitution in `carcontroller.py`, and stock MAIN/ACC parsing in `carstate.py:244-245`. Current source factors button substitution into `accord_mvl_stock.py` and has a marked native AOL path absent from C6-12. Both parse `ACC_STATUS` as cruise enabled and `MAIN_ON` as available. C6-12 source differences do not establish historical vehicle behavior, an independent session, or a different CAN2 interrupt limit.

`aol_matrix.py` rejects mismatched safety word, flags, PCM role, model and unsupported alternative marker in negative fixtures. Its affirmative result is only an offline evidence checklist; exact runtime and Panda safety remain authoritative.

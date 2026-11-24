# C18 test record

Host invocation used system `pytest`, the x86_64 analysis environment's
`pycapnp`, and read-only cached Python packages through `PYTHONPATH`. A native
Honda safety library was compiled from this worktree's C source by the test
helper. No prebuilt safety binary was used as a qualification receipt.

| Check | Result |
| --- | --- |
| R1 production `fingerprint()` late/partial/malformed/unknown/no-reply Honda paths, exact bus-0 FW, unrelated-ID generic path, registered classic Honda; existing Honda/GM/Volvo/Chrysler/Mazda/Tesla checks | 327 passed, 3 deselected (`actual_card_publication` needs unavailable `msgq`) |
| Final focused Accord discovery plus Ford firmware/source-health regression | 23 passed (R2 20 Honda, 3 Ford) and R1 37 passed (19 Honda, 18 Ford) |
| Native Honda MVL safety | 3 passed |
| Selected native Honda steering/ack tests | 11 passed, 6 skipped by test conditions, 492 deselected by focused selection |
| Full Honda native safety file plus MVL | 253 passed, 249 skipped, 10 failed because `test_tx_hook_on_wrong_safety_mode` imports unrelated test modules requiring unavailable `msgq` |
| `compileall` of changed Python source and focused tests; `git diff --check` | passed |
| Current branch diff of Panda C safety, `selfdrived.py` and `panda_faults.py` against stable base | empty |

The initial plain system `pytest` could not collect because `capnp` was absent.
An offline `uv` sync could not resolve `setuptools>=61` in its writable cache.
Using the read-only host package cache enabled focused host tests. The native
wrong-safety-mode import failures and three card publication exclusions remain
environment blockers; they are not counted as passing tests. No Qualcomm target
inference, Panda/AGNOS device check, CAN2 physical measurement or road test ran.

## R1 reviewer P0 correction

The previous 10-ID check could miss an Accord when CAN-FD ADAS arrived after
the shared 24 reads, or a required frame was missing or malformed. This could
select the generic OBD-multiplexed scan implicated in the historical CAN2
interrupt storm. Synthetic production-path tests now verify that plausible
multi-ID PT/camera evidence uses a passive extension (48 reads maximum,
0.65 s discovery deadline), then normal-wiring bus-0 Honda VIN/FW. Unknown or
absent FW HOLDS as MOCK; no OBD mux enable or all-brand scan occurs. The
single-ID unrelated case still takes the generic path. No private route bytes
or IDs are in these tests. The missing `msgq` and `libparams_c.so` dependent
checks remain blockers, not passes.

## R3 final bounded single-seed startup regression

The R2 independent review reproduced a single matching Honda normal CAN ID in the first 24 reads followed by full Accord topology on read 25. R3 now triggers extra bounded passive observation on even one matching ID, but demands corroborating topology after the observation; otherwise generic other-car discovery remains unchanged. The production-level read-25 no-OBD test and uncorroborated-one-ID generic fallback both passed. **R3 exact-source fresh host results:** cross-brand **329 passed, 3 `msgq` cases deselected**; Honda/Ford focused **25 passed**; native Honda MVL **3 passed**. No claim covers arbitrarily delayed CAN past the bounded window, real Panda/AGNOS identity, production binaries or physical CAN2 qualification. Installation/road NO-GO.

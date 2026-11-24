# C18 test record

Host invocation used system `pytest`, the x86_64 analysis environment's
`pycapnp`, and read-only cached Python packages through `PYTHONPATH`. A native
Honda safety library was compiled from this worktree's C source by the test
helper. No prebuilt safety binary was used as a qualification receipt.

| Check | Result |
| --- | --- |
| Accord discovery/signature/FW HOLD and fallback, Honda classic, Hybrid qualifier, queue/cooldown, GM, Volvo, Chrysler, Mazda, Tesla | 316 passed, 3 deselected (`actual_card_publication` needs unavailable `msgq`) |
| Ford firmware/source-health regression | 18 passed |
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

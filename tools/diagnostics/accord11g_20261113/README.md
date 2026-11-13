# Accord 11G Dom 7 offline audit, 2026-11-13

This folder contains only documentation, a sanitized aggregate, and stdlib Python checks. It does not import or execute vehicle code, use CAN, flash a Panda, or contact a device. The two Git histories have no shared ancestor; comparison is between source trees, not a merge.

Current tree: `7e6d08187b17085729851c939047cd44088b36b8` at the repository root. Older C6-12 tree: `7b4db9a26010ba9899eef242d3ca49b33cbcca9c` at `/mnt/commadrive/accord11g-dom-2df71cf-c6-12-vision-brake-comfort`. In the current tree, Panda and opendbc source live in nested `panda/` and `opendbc_repo/opendbc/`; in C6-12 the same is true, but core openpilot Python lives under `selfdrive/` rather than `openpilot/selfdrive/`. These nested repositories are flattened as ordinary tracked files in these worktrees (`git ls-files -s` mode `100644` for inspected source), so the audit reads their on-disk content rather than assuming submodule pointers identify it. Generated Cython, DBC and build output is not assumed equivalent or present in the current checkout. Static checks inspect source only.

## Run

From this checkout:

```sh
python3 tools/diagnostics/accord11g_20261113/check.py --current . --older /mnt/commadrive/accord11g-dom-2df71cf-c6-12-vision-brake-comfort
python3 -m unittest discover -s tools/diagnostics/accord11g_20261113 -p 'test_*.py' -v
```

`route-summary.json` is an aggregate transcribed from the two read-only analysis JSON files named in the task. It contains no route keys, dongle ID, VIN, coordinates, messages, or raw telemetry. `panda_states` for route 2 is 37,208, obtained from `pandaFlags` counts. Route 0 has 10,873 active fault states of 10,912, while route 1 has 230 of 230. Route 2 has no active fault. The 83rd listed rlog, route 2 segment 62, failed decompression and is excluded from full coverage; its qlog is also truncated. Counts are event-message occurrences or sampled states, not independent root-cause events.

`check.py` verifies exact text contracts in both firmware trees and exact aggregate values. It does not emulate interrupt hardware, native AOL authorization, or safety behavior. Its expected-failure tests mutate copies of the aggregate and assert rejection. It deliberately retains the 16,000/s firmware limit as an assertion.

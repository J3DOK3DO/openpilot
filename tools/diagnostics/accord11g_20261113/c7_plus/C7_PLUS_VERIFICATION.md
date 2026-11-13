# C7+ verification record — 2026-11-13

**C7+2 final addendum:** The historical 61323fdf0c stock-ACC parser test fixture was restored, and the four-module selected host run now passes 361 tests, with 24 native Card cases deselected. See C7_PLUS_QUEUE_VERIFICATION.md for the exact scope. Earlier C7+2 figures remain as intermediate evidence.

**C7+2 addendum:** The queue cleanup and startup trace were evaluated after this original C7+ record. See `C7_PLUS_QUEUE_VERIFICATION.md` and `C7_PLUS_ELM327_CAN2_STARTUP.md` for current offline candidate status, tests, and the remaining CAN2 hold. The table below is the earlier Hybrid-only run.

**Scope:** Ubuntu host, source only. Initial HEAD `9b7ca0926b3a50fb68766c343d10de2956df8165`; installed Dom `7e6d08187b17085729851c939047cd44088b36b8`. Runtime candidate is solely `opendbc_repo/opendbc/car/honda/accord_mvl_stock.py` Hybrid allowance. No device contact, CAN send, flash, Param edit, build, or push.

## Tests

| Run | Result | Meaning and limit |
|---|---|---|
| `python3 -m unittest discover -s tools/diagnostics/accord11g_20261113 -p 'test_*.py' -v` | **16 passed** | Existing offline IRQ/timeline/CP checks remain green. |
| `python3 tools/diagnostics/accord11g_20261113/c7_plus/can2_evidence.py` | **completed** | Read-only projection of existing summary: route 0 peak 17,862/s; route 1 peak 9,700/s with an already active fault; route 2 peak 14,139/s without active fault. No causal attribution. |
| `python3 -m unittest discover -s tools/diagnostics/accord11g_20261113/c7_plus -p 'test_*.py' -q` | **1 passed** | Confirms an active sticky fault can coexist with a currently below-limit sampled rate. |
| `PYTHONPATH=<cached pycapnp,setproctitle>:opendbc_repo:. python3 -m pytest -q opendbc_repo/opendbc/car/honda/tests/test_accord11g_hybrid_aol_qualification.py` | **17 passed** | Real CarInterface, profile, policy, native profile match and CAN packer code. Marking CP in the test exercises the predicate; it is not an operational workaround or a native grant. |
| Selected `test_accord_mvl_stock.py`, `test_stock_aol.py` and new Hybrid file with cached pycapnp, setproctitle, zstandard, tqdm and pyzmq on PYTHONPATH, excluding the Card integration cases | **332 passed, 24 deselected** | Includes 17 new cases. Exactly 24 integration cases require native x86 `msgq`. |
| Same selected files without exclusion | **332 passed, 24 failed at import** | Checked-in `msgq_repo/msgq/_ipc.so` is ELF AArch64, not loadable on x86_64. Three Card startup cases also encounter missing `Crypto`. These are environment blocks, not behavior assertions. Initial run before cache paths had 326 passed / 30 missing-dependency failures; superseded by the more complete run. |
| `test_honda_mvl_stock.py` native safety | **collection blocked** | `cffi` absent on system Python; no host `libsafety` artifact was built. No safety test pass claimed. |
| `git diff --check` | **pass** | Whitespace check. |

The available host had Python 3.12 and pytest 7.4.4. Cached dependencies were imported read-only from `/home/jdkd/.cache/uv/archive-v0`; `uv venv` failed because its cache lock directory is read-only. No package was installed. The new test file is based on the 91-line historical `3e7b035` test, plus current negative/withdrawal cases. Test execution does **not** certify Panda/native safety behavior on hardware.

## Independent review

`qwen` and `opencode` are not on PATH. No bounded independent agent review was available; no review pass is claimed. Historical commit titles and prior C7 reports were treated as leads and checked against current source. In particular, installed LKAS queue withdrawal logic is only partially equivalent to `61323fd`, and original C7 has no demonstrated FDCAN2 correction.

## Required hold

**NO-GO for vehicle use or release.** The Hybrid eligibility issue has a source-level offline candidate; the active CAN2 Panda fault remains unexplained and independently blocks controls. Missing: x86 native Card lifecycle execution, host safety suite with matching libsafety, independent source review, exact native lateral receipt under unchanged safety words, no active Panda faults, and separately authorized parked electrical/timing evidence. Road suitability is not inferred. See `C7_PLUS_PATCH_RECOVERY.md` for the bounded evidence list.

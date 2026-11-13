# Campaign 2 run results, 2026-11-13

Source worktree: branch `accord11g-dom7-c612-fault-diagnostics-20261113`, base `256709d4d57f289f2fb8a74aabb5dc1b38aeda3b`. Offline only; no CAN, device, firmware build, network, or runtime edits.

- Processor: `/home/jdkd/Dom7_Log_Exports/.analysis_venv/bin/python tools/diagnostics/accord11g_20261113/timeline.py --archive /home/jdkd/Dom7_Log_Exports/2026-11-12_1220-1400_UAE/Dom7_routes_2026-11-12_1220-1400_UAE_logs_only.tar --schema /home/jdkd/Dom7_Log_Exports/analysis/schema/log.capnp --manifest /home/jdkd/Dom7_Log_Exports/2026-11-12_1220-1400_UAE/Dom7_routes_2026-11-12_1220-1400_UAE_manifest.json --json-out tools/diagnostics/accord11g_20261113/c2_timeline_summary.json --md-out tools/diagnostics/accord11g_20261113/C2_TIMELINE.md`: **82 decoded, 1 excluded**. Final partial rlog SHA matches manifest.
- Existing checker: `python3 tools/diagnostics/accord11g_20261113/check.py --current . --older /mnt/commadrive/accord11g-dom-2df71cf-c6-12-vision-brake-comfort`: **PASS**, same 16,000/s FDCAN2 rate/fault contract in both trees and aggregate contracts.
- Diagnostic tests: `python3 -m unittest discover -s tools/diagnostics/accord11g_20261113 -p 'test_*.py' -v`: **11 passed**.
- Native Honda host test: `PYTHONPATH=/home/jdkd/Dom7_Log_Exports/.analysis_venv/lib/python3.12/site-packages:opendbc_repo:. pytest -q opendbc_repo/opendbc/car/honda/tests/test_stock_aol.py`: **305 passed, 27 failed from missing host build dependencies**, specifically `setproctitle` and `msgq` imports in runtime/card tests. Initial system pytest without venv site packages stopped at missing `capnp`; venv Python lacks `pytest`. No dependencies installed.
- Second independent model review: **BLOCKED**. No immediately available bounded second-model review tool; this result is a single-agent source and log audit.

The main unresolved risks are the physical source of IT0 excess (RX traffic versus repeated errors or hardware/configuration), exact AOL marker qualification failure, native proof/session state, and wall-clock alignment. No road or physical safety qualification is claimed.

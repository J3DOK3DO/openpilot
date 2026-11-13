# Verification record

Executed in the isolated current worktree on 2026-11-13, Ubuntu, Python 3.12. The first static run failed because C6-12 stores the fault bit in `panda/board/faults_declarations.h` while current stores it in `panda/board/sys/sys.h`. The checker was corrected to select the existing source path; no runtime code changed.

```text
$ python3 tools/diagnostics/accord11g_20261113/check.py --current . --older /mnt/commadrive/accord11g-dom-2df71cf-c6-12-vision-brake-comfort
PASS: current and C6-12 FDCAN2 rate/fault contract: {'limit_per_second': 16000, 'can1_controller': 'FDCAN2', 'fault_bit': 8}
PASS: three route contracts; 82/83 coverage; baseline profile; active faults; 17862 > 16000

$ python3 -m unittest discover -s tools/diagnostics/accord11g_20261113 -p 'test_*.py' -v
test_fault_and_threshold_failures (test_check.OfflineContracts.test_fault_and_threshold_failures) ... ok
test_profile_mutation_fails (test_check.OfflineContracts.test_profile_mutation_fails) ... ok
test_static_firmware_rejects_limit_and_mapping_changes (test_check.OfflineContracts.test_static_firmware_rejects_limit_and_mapping_changes) ... ok
test_summary_passes (test_check.OfflineContracts.test_summary_passes) ... ok
test_truncated_coverage_fails (test_check.OfflineContracts.test_truncated_coverage_fails) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.003s

OK
```

Native Honda tests: **SKIPPED**. `python3 -c 'import capnp'` raised `ModuleNotFoundError: No module named 'capnp'`. No dependency was installed. The stdlib checks do not claim native runtime fidelity.

Independent external review: **BLOCKED**. Host `codex` CLI exists, but bounded read-only `codex exec --ephemeral -s read-only ...` exited 1 with `failed to initialize in-process app-server client: Read-only file system (os error 30)`. No reviewer output was obtained. A manual self-review checked that the only files added are within this folder, there are no CAN/device commands, the static checker asserts rather than edits the 16,000/s limit, and the aggregate omits identifiers and raw message text. `git diff --check` passed. This review cannot establish in-vehicle behavior.

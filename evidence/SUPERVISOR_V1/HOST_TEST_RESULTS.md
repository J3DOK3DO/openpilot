# Host test results

Environment date: 2026-10-25 UTC. Tests were executed without bytecode or pytest-cache writes.

Successful full-suite command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/g8_release \
  pytest -c /dev/null -p no:cacheprovider \
  --confcutdir=tools/g8_release/tests -q -rs tools/g8_release/tests
```

Result: **531 passed, 1 skipped in 9.23s** (532 collected outcomes). The one skip was `tools/g8_release/tests/test_g8_supervisor.py:389`: unprivileged user+mount namespace unavailable on this host.

RC3-only group (`tools/g8_release/tests/test_rc3_*.py`): **100 passed in 4.05s**.

New readiness-gate and supervisor-contract group: **35 passed in 0.43s**.

Pre-change baseline under the same isolated configuration: **496 passed, 1 skipped in 16.47s**.

Two initial environment-discovery invocations did not collect tests: the repository-root conftest required unavailable `capnp`, and the host pytest lacked the configured `asyncio_default_fixture_loop_scope` option. The successful command above confines conftest discovery to this host-only suite and uses `/dev/null` configuration. These were environment/configuration limitations, not test failures. `ruff` was not installed; `git diff --check` reported no whitespace errors for the new source and tests.

## SHA256 of tested implementation and tests

```text
cf46c848d221a047421fe9d0d33342a5d4f9598cb4efaf6151449a76008a657b  tools/g8_release/rc3_hardware_readiness_gate.py
bb15ec4c65026d79724401bcd72758799ac474e873ed3c84fbee9bfbe751e0ab  tools/g8_release/rc3_supervisor_contract.py
a166943b620c6a74c238c130d8580e90722b9d138acf56fd166c3f61fb641f11  tools/g8_release/tests/test_rc3_hardware_readiness_gate.py
d4abb384b1bb8c895ede92776238fd2ceda368c6ca009697a479aec2fb71969c  tools/g8_release/tests/test_rc3_supervisor_contract.py
```

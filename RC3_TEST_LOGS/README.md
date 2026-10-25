# RC3 host-only qualification logs

Campaign date: 2026-10-25 (Asia/Dubai)

## Ubuntu scoped release-tool suite

Command:

```text
PYTHONPATH=tools/g8_release python3 -m pytest -q -c /dev/null --confcutdir=tools/g8_release tools/g8_release/tests --junitxml=RC3_TEST_LOGS/ubuntu_tools_g8_release.xml
```

Result: **479 passed, 1 skipped in 7.02 seconds**. The JUnit XML SHA-256 at
capture time was `28db562e8687cba67dd495a0d6311386cd20103bfa4a98907cf8d85d17722835`.
The focused planner/staging/publication subset accounted for 48 passing tests;
it is included in the 479 total, not additional to it.

The neutral pytest configuration was intentional: the installed host pytest is
older than the repository-level configuration and rejects the unknown
`asyncio_default_fixture_loop_scope` option before collection. `--confcutdir`
also prevents unrelated root fixtures from importing unavailable `capnp` while
running this pure host release-tool suite.

## Verified pre-existing baseline count

Command:

```text
PYTHONPATH=tools/g8_release python3 -m pytest -q -c /dev/null --confcutdir=tools/g8_release tools/g8_release/tests --ignore=tools/g8_release/tests/test_rc3_package_planner.py --ignore=tools/g8_release/tests/test_rc3_host_staging.py --junitxml=RC3_TEST_LOGS/ubuntu_baseline_without_new_tests.xml
```

Result: **444 passed, 1 skipped in 5.41 seconds**. This directly verifies the
published RC3 host baseline after excluding only the two test files added in
this campaign. The JUnit XML SHA-256 at capture time was
`574bc7c9e6934870c39af4c23972223b5b2d9752d89a597add096ee81c75511d`.
The full 479 total is exactly this 444-test baseline plus 35 new tests.

## Package planner

Command:

```text
PYTHONPATH=tools/g8_release python3 tools/g8_release/rc3_package_planner.py --root . --output RC3_DEVELOPMENT_PACKAGE_PLAN.json
```

Result: exit **78**, intentionally fail-closed because no signed external trust
policy/keyring was supplied. The canonical plan was still emitted as an
explicitly requested development artifact and labels itself `UNSIGNED
DEVELOPMENT PACKAGE`. Its SHA-256 at capture time was
`420c8a8d6fbdaffce7599388fcd4a35f18370c4363552484f3158ab760529a67`.

## AArch64/QEMU boundary probe

Commands and observed output:

```text
$ /usr/bin/qemu-aarch64-static --version
qemu-aarch64 version 8.2.2 (Debian 1:8.2.2+ds-0ubuntu1.18)

$ readelf -h selfdrive/pandad/pandad
Class: ELF64
Data: 2's complement, little endian
Type: DYN (Position-Independent Executable file)
Machine: AArch64

$ readelf -l selfdrive/pandad/pandad
[Requesting program interpreter: /lib/ld-linux-aarch64.so.1]

$ /usr/bin/qemu-aarch64-static selfdrive/pandad/pandad --help
qemu-aarch64-static: Could not open '/lib/ld-linux-aarch64.so.1': No such file or directory
```

Disposition: **NOT EXECUTED / NOT PASSED**. QEMU is present, but no AArch64
runtime sysroot or requested interpreter exists in the worktree or standard
host location. No dependency was downloaded because this campaign is offline.
The ELF identity and pinned digest were verified on the host; this is not a
substitute for native off-road startup or AArch64 runtime qualification.

## AArch64/QEMU Python suite evidence

A separate QEMU/container attempt is preserved verbatim in:

- `RC3_SAFE_STAGING_QEMU.log` / `.xml` / `.rc`: initial narrow invocation,
  stopped at collection with seven release-tool import-path errors (exit 2).
- `RC3_SAFE_STAGING_QEMU_FULL.log` / `.xml` / `.rc`: expanded pre-final-source
  invocation, **466 passed, 1 skipped, 1 failed, 11 errors** (exit 1).

The expanded run proves that 466 tests executed under the AArch64 Python/QEMU
environment. It does **not** qualify the suite: the QEMU/container view could
not resolve this linked worktree's external Git common directory
(`/home/jdkd/src/phase1_sources/starpilot-openpilot/.git/worktrees/...`), so
tests requiring the frozen Git identity failed closed. The single assertion
failure was downstream of the same missing-Git condition. This run predates the
final tracked-tree hardening test and is retained as diagnostic evidence only.

Recorded SHA-256 values:

```text
0cfd8b5c6dd7031a75388ea4a64955ea0e95095e2a3f35c0dadbb1bf12a56655  RC3_SAFE_STAGING_QEMU.log
09b2a459845fba145693512e8707191fec4716a8efa88230285ca8baa1524a4f  RC3_SAFE_STAGING_QEMU.xml
77cabf6725e3bcd2941eb55c53e7e9bd28e4c42e58798de5bdaac90676d22540  RC3_SAFE_STAGING_QEMU_FULL.log
7391313be06231c6431758640e20e86d1e986034fb894ae363a01854da3fb9de  RC3_SAFE_STAGING_QEMU_FULL.xml
```

## Corrected AArch64/QEMU scoped-suite PASS (25 October 2026)

Earlier diagnostic QEMU attempts did not mount the absolute Git common directory
of the linked worktree. With metadata mounted read-only and Git safe-directory
set explicitly, the offline read-only network-isolated AArch64/QEMU Docker
release-tool Python suite passed: **479 passed, 1 skipped, 0 failed, 0 errors**
(480 collected; exit 0). Input files were mounted read-only. Only the
qualification-output directory was writable. Native pandad execution, actual
comma startup, physical OS A/B rollback and Honda Panda/CAN remain unqualified.

Evidence SHA-256:

- RC3_SAFE_STAGING_QEMU_CORRECTED.log : 5f981a12a0455cb9bb122fa3bef553be29c8d4fe646981c93d5e75bf7946ef19
- RC3_SAFE_STAGING_QEMU_CORRECTED.xml : f1b41d660914adca7858e8af4932226524baba7919dd9f73beb8223e8a471e8a
- RC3_SAFE_STAGING_QEMU_CORRECTED.rc : 9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa


## Final raw-parent Git integrity qualification (25 October 2026)

Frozen Honda RC3 driving payload and launcher unchanged. Replaced graft-sensitive merge-base ancestry with a bounded raw commit-parent walk (git cat-file under GIT_NO_REPLACE_OBJECTS=1). A late graft injection cannot forge raw parent records. The test suite includes this adversarial scenario.

- Ubuntu 24.04 host: 496 passed, 1 skipped, no failures/errors, exit 0. JUnit SHA-256 4c0f038b0f09681ae0709eb89af62492ecc6be7f3d72f0f9f5c5859ead86ad24. Evidence: RC3_TEST_LOGS/ubuntu_rc3_RAW_PARENT_FINAL.xml and .log.
- ARM64/QEMU network-isolated read-only: 496 passed, 1 skipped, no failures/errors, exit 0. JUnit SHA-256 3abdcd5178abe16286d604eefa160a3590ccf7ad527336384f0aa99ecaeda0ec. Evidence: RC3_TEST_LOGS/rc3_RAW_PARENT_QEMU_FINAL.xml and .log.

Results are only host-side engineering qualification; independent device startup, authenticated OS/root trust, trusted OS-level health authority, physical A/B power-loss rollback, Honda Panda/CAN bench and safety release approval remain NOT QUALIFIED. AGNOS inactive OS partition B is NOT an application slot. Engineering branch (if published) is NOT an installer and contains no production signature or installation permission.

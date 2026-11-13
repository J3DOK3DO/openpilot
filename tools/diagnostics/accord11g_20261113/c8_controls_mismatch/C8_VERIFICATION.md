# C8 verification: host, offline, 2026-11-13

PYTHONPATH: cached uv packages (pycryptodome, cffi, pycparser, pycapnp, setproctitle, zstandard, tqdm, pyzmq), plus `opendbc_repo:.`.

| Command scope | Result |
|---|---|
| `honda/tests/test_accord11g_normal_discovery.py` | **59 passed** |
| Mutant: no `honda_probe` | 3 failed (caught) |
| Mutant: no FW-identity fallback | 2 failed (caught) |
| `volvo/tests/test_normal_discovery.py` (shared passive window) | 84 passed |
| Every brand `*discover*` test + all `ford/tests` + `car/tests` using car_helpers/fw_versions + all `honda/tests`, `-k 'not card'` | **with fix: 196 failed / 5544 passed. HEAD baseline: 196 failed / 5544 passed. The FAILED node-id sets are identical, so there are 0 new failures.** |
| `git diff --check` | clean |

Pre-existing failures (identical on baseline): `ford/tests/test_aol_startup.py` (140), `honda/tests/test_startup_profiles.py` (31),
`car/tests/test_pedal_capability.py` (24), `honda/tests/test_bosch_longitudinal.py` (1). They need the native ARM `msgq` /
`libparams_c.so`, which this x86 host does not have. Six modules fail collection for the same reason.

Not covered: native Card/pandad on the device, Panda behaviour, and an on-road drive. Use the parked confirmation in
`C8_CONTROLS_MISMATCH_ROOT_CAUSE_AND_FIX.md` §5.

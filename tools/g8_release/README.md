# G8 release-integrity and recovery tooling (host-side, NOT deployed)

* `g8_manifest.py` - manifest builder + fail-closed verifier (Ed25519, domain-separated; production-key trust anchor required by default; dev keys opt-in and labelled DEV_ONLY).
* `g8_slot_supervisor.py` - reference slot supervisor (atomic symlink activation, durable intent state, bounded boot attempts, journal, recovery, flock). Must live OUTSIDE the replaceable app tree; not integrated with `launch_chffrplus.sh`; no on-device qualification.
* `tests/` - fault-injection and fail-closed tests. Run: `python3 -m pytest -c /dev/null --rootdir=. --confcutdir=. tests`.

Nothing here modifies existing production behaviour. `activation_guard.sh` and `launch_chffrplus.sh` are unchanged.
No production signing key exists in this repository.

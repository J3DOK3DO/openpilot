# G8-F12 RC3 Honda Stage 2 implementation report

Date: 2026-10-25
Disposition: **SOFTWARE PROTOTYPE COMPLETE / NON-DEPLOYABLE / INTEGRATION HOLD / HARDWARE HOLD / NO INSTALL**

## Outcome

This run added an externally auditable, host-only supervised application-slot controller prototype and 28 adversarial tests. The prototype performs no process execution, device access, network access, mount, boot-control, Panda, CAN, installation, or systemd operation. It cannot self-authorize a physical gate, health decision, recovery identity, or promotion.

The frozen RC3 launcher remains byte-identical at SHA-256 `dba70ac885eee3a98f19a3830660e365f764b6970c69c3d1bf2b3d28c8be5284`; its unconditional exit code remains 78. No tracked worktree file was modified. No commit or push was made.

The required full release-tool suite reports **538 passed, 1 skipped, 0 failed, 21 setup errors**. All 21 errors are the intentionally retained package-planner exact-overlay rejection. The planner was not loosened or modified. The Stage 2/reused-boundary subset reports **63 passed**, and the new Stage 2 file reports **28 passed**.

## Inputs reviewed

The implementation was based on direct inspection of:

- `rc3_supervisor_contract.py` and its tests;
- `rc3_hardware_readiness_gate.py` and its tests;
- `g8_f6_early_boot_boundary.py`;
- `g8_protected_authority.py`;
- `g8_readonly_fd_verifier.py`;
- `rc3_host_staging.py` and its tests;
- `rc3_package_planner.py` and its exact allowlist;
- the other `tools/g8_release/tests` release gates; and
- `RC3_SAFE_STAGING_ENGINEERING_HANDOFF.md` plus the prior `evidence/SUPERVISOR_V1` handoff, scope, and lab plan.

## New implementation

`tools/g8_release/rc3_stage2_supervisor.py` provides:

- exact typed separation between `OsBootIdentity`/`OsSlot` and application `CandidateIdentity`;
- a mandatory `AuthenticatedDecisionProvider` protocol for external recovery, physical-gate, health, and promotion decisions;
- strict binding to OS boot/rootfs identity, Honda platform, comma/Panda identity, candidate manifest/source/signing identity, gate nonce/sequence, attempt nonce/count, and owner-context digest;
- reuse of `g8_protected_authority.ProtectedAuthority` for authenticated trial tickets, monotonic attempt consumption, health receipts, cancellation, and atomic promotion;
- a hard retry ceiling of three and strict non-waivable physical-gate/neutral-CAN policy;
- an ordinary-file host journal restricted to a temporary host workspace, canonical strict schema, stable no-follow reads, locking, atomic replacement, and deterministic crash hooks;
- idempotent exact-request trial start and exact-nonce attempt decision, while refusing overlapping or mismatched starts;
- fail-closed power-restart recovery that never infers health and cancels in-flight work to the exact separately approved immutable recovery identity;
- HOLD for ambiguous preauthorization, changed OS slot/rootfs without new recovery approval, invalid grants, stale counters/nonces, corrupted journal, or uncertain cancellation;
- promotion only after authenticated health and a second, monotonic, externally authenticated immutable-recovery approval; and
- metadata-only launcher decisions with all process/install/boot/Panda/CAN authorization fields false.

The host journal and `MockProtectedAuthority` remain ordinary-file simulations. fsync/rename, file locks, and crash injection do not establish TEE/RPMB rollback resistance, actual storage atomicity, secure boot, or production isolation.

## Adversarial coverage

`tools/g8_release/tests/test_rc3_stage2_supervisor.py` covers:

- missing, signature-invalid, owner-waiver, or incomplete physical gate;
- invalid grant type/binding/count and invalid protected or independent health;
- power interruption and crash after protected attempt consumption;
- bounded retry, maximum attempts, approved-recovery rollback, and no inferred health;
- concurrent double start and exact idempotency;
- stale/replayed attempt nonce, start identifier, and gate sequence;
- OS A/B versus application-slot type confusion and OS-root change;
- wrong candidate, manifest, source, device identity, and policy;
- changing owner approval between physical gate and health;
- journal tampering;
- separate monotonic immutable promotion approval;
- no self-promotion after valid health;
- no process/network/device/install/actuation surface; and
- explicit rejection of the readiness gate's custom Ed25519 implementation as a production primitive.

These tests demonstrate model behavior only. They do not attempt to prove actual hardware state.

## Cryptography finding

The existing `rc3_hardware_readiness_gate.py` is unchanged. It implements Ed25519 verification using custom Python arithmetic and does not import a vetted production cryptography dependency. New tests detect this fact and require `custom_ed25519_implementation_allowed == false` in the Stage 2 production-integration contract.

Finding: retain the gate only as offline engineering verification tooling. Production remains HOLD until a vetted, maintained cryptography dependency and its update, validation, trust-anchor, key rotation, revocation, and compromise processes are independently approved. Passing synthetic Ed25519 vectors is not a substitute for that review.

## OS/systemd contract

`STAGE2_OS_SYSTEMD_INTEGRATION_CONTRACT.md` is documentation only and deliberately supplies no unit, command, executable path, or installation instructions. It defines verified-root placement/order, TEE/RPMB monotonic state, separate health-attester boundaries, AGNOS 19.8.1 SELinux-permissive limitations, shared `/data` implications, distinct OS/app A/B namespaces, service isolation requirements, Panda safeguards, a power-loss matrix, and an implementer checklist. It presumes no physical key custody.

## Verification commands and exact results

New adversarial suite:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/g8_release python3 -m pytest -c /dev/null -p no:cacheprovider --confcutdir=tools/g8_release/tests -q -rs tools/g8_release/tests/test_rc3_stage2_supervisor.py
............................                                             [100%]
28 passed in 0.27s
exit 0
```

New and directly reused supervisor/readiness boundaries:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/g8_release python3 -m pytest -c /dev/null -p no:cacheprovider --confcutdir=tools/g8_release/tests -q -rs tools/g8_release/tests/test_rc3_supervisor_contract.py tools/g8_release/tests/test_rc3_hardware_readiness_gate.py tools/g8_release/tests/test_rc3_stage2_supervisor.py
...............................................................          [100%]
63 passed in 0.66s
exit 0
```

Required full release-tool suite:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/g8_release python3 -m pytest -c /dev/null -p no:cacheprovider --confcutdir=tools/g8_release/tests -q -rs tools/g8_release/tests
538 passed, 1 skipped, 21 errors in 6.46s
exit 1
```

The one skip is `test_g8_supervisor.py:389`, because an unprivileged user+mount namespace is unavailable on this host. There are no assertion failures. The 21 setup errors originate from `rc3_host_staging` and `rc3_package_planner` tests that call the exact engineering-overlay guard.

Direct integration-hold reproduction:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/g8_release python3 -c 'from pathlib import Path; from rc3_package_planner import build_inventory; build_inventory(Path.cwd())'
rc3_package_planner.PlanningError: engineering overlay modifies non-whitelisted path: evidence/SUPERVISOR_V1/CODEX_RESULT.md
exit 1
```

## Hashes

| Artifact | SHA-256 |
|---|---|
| `tools/g8_release/rc3_stage2_supervisor.py` | `002214c984da3de2292f6475ace863e4e9d1ce424f4d42efe42637e54a9cf1ec` |
| `tools/g8_release/tests/test_rc3_stage2_supervisor.py` | `107b8e4cfbcf75b07bf98721df99a57bb533290057607d284cafd11ca62aa23e` |
| `evidence/STAGE12_20261025/STAGE2_OS_SYSTEMD_INTEGRATION_CONTRACT.md` | `b10dd8ce72cfb53683353ccbcaa6f465b080f7142bf0fbb43ef2db5466dbd337` |
| `launch_chffrplus.sh` | `dba70ac885eee3a98f19a3830660e365f764b6970c69c3d1bf2b3d28c8be5284` |
| `rc3_supervisor_contract.py` | `bb15ec4c65026d79724401bcd72758799ac474e873ed3c84fbee9bfbe751e0ab` |
| `rc3_hardware_readiness_gate.py` | `cf46c848d221a047421fe9d0d33342a5d4f9598cb4efaf6151449a76008a657b` |
| `g8_f6_early_boot_boundary.py` | `aecc373a0fb23f3e8d026647f9755c26e76362afb5e024fdd864b896421494e7` |
| `g8_protected_authority.py` | `173f1c96a1b7ec96293a97d353123309e3245a3275b894ef5b9a51c860552e55` |
| `g8_readonly_fd_verifier.py` | `c1f79f5b3042cecf84d8c44cbcbbbf99290661f6056224aba3a94c9cb8b71e28` |
| `rc3_host_staging.py` | `aa3428d42134449c81aedb616a121937637a1ed484923cffae6fa6a615157d1f` |
| `rc3_package_planner.py` | `3adfba3868fdbfd08de45c5c0109c8800ec775b20d641059159e20d0855c0d4a` |

Git identity inspected: HEAD `e4cafdf10a59a3f7fdf27e3242b81742851b00b1`, tree `5dcf50e3dae17006ef117473e2b7e4f02deabcbf`, parent `93cf96efd6b026854464b9aa505f01ad3c45b4a2`. Frozen RC3 remains commit `bbb771a2fadf5af96f532e798846ba8171483e50`, tree `fcd3142e877a165911a677f9361c6594f3eecf6b`.

## Explicit integration hold

`rc3_package_planner.py` intentionally has an exact path allowlist. HEAD already contains `evidence/SUPERVISOR_V1/*`, the prior supervisor/gate modules, and their tests outside that allowlist; the first lexicographically rejected path is `evidence/SUPERVISOR_V1/CODEX_RESULT.md`. If this Stage 2 work were later committed, its new module, test, and Stage 2 evidence paths would also require explicit provenance review.

This run did not change the allowlist, bypass the planner, alter its tests, or reclassify the errors as a pass. Resolution belongs to an independently authorized integration change that explicitly reviews the new paths and release provenance.

## Unresolved external and hardware holds

- Verified boot, production rootfs trust, and OS antirollback are unproven.
- No TEE/RPMB monotonic state or hardware atomicity exists in this prototype.
- No OS-resident supervisor is implemented, installed, or started.
- SELinux permissive mode is not credited as containment.
- No production signing keys, physical key custody, dual control, rotation, or recovery evidence exists.
- No independent physical gate or health attester is provisioned.
- No native ARM64 startup, model execution, or Panda initialization was performed.
- No physical power-cut, bootloop, storage-fault, rollback, or recovery matrix was executed.
- No Honda Accord 11G Panda/CAN allowlist, watchdog, heartbeat, disengagement, or fail-silent bench qualification was performed.
- No independent safety/release approval exists.

Nothing in this report authorizes installation, flashing, boot-slot changes, process launch, Panda/CAN access, vehicle use, road use, commit, push, or release.

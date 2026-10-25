# Stage 2 OS-resident supervisor integration contract

Status: **DOCUMENTATION ONLY / NONINSTALLABLE / NON-DEPLOYABLE / HOLD**
Platform scope: `HONDA_ACCORD_11G` only
AGNOS reference: 19.8.1
This document supplies no service unit, start command, executable path, installation procedure, boot-control command, or activation permission.

## Trust placement and ordering

The production supervisor would have to be part of a measured, verified, read-only OS root, loaded by the OS service manager before any replaceable application, Panda-facing process, or CAN-capable process. Its binary, policy parser, cryptography provider, service policy, and recovery metadata must all be covered by the verified root-of-trust. `/data/openpilot`, `/data/safe_staging`, and all other writable application paths are outside that trust boundary.

Service ordering must establish these facts before an application observation can be returned:

1. The boot chain has authenticated the exact OS/rootfs identity and antirollback state.
2. The supervisor's protected authority and rollback-resistant journal are available.
3. The immutable recovery application identity is independently authenticated.
4. A physical-evidence gate is authenticated and bound to the exact OS, source, manifest, device, Panda, sequence, and fresh nonce.
5. The attempt is durably consumed before any launcher handoff.
6. Panda/CAN remains physically neutralized and inaccessible throughout startup probation.
7. A separate health attester authenticates health before any promotion request.

No ordering relationship may equate OS boot success with application health. The supervisor must not mark an AGNOS OS slot successful, change an OS slot, install content, or start an application by itself.

## OS A/B versus application A/B

AGNOS OS A/B selects boot/system firmware partitions. The writable `/data` volume is shared across those OS slots. Therefore an OS slot name is never an application slot name, changing the OS slot does not select an independent application checkout, and `/data/openpilot` cannot be an immutable recovery slot.

Application A/B requires separately identified immutable snapshots, signed canonical manifests, independent approval of the recovery identity, and descriptor- or verified-image-based selection. Every application decision must bind the authenticated OS slot/rootfs identity, but the namespaces and counters remain distinct. An OS slot or rootfs change invalidates an application recovery approval until a new externally authenticated approval is supplied.

## Protected state contract

Production state must be atomic, monotonic, replay resistant, authenticated, and unavailable to `/data` writers. A TEE or RPMB-backed design (or an independently reviewed equivalent with the same properties) must protect at least:

- policy generation and digest;
- OS boot sequence and used boot nonces;
- current immutable recovery application identity and approval sequence;
- active trial identity, ticket, epoch, and gate sequence/nonce;
- attempt limit, attempts consumed, and used attempt nonces;
- authenticated health receipt identity; and
- promotion/cancellation transaction state.

An ordinary file, fsync/rename journal, application parameter, owner preference, or SELinux label on writable `/data` does not satisfy this contract. On ambiguous state, rollback counter regression, authentication failure, or unavailable protected storage, the only permitted result is HOLD with no launcher decision.

## Health attester boundary

The health attester must be separate from the candidate application, owner UI, and supervisor decision code. It must use a vetted maintained production cryptography dependency and an independently provisioned trust anchor. A healthy receipt must bind the exact application candidate, signed-manifest digest, source commit, OS slot/rootfs measurement, comma and Panda identities, gate nonce/sequence, attempt nonce/count, policy generation/epoch, startup measurement, and owner-context digest.

Owner authorization or risk acceptance is context only. It cannot substitute for physical readiness, immutable provenance, an attempt receipt, neutral-CAN probation, or authenticated health. A changed owner-context digest invalidates the pending flow rather than broadening authority.

The custom Ed25519 verifier in `rc3_hardware_readiness_gate.py` is retained unchanged as offline engineering tooling. It is not approved as a production cryptographic primitive. Production integration remains blocked until a vetted dependency, update policy, validation suite, and key lifecycle are independently approved.

## AGNOS 19.8.1 and SELinux limitation

SELinux permissive mode records denials but does not enforce them. On an AGNOS 19.8.1 system observed or configured as permissive, SELinux policy cannot be credited as isolation, write protection, device denial, or containment. Production qualification requires enforcing-mode evidence for the final policy plus negative tests showing that the application cannot mutate supervisor state, recovery data, service configuration, device nodes, or attester inputs. Verified rootfs and hardware-backed state remain required even with enforcing SELinux.

## Service-manager security requirements

The future unit and executable require independent review. At minimum, they must use a dedicated identity; an empty capability set; no privilege gain; strict read-only system protection; closed device policy; a private temporary namespace; no network address families beyond a narrowly justified local IPC channel; explicit read-only access only to immutable snapshots; and explicit write access only through the hardware-backed authority adapter. The supervisor must have no shell interpretation, environment-controlled executable lookup, writable search path, dynamic application plugins, or application-controlled configuration.

This document deliberately does not provide installable syntax. The final unit must be generated and reviewed in the verified-OS build system, not copied from evidence in this worktree.

## Panda safeguards

- Keep the Panda physically disconnected or transmit-neutralized until the physical readiness gate and probation prerequisites are independently witnessed.
- Deny all Panda/USB/CAN device nodes to the supervisor and trial application during preflight and startup probation.
- Treat a software "silent" flag as supplemental only; qualification requires instrumented proof that no frames can be transmitted.
- Require Honda Accord 11G-specific allowlist, heartbeat, watchdog, disengagement, fail-silent, harness, power, and bus-topology bench evidence.
- On health timeout, attester loss, supervisor restart, counter error, or application failure, keep device access denied and select only the approved immutable recovery identity.
- Never perform this qualification on a movable vehicle or public road.

## Power-loss matrix required for implementation review

| Interruption point | Required durable fact | Required restart result |
|---|---|---|
| Before gate acceptance | No trial exists | Approved immutable recovery; no launch |
| After gate journal, before protected ticket | Ambiguous authorization recorded | HOLD; external protected-state reconciliation |
| After ticket, before attempt consumption | Trial/ticket/epoch retained | Cancel trial to approved immutable recovery |
| During attempt consumption | Protected counter is old or incremented, never refunded | Reconcile authority, then cancel to approved recovery |
| After consumption, before handoff | Attempt remains consumed | Cancel to approved recovery; never replay nonce |
| During startup probation | No inferred health | Cancel to approved recovery |
| After health authentication, before promotion approval | Health is not promotion | Cancel to approved recovery or remain HOLD |
| During protected promotion transaction | Old or new protected recovery is atomic | Accept only an externally approved immutable identity; otherwise HOLD |
| During cancellation | Old active trial or completed cancellation | Reconcile epoch/recovery; ambiguous state is HOLD |
| OS slot/rootfs changes | Previous app approval no longer binds | HOLD pending a new OS-bound recovery approval |
| Protected storage unavailable/corrupt/rolled back | No trustworthy retry truth | HOLD; no application or Panda access |

Every row requires real power cuts at each storage boundary, repeated trials, raw instrument logs, and independent review. Host fsync/rename tests are not evidence of device durability.

## Implementer checklist

- [ ] Supervisor, service policy, crypto provider, and recovery metadata are in verified read-only OS storage.
- [ ] Boot-chain, OS antirollback, and exact rootfs measurements are independently attested.
- [ ] TEE/RPMB monotonic state adapter passes rollback, replay, atomicity, wear, and power-cut testing.
- [ ] OS and application slot types are separate in every API and persisted schema.
- [ ] Recovery is an immutable, separately authenticated application identity outside mutable `/data/openpilot`.
- [ ] Physical gate decisions use fresh nonces and monotonic sequences bound to source and hardware.
- [ ] Attempts are consumed before launcher handoff and cannot be refunded by a crash.
- [ ] Candidate artifacts are verified from immutable media or stable read-only descriptors.
- [ ] Health attester is independent, authenticated, bounded in time, and unable to self-promote.
- [ ] Promotion requires a new monotonic immutable-recovery approval.
- [ ] SELinux enforcing-mode policy and negative containment tests pass on the final AGNOS image.
- [ ] Panda remains physically transmit-neutralized until all no-CAN qualification steps pass.
- [ ] Honda 11G Panda/CAN safeguards pass on an isolated non-vehicle bench.
- [ ] Vetted production cryptography and key rotation/revocation procedures are approved.
- [ ] Real key custody, recovery, compromise response, and dual-control evidence exists; none is presumed here.
- [ ] Full power-loss matrix passes on sacrificial hardware with independent witnesses.
- [ ] Production release, installation, boot-slot, and road-use approvals are separate signed decisions.

## Explicit non-claims

This contract and prototype do not establish secure boot, production key custody, an OS supervisor, TEE/RPMB behavior, actual filesystem immutability, hardware recovery, native ARM64 startup, Panda safety, Honda safety qualification, installation permission, or production readiness.

# G8-F12 RC3 host-only safe-staging engineering report

Campaign date: 2026-10-25 (Asia/Dubai)
Worktree: `/mnt/commadrive/g8-f12-rc3-installation-engineering-20261025`
Disposition: **REMEDIATION COMPLETE / INDEPENDENT RE-REVIEW PENDING / ENGINEERING PUBLICATION HOLD / NO INSTALL**

## Executive decision

The requested offline host remediation is complete. The exact frozen source,
native artifacts, model pieces, launcher HOLD, application update path, AGNOS
A/B path, trust boundary, and rollback design were audited. A deterministic
development inventory planner, strict external host-trust verifier, disposable
inactive-application-slot simulator, targeted security/fault tests, gatecard,
and handoff were added without changing the authoritative published HOLD
branch, committing, pushing, contacting GitHub, accessing a comma, starting
openpilot, operating Panda/CAN, flashing, or invoking AGNOS/`abctl`.

This work does **not** approve production or installation. The emitted plan is
an **UNSIGNED DEVELOPMENT PACKAGE**. The external signed policy required for a
host trial is absent, so the planner deliberately returned exit 78. OEM-rooted
boot trust, a trusted OS supervisor, real power-cut recovery, a signed
recoverable production artifact, native off-road startup, and independent Honda
Panda/CAN physical safety approval remain open gates. The independent review
found no critical issues and three major issues; its engineering-publication
verdict remains **HOLD pending re-review** of this remediation.

## Scope controls and source identity

- Frozen source commit: `bbb771a2fadf5af96f532e798846ba8171483e50`.
- Frozen Git tree: `fcd3142e877a165911a677f9361c6594f3eecf6b`.
- Immediate parent: `7ac485a19e1e5bd9bd53cc139e45cd607262055f`;
  Honda RC2 lineage parent: `ac670c9555c1f00d7c1e7f5424cfdd375d4a15ca`.
- The local engineering branch and published HOLD refs pointed at the same
  frozen commit at audit and remediation time. No ref, branch, commit, or
  remote was changed. The remediated planner also supports a future engineering
  commit only when HEAD descends from this exact frozen object and every path
  changed from it is on an exact engineering-only allowlist. Protected payload
  changes, unrelated history, and dirty tracked content fail closed.
- `launch_chffrplus.sh` remains byte-identical to the frozen tree, SHA-256
  `dba70ac885eee3a98f19a3830660e365f764b6970c69c3d1bf2b3d28c8be5284`.
  Lines 1–5 print the Honda HOLD and exit 78 before environment loading,
  staging, AGNOS, manager, Panda, CAN, or any other startup.
- The pre-existing untracked `RC3_CODEX_RUN.log` was preserved.

## Exact launcher, updater, supervisor, and AGNOS A/B audit

| Layer | Exact RC3 behavior | Safety conclusion |
|---|---|---|
| Launcher HOLD | `launch_chffrplus.sh` exits 78 at line 5. `launch_env.sh`, staging activation, `agnos_init`, manager, and all hardware startup are later in the file. | Fail-closed and preserved. Nothing below the guard was executed. |
| Early OS success | If the HOLD were removed, `agnos_init` calls `sudo abctl --set_success` before AGNOS version handling and long before manager/model/Panda health. | Unresolved and unsafe as an application-health signal. It is currently unreachable, not fixed. |
| App update staging | `system/updated/updated.py` uses `/data/safe_staging/{upper,metadata,merged,finalized}`, creates an OverlayFS view over the active app, fetches/checks out Git content, copies it to `finalized`, and sets `.overlay_consistent` around `os.sync()`. | A completed-copy marker is not artifact authenticity, protected policy, or power-loss-safe activation. The updater itself runs from replaceable app storage. |
| App activation | At startup the launcher checks `.overlay_init` and the finalized marker, then sources `activation_guard.sh`. The guard validates canonical/non-symlink directories, required files, executable modes, same filesystem and inode postconditions. It renames active app to `old_openpilot`, then `finalized` to active, with immediate restoration on an ordinary second-rename failure. | Useful narrow protection, but explicitly two non-atomic renames. It has no signed manifest check, protected attempt state, reboot recovery, failed-startup health decision, or independently trusted supervisor. A power cut between renames can leave no active app. |
| Existing host supervisor references | `tools/g8_release` already contains signed-manifest, protected-authority, descriptor-pinning and early-boot protocol models. They are offline references and are not wired into AGNOS startup. | Strong design evidence only; mutable `/data/openpilot` cannot supervise or authenticate itself. |
| AGNOS target selection | `get_target_slot_number()` reads `abctl --boot_slot` and selects the opposite numeric slot. Partition paths become `/dev/disk/by-partlabel/<name>_a` or `_b`. | This is operating-system/firmware A/B, not application A/B. |
| AGNOS content | `agnos.json` lists seven A/B items: `xbl`, `xbl_config`, `abl`, `aop`, `devcfg`, `boot`, and `system`. No `/data` application partition is included. The updater marks the target unbootable, writes/verifies these partitions, then `swap()` clears hash markers and loops on `abctl --set_active`. | `boot_b`/`system_b` are an inactive OS slot. They do not contain an independent `/data/openpilot` app slot. No AGNOS action was invoked. |
| Shared application data | RC3 hard-codes application-related paths under `/data`: `/data/openpilot`, `/data/safe_staging`, `/data/pythonpath`, `/data/params`, and `/data/etc`. The AGNOS A/B manifest excludes the data volume. | By design, `/data/openpilot` is shared across OS slots. Booting OS slot B would still select the same mutable application data; it cannot supply app-level rollback isolation. |

### Blockers exposed by the audit

1. There is no authenticated, OEM-rooted proof that the actual bootloader,
   boot image, system image, rollback index, dm-verity state, and security
   metadata form the intended production chain.
2. There is no trusted supervisor outside `/data/openpilot` to authenticate an
   app candidate, consume protected attempts, pin read-only content, delay boot
   success, assess health, and recover after reboot or power loss.
3. Current app activation authenticates neither source identity nor content and
   cannot atomically preserve one bootable application across both renames.
4. The published RC3 content has no production signature or independently
   signed installation policy and no qualified recovery artifact.
5. The old `abctl --set_success` location acknowledges OS boot before native app
   startup and health; removing exit 78 without redesign would be unsafe.
6. Native off-road startup and physical Honda Panda/CAN safety were not executed
   in this offline campaign.

## Development package and integrity planner

Added `tools/g8_release/rc3_package_planner.py` with these properties:

- Pins the payload inventory to the exact frozen commit and tree. HEAD may be
  the baseline or a descendant containing only the exact listed engineering
  tools, tests, reports, gatecard, and evidence; a protected payload edit,
  unrelated history, or tracked/submodule drift fails. Inventory fields remain
  pinned to `bbb771a2...` and `fcd3142e...`, never the overlay HEAD.
- Pins the frozen `G8_F12_RC3_PINNED_COMPONENTS.json` byte digest and rejects
  malformed JSON, duplicate keys, unexpected fields, invalid types, traversal,
  absolute/noncanonical paths, symlinks in any declared path, missing files,
  duplicate component paths, wrong sizes, and digest mismatches.
- Opens every path component descriptor-relatively with `O_NOFOLLOW`, verifies
  the final descriptor with `fstat`, and hashes/parses from that same descriptor.
  Small security metadata is read twice with intervening `fstat`; large native
  and model files use before/after `fstat` around the pinned stream.
- Verifies all 14 native AArch64 components, including Honda `pandad` SHA-256
  `6fec6261fae4a84de75ef16f6fa604df01cd66f56e6ccea596fdfd890698d671`.
- Verifies three chunk sizes and individual SHA-256 values before reconstructing
  the 126,302,979-byte model digest
  `27969d9da00f74ba0c1f56de575665121a967528753500cd2f809b61664e0e3f`.
- Pins the launcher digest and structurally verifies the top-level exit 78 is
  ahead of environment loading and any privileged/boot-slot command.
- Is read-only by default. It prints canonical JSON unless `--output` is
  explicitly supplied; output uses create-exclusive/no-follow semantics and
  will not overwrite an existing path.
- Performs only bounded local Git identity, ancestry, diff, and cleanliness
  queries. It selects Git from the system default executable path, removes all
  inherited `GIT_*` controls before setting its own restricted configuration,
  requires `--show-toplevel` to match the canonical requested root, and passes
  that exact root as `safe.directory` for linked-worktree/QEMU compatibility.
  It has no fetch, network, signer, installer, launcher, device, privilege, or
  override path.
- Requires an external canonical signed policy and separate public-key ring for
  host-trial eligibility. Missing policy is not bypassable: output remains a
  HOLD and the process exits 78.

The current post-remediation canonical `RC3_DEVELOPMENT_PACKAGE_PLAN.json`
is an **UNSIGNED DEVELOPMENT PACKAGE**, not an installable artifact:

- Plan SHA-256: `72cb8f43c4971795066c9f811d7cb9e439582fa3998dd31891255d3a6b20167b`.
- Frozen inventory SHA-256: `367a26711143e9692260eac6257f5e3f7310ab88f040c0c166ca52d90f6a805e`.
- External trust: `MISSING_SIGNED_EXTERNAL_TRUST_POLICY`.
- Production, installation, device and road authorization: all false.
- The earlier pre-remediation plan had SHA-256
  `420c8a8d6fbdaffce7599388fcd4a35f18370c4363552484f3158ab760529a67`.
  It is historical evidence, **not the current published plan**.

## Independent host trust and application-slot simulation

Added `rc3_external_trust.py` and `rc3_host_staging.py`. The verifier has
verification only—no signing or key-generation code. Its keyring is explicitly
caller supplied: successful verification is reported only as
`CALLER_SUPPLIED_HOST_SIMULATION_KEY_CRYPTOGRAPHICALLY_VERIFIED`, with
independent trust anchor and production release authority both false. It
requires canonical JSON, exact schemas, unique keys, Ed25519, an external
regular-file keyring outside the mutable source tree, `host-simulation-only`
purpose, exact commit/tree and inventory binding, bounded attempt count, and
explicit denial of installation and device operations. Health receipts use a
separate signing domain and bind policy ID, inventory, trial nonce, and consumed
attempt. No production key is generated or shipped.

The slot model always creates `app_a` and `app_b` beneath the host temporary
directory. An explicit caller-selected path beneath that temp tree is supported
only to test process-death/reopen persistence. This path restriction is a
host-side policy check, not a platform-enforced device barrier or sandbox.
Slot metadata is inert and marked non-executable; no payload is copied or run.
The model:

1. stages candidate identity without changing the active slot;
2. reloads and verifies external policy immediately before trial;
3. generates a fresh `secrets.token_hex(32)` trial identity and durably persists
   it with the active trial and consumed attempt before simulated startup;
4. keeps `boot_success=false` through startup and probation;
5. rolls back on failed startup, restart, or modeled power interruption;
6. reloads policy and verifies a signed, complete health receipt before promotion;
7. atomically persists simulated promotion only after health; and
8. keeps install/device authorization false in every state; and
9. strictly validates the complete state schema, phases, slots, attempt bounds,
   nonce form, health flags, and phase/event combinations on every read/reopen.

Cross-run replay of an otherwise valid signed receipt is rejected because the
persisted CSPRNG nonce changes, and a new simulator object can reopen persisted
state after modeled process death without refunding an attempt. This deliberately
proves state-machine ordering only. It does not prove flash
durability, filesystem barriers under real power removal, bootloader behavior,
hardware-backed anti-rollback, hostile concurrent writers, native startup, or
placement in a trusted AGNOS component. Likewise, the offline file scanner uses
descriptor pinning and mutation checks but is not claimed as a security boundary
against a concurrent adversarial writer; publication should scan an immutable
snapshot.

## Verification results and logs

- Python compilation: new modules and tests compiled successfully.
- Corrected pre-existing Ubuntu scoped baseline: **444 passed, 1 skipped in
  5.41 s**, recorded in `RC3_TEST_LOGS/ubuntu_baseline_without_new_tests.xml`
  with SHA-256
  `574bc7c9e6934870c39af4c23972223b5b2d9752d89a597add096ee81c75511d`.
  This run excludes exactly the two new test files and verifies the corrected
  baseline count; the legacy lower count was not reused.
- Pre-remediation scoped `tools/g8_release` suite: **479 passed, 1 skipped in
  7.02 s**, retained in `RC3_TEST_LOGS/ubuntu_tools_g8_release.xml` with SHA-256
  `28db562e8687cba67dd495a0d6311386cd20103bfa4a98907cf8d85d17722835`.
  This is historical evidence for the original 35 focused tests.
- Remediated host-scoped `tools/g8_release` suite: **493 passed, 1 skipped in
  8.51 s**, exit 0. It was run offline with `-c /dev/null` and
  `--confcutdir=tools/g8_release` to isolate the release tools from the root
  conftest and unavailable host asyncio pytest option. No persistent evidence
  file was created or overwritten by this run.
- The single skip in each listed host suite is the pre-existing real-tmpfs disk-exhaustion
  test, not an RC3 failure.
- Negative coverage now additionally includes manifest replacement after open,
  Git-root mismatch, hostile `GIT_*` controls, permitted overlay descendants,
  rejected payload edits and unrelated history, caller-key semantics, CSPRNG
  cross-run receipt replay, process-death/reopen persistence, and malformed
  phase/slot/counter/health state.
- **Retained corrected isolated ARM64/QEMU Python release-tool suite: 479 passed, 1
  skipped, 0 failed, 0 errors**, with exit 0. Evidence is in
  `RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_CORRECTED.xml` (SHA-256
  `f1b41d660914adca7858e8af4932226524baba7919dd9f73beb8223e8a471e8a`)
  and `.log` (SHA-256
  `5f981a12a0455cb9bb122fa3bef553be29c8d4fe646981c93d5e75bf7946ef19`).
  The corrected container mounted the linked worktree Git common directory
  read-only and used an explicit Git safe-directory setting. The earlier
  unsuccessful container runs were environment-only test failures and are
  preserved separately for diagnosis only; they are not pass evidence. This
  corrected run predates the present remediation, so QEMU revalidation of the
  new code remains pending with the coordinating engineer. It is release-tool
  Python validation under ARM64 emulation, not native startup or hardware
  qualification.
- The pinned `pandad` was confirmed ELF64 AArch64, but direct user-mode program
  execution stopped before startup because `/lib/ld-linux-aarch64.so.1` and an
  AArch64 runtime sysroot are absent. Native `pandad` is therefore **NOT
  EXECUTED / NOT PASSED**. Offline constraints prohibited downloading a sysroot.
- During the original campaign the package planner wrote the explicitly
  requested retained canonical plan and returned exit 78 for missing signed
  external trust, as designed. Remediation did not overwrite that evidence.

No broad repository test suite was run. The remediated suite passes on the host;
the retained pre-remediation release-tool Python suite passed under ARM64/QEMU.
No claim is made for remediated QEMU coverage, native off-road application
startup, physical power-loss recovery, device storage, or Honda Panda/CAN
hardware behavior.

## Release gate decision

| Gate | Result | Required closure evidence |
|---|---|---|
| Frozen content integrity | Host PASS | Already pinned and logged; repeat in controlled build/signing environment. |
| Signed external production trust | **HOLD** | Independent production key custody, canonical signed manifest/policy, revocation and recovery procedure. |
| Authenticated OEM boot/root trust | **HOLD** | Measured and independently reviewed bootloader/vendor/boot/system chain, rollback protection and verified security metadata. |
| Trusted OS application supervisor | **HOLD** | Implemented outside mutable app data, protected attempts/policy, pinned read-only execution, delayed health success and recovery. |
| Hardware A/B and power-cut recovery | **HOLD** | Sacrificial-device fault matrix with witnessed cuts at every boundary and bootloop/corruption recovery. |
| Native off-road startup | **HOLD** | Controlled-device AArch64 dependencies, model, manager, Panda initialization and health probation evidence. |
| Honda Panda/CAN physical safety | **HOLD** | Independent bench/fault/disengagement/watchdog/bus/harness qualification and named safety signoff. |

Final disposition: **engineering publication HOLD pending independent re-review;
not production-ready, not installable, not an inactive-slot candidate, not
road-use approved**. The earliest safe next action is independent re-review of
this remediation, followed by the authenticated OEM trust and OS-supervisor work
described in `RC3_SAFE_STAGING_ENGINEERING_HANDOFF.md`; real installation remains
prohibited.


## Final raw-parent Git integrity qualification (25 October 2026)

Frozen Honda RC3 driving payload and launcher unchanged. Replaced graft-sensitive merge-base ancestry with a bounded raw commit-parent walk (git cat-file under GIT_NO_REPLACE_OBJECTS=1). A late graft injection cannot forge raw parent records. The test suite includes this adversarial scenario.

- Ubuntu 24.04 host: 496 passed, 1 skipped, no failures/errors, exit 0. JUnit SHA-256 4c0f038b0f09681ae0709eb89af62492ecc6be7f3d72f0f9f5c5859ead86ad24. Evidence: RC3_TEST_LOGS/ubuntu_rc3_RAW_PARENT_FINAL.xml and .log.
- ARM64/QEMU network-isolated read-only: 496 passed, 1 skipped, no failures/errors, exit 0. JUnit SHA-256 3abdcd5178abe16286d604eefa160a3590ccf7ad527336384f0aa99ecaeda0ec. Evidence: RC3_TEST_LOGS/rc3_RAW_PARENT_QEMU_FINAL.xml and .log.

Results are only host-side engineering qualification; independent device startup, authenticated OS/root trust, trusted OS-level health authority, physical A/B power-loss rollback, Honda Panda/CAN bench and safety release approval remain NOT QUALIFIED. AGNOS inactive OS partition B is NOT an application slot. Engineering branch (if published) is NOT an installer and contains no production signature or installation permission.


## Independent final review and publication disposition

Independent Codex Sol High reviewed the raw-parent graft-race remediation and issued **GO for a separately labeled non-installable engineering HOLD branch**; see RC3_RAW_PARENT_INDEPENDENT_REVIEW.txt. The report was prepared while final ARM64/QEMU tests were underway; those tests subsequently finished 496 passed, one skipped, zero failed. Publication is restricted to source, host-only tools and verifiable qualification evidence. It is not an openpilot installation URL or a production tag. Production, installation, any boot slot modification and road use remain NO-GO pending actual hardware trust, supervisor, off-road startup and Honda Panda/CAN physical approval.

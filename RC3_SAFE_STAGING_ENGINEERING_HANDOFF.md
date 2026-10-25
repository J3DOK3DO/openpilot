# G8-F12 RC3 safe-staging engineering handoff

Disposition: **REMEDIATION COMPLETE / INDEPENDENT RE-REVIEW PENDING /
ENGINEERING PUBLICATION HOLD / PRODUCTION HOLD / NO INSTALL**.

The frozen RC3 content at commit `bbb771a2fadf5af96f532e798846ba8171483e50`
and tree `fcd3142e877a165911a677f9361c6594f3eecf6b` passes the scoped host integrity
checks. The deliverable is deliberately an **UNSIGNED DEVELOPMENT PACKAGE**.
There is no production key, package signature, signed external policy, install
authorization, device action, or road-use authorization.

The latest independent review reported no critical findings and three major
findings. Those findings have been remediated in the host-only tooling and
tests, but the review verdict remains HOLD until an independent re-review.

## What is ready for the next engineering owner

- `tools/g8_release/rc3_package_planner.py` deterministically verifies the
  frozen Git identity, exact pinned-component manifest, exit-78 launcher, 14
  native AArch64 files, three model chunks, and full 126,302,979-byte model.
  All declared content is opened descriptor-relatively with `O_NOFOLLOW` and
  hashed/parsed through the same verified descriptor. Git control variables are
  sanitized and the canonical Git root is enforced.
  A future engineering commit is accepted only as a descendant of the exact
  frozen baseline and only when every changed path is on the exact engineering
  tooling/test/report/evidence allowlist; protected payload edits and unrelated
  history are rejected. The inventory always records the frozen commit/tree.
  Its default is read-only; `--output` is required to create a new file, and an
  existing output is never overwritten. Missing external trust returns 78.
- `tools/g8_release/rc3_external_trust.py` strictly parses canonical JSON,
  rejects duplicate/malformed envelopes, and cryptographically verifies
  Ed25519 host-simulation policy and health receipts against a caller-supplied
  keyring stored outside the source tree. Successful status is exactly
  `CALLER_SUPPLIED_HOST_SIMULATION_KEY_CRYPTOGRAPHICALLY_VERIFIED`; it is not an
  independent trust anchor and grants no production release authority. The
  module contains no signer, key generation, private key, production key, or
  override.
- `tools/g8_release/rc3_host_staging.py` models two inactive/active application
  directories only inside the host temporary tree. It generates and durably
  saves a fresh 256-bit CSPRNG nonce with the consumed attempt before simulated
  startup, rejects cross-run receipt replay, strictly validates state invariants,
  and supports reopen testing after modeled process death. A caller-selected
  temp path enables persistence testing, but is host policy—not a
  platform-enforced device barrier. It never runs a payload and is not an
  on-device supervisor.
- `RC3_DEVELOPMENT_PACKAGE_PLAN.json` is the **current, post-remediation
  UNSIGNED DEVELOPMENT PACKAGE plan**, SHA-256
  `72cb8f43c4971795066c9f811d7cb9e439582fa3998dd31891255d3a6b20167b`;
  frozen source inventory SHA-256 is
  `367a26711143e9692260eac6257f5e3f7310ab88f040c0c166ca52d90f6a805e`.
  It grants no installation or production approval.

- `RC3_SAFE_STAGING_GATECARD.json` is the machine-readable HOLD decision.
- `RC3_TEST_LOGS/ubuntu_baseline_without_new_tests.xml` independently verifies
  the corrected pre-existing baseline of 444 passed and one skipped.
  `ubuntu_tools_g8_release.xml` records the pre-remediation 479 passed and one
  skipped suite. The remediated host-only suite is **493 passed, 1 skipped**,
  exit 0. The retained corrected offline AArch64/QEMU Python suite records
  **479 passed, 1 skipped, 0 failures, 0 errors**, exit 0, at
  `RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_CORRECTED.xml` (SHA-256
  `f1b41d660914adca7858e8af4932226524baba7919dd9f73beb8223e8a471e8a`)
  and `.log` (SHA-256
  `5f981a12a0455cb9bb122fa3bef553be29c8d4fe646981c93d5e75bf7946ef19`).
  Earlier container attempts are diagnostic failures only. The corrected QEMU
  run predates this remediation, so fresh QEMU validation is pending. It does
  not qualify native `pandad` executable/device startup, which remains
  unavailable and unqualified.

## Critical architecture constraint

Do not treat `boot_b` as an openpilot application slot. The A/B names in the
AGNOS updater select the opposite `boot`/`system` and other firmware partitions.
The application and staging paths are under the shared writable `/data` volume:
`/data/openpilot` and `/data/safe_staging`. Switching AGNOS from OS slot A to B
therefore does not produce an independent application checkout. A safe app
trial needs its own immutable identity, protected policy/attempt state, health
authority, and rollback mechanism outside mutable `/data/openpilot`.

## Fastest safe continuation path

1. Obtain independent re-review of the three remediated major findings. Keep
   engineering publication on HOLD until that verdict is recorded.
2. Re-run the scoped Python release-tool suite under the established offline
   QEMU/linked-worktree invocation. Record new JUnit/log hashes; do not conflate
   that Python result with native `pandad` startup.
3. Establish and independently attest the OEM boot chain, production image
   signing chain, rollback protection, verified root/system state, and security
   metadata. Do not infer trust from raw image similarity.
4. Implement an OS-resident, protected application supervisor outside mutable
   `/data/openpilot`. It must authenticate policy and artifacts, protect attempt
   counters against rollback, pin executable descriptors/read-only storage, and
   withhold success until a bounded manager/model/Panda health probation passes.
5. Build a separate reproducible production artifact in the controlled signing
   environment. Sign its canonical manifest with a recoverable production
   process, document key custody/revocation, and validate recovery media. The
   host-simulation key schema in this worktree intentionally cannot substitute.
6. On sacrificial, controlled hardware and while physically off-road, validate
   native AArch64 imports, dependencies, model loading, manager startup, Panda
   initialization, and a health failure before any driving use.
7. Execute witnessed hardware A/B tests: interruption at every write/activation
   boundary, abrupt power cuts, corrupted candidate, bootloop, exhausted attempts,
   failed startup, stale health, and recovery after both storage and OS faults.
8. Independently qualify Honda Accord 11G Panda/CAN transmit allowlists,
   disengagement, watchdog/fail-silent behavior, bus topology, harness/power
   behavior, and physical fault injection. Obtain named safety/release signoff.
9. Only after all prior evidence is independently reviewed may a different
   deployable candidate remove the launcher HOLD in a separate authorized change.

Until every step is closed, do not install, flash, select an inactive OS slot,
run openpilot, publish an installer URL, tag a production release, or drive with
this candidate.


## Final raw-parent Git integrity qualification (25 October 2026)

Frozen Honda RC3 driving payload and launcher unchanged. Replaced graft-sensitive merge-base ancestry with a bounded raw commit-parent walk (git cat-file under GIT_NO_REPLACE_OBJECTS=1). A late graft injection cannot forge raw parent records. The test suite includes this adversarial scenario.

- Ubuntu 24.04 host: 496 passed, 1 skipped, no failures/errors, exit 0. JUnit SHA-256 4c0f038b0f09681ae0709eb89af62492ecc6be7f3d72f0f9f5c5859ead86ad24. Evidence: RC3_TEST_LOGS/ubuntu_rc3_RAW_PARENT_FINAL.xml and .log.
- ARM64/QEMU network-isolated read-only: 496 passed, 1 skipped, no failures/errors, exit 0. JUnit SHA-256 3abdcd5178abe16286d604eefa160a3590ccf7ad527336384f0aa99ecaeda0ec. Evidence: RC3_TEST_LOGS/rc3_RAW_PARENT_QEMU_FINAL.xml and .log.

Results are only host-side engineering qualification; independent device startup, authenticated OS/root trust, trusted OS-level health authority, physical A/B power-loss rollback, Honda Panda/CAN bench and safety release approval remain NOT QUALIFIED. AGNOS inactive OS partition B is NOT an application slot. Engineering branch (if published) is NOT an installer and contains no production signature or installation permission.


## Independent final review and publication disposition

Independent Codex Sol High reviewed the raw-parent graft-race remediation and issued **GO for a separately labeled non-installable engineering HOLD branch**; see RC3_RAW_PARENT_INDEPENDENT_REVIEW.txt. The report was prepared while final ARM64/QEMU tests were underway; those tests subsequently finished 496 passed, one skipped, zero failed. Publication is restricted to source, host-only tools and verifiable qualification evidence. It is not an openpilot installation URL or a production tag. Production, installation, any boot slot modification and road use remain NO-GO pending actual hardware trust, supervisor, off-road startup and Honda Panda/CAN physical approval.

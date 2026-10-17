# C7R R0-R3 Offline Engineering Closeout

17 October 2026. Scope: MINIMAL C7R candidate, not all original 12 patches. Release HOLD.

Base F83: 83053b17827f76e887de8c610189a25c0d1e37bd

## Verified scope

- Accord-only stop change adapted from patch 0005; 116/116 LongControl tests pass including six Ford recoveries.
- Campaign A pins adapted from patch 0006; 6/6 tests pass.
- Full 44-file regression: 3727 cases, 3652 pass, 3 non-Honda fails, 72 skips, 0 errors.
- New fail-closed JUnit evidence checker: PASS; 12 injected-invalid evidence cases rejected.
- 13 source-matched ARM64 ELF components staged and combined ARM64 QEMU lifecycle smoke passed.
- Four ELF gate negative tests rejected missing, corrupted, wrong-arch and wrong-symbol inputs.
- Minimal x86 host SCons build passed; FULL AGNOS 19.8.1 target service deployment not qualified.
- Side-by-side old F83 / corrected LongControl on 29855 real archived Honda inputs: zero differences (assumed test toggles).
- Historical braking observations collected; no new C7R brake-actuator measurements.

## Incoming 12-patch disposition

| Patch | Scope | Decision | Reason |
|---|---|---|---|
| 0001 | C6-12 native hash lock | DEFER | Separate preserved C6 manifest from future signed C7 source-build manifest |
| 0002 | AOL skip inventory | REPLACED IN OFFLINE EVIDENCE | Strict frozen JUnit/skip gate; 72 skips still pending owner approval |
| 0003 | Historical brake comfort analysis | REPLACED OBSERVATIONALLY | Derived filtered acceleration and request slew, not candidate brake response |
| 0004 | F8 disposition proposal | REFERENCE | Open issue-owner decisions retained |
| 0005 | Honda-only stop scope | ADAPTED AND APPLIED | Ford six recovered; Honda differential passes |
| 0006 | Campaign A SHA re-pins | ADAPTED AND APPLIED | Two source pins corrected; six tests pass |
| 0007 | MPC artifact guard | STAGED EXTERNALLY | 13 ARM64 ELFs, source-hash and four negative controls; no signed release image |
| 0008 | HUD / brake-addon / EPS tuning | EXCLUDED FROM MINIMUM | Unqualified actuator-related feature code stays separate |
| 0009 | Honda golden CAN test harness | DEFER | No full source-reconstructed C7 controller CAN payloads |
| 0010 | Permissive upstream exception gate | SUPERSEDED | Stricter 44-file gate and explicit exception visibility |
| 0011 | Original engineering report | REFERENCE | Review document, not a production change |
| 0012 | Drop stale Hyundai gate entries | SUPERSEDED | Strict expected inventory contains no Hyundai waiver |

## Unmet release / safety gates

- Full 12-patch series was not cherry-picked to this minimal branch; only stop scope and Campaign A pins applied. The original C7R feature switches remain intentionally absent.
- Three non-Honda calibration failures and 72 AOL skips require formal owner dispositions; 39 prior G02 patch decisions remain open.
- Complete AGNOS 19.8.1 ARM64 service graph, startup/restart/timeout, target third-party provenance and Panda firmware/host matching remain incomplete.
- Staged rebuilt MPC native binaries are NOT part of a qualified installed comma package; tracked long solver is stale.
- Archived Honda side-by-side patch test uses real carParams/carState, but nominal synthetic toggles and acceleration bounds; not source-faithful complete C6-12 versus C7 dynamics.
- No byte-level C7 reproduced Honda CAN comparison, no verified brake actuator comfort or broad near-stop coverage.
- No independent safety approval, controlled parked qualification, signed rollback or authorized road test.

No comma installation, Panda flash, live CAN or road actions. Protected C6-12, protected C7 and F83 remain unmodified.

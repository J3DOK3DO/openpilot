# Honda Accord 11G C7 — Detailed Engineering Handover

**Snapshot:** 17 October 2026 (Abu Dhabi, UTC+04)
**GitHub assessment branch:** accord11g-dom-c7-f8-offline-assessment-20261017
**Purpose:** paused-work snapshot for independent **source review only**.
**Vehicle status:** **C7 RELEASE HOLD / NO-GO — DO NOT DEPLOY OR ROAD TEST.**

> Scope of claims: a successful host test, an AArch64 shared-object import, a mathematical curve calculation, or a solver smoke test does NOT certify the complete vehicle system. This report distinguishes tested subsets from unqualified release gates. It intentionally excludes raw driving logs, binaries, credentials and machine-specific configuration from the GitHub commit.

## 1. Executive summary

The C7 programme began by freezing the working C6-12 Honda Accord 11G baseline and creating a protected C7 source branch. The goal is a safer, more capable C7 while retaining the existing C6-12 tuning and a reliable rollback path.

Progress to date includes:
- Verified five important extracted AGNOS 19.8.1 runtime files against the actual offroad comma by SHA-256.
- Established Clang-on-x86 to AArch64 object compilation and an isolated ARM64 linker/QEMU loading path.
- Recovered and checksum-verified the **exact source-lockfile Cap'n Proto 1.0.1.post98 AArch64 wheel**.
- Compiled and linked new native cereal, Params, messaging, locationd pose, EKF and safety libraries, plus native Python/Cython bindings.
- Regenerated the missing lateral and longitudinal Acados MPC C code, produced both AArch64 solver libraries and their Python bindings, and called both solvers in ARM64 QEMU (Acados status **0** for initialized smoke tests).
- Completed the source-pinned 44-file host regression: **3,202 cases; 3,127 passed; three inherited non-Honda calibration failures; 72 inherited skips; zero errors**.
- Produced a real-Honda **5,998-frame time-ordered model/curve-speed input replay** over five archived segments, including 457 higher-speed tight-curve model predictions.
- Diagnosed and fixed missing GNU exception-unwinding ELF metadata in the isolated native build harness (ld --eh-frame-hdr). This required **no production Params changes**.
- Preserved both protected C6-12 and C7 sources; did not deploy, actuate, flash Panda, transmit CAN or conduct a C7 road test during these host campaigns.

**Critical unfinished fact:** all seven named engineering areas have **some source-built, tested native components**, but **zero of seven complete end-to-end application/release groups have been qualified**. A coherent, reproducible whole-application build and integration is still required. F8 independent Sol High review is pending after the Codex usage limit.

The previous estimate of **~68% overall progress** is a subjective planning estimate only, not a measured release-readiness or safety percentage. The remaining work is more integration- and safety-critical.

## 2. Source identities and release constraints

| Source | Commit / state | Rule |
|---|---|---|
| C6-12 protected working baseline | 7b4db9a26010ba9899eef242d3ca49b33cbcca9c — clean | Preserve, never overwrite |
| Protected C7 derived from C6-12 | 48bd4c1d88f2a964cc9d2f0f58aca9d43681149d — clean | Preserve, never overwrite |
| Latest F8 isolated candidate | based on protected C7 HEAD, six intentional changed/new source/test files | Review-only GitHub branch |
| F8 native build and evidence | /mnt/commadrive/c7-f8-native-closure-20261017 | Host-local only, not pushed |

The GitHub assessment branch carries **exactly the source changes/test fixtures and this handover**. It is NOT the result of rebuilding binaries on the comma. Actual native artifact hashes are recorded in local evidence manifests, not committed to GitHub.

### Changed source/test files versus protected C7

1. **starpilot/controls/lib/curve_speed_controller.py** — sole new production control-code modification. Keeps raw high model curvature for target-speed calculations up to 0.1 inverse metres, while retaining 0.02 inverse metres as the upper learning-bucket and far-field-gain bound.
2. **selfdrive/controls/tests/test_curve_speed_controller.py** — six parameterized tight-curve radius tests (40, 30, 25, 20, 15, 10 m) asserting the steady target respects the raw-curvature lateral acceleration limit.
3. **selfdrive/controls/tests/test_starpilot_planner.py** — stale Force Stop jerk test expected 0.32 instead of the already-existing production 0.20; test correction only.
4. **selfdrive/controls/tests/test_starpilot_acceleration.py** — adds the missing synthetic selfdriveState.personality fixture, required by current acceleration implementation; test-only.
5. **starpilot/controls/tests/test_fleet_aol.py** — adds an Accord 11G synthetic policy/latch check explicitly excluding real CAN/Panda/actuation proof.
6. **selfdrive/controls/tests/test_campaign_a_contract_guards.py** — Campaign A contract/source guard tests updated for the approved numerical patch; test-only.

No additional vehicle-calibration retune was made in F8. No bulk upstream imports; no waiver of hard safety or driver-override requirements.

## 3. Chronological evidence and achievements

### 3.1 C7 engineering reset from C6-12 (14 October)

C6-12 was retained as the last known working device baseline. The protected C7 branch was created from that lineage with staged release gates covering target ABI, native Params/messaging, Honda speed/jerk control, AOL policy, regression preservation and eventually reversible parked physical qualification. Previous C6 driving concerns, including low-speed lateral hunting, premature stopping, follow distance and pulsing braking, were recorded as behavioural context. **C7 offline build tests do not establish that these driving issues are solved.**

### 3.2 Campaign B1–B4: AGNOS compatibility and first native tests

**B1 — target sysroot:** extracted AGNOS 19.8.1 sysroot; live/offline SHA matched for loader, libc, libstdc++, libzmq and Python executable (5/5). The extracted image/package's full provenance and *all* dependent headers/libraries were not thereby qualified.

**B2 — early build:** targeted native Params C++ subsets compiled and linked; a full generic ARM64 QEMU SCons build timed out. Subsequent strategy shifted to x86 host Clang --target=aarch64 plus a pinned ARM64 Docker linker. No full native image pass.

**B3 — lifecycle:** generic ARM64 QEMU Params get/put/nonblocking basics passed. Initial faulty negative harness called a nonexistent method; malformed lock injection produced std::out_of_range and a timeout. Correct source-faithful isolation was needed; do not mislabel harness defects as confirmed product bugs.

**B4 — offroad passive Panda:** eight read-only pandaStates IPC samples reported Panda safetyModel=noOutput, controlsAllowed=false, ignition false and no observed CAN RX/TX, bus-off or faults in the sampled window. A passive noOutput check **does not** qualify the flashed firmware, CAN ownership, driver override or active Honda safety.

Results remained HOLD for any on-device deployment. Evidence directory: /mnt/commadrive/c7-campaign-B-closure-20261016.

### 3.3 R1–R5: reviewed curvature patch and initial Honda archive (16 October)

**Root cause addressed by reviewed numerical patch:** a curvature cap of 0.02 inverse metres intended for *learning buckets* also reduced a larger raw model curvature in the speed-target path. Tight curves under 50 m radius could therefore retain a mathematically excessive target relative to raw curvature. The candidate patch introduces MAX_TARGET_CURVATURE=0.1 and preserves raw model readings in far-field correction rather than clipping them down to the learning limit.

Synthetic example, **10 m radius**:
- Original steady target around **11.176 m/s (40.2 km/h)**.
- Patched steady target around **6.325 m/s (22.8 km/h)**.
- Implied raw lateral acceleration at target decreased from about **12.49** to **4.0 m/s²**.
- The above is mathematical target speed, **not** actual vehicle braking, achievable grip or safety proof.

Initial 44-file regression without patch: **3,195 nodes; 3,117 pass / six fail / 72 skip**. With patch: **3,201 nodes; 3,126 pass / three fail / 72 skip**. Six newly added curves pass; two previously failing Honda numerical cases improve; another “fixed” failure was a stale Force Stop jerk test expectation rather than changed production behaviour. Remaining three failures were Chevrolet Bolt, Hyundai Palisade, Genesis G70 lateral-control calibration contracts. Their applicability must be dispositioned by the owner, not hidden.

First 44-segment Honda archive scan: **51,412 modelV2 profiles**, 741 predicted curves tighter than 50 m, 601 impacted raw speed-envelope profiles, zero selected tight profiles above 10 m/s. Limited high-speed evidence.

The host-to-ARM64 compile/link proof succeeded for C++ against the extracted AGNOS sysroot using a generic ARM64 linker under QEMU. The complete native build and fault-injection lifecycle qualification remained HOLD. Independent Sol High review recorded scope and release HOLD.

Evidence: /mnt/commadrive/c7-r1-r5-20261016/results/C7_R1_R5_FINAL_MACHINE_VERIFIED.json.

### 3.4 F1–F6: toolchain, broader Honda inventory and test parity (17 October)

F1 compiled the real Params implementation object and four Cap'n Proto generated ARM64 schema objects and linked a cereal DSO. At that stage it used **generic** Cap'n Proto 1.0.1 developer files, not the precise lockfile-specified 1.0.1.post98 artifact. F1 exact SDK remained HOLD.

F2 and F3 honored the gate: no full seven-group rebuild or application test. Four existing generic ARM64 Params cases passed, but the native module was **pre-existing** and therefore did not prove a freshly rebuilt C7 runtime.

F4 expanded Honda coverage: inventoried **8 archives, 916 rlog entries and 879 unique logical segments**. Bounded 192-entry sample (179 unique) contained **228,146 real model profiles**, **4,157 predicted tight curves**, and **593 tight samples with car speed over 10 m/s**. This resolved lack of higher-speed *sample coverage*, not braking-safety evidence.

F5 distinguished old mirror coverage from true source parity. The initially more faithful test overlay found 13 acceleration failures because synthetic selfdriveState was absent, and two Campaign A guard failures because assertions expected the old curvature source hash/clipping. Test-only fixes produced a fresh **26/26** focused pass and source-pinned 44-file regression **3,202 total; 3,127 pass, three inherited non-Honda fail, 72 skip, zero errors**. Independent read-only Sol High F6 review accepted scoped results and retained release HOLD.

Evidence: /mnt/commadrive/c7-f1-f6-20261017/results/F1_F6_FINAL_MACHINE_VERIFIED.json.

### 3.5 F7: exact package recovered, exception-linking fix and ordered Honda replay

**Exact dependency recovered:** locked ARM64 comma-deps-capnproto==1.0.1.post98 wheel, verified SHA-256:

**6cdf838a8d415ac71e1f52306624ab3ab6f27777f6ce89c0059c4129ea7b7f62**

It supplies native 1.0.1 tools, headers, AArch64 libcapnp.a and libkj.a. Using its actual components, the team built four schema objects and Params object, linked a new AArch64 cereal DSO, and passed QEMU dynamic loading against the target-runtime libraries.

Four additional freshly linked native C++ subsets passed ELF and QEMU loader checks: Params, messaging/IPC, pose and vehicle EKF. All are **component-level**, not complete production services.

A deliberate invalid-root Params fault injection aborted even though the C++ caller contained exception handling. Investigation found manually linked ARM64 shared libraries missing the **GNU_EH_FRAME** unwind program header. Adding **ld --eh-frame-hdr** repaired the isolated C++ exception path: rebuilt Params sync put/get/remove, 20 async writes/destructor and invalid-root recovery then passed, without any product Params source alteration.

Real Honda archived **sequential ordered-input** curve-target replay:
- Five segments and **5,998 valid model frames**.
- **457** higher-speed (<50 m radius, ego >10 m/s) predictions.
- At most approximately **−0.779 m/s** patched minus baseline target for those predictions.
- Maximum downward filtered target step **0.125 m/s each 50 ms**, compatible with the configured 2.5 m/s² target-slew bound.
- For **1,030** model-derived binding distances **at least 1 m**, **217** constant-deceleration estimates exceeded the nominal **0.3 m/s²** approach allowance; none exceeded 2.5 m/s² under this limited formula.
- **238 positive distances below 1 m** were excluded because division by near-zero distance yields a singular and physically misleading deceleration estimate.
- Persisted learned CurvatureData, all control activation/lead states, actual brake commands, vehicle response/road friction and dynamic engagement were **not** fully recovered. **Safety HOLD**.

Evidence: /mnt/commadrive/c7-f7-crossbuild-20261017/results/F7_FINAL_MACHINE_VERIFIED.json; log_replay/results/F7_SEQ_BRAKING_FILTERED_VERIFIED.json.

### 3.6 F8: seven-area ARM64 component build and MPC source regeneration (current)

F8 created a fresh isolated candidate, preserving the authorized curvature patch and test-only changes. Codex Sol High initially inventoried/implemented a host-native build, then encountered its usage limit. Host engineering continued directly with bounded scripts; **F8 independent Codex review remains pending**.

New, source-compiled linked **AArch64 ELF artifacts = 13**:

| Area | Freshly built artifact(s) | Scoped result |
|---|---|---|
| cereal | libcereal_f8.so | Native schema shared object / loader pass |
| Params | libparams_f8.so and openpilot/common/params_pyx.so | Python Params temporary-root lifecycle pass |
| messaging | libmessaging_f8.so and msgq/ipc_pyx.so | Isolated fake local ring send/receive pass |
| opendbc CAN/safety | libsafety_f8.so | Native safety state accessor and Python CAN parser/packer tests **50 cases + 491 subtests** pass |
| locationd | liblocationd_pose_f8.so | Deterministic finite pose model check |
| Rednose EKF | libekf_car_f8.so and rednose/helpers/ekf_sym_pyx.so | Vehicle model finite check with valid synthetic state, Python import pass |
| lateral / longitudinal MPC | libacados_ocp_solver_lat.so; libacados_ocp_solver_long.so; **two** acados_ocp_solver_pyx native wrappers | Native compilation, Python imports, constructors and a basic .solve() call returning status **0** each |

The candidate checkout had Acados solver binaries but **not complete generated solver C sources**. Generation in the isolated environment yielded 16 lateral and 18 longitudinal C files. The bounded source-build compiled 12 required lateral and 14 required longitudinal units, linked two new solver libraries and two newly generated Cython bindings, then verified ARM64 ELF, dependency linkage and loader behaviour.

Pinned target context: **AGNOS 19.8.1**, Python **3.12.3**, NumPy **2.3.3**, Cython **3.1.4**, Clang **18**, exact Cap'n Proto wheel (above). ARM64 linking uses --eh-frame-hdr. Some **external Acados/HPIPM/BLASFEO/qpOASES runtime libraries are pre-existing dependencies** and were not source-rebuilt in F8; their origin and acceptance remain open.

Both native MPC solver smoke tests ran under ARM64 QEMU with initial/default synthetic states and returned **status 0**, but **did not test actual lead-follow, tight curves, lateral comfort, numerical robustness across physical operating conditions or real braking trajectories**.

A first synthetic EKF check had nonfinite output due to invalid near-zero model parameters; the harness was corrected to a meaningful synthetic state, **not** by changing EKF production code.

Machine verifier recorded **13 artifacts; all seven named engineering areas contain tested source-built native components; 0/7 end-to-end release-qualification groups complete**. F8 did **not** produce a coherent validated full SCons release build. Full multi-service application lifecycle, full native AGNOS runtime and physical hardware qualification are still HOLD.

Evidence: /mnt/commadrive/c7-f8-native-closure-20261017/results/F8_FINAL_MACHINE_VERIFIED.json and local tarball C7_F8_7_AREA_SOURCE_BUILT_ARM64_EVIDENCE_20261017.tar.gz.

## 4. Open issues and exact disposition

| ID | Issue | Result to date | Still required |
|---|---|---|---|
| 01 | Target runtime provenance | Five key AGNOS files hash-match | Full target sysroot/SDK and third-party ABI closure |
| 02 | Slow original QEMU builds | Replaced with Clang host-to-AArch64 compile + isolated ARM64 linker | Coherent complete SCons application build |
| 03 | Locked Cap'n Proto missing | Exact 1.0.1.post98 wheel SHA verified | Continue downstream consumer builds |
| 04 | C++ fault exception aborted | Linked --eh-frame-hdr, invalid-root now passes | Preserve unwind metadata across complete build and service fault coverage |
| 05 | Tight-curve target clipped at learning bound | Candidate raw-curvature speed correction and tests pass | Owner-approved real Honda target/braking safety |
| 06 | Force Stop jerk test expected obsolete 0.32 | Corrected test to existing source 0.20 | Do not claim new production brake tuning |
| 07 | Missing synthetic acceleration selfdriveState | Test-only fixture fixed | Maintain current-source test parity |
| 08 | Acados generated C sources missing | Regenerated two solvers and Python wrappers; status-0 smoke tests | External dependency provenance and realistic trajectory robustness |
| 09 | Incomplete native application | 13 new tested ELF artifacts; 0/7 fully qualified release groups | Entire dependency/service graph build and packaging |
| 10 | Full native service integration | Params/msgq/safety/EKF/MPC components pass scoped tests | Coherent manager-independent integration, lifecycle and faults |
| 11 | Other-make host test failures | Three (Chevrolet Bolt, Hyundai Palisade, Genesis G70) remain | Formal owner scope/risk dispositions |
| 12 | AOL skipped coverage | 72 inherited skips | Applicability, coverage and owner decisions |
| 13 | G02 inherited patch records | 39 dispositions remain open | Source-semantic review and approvals |
| 14 | Real Honda braking/curve behaviour | 5,998-frame ordered-input replay; 217/1,030 elevated limited deceleration estimates | Actual controller state, braking command/response, dynamics and safety signoff |
| 15 | Panda/CAN hardware | Earlier passive noOutput samples only | Current flashed firmware hash, arbitration, override, safety and rollback |
| 16 | Release device integration | No C7 device deployment | Separate controlled reversible parked qualification AFTER offline passes |
| 17 | Independent F8 review | Deterministic verifier pass; Codex limit hit | Separate independent Sol High and release-owner acceptance |
| 18 | interruptRateCan2 | Deferred offline diagnostic by user | Track as engineering deferral, NOT hardware safety waiver |

## 5. Remaining work packages and sequence

### WP-A — F8.1: reproduce and qualify the entire native application (**highest technical priority**)

1. Freeze source commit and complete pinned dependencies, including Acados, qpOASES, HPIPM, BLASFEO, NumPy/Cython, Python ABI and Cap'n Proto.
2. Build one **source-coherent complete SCons image/application layout** without counting stale precompiled Cython or solver shared objects.
3. Enumerate service-native products; obtain full ELF dependency closure, ABI versions, reproducible source/build manifests and package/install provenance.
4. Confirm **all seven groups** independently work with their real service consumers. Distinguish external accepted pinned libraries from genuine source-built modules.
5. Run integration **only when full build gate passes**. Maintain HOLD for any unproven group.

### WP-B — F8.1: native integration and fault resilience

- Fresh Params Python/C++ sync and async lifecycle, repeated writes/clear, invalid root, exception propagation, lock contention and recovery.
- Real IPC/native msgq ordering, loss/retry and bounded multi-service lifecycles in an offline non-actuating configuration.
- Offline Panda/opendbc CAN parsing and safety transitions only from recorded/synthetic data, not live bus commands.
- EKF/pose input validity, initialization, finite-value propagation, stable multi-step state progression and degraded signals.
- MPC representative longitudinal/lateral parameterization, lead-follow, obstacle, lateral curvatures and state/constraint validity; solver status, numerical residual and jitter.
- Full host-service startup/shutdown/restart/import graph, no vehicle control daemon actuation; document pass/fail by actual artifact SHA.

### WP-C — F9 Honda safety/comfort evidence

- Recover genuine controller learning, engagement, selected cruise, lead and weather/driver modes where logs support them. Identify unavailable state explicitly.
- Replay higher-speed ramps, roundabouts, close lead-follow and transitions with time-ordered data, control state and logged actual longitudinal commands.
- Test required deceleration versus physically achieved response and brake jerk; investigate elevated approach-deceleration estimates and near-zero distance cases.
- Define accepted pass thresholds with safety owner. Preserve C6-12 tuning unless evidence supports a narrow controlled correction.
- Do not infer safe roadway operation from solver status 0 or model-curvature mathematics.

### WP-D — F9/F10 acceptance and controlled hardware preparation

- Dispose of three other-make numerical test failures and 72 AOL skips with owners; close or formally accept 39 G02 patch discrepancies.
- Independent Sol High review of all exact machine manifests after availability. **No Astra.** Separate independent judgement from deterministic verification.
- Obtain actual Panda flashed firmware identity, CAN transmit ownership/driver override, disabled/safe-mode status and rollback proof under a formally approved physical test.
- Only then consider **reversible parked** qualification of C7, followed much later by separately authorized controlled driving validation.

## 6. Pause/resume instructions

**At the pause:** Ubuntu remote host was online; no ongoing Codex/F8 build was identified in the checkpoint process scan; C6-12 and protected C7 were clean. User requested a GitHub branch for a **side assessment**, not deployment.

**GitHub branch:** accord11g-dom-c7-f8-offline-assessment-20261017 (assessment snapshot based on protected C7 commit). Only six intended source/test files and this handover should be present. Verify with Git diff before giving a side reviewer access.

**On resumption:** compare reviewer findings to this exact source commit/branch. Keep the original baseline frozen. Reproduce the F8 13-artifact manifest against the pinned sources and continue WP-A and WP-B on a **new isolated workspace**, with WP-C and WP-D evidence preparation in parallel. Do not silently merge reviewer suggestions into protected C6-12/C7.

### Local evidence paths (NOT included in the GitHub push)

- /mnt/commadrive/c7-campaign-B-closure-20261016/ — B-stage ABI, generic native and passive Panda checks.
- /mnt/commadrive/c7-num-patch-review-20261016/ — numerical patch source and regression tests.
- /mnt/commadrive/c7-r1-r5-20261016/results/C7_R1_R5_FINAL_MACHINE_VERIFIED.json.
- /mnt/commadrive/c7-f1-f6-20261017/results/F1_F6_FINAL_MACHINE_VERIFIED.json.
- /mnt/commadrive/c7-f7-crossbuild-20261017/results/F7_FINAL_MACHINE_VERIFIED.json.
- /mnt/commadrive/c7-f7-crossbuild-20261017/log_replay/results/F7_SEQ_BRAKING_FILTERED_VERIFIED.json.
- /mnt/commadrive/c7-f8-native-closure-20261017/results/F8_FINAL_MACHINE_VERIFIED.json.
- /mnt/commadrive/c7-f8-native-closure-20261017/C7_F8_7_AREA_SOURCE_BUILT_ARM64_EVIDENCE_20261017.tar.gz.
- /mnt/commadrive/c7-f8-native-closure-20261017/mpc_completion/ — Acados sources, solver/native wrapper scripts, logs and manifests.

The local evidence packages may include large ELF binaries and user driving log references. They remain local, not published to GitHub. For any later code review, verify both code **and** the source-pinned evidence rather than assuming that GitHub alone proves target compatibility.

## 7. Final restrictions and decision

- Protected C6-12 and protected C7 must remain clean. Keep the working C6-12 installed until a properly qualified rollback-controlled release is authorized.
- No live CAN transmission, Panda firmware flash, vehicle controller actuation or road deployment from this branch.
- No broad upstream imports or weakening regression/policy safety tests for green counts.
- Use Codex Sol High when available for independent verification and bounded fixes; no Astra.
- The user-deferred interruptRateCan2 diagnostic is NOT a physical safety waiver.
- Explicit release owner acceptance is required before any parked or later driving qualification.

**FINAL SNAPSHOT: C7 source review branch only. ALL VEHICLE RELEASE GATES HOLD / NO-GO.**

# C20 R15–R19 combined software campaign — 28 November 2026

## Result and boundaries

Research checkout: `c20-r15-r19-full-software-qual-20261128`, R14 ancestor `7a10fb902449999054eaa4566f870656573e23b1`, current committed HEAD `4793b44feb814ec32c785468d8abfdba7a4e1bc1`. Frozen C19: clean `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`. Changes are confined to `tools/c20_accord11g_long_shadow/**`. All new compiler outputs and execution receipts are under `/home/jdkd/C20_RESEARCH_EVIDENCE_R15_R19_20261128`; no source checkout contains a newly built native binary. No network package install, push, device, vehicle, CAN, Panda, actuation, HIL, firmware or hardware work occurred. Active Alpha Long and road use remain **NO_GO**. Hardware gates are `EXCLUDED_BY_USER_FOR_SOFTWARE_CAMPAIGN` and `UNVERIFIED`.

The new result is **local native x86 execution of the unmodified frozen C19 Python `LongitudinalMpc.update()` and its generated Cython/ACADOS solver**, with deterministic synthetic inputs. It is neither full C19 `LongitudinalPlanner` message-driven execution nor authenticated vehicle replay. Independent re-review is pending. Once the remediation is committed on a clean tree, R19 can report `R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW` for offline research only; the current dirty tree is blocked.

## R15 native Python MPC

`native_python_build.py` explicitly built `libacados_ocp_solver_long.so` from C19 `acados_solver_long.c` and the 16 generated model, cost and constraint C files, then built the CPython 3.12 x86_64 `acados_ocp_solver_pyx` extension from the exact C19 generated wrapper C. Both GCC commands, source SHA-256 values, cached header-tree and library hashes, Python and compiler versions, ELF machine and `DT_NEEDED`/RUNPATH are in `native/python_build_receipt.json`. Both compiler exits were zero; output ELF machine is x86_64. The pinned original product `.so` is AArch64 and was not executed. The R14 `main_long.c` generated-C example remains separately classified `NATIVE_GENERATED_C_EXAMPLE`.

Dependency map:

| Layer | Source and role |
|---|---|
| Frozen Python MPC | C19 `openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/long_mpc.py`; actual `LongitudinalMpc`, `update`, `run`, `solver.solve`, and returned arrays. SHA-256 `3e2689f6c6366f98b2bfcfc1946074766585ed1e353a6fa22f9054934828d1ee`. |
| Generated wrapper | C19 `c_generated_code/acados_ocp_solver_pyx.c` built for host; SHA-256 of x86 extension `cecdc1367ca57ac8bb8fafbc2c9f8d4c4cefe3038ed7c3c4dc0c5170b4fc7da9`. |
| Generated solver | C19 `acados_solver_long.c`, `long_model`, `long_cost`, `long_constraints`; x86 solver library SHA-256 `b33b2b849383e0d8f4808603212e16f52240eabea473f0be2d42fde0e586f7f0`. |
| Host numeric dependencies | Cached x86 ACADOS, HPIPM, BLASFEO, qpOASES, CasADi; globally available NumPy. Their exact hashes or paths are recorded in the build and execution receipts. |
| Source constants | `ACCEL_MIN=-3.5`, `ACCEL_MAX=2.0`, takeoff max `3.5`, `DT_MDL=0.05`, lead tau `1.5`, radar offset `1.52` extracted with `ast.literal_eval` from frozen C19 source. Actual C19 model constants were imported. |
| Import-only stand-ins | `openpilot.cereal` log enum shape, `opendbc` package/interface import shape, takeoff preference import shape, realtime constant import shape, cloud logger and radard constant import shape. Exact modules are listed in `python_mpc_receipt.json` as `STUBBED_NONNUMERICAL_IMPORTS`; numerical values inside these shapes come from C19 source. No MPC class, native wrapper, solver result, NumPy function, trajectory, or prediction was stubbed. |

The dedicated `python_mpc.py` source import is narrowly allowed in `release_gate.py`'s source audit; other forbidden or dynamic imports remain rejected. The runner sets `PYTHONDONTWRITEBYTECODE`/`sys.dont_write_bytecode` before C19 imports. Three bytecode files produced during the initial prototype were removed, and frozen C19 `git status --porcelain --untracked-files=all` is empty.

Build receipt SHA-256: `ff5912cdcc399fbd81e0dd2673c394d594218dcbd84a2d1caaa9b99d9022ded0`. Remediated Python MPC execution receipt SHA-256: `bf69aedd22f4f143e6c6997e3ab64e84870f36315802c4321bdd6f2aadd0c561`. These establish local file consistency, not independent custody or product equivalence.

## R16 synthetic scenarios

Six source-bounded scenario definitions made 24 native Python MPC update/solve cycles. Each scenario starts a fresh solver, then warm-starts subsequent synthetic cycles. Each of the 24 genuine Cython `solve()` calls returned zero, exactly one call per cycle. The execution receipt records the native return before C19 can reset its mutable `solution_status`. The receipt contains rounded first five velocity, acceleration and jerk predictions, first obstacle and acceleration ceiling for each cycle. Scenario input SHA-256 is `d7ede3ffe648f8072ad56b304d3fb4567ac9acbf4467fa8b6a6c1bfcf5e15d1f`; remediated output SHA-256 is `61640ab72a448ad477ea620fc2cac00a4358877d773d9a7ae648ee724fdcf1da`.

| Scenario | Cycles | All statuses | Maximum absolute predicted acceleration in first five nodes (m/s²) |
|---|---:|---|---:|
| Steady ego input, no lead | 4 | 0 | 0.75069627 |
| Following | 4 | 0 | 0.14556015 |
| Lead cut-in then loss | 4 | 0 | 0.58105518 |
| Acceleration ceiling 0.5 m/s² | 4 | 0 | 0.50006224 |
| Braking, stop and go | 4 | 0 | 0.49639216 |
| Lead loss and recovery | 4 | 0 | 0.30706309 |

The acceleration cap trajectory peaks 0.00006224 m/s² above the nominal cap in the first five predicted nodes, consistent with solver tolerance; no hard physical constraint or safety conclusion follows. “Steady” means repeated constant ego input, not a cruise speed target: C19's MPC update uses obstacle and cost inputs but the full planner's cruise logic was not run. `modelV2` was intentionally absent, so model lead trajectory association remains unexecuted. No input or output was sent to a car or actuator.

The older C6/C12/MVL Boston material in this research package includes source-aligned historical summaries and a separate behavioral comparator, not an authenticated same-cycle C19 Python MPC replay. The required complete, pinned comparison inputs and receiver clocks were not established here. No C6/C12/MVL numerical equivalence or vehicle response comparison is claimed.

## R17 software faults

`software_faults.py` uses the existing `telemetry_gate.py` four-frame/150 ms model-history audit on sanitized synthetic cycles and a separate solver-status gate. Eleven cases cover baseline, stale model, stale radar, clock disagreement, unexpected reset, lead loss, driver override, input time reversal, corrupted capture digest, malformed inputs and injected nonzero solver status. The temporal fault cases remain `FAULT_LOCKED` after a following valid cycle. The injected solver failure tests receipt gating only; it does not modify the actual ACADOS solver. Fault receipt SHA-256 is `8c44bbed223def3e7b77739b9135bc479b2489a16b35e889c5a4facd0eee2be9`. Malformed and nonfinite input substitutions fail closed.

## R18 and R19 checks

The existing 92 host tests plus one new native reset regression passed: `Ran 93 tests ... OK`. `git diff --check`, the updated source audit and privacy/scope checks passed. The R19 gate verifies frozen C19 revision and cleanliness, research branch/R14 ancestor/clean committed scope, source audit, privacy scan, generated build receipt, Python MPC execution receipt, and exact reproducibility of the software fault report. The live gate currently reports `R19_BLOCKED_SOFTWARE_EVIDENCE` because the remediation is uncommitted. It reports all hardware verification as `UNVERIFIED`, full planner and authenticated replay as `NOT_RUN`, independent review as `PENDING`, and road/active use as `NO_GO`.

Independent review targets for the **host operator to initiate after implementation**:

1. Codex Extra High: verify source hashes and exact compiler argv against frozen C19; repeat x86 build/import/solve; inspect native ABI, source audit exception, stub boundaries, receipt tamper paths and no C19 file writes.
2. Windows OpenCode Qwen3-Coder 30B: review the same final diff, scenario provenance, fault state lock, gate classification, privacy and packaging exclusion; report environment limits if native Linux x86 execution cannot be reproduced on Windows.
3. Windows OpenCode Qwen2.5 Coder 14B: independent second code review of negative substitutions, dependency and status claims, documentation precision, and no hardware authorization; report environment limits explicitly.

The independent XHIGH review in `R18_XHIGH_REVIEW_FINAL.txt` identified three findings. This remediation captures the native solve return before C19 reset, checks R14 as an ancestor, and rejects malformed receipt shapes without an uncaught exception. A test-only injected nonzero return after a genuine zero native solve triggers C19 reset and remains classified `TEST_ONLY_INJECTED_SOLVER_FAILURE`; it is not evidence that the native solver itself failed. Additional substitutions cover hidden reset status, fake wrapper hash, absent input hash, wrong cycles, malformed JSON, and oversized JSON. The live gate remains `R19_BLOCKED_SOFTWARE_EVIDENCE` until these edits are committed cleanly; the clean-tree candidate path passes the automated test against committed HEAD `4793b44...` and genuine receipts. Final independent approval remains pending. The host operator will commit, request a new independent review, and package only after an exact clean committed SHA. No archive was created or pushed.

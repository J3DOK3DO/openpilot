# R19 offline research release recipe

This recipe permits only software research and a source-only archive. Active Alpha Long, road use and hardware remain `NO_GO`; hardware verification is `EXCLUDED_BY_USER_FOR_SOFTWARE_CAMPAIGN` and `UNVERIFIED`.

## Reproduce current local evidence

Run from `/home/jdkd/C20_ACCORD11G_LONG_SHADOW_20261125` with frozen clean C19 at `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`. The builder and runner write only under `/home/jdkd/C20_RESEARCH_EVIDENCE_R15_R19_20261128`. `verify` commands and module imports are read only; `build` and `run` are explicit operations. No network install is needed.

```sh
export PYTHONDONTWRITEBYTECODE=1
python3 -B -m tools.c20_accord11g_long_shadow.native_python_build build
python3 -B -m tools.c20_accord11g_long_shadow.native_python_build verify --expected-sha256 ff5912cdcc399fbd81e0dd2673c394d594218dcbd84a2d1caaa9b99d9022ded0
python3 -B -m tools.c20_accord11g_long_shadow.python_mpc run
python3 -B -m tools.c20_accord11g_long_shadow.python_mpc verify --expected-sha256 bf69aedd22f4f143e6c6997e3ab64e84870f36315802c4321bdd6f2aadd0c561
python3 -B -m tools.c20_accord11g_long_shadow.software_faults --write-external
python3 -B -m unittest discover -s tools/c20_accord11g_long_shadow/tests -q
python3 -B -m tools.c20_accord11g_long_shadow.r19_campaign_gate
git diff --check
git status --porcelain --untracked-files=all
git -C /home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124 status --porcelain --untracked-files=all
```

A rebuild may produce a different binary or receipt digest with another compiler/dependency environment; record the new hashes and verify against those actual local artifacts. Never relabel failed or absent native execution as passed. The remediated receipt records the actual Cython `solve()` return and one genuine native call per cycle. A nonzero return is retained even if C19 resets `solution_status`; test-only injected return values are labeled separately and cannot verify as genuine native success. The current result is a local `C19_PYTHON_MPC_NATIVE_X86_VERIFIED` synthetic execution, `FULL_C19_LONGITUDINAL_PLANNER_NOT_RUN`, and `AUTHENTICATED_VEHICLE_REPLAY_NOT_RUN`.

Each explicit rerun invalidates its prior accepted external receipt before work begins, and only a freshly verified successful MPC run replaces the invalid state.

## Independent review and source archive

R19 requires the R14 starting commit to be an ancestor of the current HEAD and the research tree to be clean. Before the host commits this remediation, the live gate correctly reports `R19_BLOCKED_SOFTWARE_EVIDENCE`; after a scoped clean commit, rerun it and require `R19_OFFLINE_RESEARCH_CANDIDATE_PENDING_INDEPENDENT_REVIEW`. The independent XHIGH review findings have been remediated locally, and final independent approval remains pending. The host operator reviews and commits only `tools/c20_accord11g_long_shadow/**` on `c20-r15-r19-full-software-qual-20261128`, records the exact new SHA, obtains the three separate independent reviews scoped in `R15_R19_COMBINED_REPORT.md`, resolves findings, reruns the checks, and creates an archive only from the final clean committed tree. If the linked worktree index cannot be written, leave permissions unchanged for the host operator.

```sh
git status --porcelain --untracked-files=all
git rev-parse HEAD
python3 -B -m tools.c20_accord11g_long_shadow.bundle --repo . --output /home/jdkd/C20_RESEARCH_EVIDENCE_R15_R19_20261128/c20_r19_offline_research.tar.gz
python3 -B -m tools.c20_accord11g_long_shadow.bundle --repo . --verify /home/jdkd/C20_RESEARCH_EVIDENCE_R15_R19_20261128/c20_r19_offline_research.tar.gz
```

`bundle.py` requires a clean committed tree and only includes the research source subtree. It rejects native binary suffixes, raw log/media suffixes, VIN patterns, GPS value fields and private route stems. The external solver binaries, receipts and scratch logs are never archive members. The operator must also review the archive manifest for private identifiers before distribution. No hardware action, push or road release follows from this source archive.

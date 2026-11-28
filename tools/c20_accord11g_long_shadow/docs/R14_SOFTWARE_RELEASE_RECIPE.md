# R14 offline software research handoff

Run from `/home/jdkd/C20_ACCORD11G_LONG_SHADOW_20261125`. The only intended release is a source-only research archive after the host operator makes an exact clean commit and obtains an independent review. There is no device, vehicle or actuation release in this recipe.

## Reproduce the native generated example

The cached dependency path below is host-specific. `build` is the only command that compiles or executes C. It writes a bounded binary, logs and receipt to the user-designated external evidence directory. `verify` is read-only and requires the independently recorded exact receipt SHA-256; a digest supplied by the same operator establishes consistency only.

```sh
export C20_C19=/home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124
export C20_ACADOS=/home/jdkd/.cache/uv/archive-v0/JcZjHB62Lhiu78Ir/comma_deps_acados-0.2.2.post103.data/purelib/acados/install
export C20_R14_EVIDENCE=/home/jdkd/C20_RESEARCH_EVIDENCE_R14_SOFTWARE_20261128
PYTHONDONTWRITEBYTECODE=1 python3 -B -m tools.c20_accord11g_long_shadow.native_host build \
  --repo "$C20_C19" --acados "$C20_ACADOS" --output "$C20_R14_EVIDENCE/native_x86"
sha256sum "$C20_R14_EVIDENCE/native_x86/native_receipt.json"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m tools.c20_accord11g_long_shadow.native_host verify \
  --repo "$C20_C19" --acados "$C20_ACADOS" --output "$C20_R14_EVIDENCE/native_x86" \
  --expected-sha256 07452c960a0fd47211d26a2b81bcc135cafbf794a3a136e17c3db709fcc60b4c
```

The receipt digest above identifies this run. Rebuilding can change wall-clock timing in `run_stdout.log`, and therefore its digest; use the newly observed receipt digest when verifying a new run. The source archive must not contain `main_long_x86`, logs or the external receipt.

## Check the software campaign

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m tools.c20_accord11g_long_shadow.telemetry_gate \
  --manifest tools/c20_accord11g_long_shadow/fixtures/r10_r12_synthetic_manifest.json \
  --capture tools/c20_accord11g_long_shadow/fixtures/r10_r12_synthetic_capture.json
PYTHONDONTWRITEBYTECODE=1 C20_C19_REPO="$C20_C19" python3 -B -m unittest discover \
  -s tools/c20_accord11g_long_shadow/tests -q
PYTHONDONTWRITEBYTECODE=1 python3 -B -m tools.c20_accord11g_long_shadow.campaign_gate \
  --repo . --c19 "$C20_C19" \
  --manifest tools/c20_accord11g_long_shadow/fixtures/r10_r12_synthetic_manifest.json \
  --capture tools/c20_accord11g_long_shadow/fixtures/r10_r12_synthetic_capture.json \
  --run-tests --check-c19-receipt \
  --native-acados "$C20_ACADOS" --native-output "$C20_R14_EVIDENCE/native_x86" \
  --native-sha256 07452c960a0fd47211d26a2b81bcc135cafbf794a3a136e17c3db709fcc60b4c
git diff --check
git -C "$C20_C19" status --porcelain
git -C "$C20_C19" rev-parse HEAD
```

Expected for this source state: 82 tests pass, source audit and C19 prebuilt receipt pass, native x86 evidence is `LOCAL_EVIDENCE_CONSISTENT_UNAUTHENTICATED`, synthetic join passes, original AArch64 native binary remains unexecuted, full C19 planner replay is `NOT_DONE`, current vehicle capture and independent custody remain unverified. All hardware gates remain `EXCLUDED_BY_USER_FOR_SOFTWARE_CAMPAIGN` and `UNVERIFIED`. Active and road decisions remain `NO_GO`.

## Host operator commit, review and archive

1. Review the diff and confirm every changed path is under `tools/c20_accord11g_long_shadow/**`. Check the stable C19 checkout is clean at `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`. Stage and commit only the research tree on `c20-r14-r10native-r11replay-r12software-20261128`; record the exact new SHA. If the shared `.git` index lock blocks staging, leave its permissions unchanged and have the host operator perform the commit.
2. Obtain independent review by Codex GPT-6-Sol XHIGH **after that commit**. Ask it to inspect native source and receipt verification, temporal/fault audit behavior, private-data scope, tests, exclusions and the integrated gate. Apply any remediation in the same research tree, rerun checks and commit a new exact SHA before packaging.
3. With the final tree clean, create and verify only the source archive in the external R14 evidence directory:

```sh
git status --porcelain
git rev-parse HEAD
PYTHONDONTWRITEBYTECODE=1 python3 -B -m tools.c20_accord11g_long_shadow.bundle \
  --repo . --output "$C20_R14_EVIDENCE/c20_r14_software_research.tar.gz"
PYTHONDONTWRITEBYTECODE=1 python3 -B -m tools.c20_accord11g_long_shadow.bundle \
  --repo . --verify "$C20_R14_EVIDENCE/c20_r14_software_research.tar.gz"
```

`bundle.py` rejects a dirty tree, symlinks, raw log/media suffixes and private route stems, and writes an exact commit and per-file digest manifest. No push, installation or vehicle operation follows from this archive.

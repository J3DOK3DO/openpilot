# R13 release preparation — 2026-11-28

**Chosen target: offline research candidate only.** The synthetic, audit-only CLI works on this host. It is not HIL-ready, device-ready, installable, display-integrated or an active Alpha Long release. A future nonactuating display candidate needs a real ARM64 product build and receipt, default-off UI/source integration, hardware validation and independent review. Active Alpha Long and public-road use remain **NO_GO**.

## Current acceptance matrix

| Gate | Evidence / result | Release consequence |
| --- | --- | --- |
| R10 source pin | [C19 platform receipt](../fixtures/r10_platform_receipt.json), exact `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`; every pinned source and AArch64 artifact digest, ELF architecture, linked tree and model option checked | Source inventory complete only when the supplied checkout matches; native C19 cycles **not executed** |
| R11 current capture | [Synthetic fixture](../fixtures/r10_r12_synthetic_capture.json), [manifest](../fixtures/r10_r12_synthetic_manifest.json), [R9 historical report](R9_CAMPAIGN_REPORT.md) | Timing validator implemented; zero authenticated current-car captures |
| R12 read-only audit | [Combined report](R10-R12_COMBINED_REPORT.md), `telemetry_gate.py`, negative tests | Synthetic faults exercised; no HIL or vehicle safety qualification |
| A1 radar/CMBS ownership | [Risk acceptance](risk_acceptance.md) and C19 interface trace | No exact-car hardware evidence; **NO_GO** |
| A2 CAN2 startup | C19 source trace and historical research only | No ignition/relay/brownout HIL evidence; **NO_GO** |
| A3 Panda/brake | No safety or control source changes | No transmit or brake-path qualification; **NO_GO** |
| A4 override/lead faults | Offline negative tests only | No independent HIL or vehicle fault acceptance; **NO_GO** |
| A5 release/legal | C19 baseline receipt can be checked; C20 ARM64 build absent | No product receipt, rollback drill, insurance/regulatory approval; **NO_GO** |

## End-to-end research gate

Run from the C20 root. It executes the test suite only with `--run-tests`, and the C19 prebuilt receipt checker only with `--check-c19-receipt`. Without those flags the JSON records `NOT_RUN` rather than implying execution.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.campaign_gate \
  --repo /home/jdkd/C20_ACCORD11G_LONG_SHADOW_20261125 \
  --c19 /home/jdkd/accord11g_c19_stable_c82_minimal_release_20261124 \
  --manifest tools/c20_accord11g_long_shadow/fixtures/r10_r12_synthetic_manifest.json \
  --capture tools/c20_accord11g_long_shadow/fixtures/r10_r12_synthetic_capture.json \
  --run-tests --check-c19-receipt
```

The JSON distinguishes the original C19 receipt from any nonexistent C20 product build receipt. It checks branch, baseline SHA **and pinned artifact bytes**, recursive source gate, `git diff --check`, default-off shadow configuration, a bounded per-file archive privacy scan, solver platform status and synthetic telemetry. A supplied telemetry manifest/capture must have `PASS_SYNTHETIC_ONLY` quality and a matching capture digest before R12/R13 can receive working candidate labels. Invalid supplied telemetry yields `BLOCKED_TELEMETRY`; absence is reported as `NOT_SUPPLIED`, with a separate conservative `offline_research_release_decision`. Neither state authorizes release. Even a passing research gate keeps `archive_ready=false`, current custody unverified, device display blocked and active/road `NO_GO` until later steps are actually completed.

For a different host, pass its C19 path through `--c19`; `--run-tests` forwards that path to the test suite as `C20_C19_REPO`. Direct suite invocation can use `C20_C19_REPO=/path/to/pinned/C19`. If the external checkout is unavailable, exactly two C19 integration tests skip and the other 74 run. With the pinned checkout present, all 76 tests run without skips. Source artifact matching ignores host Python packages and readelf version while displaying those host facts separately.

## Exact host release handoff after independent review

1. Review only `tools/c20_accord11g_long_shadow/**`. Confirm original stable C19 remains exactly `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`, and no production or safety source changed. Inspect all new Python recursively and rerun the commands above. Check no VIN, GPS, raw CAN, logs, route IDs or credentials occur in the candidate files.
2. Review `platform_receipt.py` and the pinned fixture against `readelf -d` and SHA-256 of actual C19 artifacts. Check the `SOURCE_ARTIFACT_ONLY` and external `REFERENCE_MATCH_UNVERIFIED` labels cannot be promoted to verified execution. Check malformed, oversized or substituted receipts fail closed.
3. Review `telemetry_gate.py` fault behavior, drive boundaries, exact service source/receipt ordering, gap statistics, stale/future samples, radar `mdMonoTime` selection from bounded model lead history, lead-history digest alignment, driver override and source conflicts. Confirm no acceleration proposal, CAN/API transport, Panda binding or vehicle output exists. The synthetic pass is only a test of the validator.
4. Review the R10–R12/A1–A5 matrix above and record each missing external item as pending. The owner risk acceptance is separate from independent safety acceptance.
5. If accepted, the host operator stages and commits **only** `tools/c20_accord11g_long_shadow/**` on `c20-r10-r12-combined-r13-prep-20261128`. Record the resulting exact Git SHA. Do not loosen the shared Git index or mount permissions if staging is blocked.
6. Only from that exact **clean** commit, use existing `bundle.py` to create the research archive in `/home/jdkd/C20_RESEARCH_EVIDENCE_R10_R13_20261128`. It embeds per-file SHA-256 and exact commit SHA, checks the raw manifest bytes for private route stems before parsing, rejects unknown manifest metadata, raw log/media suffixes, symlinks and nonregular entries, and verifies the archive plus sidecar. Do not package a dirty tree or raw driving data. No push or installation.

Proposed host-only archive command, after the commit and clean-tree check:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.bundle \
  --repo /home/jdkd/C20_ACCORD11G_LONG_SHADOW_20261125 \
  --output /home/jdkd/C20_RESEARCH_EVIDENCE_R10_R13_20261128/c20_r13_research.tar.gz
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.bundle \
  --repo /home/jdkd/C20_ACCORD11G_LONG_SHADOW_20261125 \
  --verify /home/jdkd/C20_RESEARCH_EVIDENCE_R10_R13_20261128/c20_r13_research.tar.gz
```

## Future display and active blockers

For a future **nonactuating** display candidate, a separate approved change would need a source integration design that cannot enable Long or vehicle transport, an actual ARM64 build, matching product receipt, disabled-by-default UI verification, hardware sanity and rollback drill from pinned C19. None exists in this campaign; no installer is provided. For **active** Long, independently authenticated current-car/firmware capture, exact input cycles and native execution, A1–A4 HIL safety evidence and A5 legal/release acceptance remain required. The accepted potential CMBS/FCW/AEB loss is a recorded research tradeoff, not proof of safe braking or permission to suppress radar.

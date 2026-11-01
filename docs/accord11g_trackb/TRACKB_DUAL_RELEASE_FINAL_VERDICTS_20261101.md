# Dual-release final verdicts — 2026-11-01

Vehicle: 2025 US Honda Accord 11G Hybrid, Bosch-C / CAN-FD. Platform: StarPilot Dom 7.0. Base `d88e2918021908b260bc0d4c427277037bfd1019`. Branch `accord11g-dom7-trackb-unified-integration-20261101` (final commit SHA recorded in the final engineering report and continuation file).

| Dimension | Verdict | Basis |
| --- | --- | --- |
| **Track A**: stock ACC + lateral | **PRESERVED (source + host/ARM64 tests)** | No production file changed vs `d88e2918`; `5fa8b2ed8` is an ancestor; Track A tests pass (final report) |
| **Release A**: publication as engineering branch | **PUBLISHABLE: non-production engineering candidate** | Source gates pass; independent review R2 APPROVE WITH FINDINGS (P3 fixed) |
| **Release A**: comma installation candidate | **NOT ESTABLISHED** | Gates 4 (installed AGNOS/Panda/hardware evidence) and 5 (known-good install record) HOLD; full ARM64 release build and packaging NOT_RUN |
| **Release B**: source engineering (non-actuating scope) | **COMPLETE for everything specifiable without B1** | Subordinate fail-closed controller, schema binding, authorization gate bound to evidence artifacts, RELEASE denial incl. MVL CAN-FD-long table, OEM forwarding tests, B1–B6 register |
| **Release B**: OEM protocol (B1) | **HOLD** | No authenticated OEM or target evidence |
| **Release B**: Panda RELEASE | Host **PASS** / target **HOLD** | Host libsafety only; flashed firmware identity unknown |
| **Release B**: device/AGNOS (B4) | Source **PARTIAL** / installed **HOLD** | Pinned image hash = `agnos.json`; device backups absent |
| **Release B**: isolated bench (B5) | **NOT_RUN → HOLD** | No bench, equipment or authorization; procedure drafted |
| **Release B**: controlled vehicle (B6) | **NOT_RUN → HOLD** | Requires B1–B5 and independent oversight; plan drafted |
| **Release B**: operational classification | **ENGINEERING COMPLETE / PHYSICAL QUALIFICATION HOLD**. Actuation disabled; no code path exists | All physical gates outstanding |
| Vehicle deployment authorization | **NONE** | A GitHub push is not deployment approval |

## Independent review record

| Round | Reviewer | Scope | Verdict | Findings → disposition |
| --- | --- | --- | --- | --- |
| d88e2918 (prior) | Codex | mandatory-final delta | REJECT | 3 findings fixed in `d88e2918`. **Re-reviewed and closed in R1** (tester-present `02 3E 80`, Int16 experiences + all 510 words, ordinal/type pinning) |
| R1 | Codex `gpt-5.6-terra`, read-only, separate session | `d88e2918^..912a49920` | REJECT | P1 gate fail-open on fabricated/wrong-class evidence → per-requirement kinds, artifact-hash resolution, author ≠ reviewer, measured-identity binding. P2 vacuous register-hash test → replaced. P2 isolation `/test_` bypass → exemption removed. P2 forwarding statement → corrected. P3 "no Bosch-long code" → corrected. P3 AGNOS reproducibility → disclosed |
| R2 | same | `915485486` remediation | APPROVE WITH FINDINGS | P3 "single accepted kind" wording → fixed after R2 (doc-only; not re-reviewed) |

Supplementary review by this Claude session found and fixed one more defect: the whole-repo isolation scan skipped 1,287 sparse-checkout files. A mutation test showed the old scan missed an index-only reference and the new one catches it.

## Exactly missing evidence for an operational Release B

1. Authenticated OEM evidence for 2025 US Accord Hybrid: ACC command owner and frames, CMBS/AEB precedence, a radar/CMBS-preserving owner-transition mechanism, and bus topology/arbitration (B1).
2. A Panda safety table derived from (1), independently reviewed. Flashed RELEASE firmware hash and provenance (B3).
3. Passive read-only device measurement: AGNOS system hash/slot, Panda firmware, current `/data/openpilot` commit and Params backup (B4, Release A gates 4/5).
4. Isolated-bench execution of B5-1…B5-8 under separate authorization (B5).
5. Independently overseen controlled-vehicle validation (B6).
6. Full ARM64 release build and packaging of the exact commit (Release A gates 1/2).

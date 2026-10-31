# Track B — independent Qwen source review and adjudication

Source parent: 27295eabc179a888e52d593cf722243cc8fa1fdc.
Original isolated commit: 0eff035f48e233ea55f0990e3fbb9d75a9fb12db.
Reviewer: OpenCode 2.1.4 / local Ollama Qwen3-Coder 30B on authorized Windows system, separate from the Ubuntu implementation process.
Final reviewed post-remediation source archive SHA256: fee10786f7afa0d8757eace348b3e8d5a2283c0b9d912aea709c57a75201f731.
Review logs kept in /mnt/commadrive/DOM7_V4_AUTOMATED_20261030/work/trackb-offline-artifacts-20261031: QWEN3_REVIEW_OUTPUT.log, QWEN3_FINAL_REVIEW.log, QWEN3_FINAL_CANDIDATE_VERDICT.log.

## Demonstrated and corrected issues

1. OwnershipEvidenceModel._valid_shape evaluated list/dict relay_state_claim or topology_claim by set membership and threw TypeError. Now verifies exact string type before membership; malformed input returns STATE_WITHDRAWN. Added explicit list/dict/None and recovery regression cases.
2. BrakeHoldContract.step retained the earlier _braking=True hysteresis latch after driver override, ACC/AEB withdrawal, invalid or duplicate decision, causing the next safe below-entry/above-release sample to enter abstract braking. Every withdrawn outcome now invokes _withdraw, clearing _braking. Added independent regression sequences.

## Other findings and evidence-based adjudication

- Reported string-validation weakness after the correction: unsupported; explicit type guard precedes membership.
- Reported equal-time reverse-clock issue: unsupported; only strictly decreasing time is rejected. Added positive equal-time and negative reversed-time regression cases.
- Reported ambiguous inclusive hysteresis: unsupported; entry uses <=, release uses >= after entry branch. Added boundary and collapsed-threshold regression cases.
- A monotonic source-only observation cannot authenticate age freshness or a physical radar relay. Wording in the migration matrix was narrowed accordingly.

## Final source acceptance

Research selected: 158 passed. Expanded native/current-source Honda and RELEASE-denial selected tests: 211 passed. Ruff PASS, Python compile PASS, git diff --check PASS, deterministic DBC source dictionary regeneration PASS.

The final independent Qwen3-Coder assessment was PASS for offline research publication. This is NOT a functional-safety certification, proof of real CAN command semantics, permission for active Bosch-C longitudinal operation, or evidence of OEM AEB/CMBS preservation. All physical device and vehicle qualification remains HOLD.

Production openpilot, opendbc, Panda safety, firmware, CAN/UDS, vehicle controller and DBC files remain untouched.

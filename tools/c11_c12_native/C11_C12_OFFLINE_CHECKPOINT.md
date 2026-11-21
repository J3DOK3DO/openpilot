# C11+C12 combined native product closure — OFFLINE CHECKPOINT (NO-GO)
Date: 2026-11-21 UAE.
Vehicle target: Honda Accord 11th Generation Hybrid, Bosch-C / Comma 4, Dom 7.0.
This is an offline product-build provenance checkpoint only. NOT a release, installation certificate, Panda safety approval, or permission for on-road use.

## Exact source
Source commit built: `586da6b91ffb43e2a1e114072104b694d3c8a2b3`.
Stage: `/tmp/c10_native_build/stage`, source HEAD matches. No source code, controls, Panda firmware, QCOM model inputs, safety authorization, or `prebuilt.json` modified in C11/C12.
Branch: `accord11g-dom7-c11c12-native-product-release-20261121`.
Build target set: `openpilot msgq_repo opendbc_repo/opendbc/can rednose_repo/rednose`.
This document itself is a later documentation-only commit; it must not be confused with the compiled source commit or used to fabricate a same-commit prebuilt receipt.

## Actual C11 build
- Genuine AGNOS 20.5.2 sysroot, source-manifest authenticated in C10, retained under `/tmp/c10_agnos2052/sysroot`; it is NOT proof of the device-installed AGNOS/Panda identity.
- C10 QEMU-only SCons continuation was interrupted with a recorded exit 137 for performance cutover, not counted as success.
- Tested a mixed toolchain: **x86_64 Clang 18.1.3 cross-compiling AArch64 objects** using the pinned target headers/sysroot, AArch64 Clang linking inside a networkless ARM64 Docker container. Independent isolated object and executable smoke tests produced real ELF64 AArch64, no vehicle-facing execution.
- Final bounded full native SCons graph **100.0% and exit 0** at parent commit `586da6...`. Build log `C11_C12_SCONS_hybrid_product.log` SHA-256 `4391fa9076bc12dab90dfbf43a7bce6e3e2cd1b2e2073d198d3afcbf7eaaefea`.
- Output inventory: 221 ELF/archive/QCOM files, 123 updated in C11, 66 additional entries, 50 changed versus preserved C10 artifact inventory, 105 unchanged, zero missing baseline keys. **152/152 ELF files were AArch64**.
- Freshly linked examples: `pandad`, `camerad`, `loggerd`, `encoderd`, `libparams_c.so`, `libcar.so`, `libpose.so`, `libacados_ocp_solver_long.so`, and IPC. Outputs are hashed and provenance distinguished from copied inputs in `C11_C12_NATIVE_ARTIFACTS_FINAL.json`.
- AArch64 loader `--list` checks against the verified sysroot completed with exit 0 for six representative targets including `pandad`, `camerad`, `loggerd`, `encoderd`, car-location and longitudinal solver libraries. The FFmpeg libraries are provided by the pinned ARM64 development venv; acados vendored copies are present in the staged build. This is not device execution.
- Fresh targeted Honda Python safety regression: **190 passed, exit 0**, post-build on isolated ARM64 Docker. Previous C10 native C safety and AOL tests are reused as historical evidence only; source unchanged. No vehicle test was performed.

## QCOM verification and remaining gates
- `qcom_artifact_contract.verify` **exit 0**, five cached inputs, exact source-signature `db2ee948465d03d8180db65d537bdccc1a7211142d4e7ba296bb78548761d6f8`. This covers CACHED INPUTS only and not freshly generated Qualcomm binaries or target inference.
- No suitable Qualcomm KGSL device available on the host; **fresh producer and target GPU runtime unverified**, hardware qualification pending.
- `check_prebuilt_receipt.py` **exit 1** (matching receipt absent). Do NOT adjust `prebuilt.json` or publish a prebuilt release without authentic product+target receipt.
- External independent Qwen review was attempted on Windows, but initial CLI returned exit 1 and had unsupported claims (invented source filename, fail-closed NO_OUTPUT misinterpreted). Its verdict is **not accepted**; an API-based scoped review was attempted separately. There is no verified independent release PASS from this attempt.
- Physical CAN2 interrupt cause and `controlsMismatch` fault still require isolated/parked hardware qualification, including actual Panda safety firmware identity and CAN2 behavior; their recurrence alone does not establish harmlessness. No CAN transmit, flash, Comma installation, hardware actuation, or road test in this campaign.

## Next decision
C11 native compilation is completed offline. C12 cached-QCOM inputs and selected dependencies pass. C12 fresh QCOM producer/target inference, matching prebuilt receipt, independent release-grade source review, physical firmware identity, and CAN2/`controlsMismatch` safety remain **open**.
Prepare documentation-only release-candidate handoff, not deployable/on-road release; preserve manual-install rollback only as a documented user-accepted approach, not as a waiver of safety-critical validation.
Evidence root:
`/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C11_C12_COMBINED_20261121/`.

# C20 R27 — Source-matched ARM64 installation candidate

Build date: 28 November 2026 (UAE). Source baseline: `7e1eea4ebc2c5b1760ea49988c35153951ebd07d`, derived from frozen C19 `a32dcc0a6e62a4e2a15d9ac4425424e598313c98`.

## Scope
- **Path A:** preserve frozen C19 factory Honda ACC and unchanged Honda/Panda/controller/safety source.
- **Path B1:** opt-in, read-only native C19 MPC shadow diagnostics. There is no manager autorun, CAN/Panda transmission, CarControl publisher, or experimental longitudinal actuator authorization.
- **Path B2:** active custom braking/acceleration is not qualified and remains **NO_GO**.

## Build evidence and limitations
The project's unmodified `./build 3` device-target workflow completed successfully in an isolated ARM64/QEMU environment using source-matched C19 build objects, with `COMMA_SCONS_SCRUB_MODE=none`. SCons revalidated the product dependency graph, imported source-matched QCOM artifacts, rebuilt Panda version-specific firmware, verified AArch64/QCOM product structures, and produced a refreshed protected-inventory `prebuilt.json` after checks. Exact command, logs, model provenance, and host environment records are retained externally in `/home/jdkd/C20_R27_EVIDENCE_20261128/`.

A successful native build and source review do **not** prove on-device boot, actual Qualcomm inference, real-car message ingest, ACC/LKAS regressions, stock AEB/FCW behavior, or physical safety. No device connection, CAN transmission, HIL testing, active Alpha Long, or road testing was performed. Debug-signed Panda firmware is an existing development configuration; this is **not a certified road-use release**.

## Device-independent checks required before publication
- The final committed `prebuilt.json` must pass `python3 tools/ci/check_prebuilt_receipt.py --revision HEAD`.
- The exact final commit must be clean and contain only the reviewed C20 source additions plus built artifacts and release documentation.
- Re-run mandatory R19 and R25 focused tests, verify output architecture, QCOM source identity, and review the signed firmware changes.
- Publish the exact Git commit by a verified Git transport; do not substitute a reconstructed commit hash.

## After publication
Manual clean installation and rollback can be prepared using the user-verified Comma 4 installer workflow. Parked-device boot/runtime/shadow acceptance is **NOT_RUN**; it must not be reported as passed or replaced by a software-only waiver. The shadow diagnostic must remain manually opt-in. All active longitudinal hardware/vehicle gates remain separate.

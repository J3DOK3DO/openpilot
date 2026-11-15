# C8.2 C7 native product dependency matrix

| Dependency | Current exact evidence | Remaining gate |
|---|---|---|
| Panda H7 main and bootstub | Fresh Cortex-M7 build, debug-signed main; hashes in `C82_C7_BUILD_MANIFEST.json` | Owner-controlled release certificate, exact final-commit rebuild, target variant/firmware identity and safety qualification |
| Panda source protection | Current Honda header SHA `44decb9c4...`; no vehicle source edit in C7 | Independent review of 80/81, TX gating and actual device mode/param |
| AArch64 compiler | Cached offline container GCC 13.2.0 compiled AOL protocol test and params object | Complete linked product and target ABI/runtime library checks |
| AGNOS and sysroot | `launch_env.sh` pins 20.5.2; `/AGNOS` and `/opt/tici-sysroot` absent | Verified actual AGNOS identity and coherent source-matched headers/libraries |
| Root SCons dependencies | Container has Cap'n Proto CLI 1.0.1, but no SCons, acados, capnproto Python, ffmpeg Python or json11 Python | Exact supported build environment; no ad hoc dependency install in this campaign |
| QCOM stock captures | Older cache package has **five current targets**. `qcom_artifact_contract.verify` passed all five: identical source signature `db2ee948465d03d8180db65d537bdccc1a7211142d4e7ba296bb78548761d6f8`, recipes, sizes, hashes, QCOM pickle structure. Contract's retired driving target is absent. | Owner provenance of old capture package and complete product build; contract is not a cryptographic producer attestation or inference test |
| Model inputs | Current ONNX/compiler/camera sources match the cached five-target manifest; C8.1 to C8.2 changed no QCOM-relevant source paths | Check final source after freeze; no silent import of stale stock outputs |
| Product inventory | Existing checkout static validator passes inherited files | Fresh AArch64 binaries and model inventory from final commit, link/runtime checks, receipt and independent review |
| Release receipt | Committed `prebuilt.json` has prior protected inventory digest; exact C8.2 check exits 1 | Generate only after complete genuine final-commit build and validate against committed inventory |

The standard build scripts `scripts/native_device_build.sh` and `scripts/laptop_device_build.sh` are the supported full-build paths. The native script requires actual `/AGNOS`/aarch64. The laptop script requires a coherent sysroot and source-matched QCOM package, then validates native outputs before setting `prebuilt`. This offline campaign did not run either mutating full-build mode because their prerequisites are absent and source/output integrity would not be met. The five-target package is a useful **matched input**, not a release product.

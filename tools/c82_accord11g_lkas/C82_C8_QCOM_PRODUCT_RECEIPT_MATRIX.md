# C8 QCOM product and receipt matrix

The executable `tools.laptop_device_build.qcom_artifact_contract.verify` was rerun against **each** current target using the exact source at `0bdc95e610d4e8766438cbc7b0de2035247adcdd` and the old TrackAB cache package. It checked source inventory/command recipes, file size, SHA-256, and QCOM pickle structure. All five passed; source signature `db2ee948465d03d8180db65d537bdccc1a7211142d4e7ba296bb78548761d6f8` equals package manifest. Log: `qcom_verify.log`. This is consistency evidence for cached inputs, not proof of their producer or inference on target GPU.

| Active cached target | SHA-256 | Size bytes | Status |
|---|---|---:|---|
| `dmonitoring_model_tinygrad.pkl` | `7f7198c63d2d9b0d015cc860fdd836db50a4b9a75ab5d56cffd4d4eee5eb7b97` | 20,768,359 | Contract PASS |
| `driving_warp_1928x1208_tinygrad.pkl` | `54a0a68e9375820049ddc09d573e06f983a1b03de7dd0750f11fd3e7871be1ba` | 837,991 | Contract PASS |
| `dm_warp_1928x1208_tinygrad.pkl` | `5711934a11792e539e72ce68837b8bab802ee7bd2a909402fd35a4cc4efc382f` | 1,397,400 | Contract PASS |
| `driving_warp_1344x760_tinygrad.pkl` | `b8c123c5a040923169e1597d6ec0b6fb46c2d95b5c39dc0c71b0d5adf3441d02` | 838,183 | Contract PASS |
| `dm_warp_1344x760_tinygrad.pkl` | `79df4a2f9701aea9cf6c21477cae07852d7d8c245737599e6b72a1e6fa4fe88f` | 1,397,448 | Contract PASS |

The historical text claiming six current targets is stale: `driving_tinygrad.pkl` is retired by the executable contract and is absent from this five-target package. No cached artifact was copied into the C8 checkout or called freshly generated. The source-matched QCOM package remains an **input candidate** pending producer provenance and an exact-final-source product build.

| Product or receipt gate | C8 finding |
|---|---|
| Exact pinned AGNOS 20.5.2 image and coherent sysroot | **Missing** in inspected caches; prior 19.8.1 roots cannot qualify. |
| Locked ARM64 builder | Core cached image lacks Python modules; old read-only venv has matching core versions and nanobind is cached, enough for a generic root dry run. Full supported environment and target ABI still unproven. |
| Fresh full native binaries/models and ABI/runtime checks | **Not produced**; inherited checkout outputs and static `validate_artifacts.py` from C7 are not new C8 build provenance. |
| Panda H7 production release | C7 DEBUG main/bootstub compile is genuine but not release signed, final-commit-built, installed or physically qualified. |
| Receipt | `python3 tools/ci/check_prebuilt_receipt.py --revision 0bdc95e610d4e8766438cbc7b0de2035247adcdd` exited **1**: no matching build receipt. Inherited `prebuilt.json` and marker were left untouched. |

An issuance gate requires an independently reviewed exact final source, verified 20.5.2 image/sysroot and actual device OS identity, full authentic ARM64 product build with fresh protected inventory and QCOM source/producer validation, target ELF and runtime checks, owner release certificate and Panda identity, then generation and independent validation of a receipt for the actual built inventory. A documentation commit cannot contain its own SHA; resolve the final C8 commit after committing. Never refresh `prebuilt.json` merely to silence the validator.

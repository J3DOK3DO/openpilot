# C8.2 C9 QCOM and release gates

The 15 November `qcom_artifact_contract.verify` log reports all **five** active cached artifacts valid against entry source `58ef6e5fcea2d0d303855784e5f0dd58313941c4`; source signature `db2ee948465d03d8180db65d537bdccc1a7211142d4e7ba296bb78548761d6f8` matched the cached package. The old sixth target is retired. This is `INPUT_CONTRACT_ONLY`: it checks cached inputs, not new generation, target inference, or GPU compatibility. The log was recovered, not regenerated in this recovery.

| Cached artifact | SHA-256 | Bytes |
|---|---|---:|
| `dmonitoring_model_tinygrad.pkl` | `7f7198c63d2d9b0d015cc860fdd836db50a4b9a75ab5d56cffd4d4eee5eb7b97` | 20,768,359 |
| `driving_warp_1928x1208_tinygrad.pkl` | `54a0a68e9375820049ddc09d573e06f983a1b03de7dd0750f11fd3e7871be1ba` | 837,991 |
| `dm_warp_1928x1208_tinygrad.pkl` | `5711934a11792e539e72ce68837b8bab802ee7bd2a909402fd35a4cc4efc382f` | 1,397,400 |
| `driving_warp_1344x760_tinygrad.pkl` | `b8c123c5a040923169e1597d6ec0b6fb46c2d95b5c39dc0c71b0d5adf3441d02` | 838,183 |
| `dm_warp_1344x760_tinygrad.pkl` | `79df4a2f9701aea9cf6c21477cae07852d7d8c245737599e6b72a1e6fa4fe88f` | 1,397,448 |

The extracted AGNOS 20.5.2 sysroot lacks `libOpenCL.so.1` and `CL/cl.h`; its vendor library path is a synthetic fallback. The full root product build was not attempted and `pandad` did not complete. Other C8 native prerequisites, complete target runtime inventory, and device GPU validation remain open. C7 Panda H7 DEBUG evidence is not a release certificate or production signature.

On 17 November, read-only `PYTHONDONTWRITEBYTECODE=1 python3 tools/ci/check_prebuilt_receipt.py --revision 58ef6e5fcea2d0d303855784e5f0dd58313941c4` exited **1**, reporting no matching build receipt. This is expected `NO_GO`; `prebuilt.json` and its marker were not edited. A final-source product inventory, independent review, physical identities, and the release process are still needed. A C9 documentation commit cannot certify itself.

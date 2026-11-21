# C13 — offline verification and hardware handoff

This is an **offline read-only handoff**, not a set of instructions to flash, install or operate the car.

## Chain of evidence

Built-code commit `586da6b91ffb43e2a1e114072104b694d3c8a2b3` → C11 100%-complete SCons graph (`C11_C12_SCONS_hybrid_product.log`, exit 0) → `C11_C12_NATIVE_ARTIFACTS_FINAL.json` with 221 entries → `C11_C12_NATIVE_ELF_ARCHITECTURE_REPORT.log` with 152 AArch64 entries → `C11_C12_VERIFIED_AGNOS_LOADER_DEPS.log` → `C11_C12_FINAL_HONDA_ARM64_TESTS.log` with 190 passes → C11/C12 SHA-256 manifest.

The subsequent C11 documentation commit (`c89df8b...`) and C13 documentation commit are **not the compiled code SHA**. If executable or vehicle-control sources change after the build, invalidate the inherited native receipt and rebuild/retest before any release decision.

Evidence root: `/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C11_C12_COMBINED_20261121/`. C13 evidence root: `/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C13_SOURCE_ONLY_RCPREP_20261121/`.

## Commands permitted for offline verification

```bash
# Read-only identification of the local C13 documentation branch:
git -C /home/jdkd/c13_source_only_rcprep_20261121 status -sb
git -C /home/jdkd/c13_source_only_rcprep_20261121 rev-parse HEAD
git -C /tmp/c10_native_build/stage rev-parse HEAD

# Check immutable evidence inventory:
cd /mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C11_C12_COMBINED_20261121
sha256sum -c C11_C12_SHA256SUMS.txt
cat C11_C12_HYBRID_BUILD.exit
cat C11_C12_QCOM_CONTRACT.exit
cat C11_C12_FINAL_HONDA_ARM64_TESTS.exit
cat C11_C12_DOC_COMMIT_PREBUILT_RECEIPT.exit
```

The last receipt exits 1 by design because there is no verified matching release receipt. Do not rewrite `prebuilt.json` to satisfy it.

## Deferred independent target qualification worksheet

When qualified personnel and suitable isolated hardware are available, collect **observed** versions of AGNOS, Panda firmware and safety model/params, model hashes and GPU runtime; compare them to the frozen source inputs. Use authenticated target runtime results to establish actual fresh QCOM execution, rather than relying on the cached `.pkl` imports. Classify CAN2 startup interruptions and `controlsMismatch` from actual logs and safety-state transitions, and verify that the system refuses unsafe engagement.

Record source-commit identity, target firmware and model hashes, observation timestamps, commands, logs, reviewer and explicit pass/fail criteria. Leave any unexecuted check as NOT TESTED. Device qualification and on-road operation are outside C13.

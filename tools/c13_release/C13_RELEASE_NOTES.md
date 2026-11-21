# C13 — Dom 7.0 Accord 11G source-only pre-release candidate (NO-GO)

**Date:** 21 November 2026 (UAE)
**Vehicle context:** Honda Accord 11G Hybrid Touring (US specification), Bosch-C, Comma 4.
**Classification:** SOURCE-ONLY RELEASE PREPARATION; **not installable, not authorized for driving, not a safety approval**.

## Objective and source provenance

C13 packages the reviewed **offline build evidence** and future qualification requirements without changing the vehicle-control source, Panda firmware, models, installed device, or generated binaries.

- Exact source tree compiled in C11: `586da6b91ffb43e2a1e114072104b694d3c8a2b3`.
- Documentation checkpoint inherited from C11/C12: `c89df8b11ba9cc9d1ff707073570eced60d88c96`.
- C13 local branch: `accord11g-dom7-c13-source-only-rcprep-nogo-20261121`.
- The C13 documentation commit will be a different Git SHA from the **built source SHA** above. Do not claim binaries were built at that later documentation commit.

## Offline evidence accepted for preparation

The C11 full ARM64 SCons product graph reached 100% and exited 0. The C11 inventory reports 221 ELF/archive/QCOM entries (123 updated during C11), including 152/152 AArch64 ELF objects. Six representative authenticated AGNOS 20.5.2 loader dependency checks exited 0. The final C11 focused Honda Python regression on isolated ARM64 Docker passed 190/190. Five cached QCOM inputs passed their source-defined integrity contract. The QCOM source signature is `db2ee948465d03d8180db65d537bdccc1a7211142d4e7ba296bb78548761d6f8`.

The target AGNOS image was authenticated for **offline compilation**; installed Comma AGNOS, Panda release firmware, actual target GPU execution, and vehicle safety were not thereby established. Some auxiliary libraries used the pinned development venv, not a measured device filesystem. Earlier source builds and host tests are recorded as historical evidence only.

## Unwaived release barriers

**Deferred from this source-only preparation:** fresh QCOM GPU producer execution and target inference; physical CAN2 interrupts and `controlsMismatch` qualification; device firmware/AGNOS identity checks. They remain open before a vehicle-facing release. The independent Qwen attempts did not produce accepted safety-review approval. The exact-commit prebuilt receipt checker exits 1.

Repeated CAN2 faults in old builds **do not prove benign behavior**. Never disable interrupt monitoring, force lateral/longitudinal eligibility, override Panda safety, or treat stock ACC functioning as proof that a modified openpilot release is safe.

## Distribution and naming constraints

Use **“C13 source-only pre-release handoff — NO-GO / NOT INSTALLABLE”** on every export. Do not advertise, publish, or supply a one-click installation URL or a deployable binary package. Do not push, merge, or change protected branches as part of C13. Full code remains in the local Git worktree; the separate C13 evidence handoff archive contains documentation and checksums, **not runnable binaries**.

The next decision is an **independent release review and separately authorized isolated target qualification**. Manual reinstall of an earlier known branch is an owner-accepted rollback approach in principle, not proof of successful recovery or a waiver of safety testing.

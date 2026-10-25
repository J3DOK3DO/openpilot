# SUPERVISOR_V1 host qualification evidence

Status: **HOLD — host-only engineering, not deployable**.

This directory records the 2026-10-25 offline engineering run for G8-F12 RC3. No comma device, Panda, CAN interface, vehicle, network, SSH session, boot control, flash path, or application launcher was accessed. The frozen Honda baseline remains `bbb771a2fadf5af96f532e798846ba8171483e50` with launcher exit 78.

The readiness gate is `tools/g8_release/rc3_hardware_readiness_gate.py`. It only reads bounded files beneath an absolute, non-symlink evidence root. A normal no-evidence invocation is:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/g8_release \
  python3 tools/g8_release/rc3_hardware_readiness_gate.py \
  --evidence-root /absolute/path/to/captured-evidence
```

That invocation returns exit 78 and a canonical JSON HOLD. Future evidence evaluation additionally requires a relative `--manifest` and an exact externally pinned `--pinned-trust-policy-sha256`. The pin must be provisioned independently of the evidence bundle. The gate has no install or boot-operation option and its action-authorization fields are always false.

Use [LAB_QUALIFICATION_PLAN.md](LAB_QUALIFICATION_PLAN.md) for the safe sequence to obtain the missing physical evidence, [SCOPE_LIMITS.md](SCOPE_LIMITS.md) for claims and exclusions, and [HANDOFF.md](HANDOFF.md) for the engineering interface and evidence schema summary.

Synthetic fixtures are useful only for attacking the verifier. Even a complete, correctly signed synthetic set returns `HOLD_SYNTHETIC_EVIDENCE_NON_DEPLOYABLE`; it cannot become physical evidence by changing a label.

# C10 offline native checkpoint — 20 November 2026

This is a source-only evidence checkpoint. The code built was entry commit
`9b402bb796037372be7fff6844d22e624ae6fb4f` (tree
`8a99d0849fff313cc0cd55669eeb5390d5b689d9`). No control, Panda safety,
model, firmware, or prebuilt marker source was changed by this campaign.

The system image pinned by `openpilot/system/hardware/tici/agnos.json` was
downloaded anew. Compressed SHA-256
`990319694ce76972667458a5318f1e7d414d1895867fd5312dcbbf175a9dbf14`,
sparse SHA-256 `ec1b9569c784dd0be5d81eb613f59c1628baba3fd13f20ca7568c740a208c5c6`,
and raw SHA-256 `4f2aa50375915e52ea24ce069ccd92dcaf68d3fbd88959adc5f9e572457bdba2`
all matched. Its extracted `/VERSION` is `20.5.2`. This identifies the offline
image, not the installed device.

The isolated ARM64 build stage linked a fresh `pandad` with SCons exit 0,
SHA-256 `caffe4292ac282e9772c2f7e47bce3cf0165024364919f6677e85837379d6761`.
Its interpreter and every resolved needed library came from the verified
AGNOS 20.5.2 sysroot. A fresh ARM64 AOL protocol test linked and ran with
exit 0. Focused Honda tests passed: 190 ARM64 Python cases, 40 x86 native
debug safety cases, and one separately executed x86 release-denial case.

The full native product graph **did not pass**. Its first SCons attempt exited
2 when a locationd generator used a Python interpreter without NumPy. A
build-wrapper PATH repair let the next attempt pass that action, but the
second attempt reached a Cython script whose absolute shebang path was not
mounted; it ended at the bounded timeout with exit 137. A read-only mount
alias for the same pinned venv then made the exact Cython SCons target exit 0.
These local wrapper repairs are recorded in evidence and do not establish a
complete product graph. Freshly compiled outputs are separated from inherited
and copied inputs in the artifact manifests.

The five cached QCOM inputs passed their standalone source and hash contract.
No KGSL target GPU was available, so there was no fresh producer or target
runtime inference. The prebuilt receipt was absent. Independent source review,
physical firmware/AGNOS identity, and the separate CAN2 `controlsMismatch`
safety diagnosis remain open. Installation and road use are **NO_GO**.

Commands, exits, source hashes, artifact inventories, and the gate matrix are
under `/mnt/commadrive/DOM7_C612_FAULT_DIAGNOSTICS_20261113/evidence/C10_NATIVE_QCOM_20261120/`.

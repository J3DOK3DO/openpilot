# C14 — reviewer checklist and release decision

## Required pre-release source-only verification
1. Verify exact parent C13 SHA `966ffe5d175d59b3ce681249841aa0b3abfae443` and exact compiled-code SHA `586da6b91ffb43e2a1e114072104b694d3c8a2b3`. The later C14 documentation SHA is **not** the compiled source identity.
2. Compare C13 → C14 Git diff. All files must be under `tools/c14_mvl_gap/` with `.py`, `.md` or `.json` extensions. Reject any changes under `opendbc_repo/`, `openpilot/selfdrive/`, `panda/`, steering safety, models, UI hooks, `prebuilt.json` or any installation hook.
3. Run read-only unit tests. Verify negative gain/delay mutations are detected and source text is AST-parsed rather than imported or executed.
4. Check the local C13 and MVL pinned source identity: Pinned MVL opendbc must be `66a3ea89f42890a99237dbf20789f1ea3d3d5611`, not the later checkout `254d6f15`. If absent, do not claim matching values.
5. Verify the release tag, attachment hash and GitHub prerelease flag. Public attachment must be evidence/text only; no installer, native binary or raw route data.
6. Review claims against the existing C9 comprehensive comparison as **historical analysis**, not imported/qualified controller changes.

## Pending after publication — cannot be waived for vehicle operation
- Independent full source/Panda safety review on the final source and firmware build
- Genuine native device/AGNOS/Panda identity and reproducible release receipt
- Physical CAN2 startup fault classification, `controlsMismatch`, steering authority/CANCEL and fail-closed behavior
- Genuine Qualcomm GPU runtime/model-inference tests
- Verified recovery and rollback and separately authorized physical qualification

A scoped AI desk review can conclude PASS_SCOPED for the C14 **source-only documents/tests**. It is not independent human functional-safety approval.

**Default decision:** Source-only publication may proceed after scoped checks; **INSTALL NO-GO / DRIVE NO-GO**.

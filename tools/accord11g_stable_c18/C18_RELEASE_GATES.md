# C18 — Stable-based Honda 11G C8.1 integration release gates

**SOURCE CODE: reviewed-source candidate pending independent reviewer.**
**INSTALLATION, FLASHING, STEERING, ACC AND DRIVING: NO-GO until hardware and safety qualification.**

## Identity
- Target: J3DOK3DO/StarPilot `stable` / J3DOK3DO/openpilot `stable` base `404ef33a969c05297d8068fdf49b2c70e23e6697`.
- Work: `accord11g-stable-c81-integrated-offline-rc-20261124`.
- Imported behavior: Accord 11G CAN-FD topology as diagnostic bus selector, bus-0-only Honda FW/VIN with bounded retries, exact Honda Accord 11G firmware identity, unknown HOLD, Hybrid flag qualification with original PCM/safety word 80/81 preserved, LKAS pulse queue fails closed.
- Original C8.1 source: `9d2da330f6539beb5afb67867b28491526c0e1bd`. User previously road-tested that OTHER version over multiple routes. This does not qualify current C18 output.
- Actual C18 source was changed. Prior C11/C17 product-build evidence is **not** a C18 exact-commit build receipt.

## Fresh sanitized-fixture regression
- Synthetic public test fixture uses zero-filled fake CAN payloads of the correct documented DLCs and public Honda firmware catalog strings. **No private captured route data, raw CAN recording, VIN, or route identifier** is included in this public commit or its Git history.
- Cross-brand Honda/GM/Volvo/Chrysler/Mazda/Tesla selected host suite: **316 passed, 3 deselected** due to missing host `msgq`.
- Ford focused firmware identity: **3 passed after fixture sanitation**, plus 18 passes previously recorded by Codex prior to fixture change.
- Native Honda MVL safety: **3 passed**, no source safety edits.
- Prior broader Honda native file: **253 passed, 249 skipped, 10 failed due to missing host `msgq`**; these are blockers, not passes.
- Additional normal host collection for selected Honda topology needs current native `libparams_c.so`; not available on this host.
- Python compileall, Git diff whitespace, source path constraints: checked on current source.
- Never interpret a source-level test suite passing as real-vehicle engagement or steering authorization.

## Mandatory missing gates
1. Original physical `controlsMismatch` root cause needs fresh route `pandaStates` fault, safety model/word, can health and 11G source on current device; note multiple mismatch causes are possible.
2. Genuine C18 full native ARM64 product build and **matching C18 commit** receipt; `prebuilt.json` must not be manufactured.
3. Qualcomm target model producer and inference execution, installed AGNOS/Panda identity, full native Panda system verification.
4. Independent final source vehicle functional safety review (distinct from scoped AI code review), strict Panda interrupt watchdog and EPS safety preserved.
5. Parked non-actuating device regression and independently approved physical safety qualification; no direct car engagement until closed.
6. Verified rollback and installation and safe state under real faults.

**Decision if blockers remain:** publish clearly marked source-only GitHub **pre-release** with explicit `NO INSTALL / NO ROAD USE`. Do not provide `openpilot` quick-install instructions or pretend CI/native receipts passed. No changes to `stable` or `Dom`.

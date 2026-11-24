# C18 — Stable-based Honda 11G C8.1 integration release gates

**SOURCE CODE: R1 P0 correction pending fresh independent PASS_SCOPED review; source-only publication is on hold.**
**INSTALLATION, FLASHING, STEERING, ACC AND DRIVING: NO-GO until hardware and safety qualification.**

## Identity
- Target: J3DOK3DO/StarPilot `stable` / J3DOK3DO/openpilot `stable` base `404ef33a969c05297d8068fdf49b2c70e23e6697`.
- Work: `accord11g-stable-c81-integrated-offline-rc-20261124`.
- Imported behavior: Accord 11G CAN-FD topology and R1 plausible partial detector as diagnostic bus selectors, bounded passive extension, bus-0-only Honda FW/VIN with bounded retries, exact Honda Accord 11G firmware identity, unknown HOLD, Hybrid flag qualification with original PCM/safety word 80/81 preserved, LKAS pulse queue fails closed.
- Original C8.1 source: `9d2da330f6539beb5afb67867b28491526c0e1bd`. User previously road-tested that OTHER version over multiple routes. This does not qualify current C18 output.
- Actual C18 source was changed. Prior C11/C17 product-build evidence is **not** a C18 exact-commit build receipt.

## Fresh sanitized-fixture regression
- Synthetic public test fixture uses zero-filled fake CAN payloads of documented DLCs, deliberate malformed-DLC variants, and public Honda firmware catalog strings. **No private captured route data, raw CAN recording, VIN, or route identifier** is included in this public commit or its Git history.
- R1 cross-brand Honda/GM/Volvo/Chrysler/Mazda/Tesla selected host suite: **327 passed, 3 deselected** due to missing host `msgq`.
- Ford focused firmware identity: **3 passed after fixture sanitation**, plus 18 passes previously recorded by Codex prior to fixture change.
- Native Honda MVL safety: **3 passed**, no source safety edits.
- Prior broader Honda native file: **253 passed, 249 skipped, 10 failed due to missing host `msgq`**; these are blockers, not passes.
- Additional normal host collection for selected Honda topology needs current native `libparams_c.so`; not available on this host.
- Python compileall, Git diff whitespace, source path constraints: checked on current source.
- Never interpret a source-level test suite passing as real-vehicle engagement or steering authorization.

## R1 review fix

The independent read-only reviewer returned **FAIL_SCOPED / P0**: the original
10-ID signature lived only in the shared 0.12 s / 24-read probe, so a late,
missing or malformed frame could send an Accord into the generic OBD mux scan
associated with historical CAN2 interrupt and controlsMismatch faults. R1
adds a multi-ID Honda PT/camera plausibility threshold, at most 48 extra
passive reads ending by 0.65 s from discovery start, and bus-0-only Honda
firmware/VIN for both full and remaining plausible partial layouts. Unknown
or absent firmware stays MOCK/HOLD. Fully proven other-car firmware retains
its standard path. Synthetic production-path tests cover those cases and
non-Honda single-ID rejection. **Fresh independent PASS_SCOPED review is
required before any source-only publication.**

## Mandatory missing gates
1. Original physical `controlsMismatch` root cause needs fresh route `pandaStates` fault, safety model/word, can health and 11G source on current device; note multiple mismatch causes are possible.
2. Genuine C18 full native ARM64 product build and **matching C18 commit** receipt; `prebuilt.json` must not be manufactured.
3. Qualcomm target model producer and inference execution, installed AGNOS/Panda identity, full native Panda system verification.
4. Independent final source vehicle functional safety review (distinct from scoped AI code review), strict Panda interrupt watchdog and EPS safety preserved.
5. Parked non-actuating device regression and independently approved physical safety qualification; no direct car engagement until closed.
6. Verified rollback and installation and safe state under real faults.

**Decision if blockers remain:** after fresh independent PASS_SCOPED review, a clearly marked source-only GitHub **pre-release** may be considered with explicit `NO INSTALL / NO ROAD USE`. Until that review passes, publication remains on hold. Do not provide `openpilot` quick-install instructions or pretend CI/native receipts passed. No changes to `stable` or `Dom`.

## C18 R2 foreign Honda firmware fail-closed correction

The R1 independent review found that even a fully attributable foreign Honda firmware version returned OTHER, triggering the generic OBD-multiplexed sweep on plausible Accord CAN-FD wiring. C18 R2 **never permits generic CAN2 OBD switching once Accord-like topology has selected the dedicated bus-0 path**. Exact unique Accord firmware remains the only way to identify Accord automatically; contradictory foreign Honda FW returns MOCK/HOLD. Production-level tests cover both full and partial Accord-like observations. Native safety/watchdog unchanged.

## C18 R3 single-seed passive-delay coverage

R2 review found one matching 11G CAN ID in the initial short probe was insufficient to trigger the bounded 48-read passive extension; a full layout on read 25 could therefore encounter generic OBD mux. R3 uses single-ID seed solely to prolong **passive** observation, not to determine vehicle identity. If corroborating frames never arrive within bounds, other-car generic discovery remains available; if they do, a conservative Honda bus0 FW path handles the Accord. Tests cover both outcomes. No guarantee is claimed for arbitrary CAN silence or delays past the bounded discovery window; vehicle release remains NO-GO.

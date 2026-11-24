# C19 — SOURCE-ONLY PRE-RELEASE / NO INSTALL / NO ROAD USE

## Identity and decision

This branch selectively adapts the C8.2 Honda Accord 11G independent lateral safeguards on the published C18 parent `d146252ba988fb892155fef5ce71ab389908ccb1`. The stable origin is `404ef33a969c05297d8068fdf49b2c70e23e6697`. The read-only C8.2 reference is `20c86ebef9023845af0f62a946125700f7d51ce7`; the historical C8.1 GUI source is `9d2da330f6539beb5afb67867b28491526c0e1bd`. C8.1 route observations do not qualify C19. The source commit is the commit containing this report; its full SHA is recorded in the off-tree campaign evidence.

**Release decision: source-only review candidate, installation and road use HOLD.** No tag, push, installer link, physical vehicle test, Panda flash, VIN harvest or road actuation was performed. The branch requires independent final source and safety review before any source-only publication. It is not an installable product candidate.

## C8.2 gap matrix

| Guard | C18 baseline | C19 disposition |
| --- | --- | --- |
| Accord 11G Park/Reverse/Neutral and other non-Drive intent | Generic AOL could pause output but retain a latch across gear return | Clear Accord latch and neutral history whenever gear is not Drive; fresh in-Drive gesture required. Other Honda intent remains unchanged. |
| Low-speed independent steering | No Accord-specific fail-closed finite-speed latch veto | Veto standstill, invalid/negative speed or minimum, and `vEgo <= max(0.3, minSteerSpeed)` for independent latch only. Standard lateral remains under ordinary stock gates. |
| Cancel, ACC drop, fault | Generic latch and C18 queue behavior | Reapply Accord guards after configured Cancel action; clear on unavailable ACC and fault. Preserve C18 hybrid and queued-source logic. |
| Native 80/81 token | Existing Honda stock AOL C extension had token, pending, session, source age and initial startup handshake | Scope new native Drive gesture and zero-host-withdrawal retirement to 80/81 only. Clear host mask at gear departure/return. Preserve initial zero before any host request, and preserve existing 80/81 model/word, EPS torque/rate limits, safety RX checks and interrupt watchdog. |
| C18 R1–R3 discovery | Bounded passive anti-CAN2-mux checks | Unchanged. No car_helpers or discovery code changed. |
| Other Honda and stock ACC | Existing stock and alpha policy | No new longitudinal authority; stock ACC remains authoritative. Fit below-engage and C18 queue semantics kept. |

Native C was ported because this stable tree has the equivalent `honda_stock_aol.h` extension and current-source native negative tests. C8.2's wholesale architecture, Panda changes outside that file, and unrelated test removals were not imported. The C8.2 reference removes C18 Fit and cancel-sample code; C19 leaves those unrelated C18 paths intact.

## Test gates on changed source

The local host uses Python 3.12, cached read-only Python dependencies and a safety test library compiled from the current C source. Synthetic public fixtures only.

| Gate | Result |
| --- | --- |
| Accord C8.2 host intent, C18 R1–R3 focused discovery, Accord hybrid/stock ACC | **72 passed**, 0 skipped, 0 errors (`/tmp/c19_host_targeted.log`). |
| Honda stock AOL native C safety and MVL 80/81, including Park/N/R/Drive, zero handshake, stale mask, withdrawal, fault, cooldown and other Honda | **40 passed**, 0 skipped, 0 errors (`/tmp/c19_native_targeted.log`). |
| Additional Honda stock host file with unavailable `actual_card` tests deselected | **383 passed, 21 deselected**, 0 skipped/errors in the selected run. This overlaps the 72-pass gate; do not sum as unique tests. |
| Python compileall of changed Python paths and `git diff --check` | Passed. |
| Honda CAN-FD/recovery end-to-end caller | **Not runnable**: collection imports unavailable host `msgq`; no passing lifecycle claim. The old Accord recovery expectation was updated to request a fresh LKAS gesture, but remains unverified here. |
| Honda `actual_card` publication/ACK scenarios | **Not runnable**: initial unfiltered run had 21 failures from unavailable `msgq`; the final host run deselected them. `libparams_c.so` is also unavailable for full native host publication checks. |

Intermediate native negatives initially failed because the C18 test harness did not expose token/session flags; additive test-only accessors fixed that. Four older test expectations were then updated to require a fresh 80/81 gesture after withdrawal or gear departure. Final native gate passed; intermediate failures are not counted as passes.

## Exact build and artifact provenance

The parent tracks `prebuilt` and `prebuilt.json`, but `tools/ci/check_prebuilt_receipt.py` rejects the C18 parent receipt. Both were deleted here to prevent this source-only branch from appearing compiled. Do not regenerate a receipt without an actual complete exact-source device build.

`scripts/laptop_device_build.sh doctor` reports Docker CLI with inaccessible daemon, no checkout-local `.comma_sysroot`, and no checkout-local ARM64 build venv. Available disk space was about **7.7 GiB** before this work. A read-only older AGNOS sysroot exists at `/tmp/c10_agnos2052/sysroot` (about 1.2 GiB), and a C11 stage has a five-artifact QCOM package. Current QCOM source signature `db2ee948465d03d8180db65d537bdccc1a7211142d4e7ba296bb78548761d6f8` matches that older package's recorded source signature; this is input compatibility only, not C19 product compilation, ABI validation, full artifact verification, or installed-device identity. The current checkout lacks the required build setup and there is no matching C19 ARM64 product receipt. No full build or Panda firmware build was started under these constraints.

Minimally sufficient next step: provide an accessible ARM64 container runtime, a version-verified matching AGNOS sysroot and complete validated QCOM package within a workspace with adequate free storage; then build the **final C19 commit** with the documented full build and verify its ARM64/QCOM artifacts and genuine exact-source receipt. Independently review the C19 source and safety gates, then separately qualify the real hardware before considering installation or road use. C8.1/C11 compiled outputs cannot serve as this receipt.

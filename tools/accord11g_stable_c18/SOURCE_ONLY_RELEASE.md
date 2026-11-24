# C18 source-only pre-release scope

The R1 corrected source is ready for fresh independent review. **Source-only
publication waits for a fresh PASS_SCOPED review.** It is not an installable
or on-road release. No GitHub push or release publication occurred here.

**Installation/on-road: NO-GO.** Required remaining gates are an independent
safety review; the missing `msgq`-dependent card and wrong-safety-mode checks;
Panda and AGNOS device identity; a genuine same-commit C18 native build and
release receipt; QCOM target inference; physical CAN2 wiring/interrupt
confirmation; and vehicle-specific safety qualification. C11 binaries or prior
C8.1 vehicle observations do not satisfy these gates. No matching
`prebuilt.json` or Qualcomm producer receipt is asserted.

Source behavior is nonactuating at discovery. Stock ACC, radar/AEB, Panda
safety mode and motor/rate fault handling are unchanged. An exact firmware
match is still required before automatic Accord identity. Unknown or
ambiguous Accord evidence HOLDS as MOCK, with no CAN2 mux sweep.

R1 corrects the independent reviewer's FAIL_SCOPED / P0 finding: the earlier
10-ID detector could miss late, absent or malformed frames in the shared
0.12 s / 24-read window and enter the generic OBD mux scan. A bounded
passive extension now follows multi-ID Honda PT/camera evidence; full or
plausible partial layouts take normal-wiring bus-0 Honda VIN/FW. Missing,
unknown or ambiguous FW remains MOCK/HOLD. Fully selected other brands and
classic/Nidec Honda keep their discovery priority. This correction has only
synthetic host evidence and needs the fresh independent review above.

The regression suite's Accord CAN packets are fabricated synthetic test inputs; no route-derived CAN payloads, route IDs or VINs are distributed.

## C18 R2 foreign Honda firmware fail-closed correction

The R1 independent review found that even a fully attributable foreign Honda firmware version returned OTHER, triggering the generic OBD-multiplexed sweep on plausible Accord CAN-FD wiring. C18 R2 **never permits generic CAN2 OBD switching once Accord-like topology has selected the dedicated bus-0 path**. Exact unique Accord firmware remains the only way to identify Accord automatically; contradictory foreign Honda FW returns MOCK/HOLD. Production-level tests cover both full and partial Accord-like observations. Native safety/watchdog unchanged.

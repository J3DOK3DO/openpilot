# C18 source-only pre-release scope

The committed source may be offered for independent review and a clearly
labeled **source-only pre-release** outside this run. It is not an installable
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

The regression suite's Accord CAN packets are fabricated synthetic test inputs; no route-derived CAN payloads, route IDs or VINs are distributed.

# C20 project risk acceptance — 2026-11-27

## Owner decision and boundary

The vehicle owner explicitly accepted that experimental Honda Alpha Long may disable factory **CMBS/FCW, including automatic emergency braking (AEB)**, and requested that this be recorded as a formal project-level risk acceptance rather than an automatic stop on **offline feasibility research**. This is the owner's stated acceptance for studying that possible loss. It is **not** engineering qualification, a finding that the loss is safe, permission to disable a system, or a release authorization. The acceptance does not waive the remaining safety gates.

If CMBS/FCW/AEB is absent, delayed, or suppressed, the car may fail to warn or brake for a collision. A driver may not react in time; consequences include a crash, injury or death to occupants or others, and property damage. Factory ACC may also cease to behave as expected when radar ownership changes. The actual effect on this exact 2024 US-spec Accord Hybrid Touring, with its ECU firmware and wiring, is **not measured** here. Other independent braking, driver assistance and diagnostics cannot be assumed to replace CMBS/FCW.

This campaign retains factory ACC and active safety in code. It does not issue diagnostic or radar suppression messages, alter Panda safety flags, modify CarParams, enable openpilot longitudinal control, send CAN, install to a device or authorize road use. Any future control-path proposal requires a separate safety case and explicit decision after independent evidence. Regulatory compliance, insurance coverage, liability allocation, and any commercial release remain unresolved and outside this acceptance.

## Source basis and residual uncertainty

* C19 `a32dcc0a6e62` `opendbc_repo/opendbc/car/honda/interface.py` gates `alphaLongitudinalAvailable` off for Bosch CAN-FD and retains `pcmCruise` when openpilot longitudinal is off. `carstate.py` observes stock AEB in the stock-longitudinal path; `carcontroller.py` conditions longitudinal sends on ownership.
* Historical C6 `7b4db9a26010` Honda interface says radar disable permits openpilot longitudinal and explicitly warns that it disables AEB. It defers radar ownership until the relay is open, showing a startup timing hazard. This is historical read-only evidence, not a validated Accord 11G release design.
* MVL `48211d6a633c` with paired opendbc `66a3ea89f428` historically allows Bosch alpha long and notes AEB loss when radar is suppressed. Its later opendbc `254d6f150b21` is not the paired source.
* Four older route segments were found and hashed, but the exact vehicle, firmware, software and DBC identity is unverified. No authentic recording of the specified configuration was admitted. No native C19 MPC ran on this x86_64 host.

## Safety case and go/no-go

| Hazard or dependency | Needed independent evidence before active control | C20 result |
| --- | --- | --- |
| Bosch-C CAN-FD radar/camera ownership; factory CMBS/FCW/AEB and ACC coexistence | Pin exact ECU firmware and wiring; capture factory behavior and takeover transitions; demonstrate independent collision mitigation or documented accepted residual loss | **NO-GO**; owner accepts research risk only |
| CAN2 relay and startup sequencing | Hardware traces of relay state, Panda mode, first messages, ignition on/off, brownout and recovery | **NO-GO**; historical C6 timing is not proof |
| Panda safety and brake command failures | Independent review of exact firmware safety policy, transmit allowlist, counters, limits, timeout, malformed and dropped frames | **NO-GO**; no safety change in C20 |
| Factory ACC coexistence and driver override | On-car confirmation of gas/brake override, cancel, engagement state, stock ACC recovery and no competing brake owner | **NO-GO** |
| Lead/model validity, false positives and radar loss | Recorded exact-cycle radar/model provenance, fresh lead and model gates, cut-in/phantom/stale fault injection, solver and vehicle feedback | **NO-GO**; synthetic only |
| Stop/go and road grade, wind, brake response | Native solver with same-cycle inputs, actuator delay and saturation, repeated hardware-in-loop and closed-course measurements | **NO-GO**; MVL numbers are uncalibrated reference estimates |
| Release and rollback | Reproducible ARM64 build, matching receipt, tested installer and rollback, independent qualification and legal/insurance review | **NO-GO**; C19 receipt alone is not C20 qualification |

No public-road deployment of an unqualified active system. A research-only offline simulator may be released with clear labeling and provenance limitations.

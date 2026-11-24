# C18 stable adaptation change matrix

Base: `404ef33a969c05297d8068fdf49b2c70e23e6697`, local stable-derived branch
`accord11g-stable-c81-integrated-offline-rc-20261124`. Upstream remote identities:
`origin=https://github.com/j3dok3do/StarPilot.git` and
`github-trackb=https://github.com/J3DOK3DO/openpilot.git`. This records local Git
identity; no remote fetch or branch update was performed.

References: C8.1 `accord11g-dom7-c8-1-gui-release-20261113` =
`9d2da330f6539beb5afb67867b28491526c0e1bd`; C8.2
`accord11g-dom7-c8-2-final-source-rc-20261115` =
`20c86ebef9023845af0f62a946125700f7d51ce7`; C17 =
`7aee7bf44993ccf94e6aed36362b08711bbd171c`.

| Area | Stable before C18 | C18 source and checked behavior |
| --- | --- | --- |
| Passive discovery | Modern shared Ford/HKG window, then Honda classic/Nidec and other brand probes | Added exact recorded 10-frame Accord 11G signature after Ford/GM/Volvo/Tesla selection and before Honda classic. A malformed or missing required frame rejects it. This only chooses diagnostic wiring. |
| VIN/FW | Generic OBD mux scan on 11G; Honda classic uses normal buses, Nidec uses bus 0 with fallback | Strong 11G signature keeps CAN2 normal, VIN and Honda requests on bus 0. Up to 10 attempts, 0.5 s spacing and a 4.5 s deadline. Exact unique Accord FW identifies; missing, mixed, unknown or ambiguous evidence HOLDS without CAN-only identity. Fully attributable other-car FW uses the original generic path. Classic/Nidec branches are unchanged. |
| Stock AOL | Accord qualifier rejected detected HYBRID | HYBRID admitted only within existing Honda Bosch CAN-FD stock profile and exact safety word 80/81, stock PCM, transmission and mode checks. `stock_aol.py`, AOL policy and intent source are unchanged. |
| Camera buttons | Queued LKAS presses could survive a between-tick withdrawal; brake/cruise withdrawal was limited to experience 32 | Brake, cruise off, LKAS not ready, disabled control, cancel and resume clear pending pulses in both stock experiences. Last transmitted frame remains, retaining 500-frame cooldown. |
| Native safety/faults | Panda C hooks, safety words, controlsMismatch sources | No changes to Panda C safety, fault counters, selfdrived mismatch, safetyRxChecksInvalid, native safety wire or axis acknowledgment. `interruptRateCan2` remains blocking; native Honda safety tests use current source. |

The owner's earlier multi-route C8.1 observation belongs to a different code epoch.
No current stable-derived vehicle observation or physical safety qualification exists.

## Public test-fixture handling

The recorded source CAN window that informed the topology constants is **not included** in this release or its committed history. Public tests use fabricated zero-valued CAN bytes with public bus IDs/DLCs and exact firmware strings from the existing public Honda fingerprint database. These tests do not substitute for real-vehicle validation.

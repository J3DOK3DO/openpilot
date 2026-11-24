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
| Passive discovery | Modern shared Ford/HKG window, then Honda classic/Nidec and other brand probes | R1 fixes reviewer P0: the original full 10-ID check could miss late, omitted or malformed frames after the 0.12 s / 24-read shared window and fall into generic OBD scanning. Full valid layout still selects Accord wiring. Two matching PT/camera addresses on buses 0 and 2, or one matching address plus another PT/camera ID and either a third PT/camera ID or a CAN-FD ADAS ID, trigger at most 48 additional passive reads, ending by 0.65 s from discovery start. A remaining plausible partial layout also selects Honda bus-0 diagnostics. Fully selected other brands and classic/Nidec Honda retain priority. |
| VIN/FW | Generic OBD mux scan on 11G; Honda classic uses normal buses, Nidec uses bus 0 with fallback | Full or plausible partial 11G evidence keeps CAN2 normal, VIN and Honda requests on bus 0. Up to 10 attempts, 0.5 s spacing and a 4.5 s deadline. Exact unique Accord FW identifies; missing, mixed, unknown or ambiguous evidence HOLDS as MOCK without CAN-only identity. Fully attributable other-car FW uses the original generic path. Classic/Nidec branches are unchanged. |
| Stock AOL | Accord qualifier rejected detected HYBRID | HYBRID admitted only within existing Honda Bosch CAN-FD stock profile and exact safety word 80/81, stock PCM, transmission and mode checks. `stock_aol.py`, AOL policy and intent source are unchanged. |
| Camera buttons | Queued LKAS presses could survive a between-tick withdrawal; brake/cruise withdrawal was limited to experience 32 | Brake, cruise off, LKAS not ready, disabled control, cancel and resume clear pending pulses in both stock experiences. Last transmitted frame remains, retaining 500-frame cooldown. |
| Native safety/faults | Panda C hooks, safety words, controlsMismatch sources | No changes to Panda C safety, fault counters, selfdrived mismatch, safetyRxChecksInvalid, native safety wire or axis acknowledgment. `interruptRateCan2` remains blocking; native Honda safety tests use current source. |

The owner's earlier multi-route C8.1 observation belongs to a different code epoch.
No current stable-derived vehicle observation or physical safety qualification exists.

## Public test-fixture handling

The recorded source CAN window that informed the topology constants is **not included** in this release or its committed history. Public tests use fabricated zero-valued CAN bytes with public bus IDs/DLCs and exact firmware strings from the existing public Honda fingerprint database. These tests do not substitute for real-vehicle validation.

## C18 R2 foreign Honda firmware fail-closed correction

The R1 independent review found that even a fully attributable foreign Honda firmware version returned OTHER, triggering the generic OBD-multiplexed sweep on plausible Accord CAN-FD wiring. C18 R2 **never permits generic CAN2 OBD switching once Accord-like topology has selected the dedicated bus-0 path**. Exact unique Accord firmware remains the only way to identify Accord automatically; contradictory foreign Honda FW returns MOCK/HOLD. Production-level tests cover both full and partial Accord-like observations. Native safety/watchdog unchanged.

## C18 R3 single-seed passive-delay coverage

R2 review found one matching 11G CAN ID in the initial short probe was insufficient to trigger the bounded 48-read passive extension; a full layout on read 25 could therefore encounter generic OBD mux. R3 uses single-ID seed solely to prolong **passive** observation, not to determine vehicle identity. If corroborating frames never arrive within bounds, other-car generic discovery remains available; if they do, a conservative Honda bus0 FW path handles the Accord. Tests cover both outcomes. No guarantee is claimed for arbitrary CAN silence or delays past the bounded discovery window; vehicle release remains NO-GO.

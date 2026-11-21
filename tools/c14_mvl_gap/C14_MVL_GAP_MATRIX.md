# C14 — MVL Boston → Dom 7 Accord 11G Hybrid/Bosch-C gap matrix

**Classification: OFFLINE RESEARCH/READ-ONLY TESTS; NOT INSTALLABLE; ROAD USE NO-GO.**

Target identity: Accord 11G Hybrid, US Touring, Bosch CAN-FD, **stock Honda PCM ACC**, Dom openpilot with `openpilotLongitudinalControl=false`. No MVL driving-control source was cherry-picked, and no safety, firmware, vehicle CAN, controller, longitudinal, or HUD code was altered.

## Exact comparison pins

| Source | Identity |
|---|---|
| MVL openpilot snapshot | `48211d6a633cd172a8a8de7bc33004f3bc5f02a0`, `sp-honda-dev-202608` |
| **MVL opendbc pinned by that snapshot** | `66a3ea89f42890a99237dbf20789f1ea3d3d5611` |
| Later MVL opendbc checkout (NOT the snapshot pin) | `254d6f150b21b82da9666b1000f7b99507f15c9a` |
| Dom C13 source release | `966ffe5d175d59b3ce681249841aa0b3abfae443` |
| Full native product compiled source (prior C11) | `586da6b91ffb43e2a1e114072104b694d3c8a2b3` |
| C9 comprehensive investigation, separate unpublished branch | `ff618c42c8bb64c53b5b0fccf305b6b591201a6d` |

## Honda-specific numerical tuning — already present, not new

`read_only_tuning.py` extracts literal assignments from the precise MVL opendbc pin and C13 Honda interface source using Python AST without importing/executing car code. On the authorized Ubuntu host the four values matched:

| Tuned property | MVL P | Dom C13 | C14 change |
|---|---:|---:|---|
| PID Kp | 0.115 | 0.115 | None |
| PID Ki | 0.052 | 0.052 | None |
| PID feed-forward Kf | 0.000035 | 0.000035 | None |
| Steering actuator delay | 0.30 s | 0.30 s | None |

The earlier C9 D1 audit also found wheelbase 2.83 m, nominal ratio 16.7, driver threshold 600 and steering lookup endpoint 12,789 present across exact versions. C14's new script **does not** independently retest those further values, so their evidence remains the prior D1 pinned-source audit.

## MVL customization disposition

| Area | Disposition | C14 next safe work |
|---|---|---|
| Accord 11G static PID, delay and geometry | Already present | Do not duplicate or arbitrarily change numerical steering gains |
| Stock Honda ACC ownership / cancel, resume, gap, gas status | Present, with unresolved historical override symptom | Pure offline replay and attribution only; do not automate accelerator, brake or SET/RES commands |
| Stock-MVL LKAS button queue and Hybrid eligibility | Selected C8.1 compatibility imported; C8.2 native guard fixes | Exact final source/safety review and physical fault qualification still required |
| MVL lane-centering differences / lateral desired-path offset | Different policy implementation | Same-route pure-model comparison; quantify predictions and false corrections before proposing feature flags |
| MVL blinker pause lateral | Different policy | Offline authority-state and driver-expectation comparison; no automatic actuation |
| MVL low-speed turn desire | Different policy | Offline turn/lane-change false-positive analysis |
| MVL nudgeless / delayed lane changes | Not qualified | Keep inactive absent BSM and native authority proof |
| MVL optional torque/friction/NNLC tuning | Not established as the active Accord PID path | Architecture/parameter provenance before any target-specific adaptation |
| MVL HondaLatAccelFactor learning | Later source learner has Nidec-only persistence, no proven stock Bosch-C steering gain | No blind import |
| MVL speed limit / vision/map curves / ICBM | Not authorized to command stock PCM ACC | Passive comparison only, avoid synthetic RES/SET transmission |
| MVL Bosch-C alpha longitudinal / radar-silence | Deliberately **not imported**, safety-unsupported | Separate program only: AEB/radar ownership, diagnostic DTC, Panda safety model, failsafe cutover and independent qualification |
| MVL HUD/CAN-FD LANE_PATH / lead substitution | Tied to radar ownership/longitudinal paths | No take-over from stock radar without the separate longitudinal safety case |
| MVL dashboard/visual customizations | Not newly added by C14 | UI-only branch and isolated comparison if desired, separately qualified |

## Why not merge the complete C9 history into this public branch?

The historical C9 branch contains 63 read-only diagnostic files, including route-derived numerical tables, source-path inventory and historical trace identifiers. C14 imports **no private route datasets** into its public deliverable. The C9 evidence is retained locally unchanged. C14 adds only a standalone literal-source comparator, synthetic tests and explanatory records.

The C9 report's 20-item survey found 10 items already present, four to investigate offline, one requiring substantial adaptation, two inapplicable and three unsafe/unsupported. This is a **review classification**, not 20 new implementations.

## Unwaived operational release gates

Fresh Qualcomm producer/target inference; physically observed CAN2 interrupt and `controlsMismatch` fail-closed handling; installed AGNOS and Panda firmware/build identity; current same-commit prebuilt receipt; full independent final-source vehicle-safety review; verified recovery and emergency stop behavior. Those remain **NO-GO** for installation and driving.

Do not treat an offline portability assessment, synthetic test pass or a source-only GitHub tag as authorization for public-road actuation.

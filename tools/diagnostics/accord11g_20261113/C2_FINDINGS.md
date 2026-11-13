# Campaign 2 findings

## FDCAN2 startup fault

The 82 complete rlogs were decoded one segment at a time. Route 0 contains a sampled FDCAN2 IT0 rate of 17,862/s, above the 16,000/s watchdog. The nearest-second timeline records only **one high-rate second**, while the active `interruptRateCan2` fault persists through 10,873/10,912 Panda samples in the prior full-resolution aggregate. The first active fault sample is at 19,575,839,471 ns and the first reported over-limit rate is at 19,676,046,137 ns, about 0.10 s later. This ordering is consistent with a rate calculated over an earlier watchdog window and sampled afterward; the log does not show the exact interrupt that triggered the fault. The fault then persists while the published rate falls. Exact raw Panda and first controlsMismatch timestamps are in `c2_timeline_summary.json`. Route 1 starts with the fault already active despite no sampled rate over limit; the trigger may precede that rlog. Route 2 has no active rate fault or mismatch. `faultTemp` is sticky and is not counted as active.

The processor reports cumulative FDCAN2 error/RX/TX deltas at nearest-second cadence, excluding counter resets. Route 0 sampled total-error delta sum is 5,780 and RX delta sum 81,968; route 1 is 1,968 and 1,430; route 2 is 3,150 and 290,833. These are observed deltas across sampled endpoints, not all physical frames, and route durations differ greatly. Neither the error counters nor the sampled IRQ rate distinguish RX traffic from protocol-error interrupts. The exact electrical/configuration cause remains unknown. Init transitions include ELM327 safety param changes before Honda Bosch 80; their timing does not establish a mux cause.

The final route 2 segment 62 is labelled TRUNCATED. Its compressed bytes match the source manifest SHA-256, so exclusion is due to the original partial file rather than processor corruption. No wall-clock time is assigned: manifest segment start times are estimated and were not verified against an independent per-route monotonic anchor.

## AOL and secondary issues

The recorded CP alternative experience is 0 while the current marked independent path requires 32. The saved preference 1 cannot prove settings qualification, physical intent mapping, native safety receipt, current session/inventory or a granted lateral axis. Stock ACC plus lateral on route 2 follows the ordinary coupled path; see `HONDA_AOL_MATRIX.md`.

Route 2's single `commIssue` occurs at logMonoTime **27,428,289,831 ns**; the adjacent cloudlog entries at 27,429,020,456 and 27,429,094,570 ns report `not_alive=['carOutput']`, with no listed invalid or frequency failures. In a ±2 s window, decoded carState is valid with no CAN timeout, stock ACC disabled and speed near 31.8 m/s; sampled managerState shows card, selfdrived, ui, modeld and camerad running as expected. `carOutput` messages exist on both sides of the event. This supports a transient liveness/timing issue; it does not prove a process crash or CAN2 fault. UI FPS warnings count 25–32 FPS in prior evidence and appear in log classifications, but no synchronized camera/model liveness failure is established. u-blox NACK and almanac logs are separate GNSS conditions, with no demonstrated CAN2 causal link.

## Confidence limits

High confidence: source rate/fault mapping, observed active fault, marked-profile absence, exact carOutput liveness classification. Medium: temporal ordering at raw Panda/event timestamps. Low/unknown: physical FDCAN2 root cause, why the marker was absent, native session state, and any C6-12 vehicle outcome. No physical safety qualification follows from this offline analysis.

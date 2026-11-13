# Offline FDCAN2 timeline

Timeline rows use one nearest Panda sample per integer monotonic second. Counter sums, IRQ peaks, first rate exceedance and high-rate-second flags use every decoded Panda snapshot. Times are logMonoTime ns. No verified wall-clock alignment.

| Route | Decoded segments | Raw Panda samples | First >16k | First active CAN2 fault | First controlsMismatch | Seconds with a high-rate sample | High-rate samples | Longest consecutive flagged seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19 | 10912 | 19676046137 | 19575839471 | 29175884571 | 2 | 6 | 2 |
| 1 | 1 | 230 | None | 1412434552452 | 1424649627451 | 0 | 0 | 0 |
| 2 | 62 | 37208 | None | None | None | 0 | 0 | 0 |

A flagged second contains at least one Panda snapshot whose last-one-second IRQ rate was over 16,000/s; it does not measure one second of continuous excess. Consecutive flagged seconds do not establish continuous excess.
Counter sums add nonnegative changes between consecutive raw snapshots within each observed epoch. A reset starts a new epoch; a nonmonotonic timestamp quarantines counter changes until past the previous timestamp high-water mark. Fault status `faultTemp` is sticky; the active `faults` list controls fault presence.
The final route 2 segment is marked TRUNCATED; its digest is compared with the source manifest.
A sampled IRQ rate over 16,000/s supports the watchdog mechanism, but cannot establish whether RX traffic or error interrupts caused it.

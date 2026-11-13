# Offline FDCAN2 timeline

One nearest Panda sample per monotonic second. Times are logMonoTime ns. No verified wall-clock alignment.

| Route | Decoded segments | First >16k | First active CAN2 fault | First controlsMismatch | High-rate seconds | Longest run |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 19 | 19676046137 | 19575839471 | 29175884571 | 1 | 1 |
| 1 | 1 | None | 1412434552452 | 1424649627451 | 0 | 0 |
| 2 | 62 | None | None | None | 0 | 0 |

Fault status `faultTemp` is sticky; the active `faults` list controls fault presence. Counter deltas exclude resets.
The final route 2 segment is marked TRUNCATED; its digest is compared with the source manifest.
A sampled IRQ rate over 16,000/s supports the watchdog mechanism, but cannot establish whether RX traffic or error interrupts caused it.

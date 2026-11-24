# C18 R1 scoped review fix

The independent read-only review returned **FAIL_SCOPED / P0**. Accord 11G
discovery required all ten IDs inside the shared 0.12 s / 24-read window.
Late, missing or malformed frames could therefore send an Accord into the
generic OBD-multiplexed firmware scan associated with historical CAN2 faults.

R1 adds a multi-ID Honda normal-harness threshold and at most 48 additional
passive CAN reads, ending by 0.65 s from discovery start. Full and plausible
partial layouts use normal-wiring bus-0 Honda VIN/FW. Exact unique Accord
firmware identifies; unknown, absent or ambiguous firmware HOLDS as MOCK.
Fully selected other brands and registered classic/Nidec Honda keep priority.

Synthetic production-path regression: 326 passed, 3 `msgq` exclusions in the
cross-brand suite; native Honda MVL: 3 passed. The `msgq` and `libparams_c.so`
host-dependent checks remain blockers. **Source-only publication waits for a
fresh independent PASS_SCOPED review. Installation and road use remain NO-GO.**

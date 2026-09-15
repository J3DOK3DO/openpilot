# Candidate-2 implementation report

## Production files modified

- `selfdrive/controls/lib/longcontrol.py`
- `opendbc_repo/opendbc/car/honda/carcontroller.py`

## Mechanism and minimality

### LS004: stopping-state relaxation

The existing LongControl stopping state machine is unchanged. Its existing
`stoppingDecelRate` decrement runs only when the live `a_target` is at least
as braking as the prior stopping output. If a non-standstill vehicle is still
moving and the live target has relaxed, that same existing rate limits the
stored stopping output upward toward the current target. The release uses
`min(a_target, ...)`, so it is monotonic and cannot overshoot the live planner
request or snap directly from a deep stale value to it. This is the smallest
generic correction because it changes only the pre-existing stopping-ramp
condition; it adds neither a state nor a tuning/comfort constant.

Stopped-lead standstill hold remains safe: release requires both nonzero ego
speed and a clear cruise standstill flag. When the live stopping request is
still strong (including when it equals or is more negative than the current
stopping output), the original stopping decrement and shaping path remain
active.

### LS003 and LS001: Accord low-speed addon

The existing `mvl_brake_pid` remains the sole Accord low-speed correction. It
continues to update only when requested deceleration exceeds measured
deceleration (`accel - aEgo < 0`). When the measured response catches up to or
exceeds the request, that same PID is reset and the final target returns to the
original requested acceleration. This removes stale negative integral output
without adding another PID or changing the activation range.

Negative-only behavior is preserved: the existing PID still has a zero positive
limit, and the active-path target remains `min(accel, accel + brake_addon)`.

## Architecture invariants

The propulsion crossover remains based on the original requested `accel` plus
the existing road-load/wind compensation; `target_accel` is not used as the
crossover coordinate. Final Honda gas/brake arbitration, PCM authority,
CAN-FD ownership/handover, radar behavior, and lateral behavior were not
changed.

## Validation

Command environment used `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` to avoid a host
third-party pytest plugin incompatibility, while retaining the required shadow
launcher, serial execution, `-o 'addopts='`, `-p no:cacheprovider`, and
`--confcutdir` arguments.

Targeted contracts:

- LS004 stopping relaxation and deep-stale recovery: PASS
- stopped-lead hold guard: PASS
- LS003 addon reset: PASS
- LS001 mixed-state stale-brake guard: PASS
- original-request crossover guard: PASS
- final gas/brake mutex guard: PASS
- Result: 13 passed (the mutex guard has six parameter cases).

Broader relevant validation:

- `selfdrive/controls/tests/test_longcontrol.py`
- `selfdrive/controls/tests/test_accord11g_native17_invariants.py`
- Result: 104 passed.

The run emitted only three existing unknown-config-option warnings from the
minimal pytest plugin environment; there were no test failures.

## Remaining risks

The stopping correction deliberately uses the existing stopping rate for stale
release rather than introducing a new comfort tune or immediate target snap.
Validation is deterministic/offline and does not substitute for vehicle or
road-log confirmation of transient feel.

## Confirmations

- Frozen tests were not modified by this implementation. Their pre-existing
  uncommitted changes were preserved.
- No deployment occurred.
- No commit occurred.

## Consolidated final host qualification

Final Candidate-2 LongControl behavior:

- stale negative stopping output may recover only while `should_stop` remains
  asserted, ego speed is nonzero, cruise standstill is false, and the current
  planner target is less braking than the retained stopping output;
- recovery uses the existing `stoppingDecelRate`;
- recovery is monotonic toward the live planner target;
- recovery cannot overshoot the live planner target;
- recovery cannot cross above zero while LongControl remains in stopping;
- once `should_stop` clears, the pre-existing stopping-release hysteresis
  remains authoritative;
- true standstill/stopped-lead hold remains unchanged;
- stronger moving stopping requests retain the original deepening path.

The Accord low-speed addon continues to use the existing `mvl_brake_pid`.
When measured deceleration has caught up to the request, retained negative PID
state is reset rather than stacked on top of LongControl.

No new PID, state machine, tuning constant, planner target, crossover
coordinate, radar/CAN-FD ownership path, PCM authority path, lateral behavior,
or final Honda gas/brake arbitration was introduced.

The complete relevant LongControl and Accord invariant test modules passed in
the offline host qualification environment.

Vehicle deployment and road qualification remain separate stages.

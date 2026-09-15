# Candidate-2 RED Test Report

BASE_IDENTITY=d49c5ff167bfa2fc3e4c7a626dd8cd3404cd060b / 33993f81c764830ac39018061281b309aa16bc78 / d5967a1fc00912edde415105973e2a93224ec423
PRODUCTION_CODE_MODIFIED=NO
TEST_FILES_MODIFIED=selfdrive/controls/tests/test_longcontrol.py; selfdrive/controls/tests/test_accord11g_native17_invariants.py

LONGCONTROL_STOPPING_RELAXATION_TEST=EXPECTED_FAIL_RED: `test_accord_ls004_stopping_relaxation_does_not_ramp_stale_brake` distinguishes the prior -1.417 planner request from the relaxed -0.186 current target and rejects another stopping-state decrement.
STOPPED_LEAD_HOLD_GUARD=EXPECTED_PASS_GUARD: `test_accord_stopped_lead_holds_current_strong_stopping_request` retains braking at least as strong as the current -1.417 stopped-lead request.
ACCORD_ADDON_BOUND_RESET_TEST=EXPECTED_FAIL_RED: `test_accord_ls003_addon_resets_when_actual_decel_matches_relaxed_request` builds the real existing `mvl_brake_pid` state at 50 Hz, then requires no residual negative correction when `aEgo == accel`.
MIXED_LS001_TEST=EXPECTED_FAIL_RED: `test_accord_ls001_mixed_stopping_and_addon_states_do_not_stack_stale_brake` combines a relaxed-plan, stale LongControl stopping output with the real accumulated Accord addon state and rejects an additional final negative layer after its error is zero.
CROSSOVER_INVARIANT_GUARD=EXPECTED_PASS_GUARD: `test_low_speed_brake_correction_preserves_requested_force_for_crossover` proves the gas-force coordinate remains original requested accel plus existing wind road-load compensation, not the addon-adjusted target.
FINAL_CAN_MUTEX_GUARD=EXPECTED_PASS_GUARD: `test_bosch_acc_command_never_combines_gas_and_braking` retains final Honda CAN gas/brake mutual exclusion.

EXPECTED_RED_FAILURES=LS004 stopping relaxation; LS003 stale Accord-addon integral; LS001 stacked stale LongControl/addon output. Static source evaluation predicts these failures on Candidate-1: the stopping branch decrements `last_output_accel` while above `stopAccel`, and the `mvl_brake_pid` retains its negative integral at zero error.
UNEXPECTED_FAILURES=All requested pytest commands were blocked before collection by `ModuleNotFoundError: No module named 'capnp'` from repository `conftest.py`. An attempted `uv run --frozen` environment bootstrap also could not download locked dependencies because DNS/network access is unavailable. No test assertion was executed.

CAUSAL_REPRODUCTION=The new tests are deterministic production-object sequences matching LS004 (-1.417 history, -0.186 current plan), LS003 (-0.492 request plus retained low-speed PID state), and LS001 (-2.0 stale stopping output plus retained addon). Runtime reproduction remains unverified because the required Python dependency is absent.
READY_FOR_MINIMAL_IMPLEMENTATION=NO — install the locked test dependencies (including `pycapnp==2.1.0`) and run the commands below to observe the required RED failures and passing guards before implementation.

## Validation commands and results

| Command | Result |
|---|---|
| `python3 -m py_compile selfdrive/controls/tests/test_longcontrol.py selfdrive/controls/tests/test_accord11g_native17_invariants.py` | PASS |
| `pytest -q selfdrive/controls/tests/test_longcontrol.py -k 'accord_ls004 or accord_stopped_lead'` | BLOCKED before collection: missing `capnp` |
| `pytest -q selfdrive/controls/tests/test_accord11g_native17_invariants.py -k 'low_speed_brake_correction_preserves_requested_force_for_crossover or ls003_addon or ls001_mixed or bosch_acc_command_never_combines_gas_and_braking'` | BLOCKED before collection: missing `capnp` |
| `pytest -q selfdrive/controls/tests/test_longcontrol.py` | BLOCKED before collection: missing `capnp` |
| `pytest -q selfdrive/controls/tests/test_accord11g_native17_invariants.py` | BLOCKED before collection: missing `capnp` |
| `pytest -q selfdrive/controls/tests/test_longitudinal_planner.py` | BLOCKED before collection: missing `capnp` |
| `UV_CACHE_DIR=/tmp/accord11g-uv-cache uv run --frozen pytest -q selfdrive/controls/tests/test_longcontrol.py -k 'accord_ls004 or accord_stopped_lead'` | BLOCKED: locked dependency download failed due DNS/network resolution |


## Superseding runtime qualification status

The original environment-blocked RED status is superseded.

All intended Candidate-1 low-speed defects were subsequently reproduced as
deterministic assertion failures before their corresponding Candidate-2
production corrections were accepted.

Additional RED coverage was added for:

- already-deep LS004 stale stopping output;
- stopping-release hysteresis while still in LongControl stopping;
- preservation of non-positive stopping output while `should_stop` remains
  asserted.

Final host-side regression qualification passed. Vehicle and road validation
remain outstanding.

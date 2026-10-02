"""C5-C terminal-stop evidence contract for the sole clean C0/45 approach.

This is deliberately a compact evidence fixture, rather than an input-identical
planner/controller/CAN replay: the supplied C5-OBS extract does not retain every
same-cycle input needed to reconstruct one.  The values below are copied from
the authoritative C5-C findings, not loaded from that workspace at test time.

C5-C behavior remains HOLD until at least two independently clean comparable
autonomous terminal approaches exist.  In particular, this fixture must not be
read as authorization to retune the terminal taper or stopping handoff.

C2/C3 preservation is covered by the existing focused gates:
  * test_accord11g_c4_baseline.py: LS003 immediate reset/release, C3
    confirmed-deficit re-arm, and Honda gas/brake mutex;
  * test_longcontrol.py::test_accord_c4_ls004_stale_stopping_output_recovers_toward_relaxed_target;
  * test_longcontrol.py's stopping-release tests and
    test_longitudinal_planner.py's Accord stopped-lead/stop-go tests; and
  * test_accord11g_c5_refresh_replay.py's C5-B crossover/release replays.
Those tests are intentionally reused rather than reimplementing their logic
here.
"""

import pytest

from cereal import car, log
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState


# route 000000c0--fc904da2d5, segment 45.  Wall time is reconstructed UAE time
# from the supplied C0 extraction anchor; it is provenance, not a controller
# input.  Tolerances allow the source values' printed precision only.
C0_45_TERMINAL_STOP = {
  "route": "000000c0--fc904da2d5",
  "segment": 45,
  "terminal_time_uae": "13:30:16.506",
  "should_stop_since_uae": "13:30:15.933",
  "max_speed_preceding_10_s": 4.418,
  "min_a_ego": -1.554,
  "a_target": -0.485,
  "raw_mpc_accel": -0.513,
  "policy_output": -0.485,
  "honda_original_accel": -0.664,
  "honda_final_accel": -0.664,
  "brake_request_samples": 100,
  "brake_request_true_samples": 100,
  "low_speed_addon": 0.000,
  "stop_duration_s": 3.85,
  # This is a discrete sampled derivative proxy, explicitly not physical jerk.
  "max_abs_sampled_derivative_jerk_proxy": 19.916,
}


def test_c5c_c0_45_provenance_and_terminal_summary_are_frozen():
  stop = C0_45_TERMINAL_STOP

  assert stop["route"] == "000000c0--fc904da2d5"
  assert stop["segment"] == 45
  assert stop["terminal_time_uae"] == "13:30:16.506"
  assert stop["should_stop_since_uae"] == "13:30:15.933"
  assert stop["max_speed_preceding_10_s"] == pytest.approx(4.418, abs=0.001)
  assert stop["min_a_ego"] == pytest.approx(-1.554, abs=0.001)
  assert stop["stop_duration_s"] == pytest.approx(3.85, abs=0.01)
  assert stop["max_abs_sampled_derivative_jerk_proxy"] == pytest.approx(19.916, abs=0.001)


def test_c5c_c0_45_classifies_current_terminal_boundary_as_ordinary_negative_request():
  """The sole comparable stop has no positive/tapered handoff request evidence."""
  stop = C0_45_TERMINAL_STOP

  # The planner target, raw MPC, policy output, and Honda original/final
  # requests are all independently recorded as ordinary negative values.
  assert stop["a_target"] == pytest.approx(-0.485, abs=0.001)
  assert stop["raw_mpc_accel"] == pytest.approx(-0.513, abs=0.001)
  assert stop["policy_output"] == pytest.approx(-0.485, abs=0.001)
  assert stop["honda_original_accel"] == pytest.approx(-0.664, abs=0.001)
  assert stop["honda_final_accel"] == pytest.approx(-0.664, abs=0.001)
  assert all(stop[field] < 0.0 for field in (
    "a_target", "raw_mpc_accel", "policy_output", "honda_original_accel", "honda_final_accel",
  ))


def test_c5c_c0_45_has_continuous_braking_not_crossover_chatter_or_addon_contribution():
  stop = C0_45_TERMINAL_STOP

  # The 100/100 sampled two-second window is continuous braking, not a sampled
  # C5-B crossover pulse train. The zero addon means this particular stop is
  # not evidence that C2/C3 addon chatter caused it; it says nothing about the
  # separate historical C2 pulse event.
  assert stop["brake_request_true_samples"] == stop["brake_request_samples"] == 100
  assert stop["low_speed_addon"] == pytest.approx(0.0, abs=1e-6)


def test_c5c_current_observability_schema_captures_future_multi_stop_trace_fields():
  """CURRENT C5-OBS can retain the terminal fields needed for future collection."""
  plan = log.LongitudinalPlan.new_message()
  plan.shouldStop = True
  plan.c5ObsRawMpcAccel = -0.513
  plan.c5ObsPolicyOutput = -0.485

  car_control = car.CarControl.new_message()
  car_control.longActive = True
  car_control.actuators.longControlState = LongCtrlState.stopping
  car_control.actuators.c5ObsHondaOriginalAccel = -0.664
  car_control.actuators.c5ObsHondaFinalAccel = -0.664
  car_control.actuators.c5ObsHondaBrakeRequest = True
  car_control.actuators.c5ObsHondaLowSpeedAddon = 0.0

  controls = log.ControlsState.new_message()
  controls.longControlState = LongCtrlState.stopping

  with log.LongitudinalPlan.from_bytes(plan.to_bytes()) as recorded_plan:
    assert recorded_plan.shouldStop
    assert recorded_plan.c5ObsRawMpcAccel == pytest.approx(-0.513, abs=1e-6)
    assert recorded_plan.c5ObsPolicyOutput == pytest.approx(-0.485, abs=1e-6)
  with car.CarControl.from_bytes(car_control.to_bytes()) as recorded_control:
    assert recorded_control.longActive
    assert recorded_control.actuators.longControlState == LongCtrlState.stopping
    assert recorded_control.actuators.c5ObsHondaOriginalAccel == pytest.approx(-0.664, abs=1e-6)
    assert recorded_control.actuators.c5ObsHondaFinalAccel == pytest.approx(-0.664, abs=1e-6)
    assert recorded_control.actuators.c5ObsHondaBrakeRequest
    assert recorded_control.actuators.c5ObsHondaLowSpeedAddon == pytest.approx(0.0, abs=1e-6)
  with log.ControlsState.from_bytes(controls.to_bytes()) as recorded_controls:
    assert recorded_controls.longControlState == LongCtrlState.stopping

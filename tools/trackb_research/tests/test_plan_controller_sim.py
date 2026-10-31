"""Synthetic tests for the isolated, non-actuating downstream simulator."""
from dataclasses import replace

import pytest

from tools.trackb_research.plan_controller_sim import (
  MODE_STOP_HOLD, MODE_TRACKING, MODE_WITHDRAWN, PlanControllerSimulation,
  PlanSnapshot, SimulationPolicy, VehicleObservation,
)


POLICY = SimulationPolicy(2.0, 2.0, -3.0, 2.0, 0.1)  # Symbolic test values, not vehicle calibration.


def plan(identity=20, published=10.0, target=0.5, **changes):
  base = PlanSnapshot(identity, identity - 1, published, target, False, True, True, False, "cruise", (1.0,), (0.5,), (0.0,))
  return replace(base, **changes)


def observation(identity=30, observed=10.0, token="token-a", **changes):
  base = VehicleObservation(identity, observed, 5.0, 0.0, False, False, False, False, "clear", token, True, False, True)
  return replace(base, **changes)


def withdrawn(record, reason):
  assert record.mode == MODE_WITHDRAWN
  assert record.acceleration_request is None
  assert record.reason == reason


def test_tracking_following_acceleration_and_deceleration_use_only_dom_a_target():
  sim = PlanControllerSimulation()
  first = sim.step(plan(target=0.8, has_lead=True), observation(), POLICY, 11.0)
  assert (first.mode, first.acceleration_request, first.reason) == (MODE_TRACKING, 0.8, "dom_a_target_only")
  second = sim.step(plan(21, target=-1.4, has_lead=True), observation(31), POLICY, 11.1)
  assert (second.mode, second.acceleration_request, second.reason) == (MODE_TRACKING, -1.4, "dom_a_target_only")


def test_stop_and_go_standstill_and_takeoff_are_downstream_modes_not_planning():
  sim = PlanControllerSimulation()
  hold = sim.step(plan(should_stop=True, target=-1.0), observation(standstill=True, v_ego=0.0), POLICY, 11.0)
  assert (hold.mode, hold.acceleration_request, hold.reason) == (MODE_STOP_HOLD, 0.0, "plan_should_stop_selects_abstract_hold")
  go = sim.step(plan(21, should_stop=False, target=0.6), observation(31, standstill=False), POLICY, 11.1)
  assert (go.mode, go.acceleration_request) == (MODE_TRACKING, 0.6)


def test_should_stop_is_plan_mode_only_and_a_target_is_the_only_magnitude_input():
  sim = PlanControllerSimulation()
  moving = sim.step(plan(should_stop=True, target=-1.2), observation(standstill=False), POLICY, 11.0)
  assert (moving.mode, moving.acceleration_request, moving.reason) == (MODE_TRACKING, -1.2, "dom_a_target_only")
  hold = sim.step(plan(21, should_stop=True, target=1.8), observation(31, standstill=True, v_ego=0.0), POLICY, 11.1)
  assert (hold.mode, hold.acceleration_request) == (MODE_STOP_HOLD, 0.0)


@pytest.mark.parametrize(("plan_changes", "observation_changes", "reason"), (
  ({"allow_throttle": False, "a_target": 0.1}, {}, "throttle_denied"),
  ({"allow_brake": False, "a_target": -0.1}, {}, "brake_denied"),
  ({}, {"brake_pressed": True}, "driver_pedal_override"),
  ({}, {"accelerator_pressed": True}, "driver_pedal_override"),
  ({}, {"cancel_pressed": True}, "driver_cancel"),
  ({}, {"stock_acc_enabled": False}, "stock_acc_disengaged"),
  ({}, {"aeb_cmbs_state": "active"}, "aeb_cmbs_not_clear"),
  ({}, {"aeb_cmbs_state": "unknown"}, "aeb_cmbs_not_clear"),
  ({}, {"contradictory": True}, "contradictory_observation"),
  ({}, {"standstill": True, "v_ego": 1.0}, "contradictory_observation"),
))
def test_authority_denials_and_overrides_fail_closed(plan_changes, observation_changes, reason):
  withdrawn(PlanControllerSimulation().step(plan(**plan_changes), observation(**observation_changes), POLICY, 11.0), reason)


@pytest.mark.parametrize(("candidate_plan", "candidate_observation", "candidate_policy", "now", "reason"), (
  (plan(published=1.0), observation(), POLICY, 11.0, "stale_plan"),
  (plan(), observation(observed=1.0), POLICY, 11.0, "stale_observation"),
  (plan(published=12.0), observation(), POLICY, 11.0, "timestamp_inconsistent"),
  (plan(), observation(observed=12.0), POLICY, 11.0, "timestamp_inconsistent"),
  (plan(a_target=float("nan")), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(speeds=(float("inf"),)), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(speeds=(1.0, 2.0)), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(), observation(a_ego=float("nan")), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(aeb_cmbs_state="bad"), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(aeb_cmbs_state=[]), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(stock_acc_enabled=None), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(), SimulationPolicy(1.0, 1.0, 2.0, -2.0, 0.1), 11.0, "policy_invalid"),
  (plan(), observation(), POLICY, float("inf"), "decision_time_invalid"),
))
def test_stale_invalid_nonfinite_and_timestamp_inconsistent_inputs_withdraw(candidate_plan, candidate_observation, candidate_policy, now, reason):
  withdrawn(PlanControllerSimulation().step(candidate_plan, candidate_observation, candidate_policy, now), reason)


@pytest.mark.parametrize(("candidate_plan", "candidate_observation", "candidate_policy", "now", "reason"), (
  (plan(published=10 ** 10000), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(target=10 ** 10000), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(), observation(observed=10 ** 10000), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(), POLICY, 10 ** 10000, "decision_time_invalid"),
  (plan(speeds=(10 ** 10000,)), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(accels=(10 ** 10000,)), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(jerks=(10 ** 10000,)), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(), observation(v_ego=10 ** 10000), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(a_ego=10 ** 10000), POLICY, 11.0, "observation_shape_invalid"),
  (plan(), observation(), SimulationPolicy(10 ** 10000, 2.0, -3.0, 2.0, 0.1), 11.0, "policy_invalid"),
  (plan(), observation(), SimulationPolicy(2.0, 10 ** 10000, -3.0, 2.0, 0.1), 11.0, "policy_invalid"),
  (plan(), observation(), SimulationPolicy(2.0, 2.0, -(10 ** 10000), 2.0, 0.1), 11.0, "policy_invalid"),
  (plan(), observation(), SimulationPolicy(2.0, 2.0, -3.0, 10 ** 10000, 0.1), 11.0, "policy_invalid"),
  (plan(), observation(), SimulationPolicy(2.0, 2.0, -3.0, 2.0, 10 ** 10000), 11.0, "policy_invalid"),
  (plan(identity=1 << 64), observation(), POLICY, 11.0, "plan_invalid"),
  (plan(), observation(), POLICY, 11.0, None),
  (plan(), observation(identity=1 << 64), POLICY, 11.0, "observation_shape_invalid"),
), ids=(
  "plan_timestamp", "plan_target", "observation_timestamp", "decision_timestamp", "speed_series", "accel_series", "jerk_series",
  "vehicle_speed", "vehicle_accel", "max_plan_age", "max_observation_age", "abstract_accel_min", "abstract_accel_max",
  "standstill_speed", "plan_id", "model_id", "observation_id",
))
def test_huge_numeric_inputs_and_uint64_overflow_identifiers_fail_closed(candidate_plan, candidate_observation, candidate_policy, now, reason):
  if reason is None:
    candidate_plan = replace(candidate_plan, model_log_monotonic=1 << 64)
    reason = "plan_invalid"
  withdrawn(PlanControllerSimulation().step(candidate_plan, candidate_observation, candidate_policy, now), reason)


def test_duplicate_out_of_order_fault_then_fresh_token_recovery_are_deterministic():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(plan(), observation(31), POLICY, 11.1), "duplicate_or_out_of_order_plan")
  withdrawn(sim.step(plan(21), observation(31), POLICY, 11.2), "retired_engagement_token")
  assert sim.step(plan(22), observation(32, token="token-b"), POLICY, 11.3).mode == MODE_TRACKING
  withdrawn(sim.step(plan(23), observation(32, token="token-c"), POLICY, 11.4), "duplicate_or_out_of_order_observation")


def test_reset_is_a_fault_boundary_that_requires_a_new_never_retired_token():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  sim.reset()
  withdrawn(sim.step(plan(), observation(), POLICY, 11.0), "retired_engagement_token")
  assert sim.step(plan(), observation(token="token-b"), POLICY, 11.0).mode == MODE_TRACKING


def test_malformed_and_multiple_faults_poison_prior_and_carried_tokens():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(token="token-a"), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(plan(21), observation(31, token="token-b", valid=1), POLICY, 11.1), "observation_shape_invalid")
  withdrawn(sim.step(plan(22), observation(32, token="token-a"), POLICY, 11.2), "retired_engagement_token")
  withdrawn(sim.step(plan(23), observation(33, token="token-b"), POLICY, 11.3), "retired_engagement_token")
  withdrawn(sim.step(plan(24), observation(34, token="token-c"), SimulationPolicy(10 ** 10000, 2.0, -3.0, 2.0, 0.1), 11.4), "policy_invalid")
  withdrawn(sim.step(plan(25), observation(35, token="token-c"), POLICY, 11.5), "retired_engagement_token")
  assert sim.step(plan(26), observation(36, token="token-d"), POLICY, 11.6).mode == MODE_TRACKING


def test_malformed_plan_type_still_poison_prior_accepted_token():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(object(), observation(31), POLICY, 11.1), "plan_type_invalid")
  withdrawn(sim.step(plan(21), observation(31), POLICY, 11.2), "retired_engagement_token")
  assert sim.step(plan(22), observation(32, token="token-b"), POLICY, 11.3).mode == MODE_TRACKING


def test_symbolic_output_envelope_is_not_a_planner_or_vehicle_limit():
  sim = PlanControllerSimulation()
  high = sim.step(plan(target=99.0), observation(), POLICY, 11.0)
  low = sim.step(plan(21, target=-99.0), observation(31), POLICY, 11.1)
  assert (high.acceleration_request, low.acceleration_request) == (2.0, -3.0)


def test_recovery_never_recycles_retired_token_and_steady_token_is_stable():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(token="token-a"), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(plan(21), observation(31, token="token-a", brake_pressed=True), POLICY, 11.1), "driver_pedal_override")
  assert sim.step(plan(22), observation(32, token="token-b"), POLICY, 11.2).mode == MODE_TRACKING
  assert sim.step(plan(23), observation(33, token="token-b"), POLICY, 11.3).mode == MODE_TRACKING
  withdrawn(sim.step(plan(24), observation(34, token="token-a"), POLICY, 11.4), "retired_engagement_token")


def test_silent_token_change_withdraws_and_recovery_retires_every_prior_token():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(token="token-a"), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(plan(21), observation(31, token="token-a", cancel_pressed=True), POLICY, 11.1), "driver_cancel")
  assert sim.step(plan(22), observation(32, token="token-b"), POLICY, 11.2).mode == MODE_TRACKING
  withdrawn(sim.step(plan(23), observation(33, token="token-c"), POLICY, 11.3), "engagement_token_changed_without_recovery")
  assert sim.step(plan(24), observation(34, token="token-d"), POLICY, 11.4).mode == MODE_TRACKING
  for identity, token in enumerate(("token-a", "token-b", "token-c"), start=25):
    withdrawn(sim.step(plan(identity), observation(identity + 10, token=token), POLICY, 11.4 + identity / 100), "retired_engagement_token")


def test_multiple_resets_and_faults_retain_tokens_for_simulator_lifetime():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(token="token-a"), POLICY, 11.0).mode == MODE_TRACKING
  sim.reset()
  assert sim.step(plan(), observation(token="token-b"), POLICY, 11.1).mode == MODE_TRACKING
  withdrawn(sim.step(plan(21), observation(31, token="token-c", cancel_pressed=True), POLICY, 11.2), "driver_cancel")
  assert sim.step(plan(22), observation(32, token="token-d"), POLICY, 11.3).mode == MODE_TRACKING
  sim.reset()
  assert sim.step(plan(), observation(token="token-e"), POLICY, 11.4).mode == MODE_TRACKING
  for identity, token in enumerate(("token-a", "token-b", "token-c", "token-d"), start=21):
    withdrawn(sim.step(plan(identity), observation(identity + 30, token=token), POLICY, 11.4 + identity / 100), "retired_engagement_token")


def test_decision_clock_rollback_with_fresh_ids_fails_closed_and_requires_new_token():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(plan(21, published=10.2), observation(31, observed=10.2), POLICY, 10.5), "decision_clock_reversed")
  withdrawn(sim.step(plan(22, published=10.3), observation(32, observed=10.3), POLICY, 11.1), "retired_engagement_token")
  assert sim.step(plan(23, published=10.4), observation(33, observed=10.4, token="token-b"), POLICY, 11.2).mode == MODE_TRACKING


def test_reset_does_not_erase_monotonic_decision_clock_evidence():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  sim.reset()
  withdrawn(sim.step(plan(published=10.1), observation(observed=10.1, token="token-b"), POLICY, 10.5),
            "decision_clock_reversed")
  assert sim.step(plan(published=10.2), observation(observed=10.2, token="token-c"), POLICY, 11.2).mode == MODE_TRACKING


def test_stock_acc_withdrawal_retires_synthetic_engagement_token():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  withdrawn(sim.step(plan(21), observation(31, stock_acc_enabled=False), POLICY, 11.1), "stock_acc_disengaged")
  withdrawn(sim.step(plan(22), observation(32), POLICY, 11.2), "retired_engagement_token")
  assert sim.step(plan(23), observation(33, token="token-b"), POLICY, 11.3).mode == MODE_TRACKING


def test_equal_non_decreasing_decision_time_is_allowed_with_fresh_ids():
  sim = PlanControllerSimulation()
  assert sim.step(plan(), observation(), POLICY, 11.0).mode == MODE_TRACKING
  assert sim.step(plan(21), observation(31), POLICY, 11.0).mode == MODE_TRACKING

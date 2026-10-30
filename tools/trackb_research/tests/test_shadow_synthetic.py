"""Deterministic tests for the non-actuating Track B synthetic harness."""
from dataclasses import FrozenInstanceError, replace

import pytest

from tools.trackb_research.shadow_synthetic import ELIGIBLE_FOR_ANALYSIS, WITHDRAWN_UNKNOWN, ExpiryPolicy, Observation, ShadowEligibility


POLICY = ExpiryPolicy(stale_after=10.0)  # Test-owned symbolic T_stale, not a vehicle target.


def observation(identifier="one", acquired=100.0, decided=101.0, token="engage-a", **changes):
  baseline = Observation(identifier, acquired, decided, True, "clear", False, False, False, True, token, False, None, 0.1)
  return replace(baseline, **changes)


def assert_withdrawn(result, reason):
  assert result.eligibility == WITHDRAWN_UNKNOWN
  assert result.reason == reason


@pytest.mark.parametrize(("age", "expected"), ((10.0 - 1e-9, ELIGIBLE_FOR_ANALYSIS), (10.0, WITHDRAWN_UNKNOWN), (10.0 + 1e-9, WITHDRAWN_UNKNOWN)))
def test_stale_boundary_t_stale_plus_and_minus_epsilon(age, expected):
  result = ShadowEligibility().evaluate(observation(decided=100.0 + age), POLICY)
  assert result.eligibility == expected


@pytest.mark.parametrize("changes, reason", (({"valid": False}, "observation_invalid"), ({"signal_conflict": True}, "signal_conflict"),
                                                ({"engagement_token": None}, "engagement_token_missing"), ({"aeb_cmbs_state": "unknown"}, "aeb_cmbs_not_clear"),
                                                ({"aeb_cmbs_state": "active"}, "aeb_cmbs_not_clear"), ({"aeb_cmbs_state": "missing"}, "aeb_cmbs_not_clear"),
                                                ({"latency": None}, "latency_unknown"), ({"latency": float("nan")}, "latency_invalid")))
def test_invalid_missing_conflicting_and_unknown_inputs_withdraw(changes, reason):
  assert_withdrawn(ShadowEligibility().evaluate(observation(**changes), POLICY), reason)


@pytest.mark.parametrize("changes, reason", (({"brake_pressed": True}, "driver_pedal_override"), ({"accelerator_pressed": True}, "driver_pedal_override"),
                                                ({"cancel_pressed": True}, "driver_cancel"), ({"acc_main_on": False}, "acc_main_off")))
def test_driver_override_withdraws_immediately(changes, reason):
  assert_withdrawn(ShadowEligibility().evaluate(observation(**changes), POLICY), reason)


@pytest.mark.parametrize("changes, reason", (({"decision_monotonic": 99.0}, "clock_jump_or_negative_age"),
                                                ({"acquisition_monotonic": float("inf")}, "nonfinite_monotonic_timestamp"),
                                                ({"decision_monotonic": float("nan")}, "nonfinite_monotonic_timestamp")))
def test_clock_jumps_and_nonfinite_timestamps_withdraw(changes, reason):
  assert_withdrawn(ShadowEligibility().evaluate(observation(**changes), POLICY), reason)


def test_duplicate_and_out_of_order_records_withdraw():
  shadow = ShadowEligibility()
  assert shadow.evaluate(observation(), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS
  assert_withdrawn(shadow.evaluate(observation(), POLICY), "duplicate_or_missing_observation_id")
  assert_withdrawn(shadow.evaluate(observation("later", acquired=99.5, decided=101.5, token="engage-b"), POLICY), "out_of_order_acquisition")


def test_recovery_requires_fresh_monotonic_observation_and_new_token_only_logically():
  shadow = ShadowEligibility()
  assert_withdrawn(shadow.evaluate(observation(brake_pressed=True), POLICY), "driver_pedal_override")
  assert_withdrawn(shadow.evaluate(observation("two", acquired=102.0, decided=103.0), POLICY), "fresh_engagement_token_required")
  result = shadow.evaluate(observation("three", acquired=104.0, decided=105.0, token="engage-b"), POLICY)
  assert result.eligibility == ELIGIBLE_FOR_ANALYSIS


def test_stateful_decision_clock_ordering_withdraws_then_recovers_with_new_token():
  shadow = ShadowEligibility()
  assert shadow.evaluate(observation(), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS
  assert_withdrawn(shadow.evaluate(observation("two", acquired=100.5, decided=100.75, token="engage-b"), POLICY), "clock_jump_backwards")
  assert shadow.evaluate(observation("three", acquired=103.0, decided=104.0, token="engage-c"), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS

def test_repeated_invalid_observations_cannot_reuse_prior_engagement_token():
  shadow = ShadowEligibility()
  assert shadow.evaluate(observation(token="engage-a"), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS
  assert_withdrawn(shadow.evaluate(observation("brake", acquired=102.0, decided=103.0,
                                               token="engage-a", brake_pressed=True), POLICY), "driver_pedal_override")
  assert_withdrawn(shadow.evaluate(observation("unknown", acquired=104.0, decided=105.0,
                                               token="engage-b", aeb_cmbs_state="unknown"), POLICY), "aeb_cmbs_not_clear")
  assert_withdrawn(shadow.evaluate(observation("reused-a", acquired=106.0, decided=107.0,
                                               token="engage-a"), POLICY), "fresh_engagement_token_required")
  assert_withdrawn(shadow.evaluate(observation("reused-b", acquired=108.0, decided=109.0,
                                               token="engage-b"), POLICY), "fresh_engagement_token_required")
  assert shadow.evaluate(observation("new-c", acquired=110.0, decided=111.0,
                                     token="engage-c"), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS


@pytest.mark.parametrize(("candidate", "reason"), (([], "observation_type_invalid"), (object(), "observation_type_invalid")))
def test_non_observation_inputs_fail_closed_without_exception(candidate, reason):
  assert_withdrawn(ShadowEligibility().evaluate(candidate, POLICY), reason)


@pytest.mark.parametrize(("candidate", "reason"), (([], "expiry_policy_type_invalid"), (object(), "expiry_policy_type_invalid"),
                                                     (ExpiryPolicy(float("nan")), "expiry_policy_invalid"),
                                                     (ExpiryPolicy(float("inf")), "expiry_policy_invalid"),
                                                     (ExpiryPolicy(10 ** 10000), "expiry_policy_invalid"),
                                                     (ExpiryPolicy(True), "expiry_policy_invalid")))
def test_malformed_or_unrepresentable_policy_fails_closed_without_exception(candidate, reason):
  assert_withdrawn(ShadowEligibility().evaluate(observation(), candidate), reason)


@pytest.mark.parametrize(("changes", "reason"), (({"observation_id": []}, "observation_id_invalid"),
                                                    ({"observation_id": " "}, "observation_id_invalid"),
                                                    ({"observation_id": " one"}, "observation_id_invalid"),
                                                    ({"engagement_token": []}, "engagement_token_invalid"),
                                                    ({"engagement_token": " "}, "engagement_token_invalid"),
                                                    ({"engagement_token": " token "}, "engagement_token_invalid"),
                                                    ({"aeb_cmbs_state": []}, "aeb_cmbs_state_invalid"),
                                                    ({"valid": 1}, "boolean_field_invalid"),
                                                    ({"brake_pressed": 0}, "boolean_field_invalid"),
                                                    ({"accelerator_pressed": "false"}, "boolean_field_invalid"),
                                                    ({"cancel_pressed": None}, "boolean_field_invalid"),
                                                    ({"acc_main_on": 1}, "boolean_field_invalid"),
                                                    ({"signal_conflict": 0}, "boolean_field_invalid"),
                                                    ({"lead_present": 0}, "lead_present_invalid"),
                                                    ({"acquisition_monotonic": 10 ** 10000}, "nonfinite_monotonic_timestamp"),
                                                    ({"decision_monotonic": -(10 ** 10000)}, "nonfinite_monotonic_timestamp"),
                                                    ({"acquisition_monotonic": True}, "nonfinite_monotonic_timestamp"),
                                                    ({"latency": 10 ** 10000}, "latency_invalid"),
                                                    ({"latency": False}, "latency_invalid"),
                                                    ({"latency": float("-inf")}, "latency_invalid"),
                                                    ({"latency": float("inf")}, "latency_invalid")))
def test_malformed_fields_fail_closed_without_exception(changes, reason):
  assert_withdrawn(ShadowEligibility().evaluate(observation(**changes), POLICY), reason)


def test_immutable_records_and_negative_zero_boundary_are_explicit():
  record = observation(acquired=-0.0, decided=0.0, token="engage-a")
  assert ShadowEligibility().evaluate(record, POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS
  with pytest.raises(FrozenInstanceError):
    record.valid = False
  with pytest.raises(FrozenInstanceError):
    POLICY.stale_after = 1.0


def test_malformed_fault_is_atomic_for_ordering_and_cannot_recycle_prior_token():
  shadow = ShadowEligibility()
  assert shadow.evaluate(observation(token="engage-a"), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS
  assert_withdrawn(shadow.evaluate(observation("bad", acquired=102.0, decided=103.0, token="engage-b", valid=1), POLICY),
                   "boolean_field_invalid")
  # The malformed record was not added to ordering state, but it still forced
  # a logical withdrawal: the previously accepted token is poisoned.
  assert_withdrawn(shadow.evaluate(observation("after-bad", acquired=102.0, decided=103.0, token="engage-a"), POLICY),
                   "fresh_engagement_token_required")
  assert shadow.evaluate(observation("fresh", acquired=104.0, decided=105.0, token="engage-c"), POLICY).eligibility == ELIGIBLE_FOR_ANALYSIS

@pytest.mark.parametrize("lead_present", (True, False))
def test_valid_optional_synthetic_lead_boolean_is_analytical_only(lead_present):
  result = ShadowEligibility().evaluate(observation(lead_present=lead_present), POLICY)
  assert result.eligibility == ELIGIBLE_FOR_ANALYSIS
  assert result.reason == "synthetic_inputs_clear"


@pytest.mark.parametrize(("changes", "reason"), (
    ({"acquisition_monotonic": float("-inf")}, "nonfinite_monotonic_timestamp"),
    ({"decision_monotonic": float("-inf")}, "nonfinite_monotonic_timestamp"),
    ({"latency": -0.0}, None),
))
def test_negative_infinity_and_signed_zero_boundary(changes, reason):
  result = ShadowEligibility().evaluate(observation(**changes), POLICY)
  if reason is None:
    assert result.eligibility == ELIGIBLE_FOR_ANALYSIS
  else:
    assert_withdrawn(result, reason)

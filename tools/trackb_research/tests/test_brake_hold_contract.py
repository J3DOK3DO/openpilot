"""Tests for the isolated synthetic brake/gas/hold contract."""

from dataclasses import replace

import pytest

from tools.trackb_research.brake_hold_contract import (
  MODE_ABSTRACT_BRAKE,
  MODE_ABSTRACT_HOLD,
  MODE_COAST,
  MODE_WITHDRAWN,
  BrakeContractInput,
  BrakeContractPolicy,
  BrakeHoldContract,
)

POLICY = BrakeContractPolicy(-0.2, -0.05, 0.1)


def sample(identity=1, acceleration=0.2, **changes):
  return replace(BrakeContractInput(identity, acceleration, 2.0, False, False, False, True, True, True), **changes)


def test_symbolic_entry_release_hysteresis_and_abstract_hold():
  contract = BrakeHoldContract()
  assert contract.step(sample(acceleration=-0.3), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(2, acceleration=-0.1), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(3, acceleration=-0.04), POLICY).mode == MODE_COAST
  assert contract.step(sample(4, standstill=True, v_ego=0.0), POLICY).mode == MODE_ABSTRACT_HOLD


@pytest.mark.parametrize(
  "changes",
  (
    {"brake_pressed": True},
    {"accelerator_pressed": True},
    {"stock_acc_enabled": False},
    {"aeb_cmbs_clear": False},
    {"valid": False},
  ),
)
def test_driver_and_safety_gates_withdraw(changes):
  assert BrakeHoldContract().step(sample(**changes), POLICY).mode == MODE_WITHDRAWN


@pytest.mark.parametrize(
  "candidate,policy",
  (
    (sample(decision_id=0), POLICY),
    (sample(acceleration=float("nan")), POLICY),
    (sample(), BrakeContractPolicy(-0.05, -0.2, 0.1)),
  ),
)
def test_invalid_data_fails_closed(candidate, policy):
  assert BrakeHoldContract().step(candidate, policy).reason == "input_invalid"


def test_duplicate_decision_is_rejected():
  contract = BrakeHoldContract()
  assert contract.step(sample(), POLICY).mode == MODE_COAST
  assert contract.step(sample(), POLICY).reason == "duplicate_or_out_of_order_decision"


@pytest.mark.parametrize(
  "fault",
  (
    {"brake_pressed": True},
    {"accelerator_pressed": True},
    {"stock_acc_enabled": False},
    {"aeb_cmbs_clear": False},
    {"valid": False},
  ),
)
def test_withdrawal_clears_prior_brake_hysteresis(fault):
  contract = BrakeHoldContract()
  assert contract.step(sample(1, acceleration=-0.3), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(2, acceleration=-0.1, **fault), POLICY).mode == MODE_WITHDRAWN
  # With -0.1 between entry (-0.2) and release (-0.05), stale braking would
  # persist without clearing the previous hysteresis on withdrawal.
  assert contract.step(sample(3, acceleration=-0.1), POLICY).mode == MODE_COAST


def test_malformed_and_reordered_events_clear_brake_hysteresis():
  contract = BrakeHoldContract()
  assert contract.step(sample(1, acceleration=-0.3), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(2, acceleration=float("nan")), POLICY).mode == MODE_WITHDRAWN
  assert contract.step(sample(3, acceleration=-0.1), POLICY).mode == MODE_COAST
  assert contract.step(sample(4, acceleration=-0.3), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(4, acceleration=-0.3), POLICY).mode == MODE_WITHDRAWN
  assert contract.step(sample(5, acceleration=-0.1), POLICY).mode == MODE_COAST


def test_inclusive_hysteresis_thresholds_have_deterministic_priority():
  contract = BrakeHoldContract()
  assert contract.step(sample(1, acceleration=-0.2), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(2, acceleration=-0.1), POLICY).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(3, acceleration=-0.05), POLICY).mode == MODE_COAST
  assert contract.step(sample(4, acceleration=-0.2), POLICY).mode == MODE_ABSTRACT_BRAKE
  collapsed = BrakeContractPolicy(-0.1, -0.1, 0.1)
  assert contract.step(sample(5, acceleration=-0.1), collapsed).mode == MODE_ABSTRACT_BRAKE
  assert contract.step(sample(6, acceleration=-0.09), collapsed).mode == MODE_COAST

"""Tests for the pure, non-actuating Bosch-C ownership evidence model."""

from dataclasses import replace

import pytest

from tools.trackb_research.ownership_evidence_model import (
  STATE_OBSERVED_STOCK,
  STATE_UNKNOWN,
  STATE_WITHDRAWN,
  OwnershipEvidenceModel,
  OwnershipObservation,
)


def observation(identity=1, observed=1.0, **changes):
  base = OwnershipObservation(identity, observed, True, "clear", False, False, "unverified", "source_only", True, True)
  return replace(base, **changes)


def test_complete_source_only_evidence_can_only_label_retained_stock_ownership():
  record = OwnershipEvidenceModel().assess(observation())
  assert (record.state, record.reason, record.observation_id) == (
    STATE_OBSERVED_STOCK,
    "stock_ownership_retained_source_only",
    1,
  )


@pytest.mark.parametrize(
  ("changes", "state", "reason"),
  (
    ({"stock_acc_enabled": False}, STATE_UNKNOWN, "stock_acc_not_enabled"),
    ({"aeb_cmbs_state": "active"}, STATE_UNKNOWN, "aeb_cmbs_not_clear"),
    ({"aeb_cmbs_state": "unknown"}, STATE_UNKNOWN, "aeb_cmbs_not_clear"),
    ({"source_complete": False}, STATE_UNKNOWN, "source_evidence_incomplete"),
    ({"relay_state_claim": "claimed_open"}, STATE_UNKNOWN, "physical_claim_not_accepted"),
    ({"topology_claim": "physical_claim"}, STATE_UNKNOWN, "physical_claim_not_accepted"),
    ({"diagnostics_requested": True}, STATE_WITHDRAWN, "diagnostics_prohibited"),
    ({"radar_suppression_requested": True}, STATE_WITHDRAWN, "radar_suppression_prohibited"),
  ),
)
def test_unknown_or_prohibited_evidence_never_grants_a_control_or_physical_claim(changes, state, reason):
  record = OwnershipEvidenceModel().assess(observation(**changes))
  assert (record.state, record.reason) == (state, reason)


@pytest.mark.parametrize(
  "changes",
  (
    {"observation_id": 0},
    {"observation_id": 1 << 64},
    {"observed_monotonic": float("nan")},
    {"stock_acc_enabled": 1},
    {"aeb_cmbs_state": "bad"},
    {"valid": False},
  ),
)
def test_malformed_synthetic_records_fail_closed(changes):
  record = OwnershipEvidenceModel().assess(observation(**changes))
  assert (record.state, record.reason) == (STATE_WITHDRAWN, "observation_shape_invalid")


def test_ordering_and_clock_regressions_fail_closed_after_a_valid_record():
  model = OwnershipEvidenceModel()
  assert model.assess(observation()).state == STATE_OBSERVED_STOCK
  assert model.assess(observation()).reason == "duplicate_or_out_of_order_observation"
  assert model.assess(observation(2, 0.5)).reason == "observation_clock_reversed"


def test_non_observation_object_fails_closed_without_an_identity():
  record = OwnershipEvidenceModel().assess(object())
  assert (record.state, record.reason, record.observation_id) == (STATE_WITHDRAWN, "observation_type_invalid", None)

"""Discriminating offline tests for all retained MVL-inspired B17 research IDs."""

from dataclasses import replace

import pytest

from tools.trackb_research.mvl_retained_sim import (
  ABSTRACT_BRAKE, ABSTRACT_COAST, RESEARCH_ONLY, UNKNOWN, WITHDRAWN,
  BrakeResearchInput, BrakeResearchPolicy, BrakeSelectionResearch,
  OwnershipResearchObservation, OwnershipTransitionResearch,
  RadarMetadataObservation, RadarMetadataResearch,
)


BRAKE_POLICY = BrakeResearchPolicy(-0.20, -0.05, -0.80, 0.10, 0.02)


def owner(sequence=1, observed=1.0, **changes):
  return replace(OwnershipResearchObservation(sequence, observed, True, "stock_source_only", "ambiguous", "none", "clear", True), **changes)


def radar(sequence=1, topic="hud", **changes):
  return replace(RadarMetadataObservation(sequence, topic, True, True, "none", True), **changes)


def brake(sequence=1, target=-0.3, corrected=-0.3, **changes):
  return replace(BrakeResearchInput(sequence, target, corrected, False, False, False, False, False, True), **changes)


def test_bc_009_to_012_are_only_fresh_stock_source_labels_with_ambiguous_relay():
  result = OwnershipTransitionResearch().observe(owner())
  assert (result.classification, result.reason) == (RESEARCH_ONLY, "stock_owner_source_only_relay_ambiguous")


@pytest.mark.parametrize(("changes", "reason"), (
  ({"source_fresh": False}, "source_evidence_stale"),
  ({"stock_owner_label": "unknown"}, "stock_owner_not_established"),
  ({"relay_label": "claimed"}, "relay_not_ambiguous_source_only"),
  ({"transition_label": "silent_transition_observed"}, "silent_transition_failure_observed"),
  ({"aeb_status": "unknown"}, "aeb_status_not_known_clear"),
))
def test_bc_009_to_012_missing_evidence_unknown_aeb_relay_and_silent_transition_are_not_passes(changes, reason):
  result = OwnershipTransitionResearch().observe(owner(**changes))
  assert result.classification == UNKNOWN and result.reason == reason


def test_bc_009_to_012_duplicate_and_restart_style_ordering_fail_closed():
  model = OwnershipTransitionResearch()
  assert model.observe(owner()).classification == RESEARCH_ONLY
  assert model.observe(owner()).classification == WITHDRAWN
  assert model.observe(owner(2, 0.5)).reason == "observation_clock_reversed"
  assert OwnershipTransitionResearch().observe(owner(1, valid=False)).classification == WITHDRAWN


@pytest.mark.parametrize("topic", ("hud", "tick", "mux", "lead", "checksum"))
def test_bc_020_to_024_claims_are_symbolic_metadata_only(topic):
  result = RadarMetadataResearch().classify(radar(topic=topic))
  assert (result.classification, result.reason, result.topic) == (RESEARCH_ONLY, "source_claim_metadata_only", topic)


@pytest.mark.parametrize(("changes", "classification", "reason"), (
  ({"source_claim_present": False}, UNKNOWN, "source_claim_missing"),
  ({"input_fresh": False}, UNKNOWN, "metadata_stale"),
  ({"anomaly_label": "missing_claim"}, UNKNOWN, "metadata_anomaly:missing_claim"),
  ({"valid": False}, WITHDRAWN, "metadata_invalid"),
))
def test_bc_020_to_024_missing_stale_anomalous_metadata_is_discriminated(changes, classification, reason):
  result = RadarMetadataResearch().classify(radar(**changes))
  assert (result.classification, result.reason) == (classification, reason)


def test_bc_020_to_024_duplicate_metadata_fails_closed():
  model = RadarMetadataResearch()
  assert model.classify(radar()).classification == RESEARCH_ONLY
  assert model.classify(radar()).reason == "duplicate_metadata"


def test_drv_001_005_006_008_select_symbolic_brake_and_keep_target_corrected_distinct():
  result = BrakeSelectionResearch().evaluate(brake(target=-0.1, corrected=-0.4), BRAKE_POLICY)
  assert (result.classification, result.selected_path, result.reason) == (RESEARCH_ONLY, ABSTRACT_BRAKE, "abstract_brake_selected")
  assert (result.target_value, result.corrected_value, result.symbolic_integrator) == (-0.1, -0.4, -0.4)


def test_drv_003_positive_target_cannot_reenter_abstract_brake_from_corrected_value():
  result = BrakeSelectionResearch().evaluate(brake(target=0.1, corrected=-0.4), BRAKE_POLICY)
  assert (result.classification, result.selected_path, result.reason) == (UNKNOWN, ABSTRACT_COAST, "positive_target_brake_reentry_suppressed")


@pytest.mark.parametrize("changes", ({"driver_brake": True}, {"driver_gas": True}))
def test_drv_005_driver_brake_or_gas_is_exclusive_and_latches_withdrawal(changes):
  result = BrakeSelectionResearch().evaluate(brake(**changes), BRAKE_POLICY)
  assert result.classification == WITHDRAWN and result.selected_path is None and result.reason == "driver_override"


def test_drv_007_fault_restart_and_rearm_are_explicit_and_clear_integrator():
  model = BrakeSelectionResearch()
  assert model.evaluate(brake(), BRAKE_POLICY).symbolic_integrator == -0.3
  assert model.evaluate(brake(2, restart=True), BRAKE_POLICY).reason == "fault_or_restart_latched"
  assert model.evaluate(brake(3), BRAKE_POLICY).reason == "rearm_required"
  result = model.evaluate(brake(4, rearm=True, target=0.0, corrected=0.0), BRAKE_POLICY)
  assert (result.classification, result.symbolic_integrator) == (RESEARCH_ONLY, 0.0)


def test_drv_009_one_sided_relaxation_is_limited_not_instantaneous():
  model = BrakeSelectionResearch()
  assert model.evaluate(brake(1, corrected=-0.5), BRAKE_POLICY).symbolic_integrator == -0.5
  result = model.evaluate(brake(2, corrected=-0.1), BRAKE_POLICY)
  assert (result.reason, result.selected_path, result.symbolic_integrator) == ("one_sided_relaxation_limited", ABSTRACT_BRAKE, -0.4)


@pytest.mark.parametrize("corrected", (-0.02, -0.0))
def test_drv_010_near_zero_negative_tolerance_is_explicit(corrected):
  result = BrakeSelectionResearch().evaluate(brake(corrected=corrected, target=0.0), BRAKE_POLICY)
  assert (result.reason, result.selected_path, result.symbolic_integrator) == ("near_zero_negative_relaxed", ABSTRACT_COAST, 0.0)


@pytest.mark.parametrize(("candidate", "policy"), (
  (brake(sequence=0), BRAKE_POLICY),
  (brake(corrected=float("nan")), BRAKE_POLICY),
  (brake(), BrakeResearchPolicy(-0.1, -0.2, -0.8, 0.1, 0.02)),
))
def test_drv_invalid_input_and_mutated_policy_fail_closed(candidate, policy):
  assert BrakeSelectionResearch().evaluate(candidate, policy).classification == WITHDRAWN


def test_drv_duplicate_after_brake_is_rejected_and_poisoned_until_rearm():
  model = BrakeSelectionResearch()
  assert model.evaluate(brake(), BRAKE_POLICY).classification == RESEARCH_ONLY
  assert model.evaluate(brake(), BRAKE_POLICY).reason == "duplicate_or_out_of_order_input"
  assert model.evaluate(brake(2), BRAKE_POLICY).reason == "rearm_required"


def test_bc_020_to_024_out_of_order_unique_sequence_is_rejected():
  model = RadarMetadataResearch()
  assert model.classify(radar(2)).classification == RESEARCH_ONLY
  record = model.classify(radar(1))
  assert (record.classification, record.reason) == (WITHDRAWN, "out_of_order_metadata")
  assert model.classify(radar(3)).classification == RESEARCH_ONLY


def test_drv_brake_entry_cannot_be_reclassified_as_near_zero():
  model = BrakeSelectionResearch()
  record = model.evaluate(brake(corrected=-0.25), BRAKE_POLICY)
  assert (record.classification, record.selected_path) == (RESEARCH_ONLY, ABSTRACT_BRAKE)
  overlap = replace(BRAKE_POLICY, symbolic_near_zero_negative=0.30)
  assert BrakeSelectionResearch().evaluate(brake(corrected=-0.25), overlap).classification == WITHDRAWN

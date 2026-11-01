"""Cross-model lifecycle proof: synthetic Dom plan + evidence + numeric policy only."""
import pytest

from tools.trackb_research.brake_policy_model import (BRAKE, COAST, PROPEL, WITHDRAWN as BRAKE_WITHDRAWN,
                                                      PolicyConfig)
from tools.trackb_research.offline_planner_chain import (EVIDENCE_FRESH, EVIDENCE_WITHDRAWN, SIMULATION_ONLY,
                                                         EvidenceBundle, OfflinePlannerChain)
from tools.trackb_research.plan_controller_sim import (MODE_STOP_HOLD, MODE_TRACKING, MODE_WITHDRAWN,
                                                       SimulationPolicy)
from tools.trackb_research.source_evidence_contracts import FRESH, StreamWindow

# These bounds and values exist only to exercise model composition. They are not
# physical units, target limits, or vehicle calibration.
PLAN_POLICY = SimulationPolicy(0.2, 0.2, -2.0, 1.0, 0.05)
BRAKE_CONFIG = PolicyConfig(accel_min=-2.0, accel_max=1.0, brake_entry=-0.1, brake_release=-0.02,
                            meaningful_brake=-0.8, release_steps=2, low_speed=2.0, integrator_gain=0.1,
                            integrator_floor=-0.2, integrator_relax=0.05, brake_relax_step=0.1,
                            standstill_tolerance=0.01)
GOOD = EvidenceBundle(StreamWindow(1, 1, 0.0), StreamWindow(1, 1, 0.0), EVIDENCE_FRESH, "clear")


def evidence(*, radar=None, camera=None, ownership=EVIDENCE_FRESH, aeb="clear"):
  return EvidenceBundle(radar or GOOD.radar, camera or GOOD.camera, ownership, aeb)


def new_chain():
  return OfflinePlannerChain(PLAN_POLICY, BRAKE_CONFIG)


def assert_nonconflicting(record):
  assert record.simulation_only == SIMULATION_ONLY
  assert record.propulsion >= 0 and record.brake >= 0
  assert not (record.propulsion > 0 and record.brake > 0)
  if record.brake_mode == BRAKE_WITHDRAWN:
    assert record.planner_mode == MODE_WITHDRAWN  # subordinate withdrawal is chain-wide
  if record.evidence_class != EVIDENCE_FRESH or record.planner_mode == MODE_WITHDRAWN:
    assert record.brake_mode == BRAKE_WITHDRAWN
    assert (record.propulsion, record.brake, record.corrected_accel) == (0.0, 0.0, 0.0)


def test_stop_and_go_lead_loss_and_brake_release_compose_across_models():
  chain = new_chain()
  records = [
    chain.advance("stock-disengaged-arm", 1.00, 0.0, False, False, None, GOOD,
                  stock_acc_enabled=False),
    chain.advance("engaged-stop", 1.01, -1.0, True, True, "token-a", GOOD, plan_published_monotonic=1.01),
    chain.advance("lead-loss-deceleration", 1.02, -0.5, False, False, "token-a", GOOD, plan_published_monotonic=1.02),
    chain.advance("release-request", 1.03, 0.2, False, False, "token-a", GOOD, plan_published_monotonic=1.03),
  ]
  assert records[0].planner_mode == MODE_WITHDRAWN
  assert records[1].planner_mode == MODE_STOP_HOLD
  assert records[2].planner_mode == MODE_TRACKING and records[2].brake_mode == BRAKE
  assert records[3].planner_mode == MODE_TRACKING and records[3].brake_mode in (BRAKE, COAST)
  assert all(r.evidence_class == EVIDENCE_FRESH for r in records)
  for record in records:
    assert_nonconflicting(record)


@pytest.mark.parametrize("window", [
  StreamWindow(1, 0, None),       # received but rejected: not silence/transfer
  StreamWindow(0, 0, 1.0),        # stale
  StreamWindow(0, 0, None),       # absent
  StreamWindow(1, 2, 0.0),        # invalid/contradictory
])
@pytest.mark.parametrize("source", ("radar", "camera"))
def test_short_interrupted_rejected_stale_or_absent_evidence_withdraws(window, source):
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=1.0)
  active = chain.advance("engage", 1.01, -0.5, False, False, "token-a", GOOD, plan_published_monotonic=1.01)
  assert active.planner_mode == MODE_TRACKING
  kwargs = {source: window}
  withdrawn = chain.advance("evidence-withdrawn", 1.02, 0.5, False, False, "token-a", evidence(**kwargs), plan_published_monotonic=1.02)
  assert withdrawn.evidence_class == EVIDENCE_WITHDRAWN
  assert withdrawn.planner_mode == MODE_WITHDRAWN
  assert_nonconflicting(withdrawn)
  recovered_without_new_token = chain.advance("old-token-rejected", 1.03, 0.5, False, False,
                                              "token-a", GOOD, plan_published_monotonic=1.03)
  assert recovered_without_new_token.planner_mode == MODE_WITHDRAWN
  assert_nonconflicting(recovered_without_new_token)


@pytest.mark.parametrize("aeb", ("unknown", "active"))
def test_any_unknown_or_active_fcwaebcmbs_state_withdraws(aeb):
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=1.0)
  chain.advance("engage", 1.01, -0.5, False, False, "token-a", GOOD, plan_published_monotonic=1.01)
  record = chain.advance("collision-state-not-clear", 1.02, 0.5, False, False, "token-a", evidence(aeb=aeb), plan_published_monotonic=1.02)
  assert record.planner_mode == MODE_WITHDRAWN
  assert record.evidence_class == EVIDENCE_WITHDRAWN
  assert_nonconflicting(record)


def test_stale_plan_driver_override_and_pending_fade_fault_all_withdraw():
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=1.0)
  chain.advance("engage", 1.01, -1.0, False, False, "token-a", GOOD, plan_published_monotonic=1.01)
  # A time gap makes both the copied plan and evidence too old; no policy state survives.
  stale = chain.advance("stale-plan-after-gap", 2.0, -1.0, False, False, "token-a", GOOD,
                        plan_published_monotonic=1.01)
  assert stale.planner_mode == MODE_WITHDRAWN and stale.brake_mode == BRAKE_WITHDRAWN
  assert_nonconflicting(stale)

  # Fresh clean engagement, then driver override must immediately clear brake state.
  chain.advance("rearm-observed", 2.01, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=2.01)
  chain.advance("new-token", 2.02, -1.0, False, False, "token-b", GOOD, plan_published_monotonic=2.02)
  override = chain.advance("driver-override", 2.03, -1.0, False, False, "token-b", GOOD,
                           brake_pressed=True, plan_published_monotonic=2.03)
  assert override.planner_mode == MODE_WITHDRAWN and override.brake_mode == BRAKE_WITHDRAWN
  assert_nonconflicting(override)

  # New token after override, put the numeric model into braking, then inject a fault
  # while its one-sided synthetic brake fade would otherwise be pending.
  chain.advance("rearm-again", 2.04, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=2.04)
  chain.advance("new-token-c", 2.05, -1.0, False, False, "token-c", GOOD, plan_published_monotonic=2.05)
  pending = chain.advance("brake-fade", 2.06, 0.2, False, False, "token-c", GOOD, plan_published_monotonic=2.06)
  assert pending.brake_mode in (BRAKE, COAST)
  failed = chain.advance("fault-during-fade", 2.07, 0.2, False, False, "token-c", GOOD, fault=True, plan_published_monotonic=2.07)
  assert failed.planner_mode == MODE_WITHDRAWN and failed.brake_mode == BRAKE_WITHDRAWN
  assert_nonconflicting(failed)


def test_reset_needs_new_engagement_and_fresh_evidence_before_rearming():
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=1.0)
  chain.advance("active", 1.01, 0.5, False, False, "token-a", GOOD)
  chain.reset()
  predating = chain.advance("predating-token", 1.02, 0.5, False, False, "token-a", GOOD)
  assert predating.planner_mode == MODE_WITHDRAWN
  assert_nonconflicting(predating)
  # A current valid disengaged observation arms the restarted planner; numeric policy
  # rearm is itself withdrawn, so activation only follows the later fresh token.
  chain.advance("fresh-disengaged", 1.03, 0.0, False, False, None, GOOD, stock_acc_enabled=False)
  fresh = chain.advance("new-engagement", 1.04, 0.5, False, False, "token-b", GOOD, plan_published_monotonic=1.04)
  assert fresh.planner_mode == MODE_TRACKING
  assert fresh.brake_mode == PROPEL  # separate brake model was rearmed by fresh disengaged evidence
  assert_nonconflicting(fresh)
  active = chain.advance("subsequent-current-plan", 1.05, 0.5, False, False, "token-b", GOOD, plan_published_monotonic=1.05)
  assert active.planner_mode == MODE_TRACKING and active.brake_mode == PROPEL
  assert_nonconflicting(active)


def test_rejected_ownership_hypothesis_is_not_successful_transfer():
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD, stock_acc_enabled=False, plan_published_monotonic=1.0)
  record = chain.advance("unproven-ownership", 1.01, 0.5, False, False, "token-a",
                         evidence(ownership="rejected_hypothesis"))
  assert record.evidence_class == EVIDENCE_WITHDRAWN
  assert record.planner_mode == MODE_WITHDRAWN
  assert_nonconflicting(record)


def test_reviewer_p2_clock_rollback_after_fault_cannot_rearm_at_earlier_time():
  chain = new_chain()
  chain.advance("initial-disengagement", 1.0, 0.0, False, False, None, GOOD,
                stock_acc_enabled=False, plan_published_monotonic=1.0)
  chain.advance("start", 1.01, 0.5, False, False, "token-a", GOOD, plan_published_monotonic=1.01)
  failed = chain.advance("fault-at-2s", 2.0, 0.0, False, False, "token-a", GOOD,
                         fault=True, plan_published_monotonic=2.0)
  assert_nonconflicting(failed)
  backwards = chain.advance("reversed-clock", 1.02, 0.0, False, False, None, GOOD,
                            stock_acc_enabled=False, plan_published_monotonic=1.02)
  assert backwards.planner_mode == MODE_WITHDRAWN
  assert backwards.brake_reason == "decision_clock_invalid_or_reversed"
  assert_nonconflicting(backwards)
  retry = chain.advance("clock-still-behind", 1.03, 0.5, False, False, "token-b", GOOD,
                        plan_published_monotonic=1.03)
  assert_nonconflicting(retry)
  assert retry.planner_mode == MODE_WITHDRAWN
  # A new, forward-time disengagement is required before a fresh token can be considered.
  chain.advance("fresh-forward-disengagement", 2.01, 0.0, False, False, None, GOOD,
                stock_acc_enabled=False, plan_published_monotonic=2.01)
  restored = chain.advance("fresh-forward-token", 2.02, 0.5, False, False, "token-c", GOOD,
                           plan_published_monotonic=2.02)
  assert restored.planner_mode == MODE_TRACKING
  assert_nonconflicting(restored)


def test_reviewer_p2_bad_negative_speed_withdraws_both_models():
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD,
                stock_acc_enabled=False, plan_published_monotonic=1.0)
  bad = chain.advance("invalid-speed", 1.01, -0.5, False, False, "token-a", GOOD,
                      v_ego=-2.0, plan_published_monotonic=1.01)
  assert bad.planner_mode == MODE_WITHDRAWN
  assert bad.brake_mode == BRAKE_WITHDRAWN
  assert_nonconflicting(bad)
  reuse = chain.advance("retired-token", 1.02, 0.5, False, False, "token-a", GOOD,
                        plan_published_monotonic=1.02)
  assert reuse.planner_mode == MODE_WITHDRAWN
  assert_nonconflicting(reuse)


def test_reviewer_p3_retired_token_never_reused_after_reset_and_fresh_disengagement():
  chain = new_chain()
  chain.advance("arm", 1.0, 0.0, False, False, None, GOOD,
                stock_acc_enabled=False, plan_published_monotonic=1.0)
  chain.advance("start", 1.01, -0.5, False, False, "token-a", GOOD,
                plan_published_monotonic=1.01)
  chain.advance("fault", 1.02, 0.0, False, False, "token-a", GOOD,
                fault=True, plan_published_monotonic=1.02)
  chain.reset()
  chain.advance("fresh-disengagement", 1.03, 0.0, False, False, None, GOOD,
                stock_acc_enabled=False, plan_published_monotonic=1.03)
  stale_token = chain.advance("reused-retired-token", 1.04, 0.5, False, False, "token-a", GOOD,
                              plan_published_monotonic=1.04)
  assert stale_token.planner_mode == MODE_WITHDRAWN
  assert_nonconflicting(stale_token)

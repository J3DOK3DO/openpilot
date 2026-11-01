"""Pure composition adapter for offline planner/brake-policy research.

Every returned record is explicitly ``simulation_only``. Evidence is symbolic
and cannot establish authenticated ownership or vehicle authority. The numeric
policy values are caller-supplied synthetic values with no calibrated meaning.
This module has no transport, frame, CAN, UDS, runtime or vehicle command path.
"""

from dataclasses import dataclass
from math import isfinite

from tools.trackb_research.brake_policy_model import (WITHDRAWN as BRAKE_WITHDRAWN, BrakePolicyModel,
                                                      PolicyConfig, PolicyInput)
from tools.trackb_research.plan_controller_sim import (MODE_TRACKING, MODE_WITHDRAWN, PlanControllerSimulation, PlanSnapshot,
                                                       SimulationPolicy, VehicleObservation)
from tools.trackb_research.source_evidence_contracts import FRESH, StreamWindow, classify_stream

SIMULATION_ONLY = "simulation_only"
EVIDENCE_FRESH = "fresh_symbolic_hypothesis"
EVIDENCE_WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
  """Synthetic evidence windows and an explicit class; never authenticated ownership."""

  radar: StreamWindow
  camera: StreamWindow
  ownership_class: str
  aeb_cmbs_state: str


@dataclass(frozen=True, slots=True)
class ChainRecord:
  label: str
  evidence_class: str
  planner_mode: str
  brake_mode: str
  brake_reason: str
  requested_accel: float
  corrected_accel: float
  propulsion: float
  brake: float
  simulation_only: str = SIMULATION_ONLY


class OfflinePlannerChain:
  """Compose existing fail-closed models without changing either model's gates."""

  def __init__(self, plan_policy: SimulationPolicy, brake_config: PolicyConfig) -> None:
    self._plan_policy = plan_policy
    self._brake_config = brake_config
    self._planner = PlanControllerSimulation()
    self._brake = BrakePolicyModel(brake_config)
    self._brake_ready = False
    self._brake_rearm_pending = True
    self._brake_input_latched = True
    self._retired_tokens: set[str] = set()
    self._require_new_token = False
    self._step = -1
    self._last_plan = 1
    self._last_observation = 1
    self._last_now: float | None = None

  def reset(self) -> None:
    self._planner.reset()
    # Brake model remains fail-closed until explicit disengaged evidence is passed.
    self._brake = BrakePolicyModel(self._brake_config)
    self._brake_ready = False
    self._brake_rearm_pending = True
    self._brake_input_latched = True
    self._require_new_token = True
    self._step = -1
    # Keep the attempted-time high-water mark across logical resets.

  def advance(self, label: str, now: float, target: float, stopping: bool, standstill: bool,
              token: str | None, evidence: EvidenceBundle, *, stock_acc_enabled: bool = True,
              brake_pressed: bool = False, accelerator_pressed: bool = False, cancel_pressed: bool = False,
              fault: bool = False, v_ego: float | None = None, plan_published_monotonic: float | None = None,
              observation_monotonic: float | None = None) -> ChainRecord:
    # Record a high-water mark of ATTEMPTED decisions, not just accepted plans.
    # Faults, restarts and malformed observations must never rewind this clock.
    if (type(now) not in (float, int) or not isfinite(now) or
        (self._last_now is not None and now < self._last_now)):
      if token is not None:
        self._retired_tokens.add(token)
      self._require_new_token = True
      self._brake_ready = False
      self._brake_input_latched = True
      self._planner.reset()
      self._brake = BrakePolicyModel(self._brake_config)
      return ChainRecord(label, EVIDENCE_WITHDRAWN, MODE_WITHDRAWN, BRAKE_WITHDRAWN,
                         "decision_clock_invalid_or_reversed", 0.0, 0.0, 0.0, 0.0)
    self._last_now = now
    self._step += 1
    self._last_plan += 1
    self._last_observation += 1
    prior_now = self._last_now
    published = now if plan_published_monotonic is None else plan_published_monotonic
    observed = now if observation_monotonic is None else observation_monotonic
    evidence_class = self._evidence_class(evidence)
    plan = PlanSnapshot(self._last_plan, self._last_plan - 1, published, target, stopping, True, True,
                        evidence.radar.accepted > 0, False, "copied_synthetic_dom_plan", (1.0,), (target,), (0.0,))
    speed = (0.0 if standstill else 5.0) if v_ego is None else v_ego
    observation = VehicleObservation(self._last_observation, observed, speed, 0.0, standstill,
                                     brake_pressed, accelerator_pressed, cancel_pressed, evidence.aeb_cmbs_state,
                                     token, True, False, stock_acc_enabled)
    planner = self._planner.step(plan, observation, self._plan_policy, now)
    if fault and planner.mode != MODE_WITHDRAWN:
      planner = type(planner)(MODE_WITHDRAWN, None, "fault_withdrawal", plan.plan_log_monotonic,
                              observation.observation_log_monotonic)

    # Evidence withdrawal, unknown safety state, or fault is forwarded as a fault
    # to the numeric layer; no gate in either underlying model is bypassed.
    chain_fault = fault or evidence_class != EVIDENCE_FRESH or planner.mode == MODE_WITHDRAWN
    rearm_observation = not stock_acc_enabled and evidence_class == EVIDENCE_FRESH and not fault
    if evidence_class != EVIDENCE_FRESH:
      planner = type(planner)(MODE_WITHDRAWN, None, "evidence_not_fresh", plan.plan_log_monotonic,
                              observation.observation_log_monotonic)
    if fault or evidence_class != EVIDENCE_FRESH or planner.mode == MODE_WITHDRAWN:
      if token is not None and planner.mode == MODE_WITHDRAWN:
        self._retired_tokens.add(token)
      self._require_new_token = True
      self._brake_ready = False
      self._brake_rearm_pending = True
      self._brake_input_latched = True
    if token is not None and token in self._retired_tokens:
      planner = type(planner)(MODE_WITHDRAWN, None, "retired_engagement_token", plan.plan_log_monotonic,
                              observation.observation_log_monotonic)
      self._brake_ready = False
    if not stock_acc_enabled and token is None and evidence_class == EVIDENCE_FRESH and not fault:
      self._brake_ready = True
    if self._require_new_token and token is not None and token not in self._retired_tokens and planner.mode != MODE_WITHDRAWN:
      self._require_new_token = False
    elif self._require_new_token and token is not None:
      planner = type(planner)(MODE_WITHDRAWN, None, "new_engagement_required", plan.plan_log_monotonic,
                              observation.observation_log_monotonic)
    disengaged_rearm = not stock_acc_enabled and token is None and evidence_class == EVIDENCE_FRESH and not fault
    if disengaged_rearm:
      self._require_new_token = True
      self._brake_rearm_pending = False
      self._brake_input_latched = False
    # Retired tokens are permanent; never discard one when tracking resumes.
    request = planner.acceleration_request if planner.acceleration_request is not None else 0.0
    chain_fault = fault or evidence_class != EVIDENCE_FRESH or planner.mode == MODE_WITHDRAWN
    if disengaged_rearm:
      numeric = self._brake.step(PolicyInput(self._step, 0.0, 0.0, observation.v_ego, False,
                                            False, False, False, True))
    else:
      numeric = self._brake.step(PolicyInput(self._step, request, 0.0, observation.v_ego,
                                           stopping and planner.mode != MODE_WITHDRAWN,
                                           brake_pressed, accelerator_pressed, chain_fault,
                                           self._brake_input_latched))
    if disengaged_rearm:
      self._brake_input_latched = False
    if disengaged_rearm and numeric.reason == "rearmed_pending":
      self._brake_rearm_pending = False
    # A failure in the subordinate numeric policy must withdraw the WHOLE chain.
    # Otherwise a nominally tracking planner could coexist with invalid speed
    # or latched brake-policy state, an unsafe split-brain model contract.
    if numeric.mode == BRAKE_WITHDRAWN and planner.mode != MODE_WITHDRAWN:
      if token is not None:
        self._retired_tokens.add(token)
      self._planner.reset()
      self._require_new_token = True
      self._brake_ready = False
      self._brake_input_latched = True
      planner = type(planner)(MODE_WITHDRAWN, None, "subordinate_policy_withdrawn",
                              plan.plan_log_monotonic, observation.observation_log_monotonic)
    return ChainRecord(label, evidence_class, planner.mode, numeric.mode, numeric.reason,
                       numeric.requested_accel, numeric.corrected_accel, numeric.propulsion, numeric.brake)

  @staticmethod
  def _evidence_class(evidence: object) -> str:
    if type(evidence) is not EvidenceBundle or evidence.ownership_class != EVIDENCE_FRESH:
      return EVIDENCE_WITHDRAWN
    radar = classify_stream(evidence.radar, 0.1)
    camera = classify_stream(evidence.camera, 0.1)
    if radar in (FRESH,) and camera in (FRESH,) and evidence.aeb_cmbs_state == "clear":
      return EVIDENCE_FRESH
    # ABSENT, REJECTED, STALE and INVALID stay distinct in source_evidence_contracts;
    # for composition each causes withdrawal, never an ownership-transfer inference.
    return EVIDENCE_WITHDRAWN

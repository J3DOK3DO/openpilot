"""Pure, non-actuating Track B downstream-controller simulation.

This module accepts a synthetic representation of an already-published Dom
``longitudinalPlan`` and synthetic driver/vehicle observations.  It does not
plan a speed or trajectory: ``a_target`` is its sole planning input.  The
result is an abstract record for tests, never a CAN, Panda, vehicle, or runtime
command.  All limits and timeouts are test-owned symbolic values.
"""
from dataclasses import dataclass
from math import isfinite


MODE_WITHDRAWN = "withdrawn"
MODE_TRACKING = "tracking"
MODE_STOP_HOLD = "stop_hold"
_AEB_STATES = frozenset(("clear", "active", "unknown"))
_MAX_SYNTHETIC_FLOAT = 1.7976931348623157e308
_MAX_UINT64 = (1 << 64) - 1


@dataclass(frozen=True, slots=True)
class PlanSnapshot:
  """Synthetic shape of current Dom longitudinalPlan publication data."""

  plan_log_monotonic: int
  model_log_monotonic: int
  published_monotonic: float
  a_target: float
  should_stop: bool
  allow_brake: bool
  allow_throttle: bool
  has_lead: bool
  longitudinal_plan_source: str
  speeds: tuple[float, ...]
  accels: tuple[float, ...]
  jerks: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class VehicleObservation:
  """Synthetic driver and vehicle observation; no transport or vehicle types."""

  observation_log_monotonic: int
  observed_monotonic: float
  v_ego: float
  a_ego: float
  standstill: bool
  brake_pressed: bool
  accelerator_pressed: bool
  cancel_pressed: bool
  aeb_cmbs_state: str
  engagement_token: str | None
  valid: bool
  contradictory: bool
  stock_acc_enabled: bool


@dataclass(frozen=True, slots=True)
class SimulationPolicy:
  """Symbolic test limits, explicitly not vehicle calibration or OEM requirements."""

  max_plan_age: float
  max_observation_age: float
  abstract_accel_min: float
  abstract_accel_max: float
  standstill_speed: float


@dataclass(frozen=True, slots=True)
class SimulationRecord:
  """Non-actuating result only; acceleration_request has no physical meaning."""

  mode: str
  acceleration_request: float | None
  reason: str
  plan_log_monotonic: int | None
  observation_log_monotonic: int | None


class PlanControllerSimulation:
  """Fail-closed state machine downstream of a synthetic Dom plan.

  Dom ``a_target`` is the sole acceleration-magnitude input. ``should_stop``
  is an existing plan mode signal, used only to select abstract downstream
  standstill-hold behavior; it is not a second planner. Tokens retired by a
  withdrawal or reset remain rejected for the simulator lifetime. Within an
  active logical session, the accepted token is stable; only recovery may
  introduce a new, never-retired token. The output is never an actuator
  command.
  """

  def __init__(self) -> None:
    self._last_plan_id: int | None = None
    self._last_observation_id: int | None = None
    self._last_decision_time: float | int | None = None
    self._retired_tokens: set[str] = set()
    self._last_accepted_token: str | None = None
    # Construction has no prior accepted engagement, so no fresh-token barrier.
    self._requires_fresh_token = False

  def reset(self) -> None:
    """Create a deterministic logical fault boundary without recycling a token.

    Reset clears ordering identifiers only. It retires the last accepted token
    and preserves every token retired for the simulator lifetime, requiring a
    new, never-retired token when an engagement existed before the reset.
    """
    self._last_plan_id: int | None = None
    self._last_observation_id: int | None = None
    if self._last_accepted_token is not None:
      self._retired_tokens.add(self._last_accepted_token)
      self._requires_fresh_token = True

  def step(self, plan: object, observation: object, policy: object, now_monotonic: object) -> SimulationRecord:
    reason = _input_reason(plan, observation, policy, now_monotonic)
    if reason is None:
      reason = self._state_reason(plan, observation, policy, now_monotonic)
    if reason is not None:
      self._withdraw(observation)
      return _withdrawn(reason, plan, observation)

    self._last_plan_id = plan.plan_log_monotonic
    self._last_observation_id = observation.observation_log_monotonic
    self._last_decision_time = now_monotonic
    self._requires_fresh_token = False
    self._last_accepted_token = observation.engagement_token

    if plan.should_stop and observation.standstill:
      return SimulationRecord(MODE_STOP_HOLD, 0.0, "plan_should_stop_selects_abstract_hold", plan.plan_log_monotonic, observation.observation_log_monotonic)

    request = min(max(plan.a_target, policy.abstract_accel_min), policy.abstract_accel_max)
    return SimulationRecord(MODE_TRACKING, request, "dom_a_target_only", plan.plan_log_monotonic, observation.observation_log_monotonic)

  def _state_reason(self, plan: PlanSnapshot, observation: VehicleObservation, policy: SimulationPolicy, now_monotonic: float) -> str | None:
    if self._last_decision_time is not None and now_monotonic < self._last_decision_time:
      return "decision_clock_reversed"
    if self._last_plan_id is not None and plan.plan_log_monotonic <= self._last_plan_id:
      return "duplicate_or_out_of_order_plan"
    if self._last_observation_id is not None and observation.observation_log_monotonic <= self._last_observation_id:
      return "duplicate_or_out_of_order_observation"
    if now_monotonic - plan.published_monotonic > policy.max_plan_age:
      return "stale_plan"
    if now_monotonic - observation.observed_monotonic > policy.max_observation_age:
      return "stale_observation"
    if not observation.valid:
      return "observation_invalid"
    if observation.contradictory or (observation.standstill and observation.v_ego > policy.standstill_speed):
      return "contradictory_observation"
    if not observation.stock_acc_enabled:
      return "stock_acc_disengaged"
    if observation.aeb_cmbs_state != "clear":
      return "aeb_cmbs_not_clear"
    if observation.brake_pressed or observation.accelerator_pressed:
      return "driver_pedal_override"
    if observation.cancel_pressed:
      return "driver_cancel"
    if not plan.allow_brake and plan.a_target < 0.0:
      return "brake_denied"
    if not plan.allow_throttle and plan.a_target > 0.0:
      return "throttle_denied"
    if observation.engagement_token is None:
      return "engagement_token_missing"
    if observation.engagement_token in self._retired_tokens:
      return "retired_engagement_token"
    if (not self._requires_fresh_token and self._last_accepted_token is not None and
        observation.engagement_token != self._last_accepted_token):
      return "engagement_token_changed_without_recovery"
    return None

  def _withdraw(self, observation: object) -> None:
    if self._last_accepted_token is not None:
      self._retired_tokens.add(self._last_accepted_token)
    self._requires_fresh_token = True
    if type(observation) is VehicleObservation and _label(observation.engagement_token):
      self._retired_tokens.add(observation.engagement_token)


def _input_reason(plan: object, observation: object, policy: object, now_monotonic: object) -> str | None:
  if type(plan) is not PlanSnapshot:
    return "plan_type_invalid"
  if type(observation) is not VehicleObservation:
    return "observation_type_invalid"
  if type(policy) is not SimulationPolicy:
    return "policy_type_invalid"
  if not _finite_synthetic_number(now_monotonic):
    return "decision_time_invalid"
  if not _plan_valid(plan):
    return "plan_invalid"
  if not _observation_valid(observation):
    return "observation_shape_invalid"
  if not _policy_valid(policy):
    return "policy_invalid"
  if plan.model_log_monotonic > plan.plan_log_monotonic or plan.published_monotonic > now_monotonic or observation.observed_monotonic > now_monotonic:
    return "timestamp_inconsistent"
  return None


def _plan_valid(plan: PlanSnapshot) -> bool:
  return (_positive_uint64(plan.plan_log_monotonic) and _positive_uint64(plan.model_log_monotonic) and
          _finite_synthetic_number(plan.published_monotonic) and _finite_synthetic_number(plan.a_target) and
          all(type(value) is bool for value in (plan.should_stop, plan.allow_brake, plan.allow_throttle, plan.has_lead)) and
          _label(plan.longitudinal_plan_source) and _equal_nonempty_series(plan.speeds, plan.accels, plan.jerks))


def _observation_valid(observation: VehicleObservation) -> bool:
  return (_positive_uint64(observation.observation_log_monotonic) and
          _finite_synthetic_number(observation.observed_monotonic) and
          _finite_synthetic_number(observation.v_ego) and _finite_synthetic_number(observation.a_ego) and
          all(type(value) is bool for value in (observation.standstill, observation.brake_pressed, observation.accelerator_pressed,
                                                observation.cancel_pressed, observation.valid, observation.contradictory,
                                                observation.stock_acc_enabled)) and
          type(observation.aeb_cmbs_state) is str and observation.aeb_cmbs_state in _AEB_STATES and
          (observation.engagement_token is None or _label(observation.engagement_token)))


def _policy_valid(policy: SimulationPolicy) -> bool:
  return (_finite_synthetic_number(policy.max_plan_age) and policy.max_plan_age >= 0.0 and
          _finite_synthetic_number(policy.max_observation_age) and policy.max_observation_age >= 0.0 and
          _finite_synthetic_number(policy.abstract_accel_min) and _finite_synthetic_number(policy.abstract_accel_max) and
          policy.abstract_accel_min <= policy.abstract_accel_max and
          _finite_synthetic_number(policy.standstill_speed) and policy.standstill_speed >= 0.0)


def _finite_series(values: object) -> bool:
  return type(values) is tuple and all(_finite_synthetic_number(value) for value in values)


def _equal_nonempty_series(*series: object) -> bool:
  return all(_finite_series(values) for values in series) and len(series[0]) > 0 and len({len(values) for values in series}) == 1


def _finite_synthetic_number(value: object) -> bool:
  """Accept representable synthetic float-field values without int-to-float overflow."""
  if type(value) is int:
    return -_MAX_SYNTHETIC_FLOAT <= value <= _MAX_SYNTHETIC_FLOAT
  return type(value) is float and isfinite(value)


def _positive_uint64(value: object) -> bool:
  """Validate monotonic synthetic identifiers in their UInt64-shaped domain."""
  return type(value) is int and 0 < value <= _MAX_UINT64


def _label(value: object) -> bool:
  return type(value) is str and bool(value) and value == value.strip()


def _withdrawn(reason: str, plan: object, observation: object) -> SimulationRecord:
  plan_id = plan.plan_log_monotonic if type(plan) is PlanSnapshot else None
  observation_id = observation.observation_log_monotonic if type(observation) is VehicleObservation else None
  return SimulationRecord(MODE_WITHDRAWN, None, reason, plan_id, observation_id)

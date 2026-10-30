"""Pure synthetic Track B eligibility research; it has no vehicle authority.

This standalone module accepts caller-supplied synthetic observations and returns
only an analytical eligibility label and reason. It does not encode, transmit,
persist, or request anything.
"""
from dataclasses import dataclass
from math import isfinite
import sys


ELIGIBLE_FOR_ANALYSIS = "eligible_for_analysis"
WITHDRAWN_UNKNOWN = "withdrawn/unknown"
_AEB_CMBS_STATES = frozenset(("clear", "active", "unknown"))
_MAX_FINITE_FLOAT = sys.float_info.max


@dataclass(frozen=True, slots=True)
class Observation:
  """An immutable, entirely synthetic observation supplied by a test."""

  observation_id: str
  acquisition_monotonic: float
  decision_monotonic: float
  valid: bool
  aeb_cmbs_state: str
  brake_pressed: bool
  accelerator_pressed: bool
  cancel_pressed: bool
  acc_main_on: bool
  engagement_token: str | None
  signal_conflict: bool
  lead_present: bool | None
  latency: float | None


@dataclass(frozen=True, slots=True)
class ExpiryPolicy:
  """A test-owned symbolic expiry bound, not a vehicle timing requirement."""

  stale_after: float


@dataclass(frozen=True, slots=True)
class Eligibility:
  """The only result: an analytical label and an explanatory reason."""

  eligibility: str
  reason: str


class ShadowEligibility:
  """Stateful ordering and logical-withdrawal checker for synthetic records.

  A withdrawal latches every valid explicit token seen until a later eligible
  record supplies a different token. This is only a logical test transition;
  it does not assert a physical driver handback.
  """

  def __init__(self) -> None:
    self._seen_ids: set[str] = set()
    self._last_acquisition: float | int | None = None
    self._last_decision: float | int | None = None
    self._blocked_tokens: set[str] = set()
    self._last_accepted_token: str | None = None
    self._requires_new_token = False

  def evaluate(self, observation: object, expiry_policy: object) -> Eligibility:
    """Fail closed on one wholly validated synthetic record and policy.

    Malformed inputs never raise or update ordering state. Validly shaped fault
    records do update ordering and poison their explicit tokens atomically with
    their withdrawal, so later malformed inputs cannot recycle an old token.
    """
    observation_reason = _observation_shape_reason(observation)
    policy_reason = _policy_shape_reason(expiry_policy)
    if observation_reason is not None:
      self._withdraw(None)
      return _withdrawn(observation_reason)
    if policy_reason is not None:
      self._withdraw(observation)
      return _withdrawn(policy_reason)

    result = self._evaluate_valid_shapes(observation, expiry_policy)
    if result.eligibility == WITHDRAWN_UNKNOWN:
      self._withdraw(observation)
    else:
      self._requires_new_token = False
      self._blocked_tokens.clear()
      self._last_accepted_token = observation.engagement_token
    self._remember(observation)
    return result

  def _withdraw(self, observation: Observation | None) -> None:
    if not self._requires_new_token and self._last_accepted_token is not None:
      self._blocked_tokens.add(self._last_accepted_token)
    self._requires_new_token = True
    if observation is not None and observation.engagement_token is not None:
      self._blocked_tokens.add(observation.engagement_token)

  def _evaluate_valid_shapes(self, observation: Observation, expiry_policy: ExpiryPolicy) -> Eligibility:
    if observation.observation_id in self._seen_ids:
      return _withdrawn("duplicate_or_missing_observation_id")
    if observation.decision_monotonic < observation.acquisition_monotonic:
      return _withdrawn("clock_jump_or_negative_age")
    if self._last_acquisition is not None and observation.acquisition_monotonic <= self._last_acquisition:
      return _withdrawn("out_of_order_acquisition")
    if self._last_decision is not None and observation.decision_monotonic < self._last_decision:
      return _withdrawn("clock_jump_backwards")
    if observation.decision_monotonic - observation.acquisition_monotonic >= expiry_policy.stale_after:
      return _withdrawn("stale_observation")
    if observation.latency is None:
      return _withdrawn("latency_unknown")
    if observation.latency < 0:
      return _withdrawn("latency_invalid")
    if not observation.valid:
      return _withdrawn("observation_invalid")
    if observation.signal_conflict:
      return _withdrawn("signal_conflict")
    if observation.aeb_cmbs_state not in _AEB_CMBS_STATES or observation.aeb_cmbs_state != "clear":
      return _withdrawn("aeb_cmbs_not_clear")
    if observation.brake_pressed or observation.accelerator_pressed:
      return _withdrawn("driver_pedal_override")
    if observation.cancel_pressed:
      return _withdrawn("driver_cancel")
    if not observation.acc_main_on:
      return _withdrawn("acc_main_off")
    if observation.engagement_token is None:
      return _withdrawn("engagement_token_missing")
    if self._requires_new_token and observation.engagement_token in self._blocked_tokens:
      return _withdrawn("fresh_engagement_token_required")
    return Eligibility(ELIGIBLE_FOR_ANALYSIS, "synthetic_inputs_clear")

  def _remember(self, observation: Observation) -> None:
    self._seen_ids.add(observation.observation_id)
    self._last_acquisition = observation.acquisition_monotonic
    self._last_decision = observation.decision_monotonic


def _observation_shape_reason(observation: object) -> str | None:
  if type(observation) is not Observation:
    return "observation_type_invalid"
  if not _nonblank_stripped_string(observation.observation_id):
    return "observation_id_invalid"
  if not _finite_number(observation.acquisition_monotonic) or not _finite_number(observation.decision_monotonic):
    return "nonfinite_monotonic_timestamp"
  if type(observation.valid) is not bool or type(observation.brake_pressed) is not bool or type(observation.accelerator_pressed) is not bool:
    return "boolean_field_invalid"
  if type(observation.cancel_pressed) is not bool or type(observation.acc_main_on) is not bool or type(observation.signal_conflict) is not bool:
    return "boolean_field_invalid"
  if observation.lead_present is not None and type(observation.lead_present) is not bool:
    return "lead_present_invalid"
  if type(observation.aeb_cmbs_state) is not str:
    return "aeb_cmbs_state_invalid"
  if observation.engagement_token is not None and not _nonblank_stripped_string(observation.engagement_token):
    return "engagement_token_invalid"
  if observation.latency is not None and not _finite_number(observation.latency):
    return "latency_invalid"
  return None


def _policy_shape_reason(expiry_policy: object) -> str | None:
  if type(expiry_policy) is not ExpiryPolicy:
    return "expiry_policy_type_invalid"
  if not _finite_number(expiry_policy.stale_after) or expiry_policy.stale_after < 0:
    return "expiry_policy_invalid"
  return None


def _nonblank_stripped_string(value: object) -> bool:
  return type(value) is str and bool(value) and value == value.strip()


def _finite_number(value: object) -> bool:
  if type(value) is int:
    return -_MAX_FINITE_FLOAT <= value <= _MAX_FINITE_FLOAT
  return type(value) is float and isfinite(value)


def _withdrawn(reason: str) -> Eligibility:
  return Eligibility(WITHDRAWN_UNKNOWN, reason)

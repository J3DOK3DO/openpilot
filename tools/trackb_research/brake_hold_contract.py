"""Synthetic brake/gas/hold contract for Track B research only.

It evaluates abstract inputs and emits no vehicle command, calibration, or transport data.
"""

from dataclasses import dataclass
from math import isfinite

MODE_WITHDRAWN = "withdrawn"
MODE_COAST = "coast"
MODE_ABSTRACT_BRAKE = "abstract_brake"
MODE_ABSTRACT_HOLD = "abstract_hold"


@dataclass(frozen=True, slots=True)
class BrakeContractInput:
  decision_id: int
  requested_acceleration: float
  v_ego: float
  standstill: bool
  brake_pressed: bool
  accelerator_pressed: bool
  stock_acc_enabled: bool
  aeb_cmbs_clear: bool
  valid: bool


@dataclass(frozen=True, slots=True)
class BrakeContractPolicy:
  symbolic_brake_entry: float
  symbolic_brake_release: float
  symbolic_standstill_speed: float


@dataclass(frozen=True, slots=True)
class BrakeContractRecord:
  mode: str
  abstract_request: float | None
  reason: str


class BrakeHoldContract:
  """Fail-closed contract with hysteresis; all thresholds are test-owned symbols."""

  def __init__(self) -> None:
    self._last_id: int | None = None
    self._braking = False

  def _withdraw(self, reason: str) -> BrakeContractRecord:
    # A rejected event must never retain hysteresis from the prior accepted session.
    self._braking = False
    return BrakeContractRecord(MODE_WITHDRAWN, None, reason)

  def step(self, candidate: object, policy: object) -> BrakeContractRecord:
    if type(candidate) is not BrakeContractInput or type(policy) is not BrakeContractPolicy:
      return self._withdraw("input_type_invalid")
    if not _valid(candidate, policy):
      return self._withdraw("input_invalid")
    if self._last_id is not None and candidate.decision_id <= self._last_id:
      return self._withdraw("duplicate_or_out_of_order_decision")
    self._last_id = candidate.decision_id
    if not candidate.valid or not candidate.stock_acc_enabled or not candidate.aeb_cmbs_clear:
      return self._withdraw("authority_or_safety_gate_denied")
    if candidate.brake_pressed or candidate.accelerator_pressed:
      return self._withdraw("driver_override")
    if candidate.standstill:
      self._braking = False
      return BrakeContractRecord(MODE_ABSTRACT_HOLD, 0.0, "synthetic_standstill_hold")
    if candidate.requested_acceleration <= policy.symbolic_brake_entry:
      self._braking = True
    elif self._braking and candidate.requested_acceleration >= policy.symbolic_brake_release:
      self._braking = False
    if self._braking:
      return BrakeContractRecord(MODE_ABSTRACT_BRAKE, candidate.requested_acceleration, "symbolic_brake_hysteresis")
    return BrakeContractRecord(MODE_COAST, candidate.requested_acceleration, "abstract_no_brake")


def _valid(candidate: BrakeContractInput, policy: BrakeContractPolicy) -> bool:
  floats = (candidate.requested_acceleration, candidate.v_ego, policy.symbolic_brake_entry, policy.symbolic_brake_release, policy.symbolic_standstill_speed)
  booleans = (
    candidate.standstill,
    candidate.brake_pressed,
    candidate.accelerator_pressed,
    candidate.stock_acc_enabled,
    candidate.aeb_cmbs_clear,
    candidate.valid,
  )
  return (
    type(candidate.decision_id) is int
    and candidate.decision_id > 0
    and all(type(value) is float and isfinite(value) for value in floats)
    and all(type(value) is bool for value in booleans)
    and policy.symbolic_brake_entry <= policy.symbolic_brake_release <= 0.0
    and policy.symbolic_standstill_speed >= 0.0
    and candidate.v_ego >= 0.0
    and (not candidate.standstill or candidate.v_ego <= policy.symbolic_standstill_speed)
  )

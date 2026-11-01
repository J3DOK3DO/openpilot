"""Numeric offline model of the retained Accord brake/propulsion policy layer (DRV-001 to DRV-010).

The earlier mvl_retained_sim models only label these requirements. This model computes them numerically so their
interactions (hysteresis, integrator, relaxation, override, fault latch) can be property-tested together. Reference
behaviour: Dom's classic-Bosch hysteresis (opendbc/car/honda/bosch_longitudinal.py) and MVL 3fec9a's Bosch extra
brake integrator (carcontroller.py), both COMMUNITY_SOURCE_ONLY for the 11G.

Everything is stdlib-only. Inputs and outputs are abstract accelerations in m/s^2; every bound is a caller-owned
synthetic value, never a calibration. There is no frame, signal, bus, CAN, UDS or actuator type, and nothing here
is reachable from production code. A passing result is model consistency, not vehicle qualification.
"""

from dataclasses import dataclass
from math import isfinite

WITHDRAWN = "withdrawn"
COAST = "coast"
PROPEL = "propel"
BRAKE = "brake"


@dataclass(frozen=True, slots=True)
class PolicyConfig:
  accel_min: float               # lower clip of the corrected request (negative)
  accel_max: float               # upper clip (positive)
  brake_entry: float             # DRV-001 enter braking below this force (negative)
  brake_release: float           # DRV-001 braking may release above this force (brake_entry < it <= 0)
  meaningful_brake: float        # DRV-002 at or below this force braking starts at once (<= brake_entry)
  release_steps: int             # DRV-004 consecutive release-eligible steps before release
  low_speed: float               # DRV-006 integrator window upper speed (m/s)
  integrator_gain: float         # DRV-006 per-step gain on (requested - measured)
  integrator_floor: float        # DRV-006 most negative integrator value
  integrator_relax: float        # DRV-007 per-step return toward zero outside the window
  brake_relax_step: float        # DRV-009 most the brake magnitude may fall in one step
  standstill_tolerance: float    # DRV-010 |v| at or below this is standstill; below -it is invalid


@dataclass(frozen=True, slots=True)
class PolicyInput:
  step: int                      # strictly increasing
  requested_accel: float         # planner request
  measured_accel: float
  v_ego: float
  stopping: bool
  driver_brake: bool
  driver_gas: bool
  fault: bool                    # any upstream fault: latches withdrawal
  stock_acc_disengaged: bool     # explicit rearm evidence (DRV-007)


@dataclass(frozen=True, slots=True)
class PolicyDecision:
  mode: str
  reason: str
  requested_accel: float         # DRV-008 kept separate from the corrected value
  corrected_accel: float
  propulsion: float              # >= 0, never with brake (DRV-005)
  brake: float                   # >= 0 magnitude
  integrator: float


def _finite(value: object) -> bool:
  return type(value) in (int, float) and isfinite(value)


def config_valid(cfg: object) -> bool:
  if type(cfg) is not PolicyConfig:
    return False
  numbers = (cfg.accel_min, cfg.accel_max, cfg.brake_entry, cfg.brake_release, cfg.meaningful_brake, cfg.low_speed,
             cfg.integrator_gain, cfg.integrator_floor, cfg.integrator_relax, cfg.brake_relax_step,
             cfg.standstill_tolerance)
  if not all(_finite(v) for v in numbers) or type(cfg.release_steps) is not int or cfg.release_steps < 1:
    return False
  return (cfg.accel_min < 0 < cfg.accel_max and cfg.accel_min <= cfg.meaningful_brake <= cfg.brake_entry <
          cfg.brake_release <= 0 and cfg.low_speed > 0 and cfg.integrator_gain >= 0 and
          cfg.integrator_floor <= 0 and cfg.integrator_relax > 0 and cfg.brake_relax_step > 0 and
          cfg.standstill_tolerance >= 0)


def _input_valid(inp: object) -> bool:
  if type(inp) is not PolicyInput or type(inp.step) is not int or inp.step < 0:
    return False
  if not all(_finite(v) for v in (inp.requested_accel, inp.measured_accel, inp.v_ego)):
    return False
  return all(type(v) is bool for v in (inp.stopping, inp.driver_brake, inp.driver_gas, inp.fault,
                                       inp.stock_acc_disengaged))


class BrakePolicyModel:
  """One instance per simulated engagement. Starts latched: it acts only after explicit rearm evidence."""

  def __init__(self, cfg: PolicyConfig) -> None:
    if not config_valid(cfg):
      raise ValueError("invalid synthetic policy config")
    self._cfg = cfg
    self._last_step: int | None = None
    self._latched = True
    self._reset()

  def _reset(self) -> None:
    self._braking = False
    self._brake = 0.0
    self._integrator = 0.0
    self._release_count = 0

  def _withdraw(self, reason: str, inp: object, latch: bool) -> PolicyDecision:
    if latch:
      self._latched = True
    self._reset()
    requested = inp.requested_accel if type(inp) is PolicyInput and _finite(inp.requested_accel) else 0.0
    return PolicyDecision(WITHDRAWN, reason, float(requested), 0.0, 0.0, 0.0, 0.0)

  def step(self, inp: object) -> PolicyDecision:
    cfg = self._cfg
    if not _input_valid(inp):
      return self._withdraw("input_invalid", inp, True)
    if self._last_step is not None and inp.step <= self._last_step:
      return self._withdraw("step_not_increasing", inp, True)
    self._last_step = inp.step
    if inp.v_ego < -cfg.standstill_tolerance:
      return self._withdraw("negative_speed_beyond_tolerance", inp, True)
    if inp.fault:
      return self._withdraw("fault_latched", inp, True)
    if self._latched:
      if inp.stock_acc_disengaged:
        # Rearm takes effect on the next step: the rearm observation itself never produces output.
        self._latched = False
        return self._withdraw("rearmed_pending", inp, False)
      return self._withdraw("awaiting_rearm", inp, False)
    if inp.driver_brake or inp.driver_gas:
      return self._withdraw("driver_override", inp, False)

    v = 0.0 if abs(inp.v_ego) <= cfg.standstill_tolerance else inp.v_ego
    requested = inp.requested_accel

    # DRV-006/007: extra negative integrator only while slowing at low speed; otherwise it relaxes to zero.
    if requested < 0 and 0 < v < cfg.low_speed:
      self._integrator += cfg.integrator_gain * (requested - inp.measured_accel)
    else:
      self._integrator += cfg.integrator_relax
    self._integrator = min(0.0, max(cfg.integrator_floor, self._integrator))

    # DRV-008: corrected never exceeds the request.
    corrected = min(requested, requested + self._integrator)
    corrected = min(cfg.accel_max, max(cfg.accel_min, corrected))

    reason = self._select(requested, corrected, inp.stopping)
    # DRV-003: a positive request contributes no brake target; an existing brake may only fade (DRV-009).
    target = max(0.0, -corrected) if (self._braking or inp.stopping) and (requested <= 0 or inp.stopping) else 0.0
    # DRV-009: brake magnitude rises at once but falls at most brake_relax_step per step.
    brake = max(target, self._brake - cfg.brake_relax_step, 0.0)
    if not self._braking and brake > 0.0:
      reason = "brake_relaxing"
    self._brake = brake
    if brake > 0.0:
      return PolicyDecision(BRAKE, reason, float(requested), float(corrected), 0.0, float(brake), self._integrator)
    if corrected > 0.0 and not self._braking:
      return PolicyDecision(PROPEL, reason, float(requested), float(corrected), float(corrected), 0.0,
                            self._integrator)
    return PolicyDecision(COAST, reason, float(requested), float(corrected), 0.0, 0.0, self._integrator)

  def _select(self, requested: float, corrected: float, stopping: bool) -> str:
    cfg = self._cfg
    if stopping:
      self._braking, self._release_count = True, 0
      return "stopping"
    if not self._braking:
      if requested > 0:
        # DRV-003: a positive request never re-enters braking, whatever the corrected value.
        return "positive_request_no_brake_entry"
      if corrected <= cfg.meaningful_brake:
        self._braking, self._release_count = True, 0
        return "meaningful_brake_immediate"
      if corrected < cfg.brake_entry:
        self._braking, self._release_count = True, 0
        return "brake_entry"
      return "no_brake"
    if corrected > cfg.brake_release or requested > 0:
      self._release_count += 1
      if self._release_count >= cfg.release_steps:
        self._braking, self._release_count = False, 0
        return "brake_released"
      return "brake_release_debounce"
    self._release_count = 0
    return "braking"

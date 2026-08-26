"""Validated MVL longitudinal output controller for the Honda Accord 11G.

This is deliberately isolated from StarPilot's shared longitudinal tuning. Honda
CAN command generation, including its low-speed brake PID, remains in the native
Honda CarController.
"""

import numpy as np

from cereal import car
from openpilot.common.pid import PIDController
from openpilot.common.realtime import DT_CTRL


LongCtrlState = car.CarControl.Actuators.LongControlState


def mvl_long_control_state_trans(CP, active, long_control_state, should_stop, brake_pressed, cruise_standstill):
  cruise_standstill = cruise_standstill and not bool(getattr(CP, "enableGasInterceptorDEPRECATED", False))
  release_condition = not should_stop and not cruise_standstill and not brake_pressed

  if not active:
    return LongCtrlState.off
  if long_control_state == LongCtrlState.off:
    return LongCtrlState.pid if release_condition else LongCtrlState.stopping
  if long_control_state == LongCtrlState.stopping and release_condition:
    return LongCtrlState.pid
  if long_control_state == LongCtrlState.pid and should_stop:
    return LongCtrlState.stopping
  return long_control_state


class MVLAccordLongControl:
  """Accord-only acceleration PID and validated stop/release state machine."""

  def __init__(self, CP):
    self.CP = CP
    self.long_control_state = LongCtrlState.off
    self.experimental_mode = False  # controlsd compatibility; intentionally unused
    self.pid = PIDController(
      (CP.longitudinalTuning.kpBP, CP.longitudinalTuning.kpV),
      (CP.longitudinalTuning.kiBP, CP.longitudinalTuning.kiV),
      rate=1 / DT_CTRL,
    )
    self.last_output_accel = 0.0

  def reset(self, *args, **kwargs):
    del args, kwargs
    self.pid.reset()

  def update(self, active, CS, a_target, should_stop, accel_limits, *args, **kwargs):
    # Accept the current generic LongControl call signature, but deliberately do
    # not apply shared traffic/profile/lead/pedal shaping to the Accord route.
    del args, kwargs
    self.pid.neg_limit = accel_limits[0]
    self.pid.pos_limit = accel_limits[1]

    self.long_control_state = mvl_long_control_state_trans(
      self.CP, active, self.long_control_state, should_stop,
      CS.brakePressed, CS.cruiseState.standstill,
    )

    if self.long_control_state == LongCtrlState.off:
      self.reset()
      output_accel = 0.0
    elif self.long_control_state == LongCtrlState.stopping:
      output_accel = self.last_output_accel
      if output_accel > self.CP.stopAccel:
        output_accel = min(output_accel, 0.0) - DT_CTRL
      self.reset()
    else:
      error = a_target - CS.aEgo
      output_accel = self.pid.update(error, speed=CS.vEgo, feedforward=a_target)

    self.last_output_accel = float(np.clip(output_accel, accel_limits[0], accel_limits[1]))
    return self.last_output_accel

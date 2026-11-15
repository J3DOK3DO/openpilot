import math

from opendbc.car import structs
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.car.cruise import CRUISE_LONG_PRESS
from openpilot.starpilot.aol.intent import AolCardIntent, AOL_TOGGLE, ButtonType


def accord11g_stationary_aol_inhibit(CP, CS, *, standard_lateral: bool = False) -> bool:
  """Veto lateral-only operation at low speed on Accord 11G."""
  if CP.carFingerprint != CAR.HONDA_ACCORD_11G or standard_lateral:
    return False
  try:
    v_ego = float(CS.vEgo)
    min_steer = float(CP.minSteerSpeed)
    if not math.isfinite(v_ego) or not math.isfinite(min_steer) or v_ego < 0 or min_steer < 0:
      return True
    return bool(CS.standstill or v_ego <= max(0.3, min_steer))
  except (AttributeError, TypeError, ValueError, OverflowError):
    return True


class HondaStockCardIntent(AolCardIntent):
  observe_stock_engagement = True

  def __init__(self, cp, settings):
    super().__init__(settings, explicit_latch=True)
    self.main_seen = False
    self.main_available = False
    self.main_neutral = False
    self.main_pulse = False
    self.cancel_held = False
    self.cancel_ticks = 0
    self.auto_main = settings.lkas_action != AOL_TOGGLE and settings.main_action != AOL_TOGGLE
    self.accord11g = cp.carFingerprint == CAR.HONDA_ACCORD_11G
    self.cp = cp

  def _clear_ineligible_accord11g_latch(self, CS):
    if not self.accord11g:
      return
    reason = ('accord11g_non_drive_gear' if CS.gearShifter != structs.CarState.GearShifter.drive else
              'accord11g_stationary' if accord11g_stationary_aol_inhibit(self.cp, CS) else '')
    if reason:
      self._record_latch_clear(reason)
      self.allowed_latch = False
      self._gesture_neutral_seen = False

  def observe_full_engagement(self, CS, **kwargs):
    super().observe_full_engagement(CS, **kwargs)
    self._clear_ineligible_accord11g_latch(CS)

  def cancel_action(self, action):
    if action == AOL_TOGGLE and self.settings.enabled:
      self.allowed_latch = not self.allowed_latch
      if self.allowed_latch:
        self.pause_lateral = False
    else:
      self._perform(action)

  def update(self, CS, **kwargs):
    state = CS
    events = []
    for event in CS.buttonEvents:
      if event.type == ButtonType.cancel:
        if event.pressed:
          self.cancel_held = True
          self.cancel_ticks = 0
        else:
          if self.cancel_held and 0 < self.cancel_ticks < CRUISE_LONG_PRESS:
            self.cancel_action(self.settings.cancel_actions[0])
          self.cancel_held = False
          self.cancel_ticks = 0
      elif event.type in (ButtonType.mainCruise, ButtonType.lkas):
        action = self.settings.main_action if event.type == ButtonType.mainCruise else self.settings.lkas_action
        if action == AOL_TOGGLE:
          events.append(structs.CarState.ButtonEvent(**event.to_dict()))
        elif event.pressed:
          self._perform(action)
      else:
        events.append(structs.CarState.ButtonEvent(**event.to_dict()))
    available = bool(CS.cruiseState.available)
    healthy = CS.canValid and not CS.canTimeout
    if healthy:
      if self.main_pulse:
        events.append(structs.CarState.ButtonEvent(type=ButtonType.mainCruise, pressed=False))
        self.main_pulse = False
      if not available:
        self.main_neutral = True
      elif self.auto_main and self.main_seen and self.main_neutral and not self.main_available:
        events.append(structs.CarState.ButtonEvent(type=ButtonType.mainCruise, pressed=True))
        self.main_pulse = True
        self.main_neutral = False
      self.main_seen = True
      self.main_available = available
    else:
      self.cancel_held = False
      self.cancel_ticks = 0
      self.main_neutral = False
    if events or len(CS.buttonEvents):
      # Copy only when button events are rewritten; most frames have none.
      state = structs.CarState(**CS.to_dict())
      state.buttonEvents = events
      CS = state.as_reader()
    super().update(CS, **kwargs)
    if self.cancel_held:
      self.cancel_ticks += 1
      if self.cancel_ticks == CRUISE_LONG_PRESS:
        self.cancel_action(self.settings.cancel_actions[1])
      elif self.cancel_ticks == CRUISE_LONG_PRESS * 5:
        self.cancel_action(self.settings.cancel_actions[2])
    # Apply the final guard after CANCEL actions, which may otherwise re-arm
    # the latch later in this same update.
    if not available:
      self._record_latch_clear('cruise_unavailable')
      self.allowed_latch = False
    if self.accord11g and self._fault_inhibit:
      self._record_latch_clear('accord11g_fault')
      self.allowed_latch = False
      self._gesture_neutral_seen = False
    self._clear_ineligible_accord11g_latch(CS)

from types import SimpleNamespace

from openpilot.selfdrive.controls.lib.longcontrol import LongControl, LongCtrlState


class FakePID:
  def __init__(self, output):
    self.output = output
    self.freeze_calls = []
    self.reset_calls = 0

  def reset(self):
    self.reset_calls += 1

  def update(self, error, speed, feedforward, freeze_integrator=False):
    self.freeze_calls.append(bool(freeze_integrator))
    return float(self.output)


def build_accord_longcontrol():
  lc = LongControl.__new__(LongControl)

  lc.CP = SimpleNamespace(
    enableGasInterceptorDEPRECATED=False,
    stopAccel=-1.5,
  )

  lc.long_control_state = LongCtrlState.pid
  lc.last_output_accel = 0.2
  lc.experimental_mode = False

  lc.prev_mode = "acc"
  lc.current_mode = "acc"
  lc.transitioning = False
  lc.mode_transition_timer = 0.0
  lc.mode_transition_duration = 1.0
  lc.mode_transition_filter = SimpleNamespace(x=0.0)

  lc.pid = FakePID(0.1)

  return lc


def car_state():
  return SimpleNamespace(
    aEgo=0.0,
    vEgo=10.0,
    brakePressed=False,
    cruiseState=SimpleNamespace(standstill=False),
  )


def test_accord_blended_to_acc_transition_is_reachable_and_slews_positive_output():
  lc = build_accord_longcontrol()
  cs = car_state()

  # Enter blended/experimental first.
  lc.experimental_mode = True

  first = lc._update_honda_accord_11g(
    True,
    cs,
    a_target=0.1,
    should_stop=False,
    accel_limits=(-3.5, 2.0),
  )

  assert lc.prev_mode == "acc"
  assert lc.current_mode == "blended"
  assert lc.transitioning
  assert not lc.pid.freeze_calls[-1]
  assert first == 0.1

  # Then leave experimental mode. This is the N15/B4 transition
  # consumed by controlsd and GasAlpha.
  lc.experimental_mode = False
  lc.pid.output = 1.0

  before = lc.last_output_accel

  second = lc._update_honda_accord_11g(
    True,
    cs,
    a_target=1.0,
    should_stop=False,
    accel_limits=(-3.5, 2.0),
  )

  transition_signal = (
    lc.transitioning
    and lc.prev_mode == "blended"
    and lc.current_mode == "acc"
  )

  assert transition_signal
  assert lc.pid.freeze_calls[-1]

  # More-positive output is slewed during the transition.
  assert before < second < 1.0


def test_accord_blended_to_acc_keeps_more_negative_output_immediate():
  lc = build_accord_longcontrol()
  cs = car_state()

  lc.experimental_mode = True
  lc.pid.output = 0.2

  lc._update_honda_accord_11g(
    True,
    cs,
    a_target=0.2,
    should_stop=False,
    accel_limits=(-3.5, 2.0),
  )

  lc.experimental_mode = False
  lc.pid.output = -0.8

  output = lc._update_honda_accord_11g(
    True,
    cs,
    a_target=-0.8,
    should_stop=False,
    accel_limits=(-3.5, 2.0),
  )

  assert lc.transitioning
  assert lc.prev_mode == "blended"
  assert lc.current_mode == "acc"
  assert lc.pid.freeze_calls[-1]

  # N15 contract: braking/decel changes are not delayed.
  assert output == -0.8

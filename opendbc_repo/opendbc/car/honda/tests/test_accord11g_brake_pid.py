import pytest

from opendbc.car.honda.carcontroller import (
  ACCORD11G_BRAKE_PID_DECEL_THRESHOLD,
  update_accord11g_low_speed_brake_pid,
)


class FakeBrakePid:
  def __init__(self, i=0.0, result=-0.25):
    self.i = i
    self.result = result
    self.updates = []
    self.resets = 0

  def update(self, *, error, speed):
    self.updates.append((error, speed))
    self.i = self.result
    return self.result

  def reset(self):
    self.i = 0.0
    self.resets += 1


def test_brake_pid_retains_negative_correction():
  pid = FakeBrakePid(i=-0.4)

  result = update_accord11g_low_speed_brake_pid(
    pid, 0.1, 0.0, 1.0,
    ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, True,
  )

  assert pid.i == pytest.approx(-0.38)
  assert result == pytest.approx(-0.28)
  assert not pid.updates


def test_brake_pid_disengage_resets():
  pid = FakeBrakePid(i=-0.4)

  assert update_accord11g_low_speed_brake_pid(
    pid, 0.0, 0.0, 1.0,
    ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, False,
  ) == pytest.approx(0.0)

  assert pid.i == pytest.approx(0.0)
  assert pid.resets == 1


@pytest.mark.parametrize("accel,active", (
  (-0.2, True),
  (0.0, True),
  (0.0005, True),
  (0.001, False),
  (0.01, False),
))
def test_decel_wide_activation(accel, active):
  pid = FakeBrakePid(result=-0.1)

  update_accord11g_low_speed_brake_pid(
    pid, accel, 0.0, 1.0,
    ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, True,
  )

  assert bool(pid.updates) is active


@pytest.mark.parametrize("speed,active", (
  (0.0, False),
  (0.001, False),
  (0.01, True),
  (1.0, True),
  (2.999, True),
  (3.0, False),
))
def test_speed_envelope(speed, active):
  pid = FakeBrakePid(result=-0.1)

  update_accord11g_low_speed_brake_pid(
    pid, -0.1, 0.0, speed,
    ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, True,
  )

  assert bool(pid.updates) is active

import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from opendbc.car.honda.carcontroller import (
  ACCORD11G_BRAKE_PID_DECEL_THRESHOLD,
  ACCORD11G_GASALPHA_LEARN_SPEED,
  ACCORD11G_GASALPHA_MAX,
  apply_accord11g_gasalpha,
  get_honda_bosch_gas_command,
  load_accord11g_gasalpha,
  update_accord11g_gasalpha,
  update_accord11g_low_speed_brake_pid,
)
from opendbc.car.honda.hondacan import create_acc_commands
from opendbc.car.honda.values import CAR, CarControllerParams


FORCES = (-0.50, -0.30, -0.20, -0.10, -0.05, -0.01, 0.00, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50)
GAS_FACTORS = (0.50, 0.75, 1.00, 1.25, 1.50, 2.00)
GASALPHAS = (0.00, 0.02, 0.10, 0.40)
SPEEDS = (0.0, 0.0005, 0.001, 0.5, 1.0, 2.0, 2.999, 3.0, 3.001, 10.0, 30.0)
ACCELS = (-1.0, -0.2, -0.01, -0.0011, -0.001, -0.0009, 0.0, 0.01)


class FakeBrakePid:
  def __init__(self, i=0.0, update_result=-0.1):
    self.i = i
    self.update_result = update_result
    self.updates = []
    self.reset_count = 0

  def update(self, *, error, speed):
    self.updates.append((error, speed))
    self.i = self.update_result
    return self.update_result

  def reset(self):
    self.i = 0.0
    self.reset_count += 1


class FakePacker:
  @staticmethod
  def make_can_msg(name, bus, values):
    return name, bus, values


def legacy_n15_bosch_command(force, factor):
  return float(np.interp(
    force * factor,
    CarControllerParams.BOSCH_GAS_LOOKUP_BP,
    CarControllerParams.BOSCH_GAS_LOOKUP_V,
  ))


def legacy_n15_accord_command(force, factor):
  min_gas = CarControllerParams.BOSCH_GAS_LOOKUP_BP[0]
  lookup_input = (force - min_gas) * factor + min_gas
  return float(np.interp(
    lookup_input,
    CarControllerParams.BOSCH_GAS_LOOKUP_BP,
    CarControllerParams.BOSCH_GAS_LOOKUP_V,
  ))


@pytest.mark.parametrize("force", FORCES)
@pytest.mark.parametrize("factor", GAS_FACTORS)
def test_non_accord_gas_command_is_exact_n15_parent(force, factor):
  assert get_honda_bosch_gas_command(force, factor, False) == legacy_n15_bosch_command(force, factor)


@pytest.mark.parametrize("force", FORCES)
def test_non_accord_can_crossover_is_exact_n15_parent(force):
  min_gas = CarControllerParams.BOSCH_GAS_LOOKUP_BP[0]
  gas_command = 123
  values = create_acc_commands(
    FakePacker(), SimpleNamespace(pt=1), True, True, force, gas_command, 0,
    SimpleNamespace(carFingerprint=CAR.HONDA_CIVIC_BOSCH), gas_force=force,
  )[1][2]
  assert values["GAS_COMMAND"] == (gas_command if force > min_gas else -30000)
  assert values["BRAKE_REQUEST"] == int(force < min_gas)


@pytest.mark.parametrize(("force", "expected_gas", "expected_brake"), (
  (-0.01, -30000, 1),
  (0.0, -30000, 0),
  (0.01, 123, 0),
))
def test_accord_can_crossover_is_zero_anchored(force, expected_gas, expected_brake):
  values = create_acc_commands(
    FakePacker(), SimpleNamespace(pt=1), True, True, force, 123, 0,
    SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G), gas_force=force,
  )[1][2]
  assert values["GAS_COMMAND"] == expected_gas
  assert values["BRAKE_REQUEST"] == expected_brake


@pytest.mark.parametrize("force", FORCES)
@pytest.mark.parametrize("factor", GAS_FACTORS)
@pytest.mark.parametrize("gasalpha", GASALPHAS)
def test_accord_command_matches_corrected_zero_based_equation(force, factor, gasalpha):
  effective_force = apply_accord11g_gasalpha(force, gasalpha, False)
  expected = float(np.interp(
    effective_force * factor,
    [0.0, CarControllerParams.BOSCH_GAS_LOOKUP_BP[1]],
    CarControllerParams.BOSCH_GAS_LOOKUP_V,
  ))
  assert get_honda_bosch_gas_command(effective_force, factor, True) == expected


@pytest.mark.parametrize("factor", GAS_FACTORS)
def test_zero_alpha_documents_parent_to_zero_anchor_change(factor):
  assert get_honda_bosch_gas_command(0.0, factor, True) == 0.0
  assert legacy_n15_accord_command(0.0, factor) >= 0.0
  if factor != 0.5:
    assert get_honda_bosch_gas_command(0.0, factor, True) != legacy_n15_accord_command(0.0, factor)


@pytest.mark.parametrize("factor", GAS_FACTORS)
@pytest.mark.parametrize("gasalpha", GASALPHAS)
def test_accord_gas_mapping_is_monotonic_through_zero(factor, gasalpha):
  forces = (-0.02, -0.01, 0.0, 0.005, 0.01, 0.02, 0.05)
  commands = [get_honda_bosch_gas_command(force + gasalpha, factor, True) for force in forces]
  assert commands == sorted(commands)
  assert all(command == 0.0 for force, command in zip(forces, commands, strict=True) if force + gasalpha <= 0.0)


@pytest.mark.parametrize("retained_i", (-0.4, -0.1, -0.02, -1e-6))
@pytest.mark.parametrize("gasalpha", GASALPHAS)
def test_n13_retained_brake_blocks_gasalpha_and_can_propulsion(retained_i, gasalpha):
  effective_force = apply_accord11g_gasalpha(retained_i, gasalpha, True)
  command = get_honda_bosch_gas_command(effective_force, 1.0, True)
  assert effective_force == retained_i
  assert command == 0.0

  values = create_acc_commands(
    FakePacker(), SimpleNamespace(pt=1), True, True, retained_i, command, 0,
    SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G), gas_force=effective_force,
  )[1][2]
  assert values["GAS_COMMAND"] == -30000
  assert values["BRAKE_REQUEST"] == 1


def test_n13_release_rate_and_n16_crossover_sequence():
  pid = FakeBrakePid(i=-0.06)
  alpha = 0.10
  retained = []
  commands = []
  for _ in range(3):
    target = update_accord11g_low_speed_brake_pid(
      pid, accel=0.10, actual_accel=0.0, v_ego=2.0,
      active_accel_threshold=ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, long_active=True,
    )
    retained.append(pid.i)
    force = apply_accord11g_gasalpha(target, alpha, pid.i < 0.0)
    commands.append(get_honda_bosch_gas_command(force, 1.0, True))
  assert retained == pytest.approx((-0.04, -0.02, 0.0))
  assert commands[:2] == [0.0, 0.0]
  assert commands[2] > 0.0

  force = apply_accord11g_gasalpha(0.10, alpha, False)
  assert get_honda_bosch_gas_command(force, 1.0, True) > 0.0


@pytest.mark.parametrize("speed", SPEEDS)
@pytest.mark.parametrize("accel", ACCELS)
def test_n14_boundary_matrix_is_unchanged(speed, accel):
  pid = FakeBrakePid()
  update_accord11g_low_speed_brake_pid(
    pid, accel=accel, actual_accel=0.0, v_ego=speed,
    active_accel_threshold=ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, long_active=True,
  )
  expected = accel < ACCORD11G_BRAKE_PID_DECEL_THRESHOLD and 0.001 < speed < 3.0
  assert bool(pid.updates) is expected


def valid_learning_args(**overrides):
  args = dict(
    gasalpha=0.2,
    desired_accel=0.1,
    actual_accel=0.0,
    gas_force_without_alpha=0.0,
    v_ego=2.0,
    long_active=True,
    pid_active=True,
    gas_pressed=False,
    brake_pressed=False,
    in_reverse=False,
    retained_brake_active=False,
    transition_active=False,
  )
  args.update(overrides)
  return args


@pytest.mark.parametrize(("name", "overrides"), (
  ("long inactive", {"long_active": False}),
  ("off/stopping", {"pid_active": False}),
  ("driver gas", {"gas_pressed": True}),
  ("driver brake", {"brake_pressed": True}),
  ("reverse", {"in_reverse": True}),
  ("retained brake", {"retained_brake_active": True}),
  ("N15 transition", {"transition_active": True}),
  ("minimum speed", {"v_ego": 1.0}),
  ("force lower boundary", {"gas_force_without_alpha": -0.5}),
  ("force upper boundary", {"gas_force_without_alpha": 0.1}),
))
def test_learning_guards_hold_alpha_exactly(name, overrides):
  del name
  assert update_accord11g_gasalpha(**valid_learning_args(**overrides)) == 0.2


@pytest.mark.parametrize("transition_stage", ("just-started", "middle", "near-complete"))
def test_n15_transition_freezes_only_gasalpha_learning(transition_stage):
  del transition_stage
  pid = FakeBrakePid(i=-0.06)
  old_alpha = 0.2
  new_alpha = update_accord11g_gasalpha(**valid_learning_args(gasalpha=old_alpha, transition_active=True))
  target = update_accord11g_low_speed_brake_pid(
    pid, accel=0.1, actual_accel=0.0, v_ego=2.0,
    active_accel_threshold=ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, long_active=True,
  )
  assert new_alpha == old_alpha
  assert pid.i == pytest.approx(-0.04)
  assert target == pytest.approx(0.06)


def test_learning_resumes_after_n15_transition():
  frozen = update_accord11g_gasalpha(**valid_learning_args(transition_active=True))
  resumed = update_accord11g_gasalpha(**valid_learning_args(gasalpha=frozen, transition_active=False))
  assert frozen == 0.2
  assert resumed == pytest.approx(0.2 + 0.1 / ACCORD11G_GASALPHA_LEARN_SPEED / 10.0)


@pytest.mark.parametrize(("desired", "actual", "direction"), (
  (0.2, 0.0, 1),
  (-0.2, 0.0, -1),
  (0.0, 0.0, 0),
))
def test_learning_direction_and_per_update_magnitude(desired, actual, direction):
  old = 0.2
  new = update_accord11g_gasalpha(**valid_learning_args(gasalpha=old, desired_accel=desired, actual_accel=actual))
  expected_delta = (desired - actual) / ACCORD11G_GASALPHA_LEARN_SPEED / 10.0
  assert new - old == pytest.approx(expected_delta)
  assert (new > old) - (new < old) == direction


def test_repeated_learning_is_gradual_and_bounded():
  alpha = 0.0
  deltas = []
  for _ in range(10000):
    new_alpha = update_accord11g_gasalpha(**valid_learning_args(gasalpha=alpha, desired_accel=0.2))
    deltas.append(new_alpha - alpha)
    alpha = new_alpha
  assert max(deltas) <= 0.2 / ACCORD11G_GASALPHA_LEARN_SPEED / 10.0 + 1e-15
  assert alpha == ACCORD11G_GASALPHA_MAX


@pytest.mark.parametrize("field", ("gasalpha", "desired_accel", "actual_accel", "gas_force_without_alpha", "v_ego"))
@pytest.mark.parametrize("invalid", (math.nan, math.inf, -math.inf))
def test_invalid_learning_input_never_changes_finite_alpha(field, invalid):
  args = valid_learning_args()
  args[field] = invalid
  assert update_accord11g_gasalpha(**args) == (0.0 if field == "gasalpha" else 0.2)


@pytest.mark.parametrize(("stored", "expected"), (
  (None, 0.0), ("", 0.0), ("invalid", 0.0),
  (math.nan, 0.0), (math.inf, 0.0), (-math.inf, 0.0),
  (-1.0, 0.0), (0.0, 0.0), (0.1, 0.1), (0.4, 0.4), (1.0, 0.4), (1e100, 0.4),
))
def test_persisted_alpha_load_is_safe(stored, expected):
  params = SimpleNamespace(get_float=lambda *args, **kwargs: stored)
  assert load_accord11g_gasalpha(params) == pytest.approx(expected)



def test_transition_signal_schema_defaults_false_and_controlsd_sets_direct_state():
  schema = Path("opendbc_repo/opendbc/car/car.capnp").read_text()
  assert "experimentalToAccTransition @10: Bool" in schema
  assert "experimentalToAccTransition" not in schema.split("struct Actuators", 1)[0]

  controlsd = Path("selfdrive/controls/controlsd.py").read_text()
  assert "actuators.experimentalToAccTransition = bool(" in controlsd
  assert "self.LoC.transitioning" in controlsd
  assert "self.LoC.prev_mode == 'blended'" in controlsd
  assert "self.LoC.current_mode == 'acc'" in controlsd


def test_accord_gasfactor_and_wind_learning_use_zero_coordinate():
  controller = Path("opendbc_repo/opendbc/car/honda/carcontroller.py").read_text()
  assert "gas_pedal_force > (0.0 if self.mvl_accord_mode else min_gas)" in controller
  assert "gas_learn_force = gas_pedal_force" in controller
  assert "wind_brake_threshold = 0.0" in controller
  assert "gas_pedal_force - min_gas" not in controller


def test_n13_n14_n15_n16_cross_layer_sequence():
  pid = FakeBrakePid(update_result=-0.3)
  alpha = 0.2

  target = update_accord11g_low_speed_brake_pid(
    pid, accel=-0.2, actual_accel=0.0, v_ego=2.0,
    active_accel_threshold=ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, long_active=True,
  )
  assert target == pytest.approx(-0.5)

  for transition_active in (False, True, True, True):
    target = update_accord11g_low_speed_brake_pid(
      pid, accel=0.1, actual_accel=0.0, v_ego=2.0,
      active_accel_threshold=ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, long_active=True,
    )
    before = alpha
    alpha = update_accord11g_gasalpha(**valid_learning_args(
      gasalpha=alpha, gas_force_without_alpha=target,
      retained_brake_active=pid.i < 0.0, transition_active=transition_active,
    ))
    force = apply_accord11g_gasalpha(target, alpha, pid.i < 0.0)
    assert alpha == before
    assert get_honda_bosch_gas_command(force, 1.0, True) == 0.0

  while pid.i < 0.0:
    update_accord11g_low_speed_brake_pid(
      pid, accel=0.1, actual_accel=0.0, v_ego=2.0,
      active_accel_threshold=ACCORD11G_BRAKE_PID_DECEL_THRESHOLD, long_active=True,
    )
  assert pid.i == 0.0

  alpha_after = update_accord11g_gasalpha(**valid_learning_args(gasalpha=alpha, transition_active=False))
  force = apply_accord11g_gasalpha(0.1, alpha_after, False)
  assert alpha_after > alpha
  assert get_honda_bosch_gas_command(force, 1.0, True) > 0.0

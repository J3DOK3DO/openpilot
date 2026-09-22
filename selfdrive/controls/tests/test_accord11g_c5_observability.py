import math
import types

import pytest

from cereal import car, custom, log
from openpilot.selfdrive.controls.controlsd import (
  C5_OBS_GUARD_APPLIED,
  C5_OBS_GUARD_INSUFFICIENT_REACH,
  limit_curvature_to_plan,
)


def _plan(xs, ys):
  return types.SimpleNamespace(position=types.SimpleNamespace(x=xs, y=ys))


def test_twitch_guard_observability_preserves_existing_output():
  plan = _plan([i * 0.5 for i in range(200)], [0.0] * 200)
  without_observation = limit_curvature_to_plan(plan, 0.0155, 1.2)
  observation = types.SimpleNamespace()
  with_observation = limit_curvature_to_plan(plan, 0.0155, 1.2, observation)

  assert with_observation == pytest.approx(without_observation)
  assert observation.c5ObsGuardApplied
  assert observation.c5ObsGuardReason == C5_OBS_GUARD_APPLIED
  assert math.isfinite(observation.c5ObsPlanCurvature)
  assert observation.c5ObsPlanReach > 0.0


def test_twitch_guard_observability_preserves_short_plan_passthrough():
  plan = _plan([0.0, 0.3], [0.0, 0.0])
  without_observation = limit_curvature_to_plan(plan, 0.0155, 0.4)
  observation = types.SimpleNamespace()
  with_observation = limit_curvature_to_plan(plan, 0.0155, 0.4, observation)

  assert with_observation == pytest.approx(without_observation)
  assert not observation.c5ObsGuardApplied
  assert observation.c5ObsGuardReason == C5_OBS_GUARD_INSUFFICIENT_REACH


def test_observability_schema_roundtrip():
  plan = log.LongitudinalPlan.new_message()
  plan.c5ObsValid = True
  plan.c5ObsBaseTFollow = 1.25
  with log.LongitudinalPlan.from_bytes(plan.to_bytes()) as reader:
    assert reader.c5ObsValid
    assert reader.c5ObsBaseTFollow == pytest.approx(1.25)

  actuators = car.CarControl.Actuators.new_message()
  actuators.c5ObsHondaValid = True
  actuators.c5ObsHondaGasPedalForce = -0.03
  with car.CarControl.Actuators.from_bytes(actuators.to_bytes()) as reader:
    assert reader.c5ObsHondaValid
    assert reader.c5ObsHondaGasPedalForce == pytest.approx(-0.03)

  lateral = custom.StarPilotLateralState.new_message()
  lateral.c5ObsValid = True
  lateral.c5ObsGuardReason = C5_OBS_GUARD_APPLIED
  with custom.StarPilotLateralState.from_bytes(lateral.to_bytes()) as reader:
    assert reader.c5ObsValid
    assert reader.c5ObsGuardReason == C5_OBS_GUARD_APPLIED

"""Independent adversarial negative control for explicit-stop/manual resume arbitration.
Fixed MPC: not a vehicle, timing, or closed-loop qualification.
"""
import pytest
from opendbc.car.honda.values import CAR
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner
from openpilot.selfdrive.controls.tests.test_longitudinal_planner import make_lead, make_toggles
from openpilot.selfdrive.controls.tests.test_campaign_b_longitudinal_remediation import (
  fixed_mpc, run_scene, SOURCE_STOP_FLAGS,
)


@pytest.mark.parametrize("flag", tuple(SOURCE_STOP_FLAGS), ids=tuple(SOURCE_STOP_FLAGS))
def test_explicit_stop_vetoes_previously_armed_manual_resume(monkeypatch, fixed_mpc, flag):
  # Force the otherwise valid manual override to be armed, isolating precedence.
  monkeypatch.setattr(LongitudinalPlanner, "_update_manual_stop_resume_override", lambda self, sm: True)
  flags = dict(SOURCE_STOP_FLAGS[flag])
  if flag == "forcingStop":
    flags["forcingStopLength"] = 0.5

  def at_standstill(sm):
    sm["carState"].standstill = True
    sm["carState"].gasPressed = False
    sm["carState"].brakePressed = False

  planner = run_scene(
    CAR.HONDA_CIVIC, 0.0, make_lead(status=False), raw_accel=-1.0,
    model_accel=-1.0, flags=flags, toggles=make_toggles(),
    edit=at_standstill,
  )
  assert planner.output_a_target <= -0.95, "Manual override must never raise a source-backed stop target"


def test_manual_resume_remains_available_without_explicit_stop(monkeypatch, fixed_mpc):
  monkeypatch.setattr(LongitudinalPlanner, "_update_manual_stop_resume_override", lambda self, sm: True)
  planner = run_scene(
    CAR.HONDA_CIVIC, 0.0, make_lead(status=False), raw_accel=-1.0,
    model_accel=-1.0, toggles=make_toggles(),
  )
  assert planner.output_a_target > -0.95, "Non-stop manual override must not be globally disabled"

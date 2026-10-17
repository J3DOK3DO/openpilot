"""Synthetic-only characterization guards for unresolved Campaign A contracts.

These tests pin and describe current behavior. They are not calibration approval,
vehicle validation, or replacements for the six intentionally failing tests.
"""

import hashlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from openpilot.common.basedir import BASEDIR
from openpilot.selfdrive.controls.lib.latcontrol_vehicle_tunes import (
  get_bolt_2022_2023_low_speed_center_output_limit,
  get_genesis_g70_friction_threshold,
  get_palisade_center_output_scale,
)
from openpilot.starpilot.controls.lib.curve_speed_controller import CurveSpeedController, MAX_CURVATURE
from openpilot.starpilot.controls.starpilot_planner import get_force_stop_jerk_scale


SOURCE_PINS = {
  "starpilot/controls/lib/curve_speed_controller.py": "9e1a9d2ddfbdd7e9324d83bb2cdf10dac8daec1e97a9f9c9f627bb828feedf92",
  "selfdrive/controls/lib/latcontrol_vehicle_tunes.py": "367e966fc7935956668fe46f926da73fb94f9c80104b747db8de5a9758803544",
  "starpilot/controls/starpilot_planner.py": "089da01cc34961c4f704f991102497a4609fab182e664fe0bb24161bc42028f1",
}


@pytest.mark.parametrize("relative_path,expected", SOURCE_PINS.items())
def test_campaign_a_driving_source_pin(relative_path, expected):
  assert hashlib.sha256((Path(BASEDIR) / relative_path).read_bytes()).hexdigest() == expected


def test_curve_correction_preserves_raw_readings_at_and_above_learning_cap():
  epsilon = 1e-12
  raw = np.array([MAX_CURVATURE, MAX_CURVATURE + epsilon, 0.1])
  corrected = CurveSpeedController._correct_far_field(raw, np.full(raw.shape, 100.0))
  assert np.array_equal(corrected, raw)


def test_non_honda_numeric_conflicts_are_stable_at_adjacent_inputs():
  epsilon = 1e-6
  bolt = [get_bolt_2022_2023_low_speed_center_output_limit(0.05, 9.0 + d) for d in (-epsilon, 0.0, epsilon)]
  palisade = [get_palisade_center_output_scale(0.0, 30.0 + d) for d in (-epsilon, 0.0, epsilon)]
  genesis = [get_genesis_g70_friction_threshold(25.0 + d, 0.8, 0.8) for d in (-epsilon, 0.0, epsilon)]
  assert bolt[1] == pytest.approx(0.8768080716037345)
  assert palisade[1] == pytest.approx(0.8222980111882578)
  assert genesis[1] == pytest.approx(0.6000030217234732)
  assert max(bolt) - min(bolt) < 1e-6
  assert max(palisade) - min(palisade) < 1e-6
  assert max(genesis) - min(genesis) < 1e-6


def test_force_stop_current_default_is_honda_relevant_and_override_is_narrow():
  assert get_force_stop_jerk_scale(SimpleNamespace(carFingerprint="HONDA_ACCORD_11G")) == 0.20
  assert get_force_stop_jerk_scale(SimpleNamespace(carFingerprint="OTHER_CAR")) == 0.20
  assert get_force_stop_jerk_scale(SimpleNamespace(carFingerprint="HYUNDAI_ELANTRA_2021")) == 0.80

"""Offline-only C8.2 characterization of Accord 11G independent LKAS guards.

These tests are not a substitute for native Panda/vehicle qualification.
"""
import math
from types import SimpleNamespace

import pytest

from opendbc.car import structs
from opendbc.car.honda.tests.test_stock_aol import final_cp, state
from opendbc.car.honda.values import CAR
from openpilot.starpilot.aol.intent import AolSettings, AOL_TOGGLE
from openpilot.starpilot.car.honda.aol import accord11g_stationary_aol_inhibit, create_intent


def accord11g_intent():
  cp = final_cp(CAR.HONDA_ACCORD_11G, hybrid=True)
  cp.alternativeExperience = 32
  settings = AolSettings(True, 0.0, AOL_TOGGLE, 0, (0, 0, 0), (0, 0, 0))
  return create_intent(cp, settings)


@pytest.mark.parametrize('gear', ['park', 'neutral', 'reverse', 'unknown'])
def test_non_driving_gear_lkas_press_cannot_prearm_lateral(gear):
  intent = accord11g_intent()
  intent.update(state(gear=gear), now_ns=10)
  intent.update(state(True, gear=gear), now_ns=20)
  assert not intent.allowed_latch
  intent.update(state(gear='drive'), now_ns=30)
  assert not intent.allowed_latch
  # An old/held gesture is insufficient after the gear transition.
  intent.update(state(True, gear='drive'), now_ns=40)
  assert not intent.allowed_latch
  intent.update(state(False, gear='drive'), now_ns=50)
  intent.update(state(True, gear='drive'), now_ns=60)
  assert intent.allowed_latch


@pytest.mark.parametrize('gear', ['park', 'neutral', 'reverse', 'unknown'])
def test_previously_armed_lateral_does_not_resume_after_non_driving_gear(gear):
  intent = accord11g_intent()
  intent.update(state(), now_ns=10)
  intent.update(state(True), now_ns=20)
  assert intent.allowed_latch
  intent.update(state(False), now_ns=30)
  intent.update(state(gear=gear), now_ns=40)
  assert not intent.allowed_latch
  intent.update(state(gear='drive'), now_ns=50)
  assert not intent.allowed_latch


def test_existing_other_honda_reverse_pause_policy_unchanged():
  cp = final_cp(CAR.HONDA_CIVIC_BOSCH)
  cp.alternativeExperience = 32
  settings = AolSettings(True, 0.0, AOL_TOGGLE, 0, (0, 0, 0), (0, 0, 0))
  intent = create_intent(cp, settings)
  intent.update(state(), now_ns=10)
  intent.update(state(True), now_ns=20)
  assert intent.allowed_latch
  intent.update(state(gear='reverse'), now_ns=30)
  assert intent.allowed_latch  # Existing non-11G policy remains unchanged.


@pytest.mark.parametrize('speed,standstill,blocked', [
  (0.0, True, True), (0.0, False, True), (0.29, False, True),
  (-0.29, False, True), (0.31, False, False), (7.0, False, False),
  (float('nan'), False, True), (float('inf'), False, True),
])
def test_accord11g_stationary_veto_is_fail_closed(speed, standstill, blocked):
  cp = SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G, minSteerSpeed=0.0)
  cs = SimpleNamespace(vEgo=speed, standstill=standstill)
  assert accord11g_stationary_aol_inhibit(cp, cs) is blocked


def test_malformed_11g_stationary_inputs_are_inhibited():
  cp = SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G, minSteerSpeed=float('nan'))
  cs = SimpleNamespace(vEgo=7.0, standstill=False)
  assert accord11g_stationary_aol_inhibit(cp, cs)
  assert accord11g_stationary_aol_inhibit(cp, SimpleNamespace(vEgo=None, standstill=False))


def test_other_honda_stationary_veto_unchanged():
  cp = SimpleNamespace(carFingerprint=CAR.HONDA_CIVIC_BOSCH, minSteerSpeed=0.0)
  cs = SimpleNamespace(vEgo=0.0, standstill=True)
  assert not accord11g_stationary_aol_inhibit(cp, cs)

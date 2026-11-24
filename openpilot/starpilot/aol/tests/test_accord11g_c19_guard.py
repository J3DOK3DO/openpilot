"""Synthetic Accord 11G independent lateral guard regression."""
from types import SimpleNamespace

import pytest

from opendbc.car import structs
from opendbc.car.honda.tests.test_stock_aol import final_cp
from opendbc.car.honda.values import CAR
from openpilot.starpilot.aol.intent import AolSettings, AOL_TOGGLE
from openpilot.starpilot.car.honda.aol import accord11g_stationary_aol_inhibit, create_intent


def sample(*, gear='drive', speed=10., standstill=False, pressed=None, available=True):
  cs = structs.CarState(canValid=True, gearShifter=gear, vEgo=speed, standstill=standstill)
  cs.cruiseState.available = available
  if pressed is not None:
    cs.buttonEvents = [structs.CarState.ButtonEvent(type='lkas', pressed=pressed)]
  return cs.as_reader()


def intent_for(candidate):
  cp = final_cp(candidate, hybrid=candidate == CAR.HONDA_ACCORD_11G)
  cp.alternativeExperience = 32
  return create_intent(cp, AolSettings(True, 0., AOL_TOGGLE, 0, (0, 0, 0), (0, 0, 0)))


@pytest.mark.parametrize('gear', ['park', 'neutral', 'reverse', 'unknown', 'sport', 'low'])
def test_non_drive_requires_new_neutral_then_gesture(gear):
  intent = intent_for(CAR.HONDA_ACCORD_11G)
  intent.update(sample(), now_ns=10)
  intent.update(sample(pressed=True), now_ns=20)
  assert intent.allowed_latch
  intent.update(sample(pressed=False), now_ns=30)
  intent.update(sample(gear=gear, pressed=True), now_ns=40)
  assert not intent.allowed_latch
  intent.update(sample(pressed=True), now_ns=50)
  assert not intent.allowed_latch
  intent.update(sample(pressed=False), now_ns=60)
  intent.update(sample(pressed=True), now_ns=70)
  assert intent.allowed_latch


def test_stationary_clears_and_requires_fresh_gesture():
  intent = intent_for(CAR.HONDA_ACCORD_11G)
  intent.update(sample(), now_ns=10)
  intent.update(sample(pressed=True), now_ns=20)
  intent.update(sample(pressed=False), now_ns=30)
  assert intent.allowed_latch
  intent.update(sample(speed=0., standstill=True), now_ns=40)
  assert not intent.allowed_latch
  intent.update(sample(), now_ns=50)
  assert not intent.allowed_latch
  intent.update(sample(pressed=True), now_ns=60)
  assert intent.allowed_latch


@pytest.mark.parametrize('speed,minimum,blocked', [
  (0., 0., True), (0.3, 0., True), (0.31, 0., False),
  (1.0, 1.0, True), (1.01, 1.0, False), (-1., 0., True),
  (float('nan'), 0., True), (float('inf'), 0., True),
  (10., float('nan'), True), (10., -1., True),
])
def test_speed_veto(speed, minimum, blocked):
  cp = SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G, minSteerSpeed=minimum)
  cs = SimpleNamespace(vEgo=speed, standstill=False)
  assert accord11g_stationary_aol_inhibit(cp, cs) is blocked


def test_ordinary_lateral_and_other_honda_unaffected():
  stopped = SimpleNamespace(vEgo=0., standstill=True)
  accord = SimpleNamespace(carFingerprint=CAR.HONDA_ACCORD_11G, minSteerSpeed=0.)
  civic = SimpleNamespace(carFingerprint=CAR.HONDA_CIVIC_BOSCH, minSteerSpeed=0.)
  assert not accord11g_stationary_aol_inhibit(accord, stopped, standard_lateral=True)
  assert not accord11g_stationary_aol_inhibit(civic, stopped)
  intent = intent_for(CAR.HONDA_CIVIC_BOSCH)
  intent.update(sample(), now_ns=10)
  intent.update(sample(pressed=True), now_ns=20)
  intent.update(sample(gear='reverse'), now_ns=30)
  assert intent.allowed_latch


def test_fault_and_main_off_clear_latch():
  for fault in (False, True):
    intent = intent_for(CAR.HONDA_ACCORD_11G)
    intent.update(sample(), now_ns=10)
    intent.update(sample(pressed=True), now_ns=20)
    assert intent.allowed_latch
    intent.update(sample(pressed=False, available=fault), now_ns=30, fault_active=fault)
    assert not intent.allowed_latch


def test_cancel_action_cannot_rearm_while_ineligible():
  cp = final_cp(CAR.HONDA_ACCORD_11G, hybrid=True)
  cp.alternativeExperience = 32
  settings = AolSettings(True, 0., AOL_TOGGLE, 0, (0, 0, 0), (AOL_TOGGLE, 0, 0))
  intent = create_intent(cp, settings)
  for tick, pressed in ((10, True), (20, False)):
    cs = structs.CarState(**sample(gear='park').to_dict())
    cs.buttonEvents = [structs.CarState.ButtonEvent(type='cancel', pressed=pressed)]
    intent.update(cs.as_reader(), now_ns=tick)
  assert not intent.allowed_latch


def test_full_engagement_at_standstill_does_not_prearm():
  intent = intent_for(CAR.HONDA_ACCORD_11G)
  intent.observe_full_engagement(sample(speed=0., standstill=True), enabled=False, active=False,
                                 source_ns=10, observation_valid=True, now_ns=10, fault_active=False)
  intent.observe_full_engagement(sample(speed=0., standstill=True), enabled=True, active=True,
                                 source_ns=20, observation_valid=True, now_ns=20, fault_active=False)
  assert not intent.allowed_latch
  intent.observe_full_engagement(sample(), enabled=True, active=True,
                                 source_ns=30, observation_valid=True, now_ns=30, fault_active=False)
  assert not intent.allowed_latch

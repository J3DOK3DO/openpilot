"""Native Accord 11G stock-MVL interrupt/cooldown regression."""
from types import SimpleNamespace as NS

import pytest

from opendbc.car.honda.accord_mvl_stock import AccordMvlStock
from opendbc.car.honda.values import CruiseSettings


def _step(obj, frame, *, enabled=True, braking=False, cruise=True,
          cancel=False, resume=False, experience=32, ready=True):
  control = NS(enabled=enabled, cruiseControl=NS(cancel=cancel, resume=resume))
  state = NS(out=NS(brakePressed=braking, cruiseState=NS(enabled=cruise)),
             lkas_hud={"LKAS_READY": int(ready)}, cruise_setting=0,
             cruise_buttons=0, scm_ambient_light=0)
  cp = NS(alternativeExperience=experience)
  can = NS(camera=2)
  return obj.update(None, can, cp, control, state, frame)


@pytest.fixture
def capture(monkeypatch):
  def send(_packer, _can, _buttons, _cp, *, cruise_setting, ambient_light, bus):
    assert bus == 2
    return {"setting": cruise_setting, "ambient": ambient_light, "bus": bus}
  monkeypatch.setattr("opendbc.car.honda.accord_mvl_stock.hondacan.spam_buttons_command", send)
  return AccordMvlStock()


def test_normal_three_pulse_cadence_is_unchanged(capture):
  assert [_step(capture, f)[0]["setting"] for f in (500, 504, 508)] == [CruiseSettings.LKAS] * 3
  assert _step(capture, 512)[0]["setting"] != CruiseSettings.LKAS
  assert capture.last_lkas_button_frame == 508


@pytest.mark.parametrize("experience", [0, 32])
@pytest.mark.parametrize("interrupt_frame", [501, 504])
@pytest.mark.parametrize("case", ["braking", "disabled", "cancel", "resume", "cruise_off", "lkas_not_ready"])
def test_interruptions_withdraw_queued_lkas_in_both_stock_experiences(capture, experience, interrupt_frame, case):
  assert _step(capture, 500, experience=experience)[0]["setting"] == CruiseSettings.LKAS
  kwargs = {
    "braking": {"braking": True},
    "disabled": {"enabled": False},
    "cancel": {"cancel": True},
    "resume": {"resume": True},
    "cruise_off": {"cruise": False},
    "lkas_not_ready": {"ready": False},
  }[case]
  assert _step(capture, interrupt_frame, experience=experience, **kwargs) == []
  assert capture.lkas_button_send_remaining == 0
  assert capture.last_lkas_button_frame == 500
  for frame in (504, 508, 996):
    if frame == interrupt_frame:
      continue
    assert _step(capture, frame, experience=experience)[0]["setting"] != CruiseSettings.LKAS
  assert _step(capture, 1000, experience=experience)[0]["setting"] == CruiseSettings.LKAS


@pytest.mark.parametrize("experience", [0, 32])
def test_cannot_start_new_pulse_on_withdrawal(capture, experience):
  for kwargs in ({"braking": True}, {"enabled": False}, {"cruise": False}, {"ready": False},
                 {"cancel": True}, {"resume": True}):
    assert _step(capture, 500, experience=experience, **kwargs) == []
    assert capture.lkas_button_send_remaining == 0
  assert _step(capture, 500, experience=experience)[0]["setting"] == CruiseSettings.LKAS

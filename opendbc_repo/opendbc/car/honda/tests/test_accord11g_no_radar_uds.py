"""Accord 11G: CarInterface init/deinit never send the radar UDS disable/enable sequence.

MVL 3fec9a (interface.py init, carcontroller.py radar_disable_counter) silences the CAN-FD radar with UDS
0x10 0x03 / 0x28 0x83 0x03 to 0x18DAB0F1, and its own comments record a brake-module CRUISE_FAULT latch when the
replacement stream starts late. Dom gates the same call on openpilotLongitudinalControl, which Accord 11G never sets.
"""
import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda import interface as honda_interface
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR


def _cp(candidate, alpha_long, is_release, alt_brake=False):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x1A3] = 8
  if alt_brake:
    fingerprint[0][0x1BE] = 3
  return CarInterface.get_params(candidate, fingerprint, [], alpha_long, is_release, False)


@pytest.fixture
def recorded(monkeypatch):
  calls = []
  monkeypatch.setattr(honda_interface, "disable_ecu", lambda *args, **kwargs: calls.append(kwargs) or True)
  return calls


@pytest.mark.parametrize("alpha_long", (False, True))
@pytest.mark.parametrize("is_release", (False, True))
@pytest.mark.parametrize("alt_brake", (False, True))
def test_accord_11g_init_and_deinit_send_no_frames(recorded, alpha_long, is_release, alt_brake):
  CP = _cp(CAR.HONDA_ACCORD_11G, alpha_long, is_release, alt_brake)
  sent = []

  def can_send(msgs):
    sent.extend(msgs)

  def can_recv(**kwargs):
    raise AssertionError("Accord 11G init must not read diagnostics")

  CarInterface.init(CP, can_recv, can_send)
  CarInterface.deinit(CP, can_recv, can_send)
  assert recorded == []
  assert sent == []


def test_positive_control_bosch_radar_long_does_reach_disable_ecu(recorded):
  # Without this, the test above would pass if the monkeypatch target were renamed.
  CP = _cp(CAR.HONDA_CIVIC_BOSCH, True, False)
  assert CP.openpilotLongitudinalControl
  CarInterface.init(CP, None, None)
  assert [c["addr"] for c in recorded] == [0x18DAB0F1]

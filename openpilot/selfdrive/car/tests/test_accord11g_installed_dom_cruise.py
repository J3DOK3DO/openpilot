"""Accord 11G on installed Dom 5b0f81ca: the new SLC engagement adoption in VCruiseHelper stays inert.

Dom b64d7cf9..5b0f81ca let initialize_v_cruise adopt a speed-limit target at engagement. The adoption is gated on
openpilotLongitudinalControl, which the Accord 11G Bosch CAN-FD port never sets, so the PCM keeps owning set speed.
"""
import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from opendbc.car.structs import car
from openpilot.selfdrive.car.cruise import V_CRUISE_UNSET, VCruiseHelper

ButtonType = car.CarState.ButtonEvent.Type


def _accord_cp(alpha_long):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x1A3] = 8
  return CarInterface.get_params(CAR.HONDA_ACCORD_11G, fingerprint, [], alpha_long, False, False)


@pytest.mark.parametrize("alpha_long", (False, True))
@pytest.mark.parametrize("slc_enabled", (False, True))
@pytest.mark.parametrize("resume", (False, True))
def test_engagement_never_adopts_slc_target_or_initializes_set_speed(alpha_long, slc_enabled, resume):
  CP = _accord_cp(alpha_long)
  assert CP.pcmCruise and not CP.openpilotLongitudinalControl
  helper = VCruiseHelper(CP)
  CS = car.CarState(vEgo=25.0, cruiseState=car.CarState.CruiseState(available=True, enabled=True, speed=30.0))
  CS.buttonEvents = [car.CarState.ButtonEvent(type=ButtonType.resumeCruise, pressed=True)] if resume else []
  helper.update_v_cruise(CS, True, False, slc_enabled=slc_enabled)
  assert helper.slc_pcm is False
  before = (helper.v_cruise_kph, helper.v_cruise_cluster_kph)
  for target in (None, 20.0, 35.0):
    assert helper.initialize_v_cruise(CS, False, resume=resume, slc_target_mps=target) is False
    assert (helper.v_cruise_kph, helper.v_cruise_cluster_kph) == before


def test_pcm_set_speed_is_reported_not_owned():
  # The cluster speed mirrors the PCM, not a value initialized by openpilot.
  CP = _accord_cp(False)
  helper = VCruiseHelper(CP)
  assert helper.v_cruise_kph == V_CRUISE_UNSET
  CS = car.CarState(vEgo=25.0, cruiseState=car.CarState.CruiseState(available=True, enabled=True, speed=30.0))
  helper.update_v_cruise(CS, True, False)
  assert helper.v_cruise_kph == pytest.approx(30.0 * 3.6)

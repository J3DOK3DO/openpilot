"""Track B boundary: Accord 11G remains stock-longitudinal in every mode."""
import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, HondaSafetyFlags


@pytest.mark.parametrize("alpha_long", (False, True))
@pytest.mark.parametrize("is_release", (False, True))
@pytest.mark.parametrize("alt_brake", (False, True))
def test_accord_11g_bosch_canfd_has_no_openpilot_longitudinal_authority(alpha_long, is_release, alt_brake):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x1A3] = 8
  if alt_brake:
    fingerprint[0][0x1BE] = 3

  cp = CarInterface.get_params(CAR.HONDA_ACCORD_11G, fingerprint, [], alpha_long, is_release, False)

  assert cp.pcmCruise is True
  assert cp.openpilotLongitudinalControl is False
  assert cp.alphaLongitudinalAvailable is False
  assert len(cp.safetyConfigs) == 1
  assert cp.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.hondaBosch
  assert cp.safetyConfigs[0].safetyParam == (81 if alt_brake else 80)
  assert not (cp.safetyConfigs[0].safetyParam & HondaSafetyFlags.BOSCH_LONG)

"""Release B Tier 2 lock-off: no configuration path gives the Accord 11G (incl. Hybrid) openpilot longitudinal.

Covers the routes a settings change could take on the installed car: AlphaLongitudinalEnabled (alpha_long), release
vs development branch, alternate brake, the Hybrid flag, and Dom's VehicleStartupPreferences prepare/finalize with
every longitudinal-relevant preference in both states. Panda TX denial, radar UDS and runtime isolation are pinned
elsewhere (test_accord11g_debug_release_parity.py, test_accord11g_no_radar_uds.py, test_architectural_isolation.py).
"""
import dataclasses
import itertools

import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, HondaSafetyFlags
from openpilot.starpilot.vehicle_preferences import VehicleStartupPreferences

LONG_FIELDS = ("openpilotLongitudinalControl", "pcmCruise", "alphaLongitudinalAvailable", "radarUnavailable")


def _cp(alpha, release, alt_brake, hybrid):
  fp = gen_empty_fingerprint()
  fp[0][0x1A3] = 8
  if alt_brake:
    fp[0][0x1BE] = 3
  if hybrid:
    fp[0][0x184] = 8
  return CarInterface.get_params(CAR.HONDA_ACCORD_11G, fp, [], alpha, release, False)


def _assert_stock(cp, alt_brake):
  assert cp.pcmCruise and not cp.openpilotLongitudinalControl and not cp.alphaLongitudinalAvailable
  assert len(cp.safetyConfigs) == 1
  assert cp.safetyConfigs[0].safetyModel == structs.CarParams.SafetyModel.hondaBosch
  assert cp.safetyConfigs[0].safetyParam == (81 if alt_brake else 80)
  assert not cp.safetyConfigs[0].safetyParam & int(HondaSafetyFlags.BOSCH_LONG)


@pytest.mark.parametrize("alpha,release,alt_brake,hybrid", itertools.product((False, True), repeat=4))
def test_every_interface_configuration_stays_stock(alpha, release, alt_brake, hybrid):
  _assert_stock(_cp(alpha, release, alt_brake, hybrid), alt_brake)


# Every boolean preference, derived from the dataclass so a future preference is covered automatically (Codex RB1).
PREFERENCE_FIELDS = tuple(f.name for f in dataclasses.fields(VehicleStartupPreferences) if f.type in (bool, "bool"))


@pytest.mark.parametrize("value", (False, True))
@pytest.mark.parametrize("alt_brake", (False, True))
def test_vehicle_preferences_cannot_change_longitudinal_ownership(value, alt_brake):
  assert len(PREFERENCE_FIELDS) >= 10
  prefs = VehicleStartupPreferences(**dict.fromkeys(PREFERENCE_FIELDS, value))
  cp = _cp(True, False, alt_brake, True)
  before = {name: getattr(cp, name) for name in LONG_FIELDS}
  cp = prefs.prepare(cp) or cp
  prefs.finalize(cp)
  assert {name: getattr(cp, name) for name in LONG_FIELDS} == before
  _assert_stock(cp, alt_brake)

"""Accord 11G Hybrid: the stock-MVL qualifier, Honda stock AOL and the Track A controller admit the hybrid car.

Root cause of "AlwaysOnLateral=1 but AOL never works" on the owner's 2025 Accord Hybrid: the car's own last-route
CarParams (installed Dom 5b0f81ca) are HONDA_ACCORD_11G, hondaBosch 80, pcmCruise, flags BOSCH|BOSCH_CANFD|HYBRID,
alternativeExperience 0. accord_mvl_stock.qualified() rejected HYBRID (0x184 present), so stock_aol.qualified() and
the Honda AOL policy were False, card never added experience 32, and AccordMvlStock was never instantiated.
Every other Honda CAN-FD stock platform already admits its hybrid variant (test_canfd_stock_aol_parity.py).
"""
import pytest

from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda.accord_mvl_stock import qualified as mvl_qualified
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.stock_aol import qualified as stock_aol_qualified
from opendbc.car.honda.values import CAR, HondaFlags

HONDA_BOSCH = int(structs.CarParams.SafetyModel.hondaBosch)


def _cp(*, hybrid=True, alt_brake=False, alpha=False, release=False):
  fp = gen_empty_fingerprint()
  fp[0][0x1A3] = 8
  if hybrid:
    fp[0][0x184] = 8
  if alt_brake:
    fp[0][0x1BE] = 3
  return CarInterface.get_params(CAR.HONDA_ACCORD_11G, fp, [], alpha, release, False)


@pytest.mark.parametrize("alt_brake", (False, True))
@pytest.mark.parametrize("alpha,release", ((False, False), (True, False), (True, True)))
def test_device_equivalent_hybrid_carparams_qualify(alt_brake, alpha, release):
  cp = _cp(alt_brake=alt_brake, alpha=alpha, release=release)
  expected_flags = HondaFlags.BOSCH | HondaFlags.BOSCH_CANFD | HondaFlags.HYBRID | (HondaFlags.BOSCH_ALT_BRAKE if alt_brake else 0)
  assert int(cp.flags) == int(expected_flags)
  assert cp.pcmCruise and not cp.openpilotLongitudinalControl and cp.alternativeExperience == 0
  assert cp.safetyConfigs[0].safetyParam == (81 if alt_brake else 80)
  assert mvl_qualified(cp)
  assert stock_aol_qualified(cp)


def test_honda_aol_policy_marks_the_hybrid_and_native_receipt_accepts_its_word():
  from openpilot.starpilot.car.honda.aol import aol_safety_config, native_accepts_cp, policy_for
  cp = _cp()
  policy = policy_for(cp)
  assert policy.intent_supported and policy.explicit_latch and policy.normal_runtime_supported
  assert policy.alternative_experience_addition == 32 and policy.safety_param_addition == 0
  cp.alternativeExperience |= policy.alternative_experience_addition
  assert stock_aol_qualified(cp, marked_only=True)
  assert aol_safety_config(cp).safetyParam == 80
  assert native_accepts_cp(cp, HONDA_BOSCH, 80)
  assert not native_accepts_cp(cp, HONDA_BOSCH, 82)


def test_marked_only_requires_experience_32_for_the_11g_too():
  cp = _cp()
  assert cp.alternativeExperience == 0
  assert stock_aol_qualified(cp) and not stock_aol_qualified(cp, marked_only=True)
  from openpilot.starpilot.car.honda.aol import aol_safety_config, native_accepts_cp
  assert aol_safety_config(cp) is None
  assert not native_accepts_cp(cp, HONDA_BOSCH, 80)


def test_track_a_controller_is_instantiated_for_the_hybrid():
  from opendbc.car.honda.carcontroller import CarController
  from opendbc.car.honda.values import DBC
  cp = _cp()
  controller = CarController(DBC[cp.carFingerprint], cp)
  assert controller.accord_mvl_stock is not None


@pytest.mark.parametrize("field,value", (("passive", True), ("dashcamOnly", True), ("notCar", True)))
def test_hybrid_admission_keeps_every_other_rejection(field, value):
  cp = _cp()
  setattr(cp, field, value)
  assert not mvl_qualified(cp) and not stock_aol_qualified(cp)


def test_hybrid_admission_does_not_widen_flags_or_safety_words():
  cp = _cp()
  for word in (16, 17, 82, 112, 0x4050):
    bad = cp.as_reader().as_builder()
    bad.safetyConfigs[0].safetyParam = word
    assert not mvl_qualified(bad) and not stock_aol_qualified(bad)
  for flag in (HondaFlags.GAS_INTERCEPTOR, HondaFlags.EPS_MODIFIED, HondaFlags.BOSCH_RADARLESS, HondaFlags.BOSCH_ALT_RADAR):
    bad = cp.as_reader().as_builder()
    bad.flags = int(cp.flags) | int(flag)
    assert not mvl_qualified(bad), flag
  bad = cp.as_reader().as_builder()
  bad.openpilotLongitudinalControl = True
  assert not mvl_qualified(bad)


def test_nonhybrid_and_stock_acc_boundaries():
  from openpilot.starpilot.car.honda.aol import policy_for
  for hybrid in (False, True):
    cp = _cp(hybrid=hybrid)
    assert mvl_qualified(cp) and stock_aol_qualified(cp)
    assert policy_for(cp).alternative_experience_addition == 32
    for field, value in (("pcmCruise", False), ("openpilotLongitudinalControl", True),
                         ("alternativeExperience", 16), ("brand", "toyota")):
      bad = cp.as_reader().as_builder()
      setattr(bad, field, value)
      assert not mvl_qualified(bad) and not stock_aol_qualified(bad)


@pytest.mark.parametrize("alt_brake", (False, True))
def test_native_receipt_is_separate_from_unmarked_eligibility(alt_brake):
  from types import SimpleNamespace
  from openpilot.starpilot.car.honda.aol import native_accepts_cp, native_latch_rejected
  cp = _cp(alt_brake=alt_brake)
  word = 81 if alt_brake else 80
  assert stock_aol_qualified(cp)
  assert not stock_aol_qualified(cp, marked_only=True)
  assert not native_accepts_cp(cp, HONDA_BOSCH, word)
  # A marked CP is still only profile eligibility, never proof that a live native grant exists.
  cp.alternativeExperience = 32
  assert stock_aol_qualified(cp, marked_only=True)
  assert native_accepts_cp(cp, HONDA_BOSCH, word)
  assert not native_accepts_cp(cp, HONDA_BOSCH, 81 if word == 80 else 80)
  assert not native_accepts_cp(cp, int(structs.CarParams.SafetyModel.hondaNidec), word)
  assert native_latch_rejected(cp, SimpleNamespace(requestedLateral=True, lateralAllowed=False))
  assert not native_latch_rejected(cp, SimpleNamespace(requestedLateral=True, lateralAllowed=True))
  assert not native_latch_rejected(cp, SimpleNamespace(requestedLateral=False, lateralAllowed=False))


def test_hybrid_camera_button_withdrawal_and_brake():
  from types import SimpleNamespace
  from opendbc.can import CANPacker
  from opendbc.car import Bus
  from opendbc.car.honda.accord_mvl_stock import AccordMvlStock
  from opendbc.car.honda.values import DBC
  cp = _cp()
  cp.alternativeExperience = 32
  mvl = AccordMvlStock()
  state = SimpleNamespace(out=SimpleNamespace(brakePressed=False, cruiseState=SimpleNamespace(enabled=True)),
                          lkas_hud={"LKAS_READY": 1}, cruise_setting=0, cruise_buttons=0, scm_ambient_light=0)
  control = SimpleNamespace(enabled=True, cruiseControl=SimpleNamespace(cancel=False, resume=False))
  can = SimpleNamespace(camera=2)
  packer = CANPacker(DBC[cp.carFingerprint][Bus.pt])
  # Frame 500 starts the synthetic LKAS sequence on the actual qualifier profile.
  assert len(mvl.update(packer, can, cp, control, state, 500)) == 1
  state.out.brakePressed = True
  assert mvl.update(packer, can, cp, control, state, 504) == []
  state.out.brakePressed = False
  state.out.cruiseState.enabled = False
  assert mvl.update(packer, can, cp, control, state, 508) == []

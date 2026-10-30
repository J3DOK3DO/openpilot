"""Additional native RELEASE rejections for stock Accord 11G source policy only."""
import pytest

from opendbc.car import structs
from opendbc.safety.tests.libsafety import libsafety_py


@pytest.fixture(scope="module")
def release_safety():
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=True))


GENERIC_BOSCH_LONG = (
  (0xE4, 1, bytes(5)),
  (0x1DF, 1, bytes(8)),
  (0x1EF, 1, bytes(8)),
  (0x1FA, 1, bytes(8)),
  (0x30C, 1, bytes(8)),
  (0x33D, 1, bytes(5)),
  (0x33D, 1, bytes(8)),
  (0x33DA, 1, bytes(5)),
  (0x33DB, 1, bytes(8)),
  (0x39F, 1, bytes(8)),
  # Valid UDS single-frame tester-present form; it is not an 11G protocol claim.
  (0x18DAB0F1, 1, bytes((0x02, 0x3E, 0x00)) + bytes(5)),
)


@pytest.mark.parametrize("safety_param", (80, 81))
@pytest.mark.parametrize("alternative_experience", (0, 32))
@pytest.mark.parametrize("controls_allowed", (False, True))
def test_release_accord11g_stock_words_reject_generic_bosch_long_frames(release_safety, safety_param, alternative_experience, controls_allowed):
  safety = release_safety
  safety.init_tests()
  safety.set_alternative_experience(alternative_experience)
  assert safety.set_safety_hooks(structs.CarParams.SafetyModel.hondaBosch, safety_param) == 0
  safety.set_controls_allowed(controls_allowed)

  for address, bus, data in GENERIC_BOSCH_LONG:
    assert not safety.safety_tx_hook(libsafety_py.make_CANPacket(address, bus, data)), (
      f"RELEASE unexpectedly permitted generic Bosch-long example {address:#x} on bus {bus}")

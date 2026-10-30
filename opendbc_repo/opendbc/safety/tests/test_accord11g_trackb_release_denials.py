"""Fresh native RELEASE boundary for Accord 11G Track B: deny unqualified longitudinal TX.

Only a locally compiled libsafety shared object is used; no hardware or CAN bus.
"""
import pytest

from opendbc.car import structs
from opendbc.safety.tests.libsafety import libsafety_py


@pytest.fixture(scope="module")
def release_safety():
  # release=True omits ALLOW_DEBUG; never substitute the normal DEBUG test library.
  path = libsafety_py._build_libsafety(release=True)
  return libsafety_py.ffi.dlopen(path)


@pytest.mark.parametrize("safety_param", (80, 81))
@pytest.mark.parametrize("experience", (0, 32))
def test_release_accord11g_stock_denies_longitudinal_and_diagnostic_tx(release_safety, safety_param, experience):
  safety = release_safety
  safety.init_tests()
  safety.set_alternative_experience(experience)
  assert safety.set_safety_hooks(structs.CarParams.SafetyModel.hondaBosch, safety_param) == 0
  safety.set_controls_allowed(True)  # Ensure denials are not merely disengagement denials.

  # These are disallowed examples, NOT a proposed Track B command protocol.
  # Exercise the actual bus/length entries of the generic Bosch long TX table,
  # not just wrong-bus packets that would be denied for unrelated reasons.
  forbidden = ((0x1DF, 1, b"\0" * 8), (0x1EF, 1, b"\0" * 8),
               (0x1FA, 1, b"\0" * 8), (0x30C, 1, b"\0" * 8),
               (0x39F, 1, b"\0" * 8),
               # Valid UDS single-frame tester-present request, not a protocol proposal.
               (0x18DAB0F1, 1, bytes((0x02, 0x3E, 0x00)) + b"\0" * 5),
               (0x1C8, 0, b"\0" * 8))
  for address, bus, data in forbidden:
    packet = libsafety_py.make_CANPacket(address, bus, data)
    assert not safety.safety_tx_hook(packet), f"RELEASE unexpectedly permitted {address:#x} on bus {bus}"

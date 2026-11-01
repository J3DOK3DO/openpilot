"""Accord 11G Track B: Dom Honda CAN-FD safety rejects the MVL 3fec9a CAN-FD-long table and keeps OEM forwarding.

Reference (read-only research evidence, not authority): mvl-boston/opendbc 3fec9a418a659de31d7b1f494193161697a35071,
opendbc/safety/modes/honda.h HONDA_CANFD_LONG_TX_MSGS and honda_bosch_fwd_hook. Those entries describe what the fork
attempted (custom gas/brake/HUD, radar emulation, radar-disable UDS); they are not authenticated Accord protocol and are
used here only as negative examples. Host libsafety only: this is not validation of any flashed Panda firmware.
"""
import pytest

from opendbc.car import structs
from opendbc.safety.tests.libsafety import libsafety_py

STOCK_WORDS = (80, 81)
STOCK_EXPERIENCES = (0, 32)
PARAM_RADARLESS = 8
PARAM_BOSCH_CANFD = 16
TESTER_PRESENT = bytes((0x02, 0x3E, 0x80)) + bytes(5)
# MVL HONDA_CANFD_LONG_TX_MSGS entries that are not in Dom's stock CAN-FD tables (0xE4/0x33D bus 0, 0x296 bus 0/2).
MVL_RADAR_EMULATION = (0x310, 0x6CD5558, 0x6CD5559, 0xF31AA52, 0xF31AA5C, 0x1A45AA4E)
MVL_CANFD_LONG_ONLY = (
  (0x1DF, 0, bytes(8)), (0x1EF, 0, bytes(8)), (0x30C, 0, bytes(8)), (0x18DAB0F1, 0, TESTER_PRESENT),
  *((address, bus, bytes(8)) for address in MVL_RADAR_EMULATION for bus in (0, 2)),
)
# Dom relay-checked stock TX on bus 0: the only camera addresses the Panda may withhold from the powertrain bus.
STOCK_RELAY_CHECKED = {0xE4, 0x33D}
EXPERIENCES = (0, 32, 1, 2, 16)


@pytest.fixture(scope="module")
def release_safety():
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=True))


@pytest.fixture(scope="module")
def debug_safety():
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=False))


def _configure(lib, param, experience, controls_allowed):
  lib.init_tests()
  lib.set_alternative_experience(experience)
  assert lib.set_safety_hooks(structs.CarParams.SafetyModel.hondaBosch, param) == 0
  lib.set_controls_allowed(controls_allowed)


def _permitted(lib, frames):
  return [(hex(a), b) for a, b, d in frames if lib.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d))]


def _canfd_words(include_radarless):
  return [p for p in range(512) if p & PARAM_BOSCH_CANFD and (include_radarless or not p & PARAM_RADARLESS)]


@pytest.mark.parametrize("experience", EXPERIENCES)
def test_release_every_canfd_word_denies_mvl_canfd_long_table(release_safety, experience):
  for param in _canfd_words(include_radarless=True):
    _configure(release_safety, param, experience, True)
    assert _permitted(release_safety, MVL_CANFD_LONG_ONLY) == [], f"param {param}"


@pytest.mark.parametrize("experience", EXPERIENCES)
def test_debug_canfd_words_also_deny_mvl_canfd_long_table(debug_safety, experience):
  # Dom has no CAN-FD long table at all, so even ALLOW_DEBUG with the Bosch-long bit (2) selects only stock
  # CAN-FD TX. Radarless words are excluded: they select the radarless tables, which are covered elsewhere.
  for param in _canfd_words(include_radarless=False):
    _configure(debug_safety, param, experience, True)
    assert _permitted(debug_safety, MVL_CANFD_LONG_ONLY) == [], f"param {param}"


def test_debug_positive_control_still_reaches_bosch_long_table(debug_safety):
  # Without this the DEBUG denial above could pass because the DEBUG build lost ALLOW_DEBUG entirely.
  _configure(debug_safety, 2, 0, True)
  assert _permitted(debug_safety, [(0x1DF, 1, bytes(8))]) == [("0x1df", 1)]


@pytest.mark.parametrize("param", STOCK_WORDS)
@pytest.mark.parametrize("experience", STOCK_EXPERIENCES)
@pytest.mark.parametrize("controls_allowed", (False, True))
def test_release_stock_words_forward_every_camera_frame_except_stock_lkas(release_safety, param, experience, controls_allowed):
  # OEM ACC/CMBS/AEB/HUD frames from the camera side must reach the powertrain bus unchanged in every
  # stock state; only the relay-checked LKAS frames Dom replaces may be withheld.
  _configure(release_safety, param, experience, controls_allowed)
  blocked = [hex(a) for a in range(0x800) if release_safety.safety_fwd_hook(2, a) != 0]
  assert blocked == [hex(a) for a in sorted(STOCK_RELAY_CHECKED)]
  for address in MVL_RADAR_EMULATION:
    assert release_safety.safety_fwd_hook(2, address) == 0


@pytest.mark.parametrize("param", STOCK_WORDS)
@pytest.mark.parametrize("controls_allowed", (False, True))
def test_release_stock_words_do_not_adopt_mvl_radar_disable_forwarding_block(release_safety, param, controls_allowed):
  # MVL blocks radar UDS responses (0x18DAF1B0, bus 0) during its radar-disable handshake. Dom performs no radar
  # disable, so radar diagnostics and all powertrain frames other than SCM_BUTTONS keep forwarding to the camera.
  _configure(release_safety, param, 0, controls_allowed)
  assert release_safety.safety_fwd_hook(0, 0x18DAF1B0) == 2
  blocked = [hex(a) for a in range(0x800) if release_safety.safety_fwd_hook(0, a) != 2]
  assert blocked == []

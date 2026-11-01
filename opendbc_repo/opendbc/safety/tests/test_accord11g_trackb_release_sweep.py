"""Native RELEASE sweep for Accord 11G Track B: deny longitudinal/diagnostic TX in every non-stock configuration.

Host libsafety only. This is not validation of any flashed Panda firmware, and the frames below
are disallowed examples, not a proposed Track B command protocol.
"""
import pytest

from opendbc.car import structs
from opendbc.safety.tests.libsafety import libsafety_py

STOCK_WORDS = (80, 81)
STOCK_EXPERIENCES = (0, 32)
# Bosch-long and UDS examples (bus 1 is the Bosch-long table's bus; bus 0 repeats them on the stock bus).
FORBIDDEN = tuple((address, bus, bytes(length)) for address, length in
                  ((0x1DF, 8), (0x1EF, 8), (0x1FA, 8), (0x30C, 8), (0x39F, 8)) for bus in (0, 1, 2)) + (
  # Both tester-present forms: with and without the suppress-positive-response bit (0x80).
  *((0x18DAB0F1, bus, bytes((0x02, 0x3E, sub)) + bytes(5)) for bus in (0, 1) for sub in (0x00, 0x80)),
)
# alternativeExperience is Int16: dense low range, every single-bit value, and the signed extremes.
EXPERIENCES = (*range(512), *(1 << bit for bit in range(9, 15)), 0x7FFF, -1, -0x8000)
STOCK_TX = ((0xE4, 0, 5), (0x296, 0, 4), (0x296, 2, 4), (0x33D, 0, 8))


@pytest.fixture(scope="module")
def release_safety():
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=True))


@pytest.fixture(scope="module")
def debug_safety():
  # Positive control only: proves the forbidden frames are reachable when ALLOW_DEBUG is compiled in.
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=False))


def _configure(lib, param, experience, controls_allowed):
  lib.init_tests()
  lib.set_alternative_experience(experience)
  assert lib.set_safety_hooks(structs.CarParams.SafetyModel.hondaBosch, param) == 0
  lib.set_controls_allowed(controls_allowed)


def _permitted(lib, frames):
  return [(hex(a), b) for a, b, d in frames if lib.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d))]


@pytest.mark.parametrize("param", STOCK_WORDS)
@pytest.mark.parametrize("controls_allowed", (False, True))
def test_release_stock_words_deny_forbidden_frames_for_every_alternative_experience(release_safety, param, controls_allowed):
  for experience in EXPERIENCES:
    _configure(release_safety, param, experience, controls_allowed)
    assert _permitted(release_safety, FORBIDDEN) == [], f"experience {experience}"
    if experience not in STOCK_EXPERIENCES:
      # Non-stock experiences leave no TX table at all: even the stock LKAS/button frames are denied.
      assert _permitted(release_safety, [(a, b, bytes(n)) for a, b, n in STOCK_TX]) == [], f"experience {experience}"


# Every 9-bit safety word except the two stock words, which have their own test above.
@pytest.mark.parametrize("experience", (0, 32, 1, 2, 16))
def test_release_every_non_stock_bosch_word_denies_forbidden_frames(release_safety, experience):
  for param in range(512):
    if param in STOCK_WORDS:
      continue
    _configure(release_safety, param, experience, True)
    assert _permitted(release_safety, FORBIDDEN) == [], f"param {param}"


def test_release_build_differs_from_debug_build_positive_control(release_safety, debug_safety):
  # Frames RELEASE denies must be reachable in the DEBUG library, otherwise the denial tests prove nothing.
  frames = [(0x1DF, 1, bytes(8)), (0x18DAB0F1, 1, bytes((0x02, 0x3E, 0x80)) + bytes(5))]
  _configure(debug_safety, 2, 0, True)
  debug_hits = _permitted(debug_safety, frames)
  _configure(release_safety, 2, 0, True)
  assert _permitted(release_safety, frames) == []
  assert debug_hits == [("0x1df", 1), ("0x18dab0f1", 1)], "positive control failed: DEBUG library no longer reaches the Bosch-long/UDS table"

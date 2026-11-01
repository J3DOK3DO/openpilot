"""Accord 11G Release A: the shipped DEBUG Panda build behaves exactly like RELEASE for the stock words 80/81.

Dom commits panda/board/obj firmware built without RELEASE=1, so it is compiled with ALLOW_DEBUG and signed with
the debug key (panda/board/obj/version ends in -DEBUG). The RELEASE-library tests elsewhere therefore do not by
themselves describe that firmware. In honda.h the only ALLOW_DEBUG difference is the Bosch-long bit (2) and the
RDX/AOL words, and in honda_stock_aol.h extra Bosch words (10, 11, 1058, ...); none of them is 80 or 81. This test
proves the equivalence on the host libraries rather than relying on that reading.

Host libsafety only: it is not a measurement of the flashed Panda.
"""
import random

import pytest

from opendbc.car import structs
from opendbc.safety.tests.libsafety import libsafety_py

STOCK_WORDS = (80, 81)
EXPERIENCES = (0, 32, 1, 2, 16, 33)
BUSES = (0, 1, 2)
# Dom stock CAN-FD TX lengths plus the classic 8-byte length, each with zero, all-ones and seeded payloads.
LENGTHS = (4, 5, 8)
EXTENDED = (0x18DAB0F1, 0x18DAF1B0, 0x18DB33F1, 0x6CD5558, 0xF31AA52, 0x1A45AA4E)


@pytest.fixture(scope="module")
def release_safety():
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=True))


@pytest.fixture(scope="module")
def debug_safety():
  return libsafety_py.ffi.dlopen(libsafety_py._build_libsafety(release=False))


def _configure(lib, model, param, experience, controls_allowed):
  lib.init_tests()
  lib.set_alternative_experience(experience)
  ret = lib.set_safety_hooks(model, param)
  lib.set_controls_allowed(controls_allowed)
  return ret


def _payloads():
  rng = random.Random(0xACC11)
  for length in LENGTHS:
    yield bytes(length)
    yield bytes((0xFF,) * length)
    yield bytes(rng.randrange(256) for _ in range(length))


def _tx_profile(lib):
  addresses = (*range(0x800), *EXTENDED)
  return [(a, b, d) for a in addresses for b in BUSES for d in _payloads()
          if lib.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d))]


def _fwd_profile(lib):
  return [(b, a, lib.safety_fwd_hook(b, a)) for b in BUSES for a in (*range(0x800), *EXTENDED)]


@pytest.mark.parametrize("param", STOCK_WORDS)
@pytest.mark.parametrize("experience", EXPERIENCES)
@pytest.mark.parametrize("controls_allowed", (False, True))
def test_debug_matches_release_tx_and_forwarding_for_stock_words(release_safety, debug_safety, param, experience, controls_allowed):
  model = structs.CarParams.SafetyModel.hondaBosch
  assert _configure(release_safety, model, param, experience, controls_allowed) == 0
  release_tx, release_fwd = _tx_profile(release_safety), _fwd_profile(release_safety)
  assert _configure(debug_safety, model, param, experience, controls_allowed) == 0
  assert _tx_profile(debug_safety) == release_tx
  assert _fwd_profile(debug_safety) == release_fwd
  # Never a Bosch-long, radar-emulation or diagnostic frame in either build.
  assert not {a for a, _, _ in release_tx} & {0x1DF, 0x1EF, 0x1FA, 0x30C, 0x39F, *EXTENDED}


def test_stock_word_tx_profile_is_the_dom_mvl_stock_table(release_safety):
  # Pins what the parity above is equal to: only the stock LKAS/button/HUD frames, only with controls allowed.
  model = structs.CarParams.SafetyModel.hondaBosch
  for param in STOCK_WORDS:
    assert _configure(release_safety, model, param, 32, True) == 0
    assert sorted({(hex(a), b) for a, b, _ in _tx_profile(release_safety)}) == \
      [("0x296", 0), ("0x296", 2), ("0x33d", 0), ("0xe4", 0)]


def test_debug_library_really_has_allow_debug(release_safety, debug_safety):
  # Positive control: without it the parity could hold because both libraries were built the same way.
  frame = [(0x1DF, 1, bytes(8))]
  model = structs.CarParams.SafetyModel.hondaBosch
  _configure(debug_safety, model, 2, 0, True)
  assert [a for a, b, d in frame if debug_safety.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d))] == [0x1DF]
  _configure(release_safety, model, 2, 0, True)
  assert [a for a, b, d in frame if release_safety.safety_tx_hook(libsafety_py.make_CANPacket(a, b, d))] == []


def test_all_output_model_is_debug_only(release_safety, debug_safety):
  # Residual DEBUG hazard, recorded rather than hidden: allOutput exists only with ALLOW_DEBUG. Accord 11G CarParams
  # select hondaBosch 80/81 (test_accord11g_trackb_no_long_authority.py), so it is reachable only by a host that asks
  # for allOutput explicitly.
  model = structs.CarParams.SafetyModel.allOutput
  assert _configure(release_safety, model, 0, 0, False) != 0
  assert _configure(debug_safety, model, 0, 0, False) == 0

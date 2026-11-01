"""Accord 11G on installed Dom 5b0f81ca: the PID lateral controller is not replaced by the new shared torque law.

Dom b64d7cf9..5b0f81ca registered every platform in KNOWN_POLICIES and added a "generic" torque policy. The Accord
11G port uses PID lateral tuning, so it must keep the standard controller, ignore any saved selection document entry
and refuse a mode change, exactly as it did before that change.
"""
import json

import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from openpilot.starpilot.lateral import controller_selection as cs


def _accord_cp(alpha_long):
  fingerprint = gen_empty_fingerprint()
  fingerprint[0][0x1A3] = 8
  return CarInterface.get_params(CAR.HONDA_ACCORD_11G, fingerprint, [], alpha_long, False, False)


@pytest.mark.parametrize("alpha_long", (False, True))
def test_accord_keeps_pid_and_standard_controller(alpha_long):
  CP = _accord_cp(alpha_long)
  assert CP.lateralTuning.which() == "pid"
  assert cs.KNOWN_POLICIES["HONDA_ACCORD_11G"] == "honda"
  assert not cs.generic_torque_supported(CP)
  assert cs.policy_for(CP) is None
  assert not cs.turn_assist_supported(CP)
  assert not cs.model_turn_assist_supported(CP)
  assert cs.default_selection(CP) == cs.ControllerSelection(cs.ControllerMode.STANDARD, None, "default")


@pytest.mark.parametrize("mode", (cs.ControllerMode.STANDARD, cs.ControllerMode.STARPILOT))
def test_saved_accord_entry_is_parseable_but_ignored(mode):
  CP = _accord_cp(False)
  raw = json.dumps({"version": cs.DOCUMENT_VERSION,
                    "vehicles": {"HONDA_ACCORD_11G": {"brand": "honda", "mode": mode.value}}}).encode()
  assert cs.parse_document(raw)["vehicles"]["HONDA_ACCORD_11G"]["mode"] == mode.value
  assert cs.selection_from_bytes(CP, raw) == cs.default_selection(CP)
  with pytest.raises(ValueError):
    cs.replace_mode(raw, CP, mode)

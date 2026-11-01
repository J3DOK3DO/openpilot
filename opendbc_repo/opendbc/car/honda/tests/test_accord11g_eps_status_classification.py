"""BC-013: the Accord 11G EPS status classification through the real CAN-FD parser.

Characterizes installed Dom behaviour for the 11G (not BOSCH_ALT_RADAR, so the generic Honda branch): an EPS
low-speed lockout is not a fault, NO_TORQUE_ALERT_2 is tolerated, and every other non-NORMAL state is a fault. The
mapping is native Dom code, unchanged by Track A/B; the test pins it so a later patch cannot silently relax it.
"""
import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.tests.test_canfd_stock_aol_parity import frames
from opendbc.car.honda.values import CAR, HondaFlags

# status name -> (steerFaultPermanent, steerFaultTemporary)
EXPECTED = {
  "NORMAL": (False, False),
  "TJA_LOW_SPEED_LOCKOUT": (True, True),
  "NO_TORQUE_ALERT_1": (False, True),
  "LOW_SPEED_LOCKOUT": (False, False),
  "NO_TORQUE_ALERT_2": (False, False),
  "FAULT_1": (True, True),
  "TMP_FAULT": (False, True),
}


def _interface(hybrid):
  fp = gen_empty_fingerprint()
  fp[0][0x1A3] = 8
  if hybrid:
    fp[0][0x184] = 8
  ci = CarInterface(CarInterface.get_params(CAR.HONDA_ACCORD_11G, fp, [], False, False, False))
  ci._canfd_test_packers = {}
  return ci


def _parse(ci, eps, ticks=5):
  out = None
  for tick in range(ticks):
    now = 10_000_000_000 + tick * 10_000_000
    out = ci.update([(now, frames(ci, eps=eps))])
  return out


def test_status_table_matches_the_dbc():
  ci = _interface(True)
  assert ci.CP.carFingerprint == CAR.HONDA_ACCORD_11G
  assert ci.CP.flags & HondaFlags.BOSCH_CANFD and ci.CP.flags & HondaFlags.HYBRID
  assert not ci.CP.flags & HondaFlags.BOSCH_ALT_RADAR
  assert set(ci.CS.steer_status_values.values()) == set(EXPECTED)


@pytest.mark.parametrize("hybrid", (False, True))
@pytest.mark.parametrize("name", tuple(EXPECTED))
def test_parsed_eps_status_fault_classification(hybrid, name):
  ci = _interface(hybrid)
  raw = {v: k for k, v in ci.CS.steer_status_values.items()}[name]
  out = _parse(ci, raw)
  assert (out.steerFaultPermanent, out.steerFaultTemporary) == EXPECTED[name]


@pytest.mark.parametrize("name", ("NO_TORQUE_ALERT_2", "TMP_FAULT"))
def test_contrast_alt_radar_branch_classifies_differently(name):
  # Same parser and frames with only BOSCH_ALT_RADAR added: at 45 m/s NO_TORQUE_ALERT_2 becomes a temporary fault in
  # the ALT_RADAR branch, so the generic-branch result above is proven to come from the 11G (non ALT_RADAR) path.
  ci = _interface(True)
  raw = {v: k for k, v in ci.CS.steer_status_values.items()}[name]
  generic = _parse(ci, raw).steerFaultTemporary
  ci.CS.CP.flags |= int(HondaFlags.BOSCH_ALT_RADAR)
  alt = _parse(ci, raw).steerFaultTemporary
  assert alt is True
  assert generic is (name == "TMP_FAULT")


def test_fault_clears_only_when_eps_reports_normal():
  ci = _interface(True)
  raw = {v: k for k, v in ci.CS.steer_status_values.items()}
  assert _parse(ci, raw["TMP_FAULT"]).steerFaultTemporary
  assert _parse(ci, raw["LOW_SPEED_LOCKOUT"]).steerFaultTemporary is False
  assert _parse(ci, raw["FAULT_1"]).steerFaultPermanent
  out = _parse(ci, raw["NORMAL"])
  assert not out.steerFaultPermanent and not out.steerFaultTemporary

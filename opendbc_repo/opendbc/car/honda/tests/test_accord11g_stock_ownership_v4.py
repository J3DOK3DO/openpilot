"""Accord11G native CarParams ownership matrix, fresh sources only."""
import pytest

from opendbc.car import gen_empty_fingerprint
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR
from opendbc.car.honda.accord_mvl_stock import qualified as stock_mvl_qualified
from opendbc.car.honda.stock_aol import qualified as stock_aol_qualified


@pytest.mark.parametrize("release", [False, True])
@pytest.mark.parametrize("alpha", [False, True])
@pytest.mark.parametrize("alt_brake", [False, True])
def test_stock_acc_not_replaced_by_alpha_and_release(release, alpha, alt_brake):
  fp = gen_empty_fingerprint()
  fp[0][0x1A3] = 8
  if alt_brake:
    fp[0][0x1BE] = 3
  cp = CarInterface.get_params(CAR.HONDA_ACCORD_11G, fp, [], alpha, release, False)
  assert cp.pcmCruise
  assert not cp.openpilotLongitudinalControl
  assert not cp.alphaLongitudinalAvailable
  assert cp.safetyConfigs[0].safetyParam == (81 if alt_brake else 80)
  assert stock_mvl_qualified(cp)
  assert stock_aol_qualified(cp)
  # A different safety word must not inherit the stock-MVL authority.
  cp.safetyConfigs[0].safetyParam = 82
  assert not stock_mvl_qualified(cp)
  assert not stock_aol_qualified(cp)

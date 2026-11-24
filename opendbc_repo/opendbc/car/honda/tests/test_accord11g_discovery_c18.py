"""Synthetic normal-harness signature selects query wiring, never CAN identity."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from opendbc.car import car_helpers, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.honda.discovery import (ACCORD_11G_LAYOUT, accord_11g_topology,
                                         accord_11g_outcome, IDENTIFIED, HOLD, OTHER)
from opendbc.car.honda.values import CAR
from opendbc.car.vin import VIN_UNKNOWN


SYNTHETIC = json.loads((Path(__file__).parent / 'testdata/accord11g_startup_discovery.json').read_text())


def window():
  return [[CanData(f['address'], bytes.fromhex(f['hex']), f['bus']) for f in batch]
          for batch in SYNTHETIC['windowBatches']]


def synthetic_fw():
  return [structs.CarParams.CarFw(ecu=getattr(structs.CarParams.Ecu, f['ecu']), fwVersion=bytes.fromhex(f['fwVersion']),
                                  address=f['address'], subAddress=f['subAddress'], bus=f['bus'],
                                  request=[bytes.fromhex(r) for r in f['request']], brand=f['brand'],
                                  obdMultiplexing=f['obdMultiplexing'], logging=f['logging'])
          for f in SYNTHETIC['carFw']]


def test_synthetic_signature_and_every_required_source():
  batches = window()
  assert accord_11g_topology(batches)
  for key in ACCORD_11G_LAYOUT:
    filtered = [[f for f in batch if (f.src, f.address) != key] for batch in batches]
    assert not accord_11g_topology(filtered)
    bus, addr = key
    assert not accord_11g_topology(filtered + [[CanData(addr, bytes(ACCORD_11G_LAYOUT[key] - 1), bus)]])
  assert not accord_11g_topology([])


def test_exact_firmware_outcomes():
  fw = synthetic_fw()
  assert accord_11g_outcome(fw, VIN_UNKNOWN) == IDENTIFIED
  assert accord_11g_outcome([], VIN_UNKNOWN) == HOLD
  assert accord_11g_outcome(fw[:1], VIN_UNKNOWN) == HOLD
  unknown = synthetic_fw()
  unknown[-1].fwVersion = b'8S102-30A-A999\x00\x00'
  assert accord_11g_outcome(unknown, VIN_UNKNOWN) == HOLD
  from opendbc.car.fw_versions import FW_VERSIONS
  for row in fw:
    row.fwVersion = next(v[0] for (_, addr, _), v in FW_VERSIONS[CAR.HONDA_CRV_6G].items() if addr == row.address)
  assert accord_11g_outcome(fw, VIN_UNKNOWN) == OTHER


def test_honda_query_filter_sends_only_normal_bus0():
  from opendbc.car import fw_versions
  buses, switches = [], []

  class Query:
    def __init__(self, send, recv, bus, *args):
      buses.append(bus)

    def get_data(self, timeout):
      return {}

  with patch.object(fw_versions, 'IsoTpParallelQuery', Query):
    fw_versions.get_fw_versions(lambda **kw: [], lambda frames: None, switches.append,
                                query_brand='honda', normal_bus_only=True, query_bus=0)
  assert buses and set(buses) == {0} and switches == []


@pytest.mark.parametrize('case', ('exact', 'none', 'partial', 'other'))
def test_discovery_no_mux_on_accord_and_other_honda_fallback(case):
  batches = window()
  switches = []
  clock = [10.]

  def recv(**kwargs):
    clock[0] += .01
    return [batches.pop(0)] if batches else []

  fw = synthetic_fw()
  if case == 'none':
    fw = []
  elif case == 'partial':
    fw = fw[:1]
  elif case == 'other':
    from opendbc.car.fw_versions import FW_VERSIONS
    for row in fw:
      row.fwVersion = next(v[0] for (_, addr, _), v in FW_VERSIONS[CAR.HONDA_CRV_6G].items() if addr == row.address)
  with patch.dict(car_helpers.os.environ, {'FINGERPRINT': '', 'SKIP_FW_QUERY': '', 'DISABLE_FW_CACHE': ''}), \
       patch.object(car_helpers.time, 'monotonic', side_effect=lambda: clock[0]), \
       patch.object(car_helpers.time, 'sleep', side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)), \
       patch.object(car_helpers, 'get_vin', return_value=(-1, -1, VIN_UNKNOWN)) as vin, \
       patch.object(car_helpers, 'get_fw_versions', return_value=fw) as query, \
       patch.object(car_helpers, 'get_present_ecus', return_value=set()) as present, \
       patch.object(car_helpers, 'get_fw_versions_ordered', return_value=[]) as generic, \
       patch.object(car_helpers, 'can_fingerprint', return_value=(CAR.HONDA_ACCORD_11G, {})):
    candidate, _, _, _, _, _ = car_helpers.fingerprint(recv, lambda frames: None, switches.append, None)
  if case == 'other':
    assert True in switches and present.called and generic.called
    assert query.call_count == 1
  else:
    assert switches and not any(switches) and not present.called and not generic.called
    assert vin.call_args.args[2] == (0,)
    assert all(call.kwargs == {'query_brand': 'honda', 'normal_bus_only': True, 'query_bus': 0}
               for call in query.call_args_list)
    if case == 'exact':
      assert candidate == CAR.HONDA_ACCORD_11G and query.call_count == 1
    else:
      assert candidate is None and 2 <= query.call_count <= 10
      assert clock[0] - 10. >= 4.5


def test_unrelated_vehicle_keeps_generic_path():
  switches = []
  with patch('opendbc.car.car_helpers.get_vin', return_value=(-1, -1, VIN_UNKNOWN)), \
       patch('opendbc.car.car_helpers.get_present_ecus', return_value=set()) as present, \
       patch('opendbc.car.car_helpers.get_fw_versions_ordered', return_value=[]) as generic, \
       patch('opendbc.car.car_helpers.can_fingerprint', return_value=(None, {})):
    car_helpers.fingerprint(lambda **kw: [], lambda frames: None, switches.append, None)
  assert switches == [True, False] and present.called and generic.called


def test_interrupt_rate_can2_remains_a_blocking_fault():
  from openpilot.cereal import log
  from openpilot.starpilot.aol.panda_faults import blocking_fault_list, blocking_fault_mask
  from opendbc.car.honda.interface import CarInterface
  from opendbc.car import gen_empty_fingerprint
  cp = CarInterface.get_params(CAR.HONDA_ACCORD_11G, gen_empty_fingerprint(), [], False, False, False)
  assert blocking_fault_mask(1 << 3, cp)
  assert blocking_fault_list([log.PandaState.FaultType.interruptRateCan2], cp)

"""Recorded Accord 11G discovery must not switch its normal harness CAN2 into OBD.

2026-11-12 routes: every boot muxed CAN2 to the OBD port, VIN and all muxed
requests timed out, and CAN2 accumulated ~35k protocol errors. Route 0 peaked
at 17,862 IRQ/s (> 16,000) and latched interruptRateCan2 -> controlsMismatch.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from opendbc.car import car_helpers, fw_versions, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.ford.discovery import normal_bus_query_brand
from opendbc.car.honda.discovery import NORMAL_BUS_LAYOUT, normal_bus_identified, normal_bus_queries, normal_bus_topology
from opendbc.car.honda.values import CAR, HondaFlags
from opendbc.car.hyundai.discovery import normal_bus_topology as hyundai_probe
from opendbc.car.vin import VIN_UNKNOWN

CAPTURE = json.loads((Path(__file__).parent / 'testdata/accord11g_startup_discovery.json').read_text())


def window():
  return [[CanData(f['address'], bytes.fromhex(f['hex']), f['bus']) for f in batch] for batch in CAPTURE['windowBatches']]


def fingerprint_frames():
  return [CanData(f['address'], bytes.fromhex(f['hex']), f['bus']) for f in CAPTURE['fingerprintFrames']]


def recorded_fw():
  return [structs.CarParams.CarFw(ecu=getattr(structs.CarParams.Ecu, f['ecu']), fwVersion=bytes.fromhex(f['fwVersion']),
                                  address=f['address'], subAddress=f['subAddress'], bus=f['bus'],
                                  request=[bytes.fromhex(r) for r in f['request']], brand=f['brand'],
                                  obdMultiplexing=f['obdMultiplexing'], logging=f['logging'])
          for f in CAPTURE['carFw']]


def layout(rows):
  result = {}
  for f in rows:
    result.setdefault(f.src, {})[f.address] = len(f.dat)
  return result


def batches_reader(batches):
  remaining = list(batches)
  return lambda **kw: [remaining.pop(0)] if remaining else []


def test_recorded_pre_query_window_selects_only_honda_normal_wiring():
  rows = [f for batch in window() for f in batch]
  assert normal_bus_topology(layout(rows))
  assert normal_bus_query_brand(batches_reader(window()), hyundai_probe,
                                honda_probe=normal_bus_topology, clock=lambda: 0.) == 'honda'


def test_honda_probe_is_last_and_absent_probe_keeps_old_result():
  assert normal_bus_query_brand(batches_reader(window()), hyundai_probe, clock=lambda: 0.) is None


@pytest.mark.parametrize('key', NORMAL_BUS_LAYOUT)
@pytest.mark.parametrize('defect', ('missing', 'length', 'bus', 'echo', 'contradiction'))
def test_every_layout_source_must_be_consistent(key, defect):
  rows = [CanData(a, bytes(n), b) for (b, a), n in NORMAL_BUS_LAYOUT.items()]
  original = next(f for f in rows if (f.src, f.address) == key)
  rows.remove(original)
  if defect in ('length', 'contradiction'):
    rows.append(CanData(original.address, original.dat[:-1], original.src))
    if defect == 'contradiction':
      rows.append(original)
  elif defect != 'missing':
    rows.append(CanData(original.address, original.dat, original.src + (128 if defect == 'echo' else 1)))
  assert normal_bus_query_brand(lambda **kw: [rows], hyundai_probe,
                                honda_probe=normal_bus_topology, clock=lambda: 0.) is None


def test_normal_bus_filter_keeps_bus0_identity_request_and_no_mux():
  assert normal_bus_queries()
  honda = [r for brand, _, r in fw_versions.REQUESTS if brand == 'honda']
  assert any(r.bus % 4 == 1 and r.obd_multiplexing for r in honda)  # the requests being skipped exist
  assert all(fw.bus == 0 for fw in recorded_fw())  # and the recorded identity never came from them


def test_recorded_fw_identifies_only_accord_11g():
  assert normal_bus_identified(recorded_fw(), VIN_UNKNOWN)
  assert not normal_bus_identified([], VIN_UNKNOWN)
  other = [fw for fw in recorded_fw() if fw.ecu == structs.CarParams.Ecu.fwdCamera]
  other[0].fwVersion = b'39990-XXX-A000\x00\x00'
  assert not normal_bus_identified(other, VIN_UNKNOWN)


class CapturedCan:
  def __init__(self):
    self.clock = 10.
    self.sent = []
    self.switches = []
    self.pending = window()

  def recv(self, wait_for_one=False):
    self.clock += .01
    return [self.pending.pop(0)] if self.pending else [fingerprint_frames()]

  def send(self, rows):
    self.sent.extend(rows)


def discover(*, fw=None, old=False):
  peer = CapturedCan()
  fw = recorded_fw() if fw is None else fw
  with patch.dict(car_helpers.os.environ, {'FINGERPRINT': '', 'SKIP_FW_QUERY': '', 'DISABLE_FW_CACHE': ''}), \
       patch.object(car_helpers.time, 'monotonic', side_effect=lambda: peer.clock), \
       patch.object(car_helpers.time, 'sleep', side_effect=lambda seconds: setattr(peer, 'clock', peer.clock + seconds)), \
       patch.object(car_helpers, 'get_present_ecus', return_value=set()) as present, \
       patch.object(car_helpers, 'get_fw_versions_ordered', return_value=recorded_fw()) as generic, \
       patch.object(car_helpers, 'get_fw_versions', return_value=fw) as normal, \
       patch.object(car_helpers, 'honda_normal_bus_topology', side_effect=(lambda fp: False) if old else normal_bus_topology):
    ci = car_helpers.get_car(peer.recv, peer.send, peer.switches.append, False, False)
  return ci, peer, present, generic, normal


def test_recorded_discovery_keeps_can2_on_normal_wiring_and_same_profile():
  ci, peer, present, generic, normal = discover()
  assert peer.switches and set(peer.switches) == {False}
  assert peer.sent and all(f.src == 0 for f in peer.sent)
  normal.assert_called_once()
  assert normal.call_args.kwargs == {'query_brand': 'honda', 'normal_bus_only': True, 'request_buses': frozenset({0})}
  present.assert_not_called()
  generic.assert_not_called()
  cp = ci.CP
  assert cp.carFingerprint == CAR.HONDA_ACCORD_11G
  assert cp.fingerprintSource == structs.CarParams.FingerprintSource.fw and not cp.fuzzyFingerprint
  assert int(cp.flags) & int(HondaFlags.BOSCH_CANFD) and int(cp.flags) & int(HondaFlags.HYBRID)
  assert cp.safetyConfigs[-1].safetyModel == structs.CarParams.SafetyModel.hondaBosch
  assert cp.pcmCruise and not cp.openpilotLongitudinalControl


def test_same_profile_as_recorded_obd_sweep():
  new, *_ = discover()
  old, peer, present, generic, _ = discover(old=True)
  assert True in peer.switches and any(f.src == 1 for f in peer.sent)
  present.assert_called_once()
  generic.assert_called_once()
  for field in ('carFingerprint', 'flags', 'pcmCruise', 'openpilotLongitudinalControl', 'alternativeExperience', 'steerActuatorDelay'):
    assert getattr(new.CP, field) == getattr(old.CP, field), field
  assert [(c.safetyModel, c.safetyParam) for c in new.CP.safetyConfigs] == [(c.safetyModel, c.safetyParam) for c in old.CP.safetyConfigs]


def degraded_fw(kind):
  fw = recorded_fw()
  if kind == 'none':
    return []
  if kind == 'unknown':
    fw[1].fwVersion = b'8S102-30A-A999\x00\x00'
    return fw
  keep = structs.CarParams.Ecu.fwdRadar if kind == 'radar_only' else structs.CarParams.Ecu.fwdCamera
  return [f for f in fw if f.ecu == keep]


@pytest.mark.parametrize('kind', ('none', 'unknown', 'radar_only', 'camera_only'))
def test_incomplete_accord_firmware_holds_closed_without_obd_sweep(kind):
  # C8.1: retry once on bus 0, then hold. Never rerun the storm-producing OBD scan.
  fw = degraded_fw(kind)
  ci, peer, present, generic, normal = discover(fw=fw)
  assert normal.call_count >= 2  # spaced bus-0 retries until the discovery deadline
  assert True not in peer.switches
  present.assert_not_called()
  generic.assert_not_called()
  assert ci.CP.carFingerprint == 'MOCK'


def test_firmware_of_another_honda_keeps_original_obd_sweep():
  from opendbc.car.fw_versions import FW_VERSIONS
  fw = recorded_fw()
  for f in fw:
    f.fwVersion = next(v[0] for (_, address, _), v in FW_VERSIONS[CAR.HONDA_CRV_6G].items() if address == f.address)
  _, peer, present, generic, normal = discover(fw=fw)
  normal.assert_called_once()
  assert True in peer.switches and peer.switches[-1] is False
  present.assert_called_once()
  generic.assert_called_once()


def test_discovery_fix_keeps_reported_irq_fault_blocking():
  from openpilot.cereal import log
  from openpilot.starpilot.aol.panda_faults import blocking_fault_list, blocking_fault_mask
  ci, *_ = discover()
  assert blocking_fault_mask(8, ci.CP)
  assert blocking_fault_list([log.PandaState.FaultType.interruptRateCan2], ci.CP)

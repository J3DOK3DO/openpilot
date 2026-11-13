"""C8.1: production FW/VIN/ISO-TP logic against a transport-level Accord 11G ECU simulator.

Nothing in fw_versions, isotp_parallel_query, uds, vin or car_helpers is mocked. The fake
peer implements ISO-TP on CAN frames: the recorded radar (0x18dab0f1) and camera
(0x18dab5f1) answer UDS 0x22 F1 81 on bus 0 only, as on the 2026-11-12 routes. A virtual
clock advances 10 ms per receive, so production timeouts and the passive-window deadline run.
"""
import glob
import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from opendbc.car import car_helpers, structs, uds
from opendbc.car.can_definitions import CanData
from opendbc.car.ford.discovery import normal_bus_query_brand
from opendbc.car.fw_versions import FW_VERSIONS, get_fw_versions
from opendbc.car.honda.discovery import (HOLD, IDENTIFIED, NORMAL_BUS_LAYOUT, OTHER, normal_bus_fw,
                                         normal_bus_topology)
from opendbc.car.honda.values import CAR
from opendbc.car.hyundai.discovery import normal_bus_topology as hyundai_probe
from opendbc.car.vin import VIN_UNKNOWN

HERE = Path(__file__).parent
CAPTURE = json.loads((HERE / 'testdata/accord11g_startup_discovery.json').read_text())
RADAR, CAMERA = 0x18DAB0F1, 0x18DAB5F1
RECORDED = {RADAR: b'8S302-30A-A040\x00\x00', CAMERA: b'8S102-30A-A060\x00\x00'}
TIMEOUT = 0.1  # production get_fw_versions default


class Ecu:
  def __init__(self, fw, *, delay=0.02, silent_attempts=0, silent=False, buses=(0,)):
    self.fw, self.delay, self.silent_attempts, self.silent, self.buses = fw, delay, silent_attempts, silent, buses
    self.requests = 0
    self.pending_cf = []


class Peer:
  def __init__(self, ecus, background=None):
    self.now = 100.
    self.ecus = ecus
    self.background = list(background or [])
    self.tail = []
    self.queue = []  # (due, CanData)
    self.sent = []
    self.switches = []

  def recv(self, wait_for_one=False):
    self.now += .01
    due = [f for t, f in self.queue if t <= self.now]
    self.queue = [(t, f) for t, f in self.queue if t > self.now]
    batch = self.background.pop(0) if self.background else list(self.tail)
    if self.switches and self.switches[-1] is True:
      batch = [f for f in batch if f.src != 1]  # CAN2 is on the OBD port, not the ADAS bus
    return [due + batch] if (due or batch) else []

  def send(self, msgs):
    for m in msgs:
      self.sent.append((m.src, m.address, bytes(m.dat)))
      ecu = self.ecus.get(m.address)
      if ecu is None or m.src not in ecu.buses:
        continue
      rx = uds.get_rx_addr_for_tx_addr(m.address)
      kind = m.dat[0] >> 4
      if kind == 0 and bytes(m.dat[1:3]) == b'\x3e\x00' and not ecu.silent:
        self.queue.append((self.now + ecu.delay, CanData(rx, b'\x02\x7e\x00'.ljust(8, b'\x00'), m.src)))
      elif kind == 0 and bytes(m.dat[1:1 + (m.dat[0] & 0xF)]) == b'\x22\xf1\x81':
        ecu.requests += 1
        if ecu.silent or ecu.requests <= ecu.silent_attempts:
          continue
        payload = b'\x62\xf1\x81' + ecu.fw
        ecu.pending_cf = [payload[6 + 7 * i:13 + 7 * i] for i in range((len(payload) - 6 + 6) // 7)]
        first = bytes([0x10 | (len(payload) >> 8), len(payload) & 0xFF]) + payload[:6]
        self.queue.append((self.now + ecu.delay, CanData(rx, first, m.src)))
      elif kind == 3 and ecu.pending_cf:
        for i, chunk in enumerate(ecu.pending_cf):
          self.queue.append((self.now + .001 * (i + 1), CanData(rx, bytes([0x20 | ((i + 1) & 0xF)]) + chunk.ljust(7, b'\x00'), m.src)))
        ecu.pending_cf = []

  def sleep(self, seconds):
    self.now += max(seconds, 0.)


def clocked(peer):
  return patch.multiple(time, monotonic=lambda: peer.now, sleep=peer.sleep)


def accord_ecus(**overrides):
  ecus = {RADAR: Ecu(RECORDED[RADAR]), CAMERA: Ecu(RECORDED[CAMERA])}
  for addr, kw in overrides.items():
    ecus[{'radar': RADAR, 'camera': CAMERA}[addr]].__dict__.update(kw)
  return ecus


def query(peer, **kw):
  with clocked(peer):
    return get_fw_versions(peer.recv, peer.send, peer.switches.append, **kw)


def versions(fw):
  return {f.address: bytes(f.fwVersion) for f in fw}


# ---- gap 1: no CAN2 diagnostic traffic -------------------------------------------------

def test_c8_call_shape_still_sends_bus1_requests_reproducing_review_finding():
  peer = Peer(accord_ecus())
  query(peer, query_brand='honda', normal_bus_only=True)
  assert {bus for bus, _, _ in peer.sent} == {0, 1}
  assert set(peer.switches) == {False}


def test_c8_1_strict_query_uses_only_bus0_never_toggles_mux_and_identifies():
  peer = Peer(accord_ecus())
  fw = query(peer, query_brand='honda', normal_bus_only=True, request_buses=frozenset({0}))
  assert peer.sent and {bus for bus, _, _ in peer.sent} == {0}
  assert peer.switches == []
  assert versions(fw) == RECORDED
  assert all(f.bus == 0 and f.brand == 'honda' for f in fw)


# ---- gap 2: missing replies, timing boundaries, retry, hold ----------------------------

@pytest.mark.parametrize('delay,answered', ((0.02, True), (0.08, True), (0.13, False), (0.5, False)))
def test_first_frame_timing_boundary_against_production_timeout(delay, answered):
  peer = Peer(accord_ecus(camera={'delay': delay}))
  fw = query(peer, query_brand='honda', normal_bus_only=True, request_buses=frozenset({0}))
  assert (CAMERA in versions(fw)) == answered
  assert RADAR in versions(fw)


@pytest.mark.parametrize('case,expected,attempts', (
  ('healthy', IDENTIFIED, 1),
  ('camera_late_first_attempt', IDENTIFIED, 2),
  ('radar_silent', HOLD, 2),
  ('camera_silent', HOLD, 2),
  ('both_silent', HOLD, 2),
  ('camera_reply_late_collected_by_retry', IDENTIFIED, 2),
  ('camera_slower_than_both_windows', HOLD, 2),
  ('camera_unknown_version', HOLD, 2),
  ('crv6g_firmware', OTHER, 1),
))
def test_normal_bus_outcome_with_production_query(case, expected, attempts):
  crv = {address: v[0] for (_, address, _), v in FW_VERSIONS[CAR.HONDA_CRV_6G].items()}
  overrides = {
    'camera_late_first_attempt': {'camera': {'silent_attempts': 1}},
    'radar_silent': {'radar': {'silent': True}},
    'camera_silent': {'camera': {'silent': True}},
    'both_silent': {'radar': {'silent': True}, 'camera': {'silent': True}},
    'camera_reply_late_collected_by_retry': {'camera': {'delay': 0.2}},
    'camera_slower_than_both_windows': {'camera': {'delay': 0.6}},
    'camera_unknown_version': {'camera': {'fw': b'8S102-30A-A999\x00\x00'}},
    'crv6g_firmware': {'radar': {'fw': crv[RADAR]}, 'camera': {'fw': crv[CAMERA]}},
  }.get(case, {})
  peer = Peer(accord_ecus(**overrides))
  with clocked(peer):
    fw, outcome = normal_bus_fw(lambda **kw: get_fw_versions(peer.recv, peer.send, peer.switches.append, **kw), VIN_UNKNOWN)
  assert outcome == expected
  assert peer.ecus[RADAR].requests == attempts and peer.ecus[CAMERA].requests == attempts
  assert {bus for bus, _, _ in peer.sent} == {0} and peer.switches == []


# ---- end to end through get_car ---------------------------------------------------------

def window():
  return [[CanData(f['address'], bytes.fromhex(f['hex']), f['bus']) for f in batch] for batch in CAPTURE['windowBatches']]


def fingerprint_frames():
  return [CanData(f['address'], bytes.fromhex(f['hex']), f['bus']) for f in CAPTURE['fingerprintFrames']]


def get_car(peer, env=None):
  peer.background, peer.tail = window(), fingerprint_frames()
  environ = {'FINGERPRINT': '', 'SKIP_FW_QUERY': '', 'DISABLE_FW_CACHE': '', **(env or {})}
  with patch.dict(car_helpers.os.environ, environ), clocked(peer), \
       patch.object(car_helpers, 'get_present_ecus', wraps=car_helpers.get_present_ecus) as present, \
       patch.object(car_helpers, 'get_fw_versions_ordered', wraps=car_helpers.get_fw_versions_ordered) as sweep:
    ci = car_helpers.get_car(peer.recv, peer.send, peer.switches.append, False, False)
  return ci, present, sweep


def test_end_to_end_recorded_accord_identifies_with_no_mux_and_no_can2_traffic():
  peer = Peer(accord_ecus())
  ci, present, sweep = get_car(peer)
  assert ci.CP.carFingerprint == CAR.HONDA_ACCORD_11G and not ci.CP.fuzzyFingerprint
  assert ci.CP.fingerprintSource == structs.CarParams.FingerprintSource.fw
  assert versions(ci.CP.carFw) == RECORDED and ci.CP.carVin == VIN_UNKNOWN
  assert True not in peer.switches
  assert {bus for bus, _, _ in peer.sent} == {0}
  present.assert_not_called()
  sweep.assert_not_called()


@pytest.mark.parametrize('overrides', (
  {'radar': {'silent': True}},
  {'camera': {'silent': True}},
  {'radar': {'silent': True}, 'camera': {'silent': True}},
  {'camera': {'delay': 0.6}},
  {'camera': {'fw': b'8S102-30A-A999\x00\x00'}},
))
def test_end_to_end_incomplete_identification_holds_closed(overrides):
  peer = Peer(accord_ecus(**overrides))
  ci, present, sweep = get_car(peer)
  assert ci.CP.carFingerprint == 'MOCK'
  assert True not in peer.switches
  assert {bus for bus, _, _ in peer.sent} == {0}
  present.assert_not_called()
  sweep.assert_not_called()


def test_end_to_end_retry_recovers_late_camera_without_mux():
  peer = Peer(accord_ecus(camera={'silent_attempts': 1}))
  ci, _, sweep = get_car(peer)
  assert ci.CP.carFingerprint == CAR.HONDA_ACCORD_11G
  assert peer.ecus[CAMERA].requests == 2 and True not in peer.switches
  sweep.assert_not_called()


def test_end_to_end_other_honda_canfd_keeps_original_obd_sweep():
  crv = {address: v[0] for (_, address, _), v in FW_VERSIONS[CAR.HONDA_CRV_6G].items()}
  peer = Peer(accord_ecus(radar={'fw': crv[RADAR]}, camera={'fw': crv[CAMERA]}))
  ci, present, sweep = get_car(peer)
  assert True in peer.switches and peer.switches[-1] is False
  present.assert_called_once()
  sweep.assert_called_once()
  assert ci.CP.carFingerprint == CAR.HONDA_CRV_6G


def test_explicit_developer_fingerprint_still_overrides_hold():
  peer = Peer(accord_ecus(camera={'silent': True}))
  ci, _, sweep = get_car(peer, env={'FINGERPRINT': str(CAR.HONDA_ACCORD_11G)})
  assert ci.CP.fingerprintSource == structs.CarParams.FingerprintSource.fixed
  assert True not in peer.switches
  sweep.assert_not_called()


def test_without_signature_original_obd_sweep_is_unchanged():
  peer = Peer(accord_ecus())
  peer_window = [[f for f in batch if (f.src, f.address) != (1, 0x601)] for batch in window()]
  peer.background, peer.tail = peer_window, [f for f in fingerprint_frames() if (f.src, f.address) != (1, 0x601)]
  with patch.dict(car_helpers.os.environ, {'FINGERPRINT': '', 'SKIP_FW_QUERY': '', 'DISABLE_FW_CACHE': ''}), clocked(peer):
    car_helpers.get_car(peer.recv, peer.send, peer.switches.append, False, False)
  assert True in peer.switches


# ---- gap 3: passive window under a running clock -----------------------------------------

def probe(peer):
  with clocked(peer):
    # hyundai normal_bus_topology binds clock=time.monotonic at definition; give it the virtual clock
    return normal_bus_query_brand(peer.recv, lambda observe: hyundai_probe(observe, clock=lambda: peer.now),
                                  honda_probe=normal_bus_topology, clock=lambda: peer.now)


def layout_frames():
  return [CanData(a, bytes(n), b) for (b, a), n in NORMAL_BUS_LAYOUT.items()]


def test_recorded_window_matches_with_advancing_clock():
  assert probe(Peer({}, window())) == 'honda'


def test_signature_split_across_batches_inside_deadline():
  assert probe(Peer({}, [[f] for f in layout_frames()])) == 'honda'


def test_signature_completing_after_120ms_deadline_is_rejected():
  frames = layout_frames()
  late = [f for f in frames if f.src == 1]
  assert probe(Peer({}, [[f for f in frames if f.src != 1]] + [[]] * 13 + [late])) is None


@pytest.mark.parametrize('frame', ((1, 0x601, 32), (1, 0x603, 64), (0, 0x18F, 8)))
def test_malformed_dlc_rejects(frame):
  bus, address, size = frame
  rows = [f for f in layout_frames() if (f.src, f.address) != (bus, address)] + [CanData(address, bytes(size), bus)]
  assert probe(Peer({}, [rows])) is None


def test_no_can_terminates_inside_budget_without_match():
  peer = Peer({})
  assert probe(peer) is None
  assert peer.now - 100. <= 0.5


# ---- gap 4: cross-brand collisions -------------------------------------------------------

def _fingerprints(node, out):
  if isinstance(node, dict):
    frame_keys = {'address'} <= node.keys() and ({'hex', 'dat', 'data'} & node.keys()) and ({'bus', 'src'} & node.keys())
    if frame_keys:
      raw = node.get('hex') or node.get('dat') or node.get('data')
      size = len(bytes.fromhex(raw)) if isinstance(raw, str) else len(raw)
      out.setdefault('frames', {}).setdefault(node.get('bus', node.get('src')), {})[node['address']] = size
    elif node and all(str(k).isdigit() for k in node) and all(isinstance(v, dict) for v in node.values()):
      out.setdefault(len(out), {int(b): {int(a): s for a, s in v.items() if isinstance(s, int)} for b, v in node.items()})
    for v in node.values():
      _fingerprints(v, out)
  elif isinstance(node, list):
    for v in node:
      _fingerprints(v, out)
  return out


OTHER_CAPTURES = sorted(p for p in glob.glob(str(HERE.parent.parent / '*/tests/testdata/*.json')) if '/honda/' not in p)


@pytest.mark.parametrize('path', OTHER_CAPTURES, ids=lambda p: Path(p).stem)
def test_other_brand_recordings_never_match_honda_signature(path):
  found = _fingerprints(json.loads(Path(path).read_text()), {})
  assert all(not normal_bus_topology(fp) for fp in found.values())


def test_no_earlier_brand_probe_claims_recorded_accord():
  from opendbc.car.gm.discovery import normal_bus0_topology as gm
  from opendbc.car.tesla.discovery import normal_bus0_topology as tesla
  from opendbc.car.volvo.discovery import normal_bus_topology as volvo
  peer = Peer({}, window())
  with clocked(peer):
    assert normal_bus_query_brand(peer.recv, hyundai_probe, gm_probe=gm, volvo_probe=volvo, tesla_probe=tesla,
                                  honda_probe=normal_bus_topology, clock=lambda: peer.now) == 'honda'


def test_hold_refuses_a_can_only_identity_even_if_can_fingerprint_names_a_car():
  # A legacy CAN-elimination match must never stand in for missing Accord 11G firmware.
  peer = Peer(accord_ecus(camera={'silent': True}))
  with patch.object(car_helpers, 'can_fingerprint', return_value=(str(CAR.HONDA_ACCORD), {})):
    ci, _, sweep = get_car(peer)
  assert ci.CP.carFingerprint == 'MOCK'
  assert True not in peer.switches
  sweep.assert_not_called()


def test_panda_fault_policy_unchanged_for_identified_profile():
  from openpilot.cereal import log
  from openpilot.starpilot.aol.panda_faults import blocking_fault_list, blocking_fault_mask
  ci, _, _ = get_car(Peer(accord_ecus()))
  assert blocking_fault_mask(8, ci.CP)
  assert blocking_fault_list([log.PandaState.FaultType.interruptRateCan2], ci.CP)

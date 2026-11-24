import time

from opendbc.car.carlog import carlog
from opendbc.car.honda.hondacan import honda_checksum
from opendbc.car.honda.values import CAR


# Classic Bosch: PT on bus 1 and the stock ACC camera on bus 2. This selects
# diagnostic wiring only; fresh firmware and CAN fingerprinting own identity.
NORMAL_BUS_LAYOUT = {(1, 0x158): 8, (1, 0x17C): 8, (1, 0x18F): 7,
                     (1, 0x296): 4, (2, 0xE4): 5, (2, 0x400): 4}


# Nidec uses two SCM layouts and two EPS status lengths on normal bus 0.
NIDEC_BUS0_COMMON = {(0, 0x158): 8, (0, 0x17C): 8}
NIDEC_BUS0_LAYOUTS = (
  *({**NIDEC_BUS0_COMMON, (0, 0x18F): eps_length, (0, 0x1A6): 8, (0, 0x156): 6} for eps_length in (6, 7)),
  {**NIDEC_BUS0_COMMON, (0, 0x18F): 7, (0, 0x296): 4, (0, 0x326): 8},
)


def normal_bus_topology(packets, *, layout=NORMAL_BUS_LAYOUT):
  observed = set()
  for packet in packets:
    for frame in packet:
      key = (frame.src, frame.address)
      if key in layout:
        if (len(frame.dat) != layout[key] or
            honda_checksum(frame.address, None, frame.dat) != frame.dat[-1] & 0xF):
          return False
        observed.add(key)
  return observed == layout.keys()


def nidec_bus0_topology(packets):
  return any(normal_bus_topology(packets, layout=layout) for layout in NIDEC_BUS0_LAYOUTS)


# Recorded Accord 11G Hybrid normal-harness PT/camera and CAN-FD ADAS layout.
# This selects diagnostic wiring only; exact ECU firmware determines identity.
ACCORD_11G_LAYOUT = {(bus, address): size for bus in (0, 2)
                     for address, size in ((0x14A, 8), (0x18F, 7), (0x17C, 8), (0x158, 8))}
ACCORD_11G_LAYOUT.update({(1, 0x601): 48, (1, 0x603): 32})
ACCORD_11G_DEADLINE = 4.5
ACCORD_11G_SPACING = 0.5
ACCORD_11G_MAX_ATTEMPTS = 10
IDENTIFIED, OTHER, HOLD = 'identified', 'other', 'hold'


def accord_11g_topology(packets):
  observed = set()
  for packet in packets:
    for frame in packet:
      key = (frame.src, frame.address)
      if key in ACCORD_11G_LAYOUT:
        if len(frame.dat) != ACCORD_11G_LAYOUT[key]:
          return False
        observed.add(key)
  return observed == ACCORD_11G_LAYOUT.keys()


def accord_11g_seed(packets):
  # One matching bus/ID is a reason to observe more passive frames, NEVER a
  # vehicle identity or authorization to transmit diagnostics or controls.
  return any((frame.src, frame.address) in ACCORD_11G_LAYOUT
             for packet in packets for frame in packet)


def accord_11g_plausible(packets):
  # Require a repeated PT/camera address on both normal buses, plus another
  # independent source. One incidental CAN ID (or one malformed frame) cannot
  # divert an unrelated car from its usual discovery path. DLC is deliberately
  # not required here: a damaged required frame must still fail closed.
  observed = {(frame.src, frame.address) for packet in packets for frame in packet
              if (frame.src, frame.address) in ACCORD_11G_LAYOUT}
  shared = {address for address in (0x14A, 0x18F, 0x17C, 0x158)
            if (0, address) in observed and (2, address) in observed}
  pt_camera = {address for bus, address in observed if bus in (0, 2)}
  adas = any((1, address) in observed for address in (0x601, 0x603))
  return len(shared) >= 2 or (bool(shared) and len(pt_camera) >= 3) or \
         (bool(shared) and len(pt_camera) >= 2 and adas)


def accord_11g_bus0_queries():
  from opendbc.car import fw_versions
  return any(brand == 'honda' and request.bus == 0 and not request.logging
             for brand, _, request in fw_versions.REQUESTS)


def accord_11g_outcome(car_fw, vin):
  from opendbc.car.fw_versions import FW_VERSIONS, match_fw_to_car
  if any(fw.bus != 0 or fw.brand != 'honda' for fw in car_fw):
    return HOLD
  exact, candidates = match_fw_to_car(car_fw, vin, log=False)
  known = {}
  for car, ecus in FW_VERSIONS.items():
    for (_, address, sub_address), versions in ecus.items():
      for version in versions:
        known.setdefault((address, sub_address, version), set()).add(car)
  attributed = [known.get((fw.address, fw.subAddress or None, bytes(fw.fwVersion)), set()) for fw in car_fw]
  if exact and candidates == {CAR.HONDA_ACCORD_11G} and attributed and all(attributed):
    return IDENTIFIED
  if CAR.HONDA_ACCORD_11G in candidates or any(CAR.HONDA_ACCORD_11G in cars for cars in attributed):
    return HOLD
  # A foreign identity needs fully attributable evidence; an unknown Honda ECU
  # reply could be a newer Accord firmware and must not trigger the CAN2 sweep.
  if exact and len(candidates) == 1 and CAR.HONDA_ACCORD_11G not in candidates and \
     attributed and all(next(iter(candidates)) in cars for cars in attributed):
    return OTHER
  return HOLD


def accord_11g_fw(query, vin, *, start):
  car_fw, seen = [], set()
  for attempt in range(1, ACCORD_11G_MAX_ATTEMPTS + 1):
    for fw in query(query_brand='honda', normal_bus_only=True, query_bus=0):
      key = (fw.address, fw.subAddress, bytes(fw.fwVersion), fw.bus)
      if key not in seen:
        seen.add(key)
        car_fw.append(fw)
    outcome = accord_11g_outcome(car_fw, vin)
    carlog.warning({'event': 'accord_11g_bus0_attempt', 'attempt': attempt, 'outcome': outcome,
                    'fw_count': len(car_fw)})
    if outcome != HOLD or (attempt >= 2 and time.monotonic() >= start + ACCORD_11G_DEADLINE):
      return car_fw, outcome
    time.sleep(ACCORD_11G_SPACING)
  return car_fw, accord_11g_outcome(car_fw, vin)

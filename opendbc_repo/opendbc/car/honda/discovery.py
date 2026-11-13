"""Recognize recorded Accord 11G normal wiring before the generic OBD scan.

The generic discovery path muxes Panda CAN2 onto the OBD port. On the recorded
Accord 11G Hybrid (Bosch CAN-FD, stock ACC) nothing answers there: VIN and every
OBD-muxed request time out while CAN2 runs error-passive with ~35k protocol
errors in ~3 s. That burst peaks around the 16,000/s FDCAN2 IRQ watchdog and,
when it trips, latches interruptRateCan2 until the next Panda reset, which then
blocks engagement as controlsMismatch. Every recorded firmware response came
from the normal bus-0 request, so the OBD sweep adds no identity evidence.

This layout selects only diagnostic query wiring, and it is shared by the other
Honda CAN-FD platforms. Firmware is queried on bus 0 only (no CAN2 traffic), with
one retry. Then:
  IDENTIFIED  exact {HONDA_ACCORD_11G} -> normal identification.
  OTHER       firmware attributed to another car -> original OBD sweep (unchanged).
  HOLD        missing/unknown/11G-only evidence -> no mux, no CAN-only identity (MOCK).
On this car the OBD sweep never returned Honda firmware, so HOLD loses no
identity evidence and avoids the storm. CarParams construction is unchanged.
"""
from opendbc.car.honda.values import CAR

# Mirrored PT/camera Honda sources at 100 Hz plus the 11G CAN-FD ADAS bus
# frames (65-92 Hz at boot). All seen within 0.5 s of first CAN on 3/3 routes.
NORMAL_BUS_LAYOUT = {(bus, address): size for bus in (0, 2)
                     for address, size in ((0x14A, 8), (0x18F, 7), (0x17C, 8), (0x158, 8))}
NORMAL_BUS_LAYOUT.update({(1, 0x601): 48, (1, 0x603): 32})


def normal_bus_topology(fingerprint):
  return all(fingerprint.get(bus, {}).get(address) == size
             for (bus, address), size in NORMAL_BUS_LAYOUT.items())


def normal_bus_queries():
  # The essential Honda request must survive normal_bus_only filtering, and the
  # filtered set must never ask for OBD multiplexing on the CAN2 slot.
  from opendbc.car import fw_versions
  requests = [request for brand, _, request in fw_versions.REQUESTS if brand == 'honda']
  kept = [request for request in requests if not (request.bus % 4 == 1 and request.obd_multiplexing)]
  return (any(request.bus == 0 and not request.logging for request in kept) and
          not any(request.bus % 4 == 1 and request.obd_multiplexing for request in kept))


IDENTIFIED, OTHER, HOLD = 'identified', 'other', 'hold'
NORMAL_BUS_ATTEMPTS = 2


def normal_bus_outcome(car_fw, vin):
  from opendbc.car.fw_versions import FW_VERSIONS, match_fw_to_car
  exact, candidates = match_fw_to_car(car_fw, vin, log=False)
  if exact and candidates == {CAR.HONDA_ACCORD_11G}:
    return IDENTIFIED
  if candidates - {CAR.HONDA_ACCORD_11G}:
    return OTHER
  # Keyed by (address, subaddress) like production matching; live CarFw.ecu is a capnp enum.
  known = {}
  for car, ecus in FW_VERSIONS.items():
    for (_, address, sub_address), versions in ecus.items():
      for version in versions:
        known.setdefault((address, sub_address, version), set()).add(car)
  for fw in car_fw:
    cars = known.get((fw.address, fw.subAddress or None, bytes(fw.fwVersion)), set())
    if cars and CAR.HONDA_ACCORD_11G not in cars:
      return OTHER
  return HOLD


def normal_bus_fw(query, vin):
  """query(**kw) is production get_fw_versions bound to the live transport."""
  car_fw, seen, outcome = [], set(), HOLD
  for _ in range(NORMAL_BUS_ATTEMPTS):
    for fw in query(query_brand='honda', normal_bus_only=True, request_buses=frozenset({0})):
      key = (fw.address, fw.subAddress, bytes(fw.fwVersion), fw.bus)
      if key not in seen:
        seen.add(key)
        car_fw.append(fw)
    outcome = normal_bus_outcome(car_fw, vin)
    if outcome != HOLD:
      break
  return car_fw, outcome


def normal_bus_identified(car_fw, vin):
  return bool(car_fw) and normal_bus_outcome(car_fw, vin) == IDENTIFIED

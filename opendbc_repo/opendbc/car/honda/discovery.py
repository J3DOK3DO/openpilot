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
spaced retries until about 4.5 s after discovery start (the recorded replies came
about 2-4 s in, so a cold ECU is given the same time as before). Then:
  IDENTIFIED  exact {HONDA_ACCORD_11G} -> normal identification.
  OTHER       firmware attributed to another car -> original OBD sweep (unchanged).
  HOLD        missing/unknown/11G-only evidence -> no mux, no CAN-only identity (MOCK).
On this car the OBD sweep never returned Honda firmware, so HOLD loses no
identity evidence and avoids the storm. CarParams construction is unchanged.
"""
import time

from opendbc.car.carlog import carlog
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
  # The essential Honda identity request must exist on normal bus 0.
  from opendbc.car import fw_versions
  return any(request.bus == 0 and not request.logging
             for brand, _, request in fw_versions.REQUESTS if brand == 'honda')


IDENTIFIED, OTHER, HOLD = 'identified', 'other', 'hold'
NORMAL_BUS_DEADLINE = 4.5  # s after discovery start; the old sweep reached its bus-0 request ~2-4 s in
NORMAL_BUS_SPACING = 0.5   # s between bus-0 attempts
NORMAL_BUS_MAX_ATTEMPTS = 10  # safety bound only; the deadline governs


def normal_bus_outcome(car_fw, vin):
  from opendbc.car.fw_versions import FW_VERSIONS, match_fw_to_car
  exact, candidates = match_fw_to_car(car_fw, vin, log=False)
  if exact and candidates == {CAR.HONDA_ACCORD_11G}:
    return IDENTIFIED
  # Keyed by (address, subaddress) like production matching; live CarFw.ecu is a capnp enum.
  known = {}
  for car, ecus in FW_VERSIONS.items():
    for (_, address, sub_address), versions in ecus.items():
      for version in versions:
        known.setdefault((address, sub_address, version), set()).add(car)
  attributed = [known.get((fw.address, fw.subAddress or None, bytes(fw.fwVersion)), set()) for fw in car_fw]
  # Any Accord 11G evidence (including an ambiguous {11G, X} match) holds closed rather
  # than risking the storm-producing sweep. OTHER only with purely foreign evidence.
  if CAR.HONDA_ACCORD_11G in candidates or any(CAR.HONDA_ACCORD_11G in cars for cars in attributed):
    return HOLD
  if (candidates - {CAR.HONDA_ACCORD_11G}) or any(attributed):
    return OTHER
  return HOLD


def normal_bus_fw(query, vin, *, start):
  """query(**kw) is production get_fw_versions bound to the live transport.

  Bus 0 only. Retries are spaced so a slow-to-wake ECU gets the time the old sweep gave it.
  time.* is looked up at call time (not bound as a default) so the real clock is always used.
  """
  car_fw, seen, outcome, attempt = [], set(), HOLD, 0
  while True:
    attempt += 1
    sent = time.monotonic()
    for fw in query(query_brand='honda', normal_bus_only=True, request_buses=frozenset({0})):
      key = (fw.address, fw.subAddress, bytes(fw.fwVersion), fw.bus)
      if key not in seen:
        seen.add(key)
        car_fw.append(fw)
    outcome = normal_bus_outcome(car_fw, vin)
    carlog.warning({"event": "honda_normal_bus_attempt", "attempt": attempt, "t": round(sent - start, 3),
                    "outcome": outcome, "fw_count": len(car_fw)})
    if (outcome != HOLD or attempt >= NORMAL_BUS_MAX_ATTEMPTS or
        (attempt >= 2 and time.monotonic() >= start + NORMAL_BUS_DEADLINE)):
      return car_fw, outcome
    time.sleep(NORMAL_BUS_SPACING)


def normal_bus_identified(car_fw, vin):
  return bool(car_fw) and normal_bus_outcome(car_fw, vin) == IDENTIFIED

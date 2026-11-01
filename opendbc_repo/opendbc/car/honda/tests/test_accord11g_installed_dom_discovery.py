"""Accord 11G on installed Dom 5b0f81ca: the new Volvo normal-bus probe cannot claim Honda CAN-FD wiring.

Dom b64d7cf9..5b0f81ca added volvo.discovery.normal_bus_topology to car_helpers.fingerprint. It selects Volvo
diagnostic wiring only when all 16 (bus, address) pairs are present at length 8. This checks the source claim that
no Honda CAN-FD DBC message has one of those addresses; it is not a recording of the vehicle's buses.
"""
from opendbc.can.dbc import DBC as DBCFile
from opendbc.car import Bus, gen_empty_fingerprint
from opendbc.car.honda.values import CAR, DBC
from opendbc.car.volvo.discovery import NORMAL_BUS_LAYOUT, normal_bus_topology


def _accord_canfd_addresses():
  name = DBC[CAR.HONDA_ACCORD_11G][Bus.pt]
  assert name == "honda_common_canfd_generated"
  return {msg.address for msg in DBCFile(name).msgs.values()}


def test_honda_canfd_dbc_shares_no_address_with_volvo_probe():
  addresses = _accord_canfd_addresses()
  assert len(addresses) > 10
  assert not addresses & {address for _, address in NORMAL_BUS_LAYOUT}


def test_full_honda_canfd_dbc_on_every_bus_does_not_match_volvo_probe():
  fingerprint = gen_empty_fingerprint()
  for bus in (0, 1, 2):
    fingerprint[bus].update({address: 8 for address in _accord_canfd_addresses()})
  assert not normal_bus_topology(fingerprint)

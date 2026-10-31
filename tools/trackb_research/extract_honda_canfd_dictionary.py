"""Deterministically emit the current generic Honda CAN-FD DBC source closure.

This is a B1 documentation extractor, not a decoder, logger, transport, or
runtime component.  Its output describes only source records and intentionally
does not infer that any entry is present on a target vehicle.
"""
import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
DBC_ROOT = ROOT / "opendbc_repo" / "opendbc" / "dbc" / "generator" / "honda"
DBC_FILES = (
  "honda_common_canfd.dbc", "_honda_common.dbc", "_bosch_2018.dbc", "_bosch_radar_acc.dbc",
  "_lkas_hud_8byte.dbc", "_bosch_standstill.dbc", "_steering_sensors_a.dbc", "_gearbox_common.dbc",
)
MESSAGE = re.compile(r"^BO_ (\d+) ([A-Za-z0-9_]+): (\d+) ([A-Za-z0-9_]+)$")
SIGNAL = re.compile(r"^ SG_ ([A-Za-z0-9_]+)(?: [Mm]\d+)? : ([^ ]+) \(([^)]*)\) \[([^]]*)\] \"([^\"]*)\" ([A-Za-z0-9_]+)$")


def extract() -> dict[str, object]:
  messages = []
  for filename in DBC_FILES:
    path = DBC_ROOT / filename
    active = None
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
      message = MESSAGE.match(line)
      if message:
        address, name, dlc, producer = message.groups()
        numeric_address = int(address)
        active = {
          "identifier": f"0x{numeric_address:X}",
          "identifier_format": "standard_11_bit" if numeric_address <= 0x7FF else "extended_29_bit",
          "name": name,
          "dlc": int(dlc),
          "producer_source_label": producer,
          "candidate_buses": "UNVERIFIED: DBC does not encode a physical bus; current CanBus maps CAN-FD pt=offset, radar=offset+1, camera=offset+2.",
          "consumers": "UNVERIFIED: DBC does not name consumers; production use, if any, is source-specific rather than target validation.",
          "rate_assumption": "UNVERIFIED: no publication period is defined by this DBC record.",
          "signals": [],
          "counter_checksum_hypothesis": "none named in this record",
          "source": f"opendbc_repo/opendbc/dbc/generator/honda/{filename}:{line_number}",
        }
        messages.append(active)
        continue
      signal = SIGNAL.match(line)
      if signal and active is not None:
        name, layout, scale_offset, bounds, unit, receiver = signal.groups()
        active["signals"].append({"name": name, "layout": layout, "scale_offset": scale_offset,
                                  "bounds": bounds, "unit": unit, "receiver_source_label": receiver,
                                  "source": f"opendbc_repo/opendbc/dbc/generator/honda/{filename}:{line_number}"})
  for message in messages:
    fields = [field["name"] for field in message["signals"]]
    named = [field for field in fields if "COUNTER" in field or "CHECKSUM" in field]
    if named:
      message["counter_checksum_hypothesis"] = {
        "named_fields": named,
        "algorithm": "SOURCE_DERIVED_HYPOTHESIS: current honda_checksum is nibble-sum based; applicability to any CAN-FD target is unverified.",
        "algorithm_source": "opendbc_repo/opendbc/car/honda/hondacan.py:239-254",
      }
  return {
    "schema": "trackb_b1_current_generic_honda_canfd_source_dictionary/v1",
    "scope": "Current source DBC closure only. Every entry is SOURCE_DERIVED_HYPOTHESIS for the named 2025 US Accord Hybrid target.",
    "platform_source": "opendbc_repo/opendbc/car/honda/values.py:175-180,218-224",
    "bus_mapping_source": "opendbc_repo/opendbc/car/honda/hondacan.py:5-45",
    "messages": messages,
  }


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("--output", type=Path)
  args = parser.parse_args()
  payload = json.dumps(extract(), indent=2, sort_keys=True) + "\n"
  if args.output is None:
    print(payload, end="")
  else:
    args.output.write_text(payload, encoding="utf-8")


if __name__ == "__main__":
  main()

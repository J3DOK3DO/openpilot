"""Descriptive, source-aligned historical measurement summary; no tuning output."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .historical_audit import SOURCES, audit_csv, digest


def _percentiles(values: list[float]) -> dict:
  ordered = sorted(values)
  return {name: round(ordered[min(len(ordered) - 1, (len(ordered) - 1) * percentile // 100)], 4)
          for name, percentile in (("p50", 50), ("p90", 90), ("p99", 99), ("max", 100))}


def summarize(path: Path) -> dict:
  validated = audit_csv(path)
  ages = {name: [] for name in SOURCES}
  differences = {name: [] for name in ("plan_to_longcontrol", "longcontrol_to_can", "can_to_measured")}
  with path.open(newline='', encoding='utf-8') as stream:
    for row in csv.DictReader(stream):
      if row['in_qualifying_event'] != 'True':
        continue
      for name in SOURCES:
        ages[name].append(float(row[name + '_age_ms']))
      differences['plan_to_longcontrol'].append(float(row['carControl.actuators.accel']) - float(row['longitudinalPlan.aTarget']))
      differences['longcontrol_to_can'].append(float(row['ACC_CONTROL.ACCEL_COMMAND']) - float(row['carControl.actuators.accel']))
      differences['can_to_measured'].append(float(row['carState.aEgo']) - float(row['ACC_CONTROL.ACCEL_COMMAND']))
  if digest(path) != validated['sha256']:
    raise ValueError('CSV changed after validation')
  return {'label': validated['label'], 'event_id': validated['event_id'], 'csv_sha256': validated['sha256'],
          'alignment': 'decoded CAN publication with older-or-equal source holds; no response-time causality inferred',
          'qualifying_rows': validated['counts']['event_rows'],
          'source_hold_age_ms': {name: {'distribution': _percentiles(values),
                                        'over_200ms_rows': sum(value > 200 for value in values)}
                                 for name, values in ages.items()},
          'same_row_differences_mps2': {name: _percentiles(values) for name, values in differences.items()},
          'stale_threshold_ms': 200, 'future_source_rows': 0,
          'safe_event_counts': {'gas_to_brake': validated['counts']['gas_to_brake'],
                                'brake_to_gas': validated['counts']['brake_to_gas'],
                                'standstill_brake_rows': validated['counts']['standstill_brake_rows']},
          'executed_solver': False}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('csv', type=Path, nargs='+')
  args = parser.parse_args()
  print(json.dumps([summarize(path) for path in args.csv], indent=2, sort_keys=True))


if __name__ == '__main__':
  main()

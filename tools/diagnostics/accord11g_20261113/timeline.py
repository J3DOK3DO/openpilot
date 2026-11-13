#!/usr/bin/env python3
"""Read-only, one-segment-at-a-time rlog audit. Requires pycapnp and zstandard.

Output is allowlisted aggregates and sparse transition windows. No raw messages or IDs.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import tarfile

LIMIT = 16000
COUNTERS = ('totalErrorCnt', 'totalRxCnt', 'totalTxCnt', 'totalRxLostCnt', 'totalTxLostCnt', 'busOffCnt', 'canCoreResetCnt')
SAFE_EVENTS = {'controlsMismatch', 'commIssue'}
SAFE_LOGS = {'temporary_can2_fault': ('temporary fault occurred: 0x00000008',),
             'gnss_nack': ('ublox', 'nack'), 'gnss_almanac': ('almanac',),
             'ui_fps': ('fps',), 'caroutput_liveness': ('caroutput', 'not alive')}


def delta(now, previous):
  """Cumulative counters reset across Panda reboot; no wraparound inference."""
  if previous is None:
    return None, False
  return (now - previous, False) if now >= previous else (None, True)


def safe_log(raw):
  try:
    msg = str(json.loads(raw).get('msg', '')).lower()
  except (ValueError, TypeError):
    return None
  for label, words in SAFE_LOGS.items():
    if all(word in msg for word in words):
      return label
  return None


def panda_record(ps, ns, previous=None):
  c = ps.canState1
  uptime = int(ps.uptime)
  reset = previous is not None and uptime < previous['uptime']
  prior = None if reset else previous
  reset |= any(prior is not None and int(getattr(c, key)) < prior['counters'][key] for key in COUNTERS)
  if reset:
    prior = None
  changes = {key: delta(int(getattr(c, key)), None if prior is None else prior['counters'][key])[0] for key in COUNTERS}
  record = {
    'mono_ns': int(ns), 'uptime': uptime, 'irq0': int(c.irq0CallRate), 'irq1': int(c.irq1CallRate),
    'counter_deltas': changes, 'receive_error': int(c.receiveErrorCnt), 'total_error': int(c.totalErrorCnt),
    'error_warning': bool(c.errorWarning), 'error_passive': bool(c.errorPassive), 'bus_off': bool(c.busOff),
    'last_error': str(c.lastError), 'safety_model': str(ps.safetyModel), 'safety_param': int(ps.safetyParam),
    'alternative_experience': int(ps.alternativeExperience), 'controls_allowed': bool(ps.controlsAllowed),
    'active_faults': sorted(str(x) for x in ps.faults), 'fault_status': str(ps.faultStatus),
    'safety_rx_checks_invalid': bool(ps.safetyRxChecksInvalid), 'heartbeat_lost': bool(ps.heartbeatLost),
    'reset': bool(reset), 'counters': {key: int(getattr(c, key)) for key in COUNTERS},
  }
  return record


def sparse_record(row):
  return {k: v for k, v in row.items() if k not in ('counters', 'uptime')}


def summarize_rows(rows, events, logs, status):
  """Rows are nearest Panda sample in each integer monotonic second."""
  rows.sort(key=lambda x: x['mono_ns'])
  events.sort(key=lambda x: x['mono_ns'])
  first = lambda pred: next((x for x in rows if pred(x)), None)
  exceed = first(lambda x: x['irq0'] > LIMIT)
  fault = first(lambda x: 'interruptRateCan2' in x['active_faults'])
  mismatch = next((x for x in events if x['name'] == 'controlsMismatch'), None)
  transitions = []
  prev = None
  high_run = longest = 0
  high_count = 0
  totals = Counter()
  for row in rows:
    high = row['irq0'] > LIMIT
    high_run = high_run + 1 if high else 0
    longest = max(longest, high_run)
    high_count += high
    for k, v in row['counter_deltas'].items():
      if v is not None:
        totals[k] += v
    state = (tuple(row['active_faults']), row['safety_model'], row['safety_param'], row['controls_allowed'], row['safety_rx_checks_invalid'], row['heartbeat_lost'])
    if state != prev or row['reset']:
      transitions.append({'mono_ns': row['mono_ns'], 'active_faults': row['active_faults'], 'fault_status': row['fault_status'],
                          'safety_model': row['safety_model'], 'safety_param': row['safety_param'],
                          'controls_allowed': row['controls_allowed'], 'safety_rx_checks_invalid': row['safety_rx_checks_invalid'],
                          'heartbeat_lost': row['heartbeat_lost'], 'counter_reset': row['reset']})
    prev = state
  anchors = [x['mono_ns'] for x in (exceed, fault, mismatch) if x]
  anchors += [x['mono_ns'] for x in events if x['name'] == 'commIssue']
  windows = [sparse_record(x) for x in rows if any(abs(x['mono_ns'] - a) <= 3_000_000_000 for a in anchors)]
  return {'status': status, 'sample_cadence': 'nearest Panda sample per integer monotonic second',
          'panda_seconds': len(rows), 'first_rate_exceed_ns': exceed['mono_ns'] if exceed else None,
          'first_active_fault_ns': fault['mono_ns'] if fault else None,
          'first_controls_mismatch_ns': mismatch['mono_ns'] if mismatch else None,
          'peak_irq0': max((x['irq0'] for x in rows), default=None), 'peak_irq1': max((x['irq1'] for x in rows), default=None),
          'high_rate_seconds': high_count, 'longest_high_rate_run_seconds': longest,
          'observed_counter_delta_sum': dict(totals), 'transitions': transitions[:80], 'windows': windows[:100],
          'events': events[:100], 'log_class_counts': dict(Counter(logs)),
          'confidence': 'sampled: one Panda state per monotonic second; no subsecond peak inference'}


def process(archive, schema, manifest=None):
  import capnp
  import zstandard as zstd
  log = capnp.load(str(schema), imports=[str(schema.parent)])
  manifest_data = json.loads(manifest.read_text()) if manifest else {}
  checksums = manifest_data.get('copied_file_digests', {})
  output = {'schema': 2, 'limit_per_second': LIMIT, 'routes': [], 'excluded_segments': [],
            'time_basis': 'logMonoTime nanoseconds; UAE wall clock omitted because no independently validated per-route anchor'}
  route_data = defaultdict(lambda: {'rows': {}, 'events': [], 'logs': [], 'previous': None, 'segments': 0, 'first_rate': None, 'first_fault': None})
  with tarfile.open(archive, 'r:') as tf:
    members = [m for m in tf if m.isfile() and m.name.endswith('/rlog.zst')]
    members.sort(key=lambda m: (int(m.name[:8]), int(m.name.split('--')[-1].split('/')[0])))
    for m in members:
      route = int(m.name[:8])
      segment = int(m.name.split('--')[-1].split('/')[0])
      state = route_data[route]
      compressed = tf.extractfile(m).read()
      if route == 2 and segment == 62:
        digest = hashlib.sha256(compressed).hexdigest()
        expected = checksums.get(m.name, {}).get('sha256')
        output['excluded_segments'].append({'route_index': route, 'segment_index': segment, 'status': 'TRUNCATED',
                                            'sha256_matches_manifest': digest == expected if expected else None})
        continue
      try:
        data = zstd.ZstdDecompressor().decompress(compressed, max_output_size=600_000_000)
      except zstd.ZstdError as ex:
        output['excluded_segments'].append({'route_index': route, 'segment_index': segment, 'status': 'DECODE_FAILED'})
        continue
      state['segments'] += 1
      for ev in log.Event.read_multiple_bytes(data):
        ns = int(ev.logMonoTime)
        typ = ev.which()
        if typ == 'pandaStates' and ev.pandaStates:
          row = panda_record(ev.pandaStates[0], ns, state['previous'])
          state['previous'] = row
          if row['irq0'] > LIMIT and state['first_rate'] is None:
            state['first_rate'] = ns
          if 'interruptRateCan2' in row['active_faults'] and state['first_fault'] is None:
            state['first_fault'] = ns
          second = ns // 1_000_000_000
          old = state['rows'].get(second)
          if old is None or abs(ns - second * 1_000_000_000) < abs(old['mono_ns'] - second * 1_000_000_000):
            state['rows'][second] = row
        elif typ == 'onroadEvents':
          for event in ev.onroadEvents:
            name = str(event.name)
            if name in SAFE_EVENTS:
              state['events'].append({'mono_ns': ns, 'name': name})
        elif typ in ('logMessage', 'errorLogMessage'):
          label = safe_log(getattr(ev, typ))
          if label:
            state['logs'].append(label)
  for route, state in sorted(route_data.items()):
    summary = summarize_rows(list(state['rows'].values()), state['events'], state['logs'], 'COMPLETE_EXCEPT_FINAL' if route == 2 else 'COMPLETE')
    summary['first_rate_exceed_ns'] = state['first_rate']
    summary['first_active_fault_ns'] = state['first_fault']
    summary['route_index'] = route
    summary['decoded_segments'] = state['segments']
    output['routes'].append(summary)
  return output


def markdown(result):
  lines = ['# Offline FDCAN2 timeline', '', 'One nearest Panda sample per monotonic second. Times are logMonoTime ns. No verified wall-clock alignment.', '',
           '| Route | Decoded segments | First >16k | First active CAN2 fault | First controlsMismatch | High-rate seconds | Longest run |',
           '|---|---:|---:|---:|---:|---:|---:|']
  for r in result['routes']:
    lines.append(f"| {r['route_index']} | {r['decoded_segments']} | {r['first_rate_exceed_ns']} | {r['first_active_fault_ns']} | {r['first_controls_mismatch_ns']} | {r['high_rate_seconds']} | {r['longest_high_rate_run_seconds']} |")
  lines += ['', 'Fault status `faultTemp` is sticky; the active `faults` list controls fault presence. Counter deltas exclude resets.',
            'The final route 2 segment is marked TRUNCATED; its digest is compared with the source manifest.',
            'A sampled IRQ rate over 16,000/s supports the watchdog mechanism, but cannot establish whether RX traffic or error interrupts caused it.']
  return '\n'.join(lines) + '\n'


def main():
  p = argparse.ArgumentParser()
  p.add_argument('--archive', type=Path, required=True)
  p.add_argument('--schema', type=Path, required=True)
  p.add_argument('--manifest', type=Path)
  p.add_argument('--json-out', type=Path, required=True)
  p.add_argument('--md-out', type=Path, required=True)
  a = p.parse_args()
  result = process(a.archive, a.schema, a.manifest)
  a.json_out.write_text(json.dumps(result, indent=2) + '\n')
  a.md_out.write_text(markdown(result))
  print(f"decoded {sum(r['decoded_segments'] for r in result['routes'])} segments; excluded {len(result['excluded_segments'])}")

if __name__ == '__main__':
  main()

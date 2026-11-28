"""Bounded, read-only census of four pinned historical compressed segments.

The optional summary is independently produced and contains counts and clocks only.
This module never imports a vehicle schema or reads decompressed messages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

EXPECTED = {
  5: '495800114585f060007efa56472622125182b064834528511fb5576b0c95b435',
  6: '1646f143bc0a90bac360c0db329e302b022808a5f4c7ff70aa6f5f92b095355a',
  105: '1fba3eb1e1b37e217ab387b430073ad3a62672763e0d139325372ffc4a28135f',
  106: 'd4d8c4c368557e920c52f1484f307aa2859876f4e168d4396df264c40a5a0202',
}


def segment_path(root: Path, segment: int) -> Path:
  """Locate a single segment by numeric suffix without exposing its route stem."""
  if type(segment) is not int or segment < 0:
    raise ValueError('invalid segment')
  matches = sorted(root.glob(f'*--{segment}/rlog.zst'))
  if len(matches) != 1:
    raise ValueError(f'segment {segment}: missing or ambiguous input')
  return matches[0]


def discover_root() -> Path:
  supplied = os.environ.get('C20_R9_RAW_ROOT')
  if supplied:
    return Path(supplied)
  base = Path('/home/jdkd/AI_Workspace/projects')
  for candidate in sorted(base.glob('*/*/original_rlogs/data/media/0/realdata')):
    try:
      if all(segment_path(candidate, number).is_file() for number in EXPECTED):
        return candidate
    except ValueError:
      continue
  return Path('__R9_HISTORICAL_INPUT_UNAVAILABLE__')


ROOT = discover_root()
SERVICES = ('modelV2', 'carState', 'radarState', 'controlsState', 'selfdriveState',
            'carControl', 'carParams', 'longitudinalPlan', 'sendcan')
SUMMARY = Path(__file__).parent / 'fixtures/r9_decoded_summary.json'
SCHEMA_SHA256 = {
  'log_capnp_sha256': 'c1f016626dea66d3de42beaf1b31418da6071494ccde7bba71baaa6787b3921a',
  'car_capnp_sha256': 'd86c2a9c52eb8670ff99b31346ec0644f16ffee6194aba880ec7ec7204d78f8a',
  'custom_capnp_sha256': '428a40e32724188d2fedfc4db107a220e5f14ed0bc6a161297541740ee151c1a',
}


def _sha256(path: Path) -> str:
  h = hashlib.sha256()
  with path.open('rb') as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b''):
      h.update(block)
  return h.hexdigest()


def census(root: Path = ROOT, expected: dict[int, str] = EXPECTED,
           summary: dict | None = None, decoder: str = 'zstd') -> dict:
  """Verify exact byte identity and complete zstd frames before accepting counts."""
  if decoder != 'zstd':
    raise ValueError('unsupported integrity decoder')
  if summary is not None and (summary.get('method') != 'offline_capnp_historical_schema'
                              or set(summary.get('segments', {})) != {str(x) for x in expected}
                              or any(summary.get('schema_lineage', {}).get(key) != value for key, value in SCHEMA_SHA256.items())):
    raise ValueError('unsupported or incomplete reader summary')
  reports = []
  for segment in sorted(expected):
    path = segment_path(root, segment)
    if path.is_symlink() or not path.is_file():
      raise ValueError(f'segment {segment}: missing or nonregular input')
    before = path.stat()
    actual = _sha256(path)
    if actual != expected[segment]:
      raise ValueError(f'segment {segment}: SHA-256 mismatch')
    try:
      check = subprocess.run(['zstd', '-q', '-t', '--', str(path)], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
      raise ValueError(f'segment {segment}: zstd integrity unavailable') from exc
    if check.returncode:
      raise ValueError(f'segment {segment}: zstd frame integrity failure')
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or _sha256(path) != actual:
      raise ValueError(f'segment {segment}: input changed during verification')
    item = {'segment': segment, 'bytes': before.st_size, 'sha256': actual,
            'zstd_frame': 'PASS', 'event_parse': 'UNPARSED',
            'services': {name: {'state': 'UNPARSED', 'count': None} for name in SERVICES}}
    if summary is not None:
      decoded = summary['segments'][str(segment)]
      counts = decoded.get('counts', {})
      first, last = decoded.get('first_t_ns'), decoded.get('last_t_ns')
      if (decoded.get('raw_sha256') != actual or set(counts) != set(SERVICES)
          or any(type(v) is not int or v < 0 for v in counts.values())
          or type(first) is not int or type(last) is not int or not 0 < first <= last
          or type(decoded.get('bad_events')) is not int or decoded['bad_events'] != 0):
        raise ValueError(f'segment {segment}: invalid or unbound reader summary')
      item.update(event_parse='DECODED_HISTORICAL_SCHEMA', first_t_ns=first, last_t_ns=last,
                  bad_events=0, services={name: {'state': 'DECODED_HISTORICAL_SCHEMA', 'count': counts[name]} for name in SERVICES})
    reports.append(item)
  return {'status': 'PASS', 'current_vehicle_authenticated_routes': 0,
          'schema_lineage': summary.get('schema_lineage') if summary else None,
          'segments': reports}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--summary', type=Path, help='independent sanitized reader summary')
  args = parser.parse_args()
  summary = json.loads(args.summary.read_text()) if args.summary else None
  print(json.dumps(census(summary=summary), indent=2, sort_keys=True))


if __name__ == '__main__':
  main()

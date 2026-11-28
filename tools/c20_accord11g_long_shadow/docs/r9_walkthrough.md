# R9 bounded offline reproduction

Run from the repository root. These commands read only four pinned historical compressed files and three existing derived CSVs. They do not install packages, copy raw logs, publish messages or connect to a vehicle. Set `PYTHONDONTWRITEBYTECODE=1` to keep the research tree free of bytecode.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.rawlog_census
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.rawlog_census --summary tools/c20_accord11g_long_shadow/fixtures/r9_decoded_summary.json
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.native_preflight --repo .
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.release_gate --repo .
```

The first census reports `UNPARSED` service counts after SHA-256 and zstd frame checks. The second validates a separately collected sanitized decoder summary against the same raw digests and pinned historical schema hashes. Neither command authenticates the recording source. To regenerate the independent service counts from local cached packages, use the following read-only probe. It prints only service counts, monotonic clock extrema and parser exception counts; it never prints message payloads. Memory use is bounded by one decompressed segment at a time (largest observed: 65,243,176 bytes). The schema's checkout is a historical source input, not C19.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/jdkd/.cache/uv/archive-v0/i7wuLLr-rrR7DuZ2:/home/jdkd/.cache/uv/archive-v0/my2o4q-92WVATYjh python3 - <<'PY'
import capnp
import collections
import json
from pathlib import Path
import zstandard as zstd
from tools.c20_accord11g_long_shadow.rawlog_census import ROOT, segment_path

schema = capnp.load('/home/jdkd/src/phase1_sources/starpilot-openpilot/cereal/log.capnp')
services = ('modelV2', 'carState', 'radarState', 'controlsState', 'selfdriveState', 'carControl', 'carParams', 'longitudinalPlan', 'sendcan')
for segment in (5, 6, 105, 106):
  path = segment_path(ROOT, segment)
  with path.open('rb') as stream:
    data = zstd.ZstdDecompressor().stream_reader(stream).read()
  counts = collections.Counter()
  first = last = None
  bad = 0
  for event in schema.Event.read_multiple_bytes(data):
    try:
      name, stamp = event.which(), event.logMonoTime
    except capnp.KjException:
      bad += 1
      continue
    if name in services:
      counts[name] += 1
    first = stamp if first is None else min(first, stamp)
    last = stamp if last is None else max(last, stamp)
  print(json.dumps({'segment': segment, 'counts': {name: counts[name] for name in services},
                    'first_t_ns': first, 'last_t_ns': last, 'bad_events': bad}, sort_keys=True))
PY
```

Check the three derived event windows and the same-cycle gap:

```sh
R9_HISTORY=/path/to/privately/held/derived/windows
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.historical_attribution "$R9_HISTORY/LS001_FULL_RATE.csv" "$R9_HISTORY/LS003_FULL_RATE.csv" "$R9_HISTORY/LS004_FULL_RATE.csv"
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.c20_accord11g_long_shadow.native_gap "$R9_HISTORY/LS001_FULL_RATE.csv"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/c20_accord11g_long_shadow/tests -q
git diff --check
git rev-parse a32dcc0a6e62a4e2a15d9ac4425424e598313c98
git status --short
```

After an exact research-only commit and clean tree, the host operator can use the existing `bundle.py` release recipe to produce the deterministic archive. Do not include raw logs or temporary decoder output.

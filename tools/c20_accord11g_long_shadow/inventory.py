"""Bounded, read-only inventory of local route artifacts. Never authenticates a car."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from .admission import load_json_bytes

SUFFIXES = ("rlog", "rlog.zst", "rlog.bz2", "qlog", "qlog.zst", "qlog.bz2", "trace.json")
METADATA = ("manifest.json", "metadata.json", "carparams.json", "firmware.json")
MAX_FILES = 2000
MAX_DEPTH = 9
MAX_BYTES = 256 * 1024 * 1024


def sha256_file(path: Path) -> str:
  digest = hashlib.sha256()
  fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
  with os.fdopen(fd, "rb") as stream:
    before = os.fstat(stream.fileno())
    while chunk := stream.read(1024 * 1024):
      digest.update(chunk)
    after = os.fstat(stream.fileno())
  if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
    raise ValueError("artifact changed while hashing")
  return digest.hexdigest()


def inventory(roots: list[Path], *, max_files: int = MAX_FILES) -> dict:
  if not 1 <= max_files <= MAX_FILES:
    raise ValueError("max_files outside bound")
  entries: list[dict] = []
  examined = 0
  truncated = False
  for root in roots:
    if root.is_symlink() or not root.is_dir():
      entries.append({"path": str(root), "kind": "ROOT_REJECTED"})
      continue
    for base, dirs, files in os.walk(root, followlinks=False):
      depth = len(Path(base).relative_to(root).parts)
      dirs[:] = sorted(d for d in dirs if not (Path(base) / d).is_symlink()) if depth < MAX_DEPTH else []
      for name in sorted(files):
        examined += 1
        if examined > max_files:
          truncated = True
          break
        path = Path(base) / name
        lower = name.lower()
        kind = "RAW_LOG" if lower in SUFFIXES or any(lower.endswith("." + x) for x in SUFFIXES) else "METADATA" if lower in METADATA else None
        if kind is None:
          continue
        if path.is_symlink() or not path.is_file():
          entries.append({"path": str(path), "kind": "REJECTED_SYMLINK_OR_NONFILE"})
          continue
        size = path.stat().st_size
        if size > MAX_BYTES:
          entries.append({"path": str(path), "kind": "OVERSIZE", "bytes": size})
          continue
        try:
          digest = sha256_file(path)
        except (OSError, ValueError):
          entries.append({"path": str(path), "kind": "UNSTABLE_OR_UNREADABLE", "identity": "UNVERIFIED"})
          continue
        item = {"path": str(path), "kind": kind, "bytes": size, "sha256": digest, "identity": "UNVERIFIED"}
        if kind == "METADATA":
          if size > 2 * 1024 * 1024:
            item["parse"] = "METADATA_TOO_LARGE"
          else:
            try:
              data = load_json_bytes(path.read_bytes())
              item["fields_present"] = sorted(k for k in ("route_id", "carFingerprint", "vehicle", "ecu_firmware", "software_sha", "dbc_sha") if isinstance(data, dict) and k in data)
            except (ValueError, UnicodeError):
              item["parse"] = "INVALID_JSON"
        entries.append(item)
      if truncated:
        break
    if truncated:
      break
  return {"schema": 1, "examined_files": examined, "truncated": truncated, "entries": entries,
          "authentic_verified_routes": 0,
          "note": "Raw bytes and matching filenames do not establish vehicle, firmware, software or DBC provenance."}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("roots", nargs="+", type=Path)
  parser.add_argument("--max-files", type=int, default=MAX_FILES)
  args = parser.parse_args()
  print(json.dumps(inventory(args.roots, max_files=args.max_files), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

"""Bounded, read-only inventory of local route artifacts. Never authenticates a car."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

from .admission import load_json_bytes

SUFFIXES = ("rlog", "rlog.zst", "rlog.bz2", "qlog", "qlog.zst", "qlog.bz2", "trace.json")
METADATA = ("manifest.json", "metadata.json", "carparams.json", "firmware.json")
MAX_FILES = 2000
MAX_DIRS = 2000
MAX_DEPTH = 9
MAX_BYTES = 256 * 1024 * 1024
MAX_METADATA_BYTES = 2 * 1024 * 1024


class ArtifactTooLarge(ValueError):
  def __init__(self, size: int):
    self.size = size


def _read_snapshot(path: Path, *, metadata: bool) -> tuple[str, int, bytes | None]:
  """Hash one opened regular file and retain metadata bytes from that same read."""
  digest = hashlib.sha256()
  fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
  with os.fdopen(fd, "rb") as stream:
    before = os.fstat(stream.fileno())
    if not stat.S_ISREG(before.st_mode):
      raise ValueError("artifact is not a regular file")
    if before.st_size > MAX_BYTES:
      raise ArtifactTooLarge(before.st_size)
    chunks = [] if metadata else None
    total = 0
    while chunk := stream.read(1024 * 1024):
      total += len(chunk)
      if total > MAX_BYTES:
        raise ArtifactTooLarge(total)
      digest.update(chunk)
      if chunks is not None:
        if total <= MAX_METADATA_BYTES:
          chunks.append(chunk)
        else:
          chunks = None
    after = os.fstat(stream.fileno())
    current = path.stat(follow_symlinks=False)
  identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
  if total != before.st_size or identity(before) != identity(after) or identity(before) != identity(current) or not stat.S_ISREG(current.st_mode):
    raise ValueError("artifact changed while hashing")
  return digest.hexdigest(), total, b"".join(chunks) if chunks is not None else None


def inventory(roots: list[Path], *, max_files: int = MAX_FILES, max_dirs: int = MAX_DIRS) -> dict:
  if not 1 <= max_files <= MAX_FILES:
    raise ValueError("max_files outside bound")
  if not 1 <= max_dirs <= MAX_DIRS:
    raise ValueError("max_dirs outside bound")
  entries: list[dict] = []
  examined_files = 0
  examined_dirs = 0
  truncation_reason = None
  for root in roots:
    if root.is_symlink() or not root.is_dir():
      entries.append({"path": str(root), "kind": "ROOT_REJECTED"})
      continue
    pending = [(root, 0)]
    while pending:
      base, depth = pending.pop()
      if examined_dirs >= max_dirs:
        truncation_reason = "MAX_DIRS"
        break
      examined_dirs += 1
      try:
        fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
          with os.scandir(fd) as scan:
            children = []
            candidate_dirs = 0
            candidate_files = 0
            for child in scan:
              if child.is_dir(follow_symlinks=False):
                if depth < MAX_DEPTH:
                  candidate_dirs += 1
                  children.append((child.name, True))
                else:
                  truncation_reason = "MAX_DEPTH"
              else:
                candidate_files += 1
                children.append((child.name, False))
              # Bound enumeration and sorting before materializing a broad directory.
              if candidate_dirs > max_dirs - examined_dirs - len(pending):
                truncation_reason = "MAX_DIRS"
                break
              if candidate_files > max_files - examined_files:
                truncation_reason = "MAX_FILES"
                break
        finally:
          os.close(fd)
      except OSError:
        entries.append({"path": str(base), "kind": "UNSTABLE_OR_UNREADABLE", "identity": "UNVERIFIED"})
        continue
      directories = []
      for name, is_dir in sorted(children):
        path = base / name
        if is_dir:
          if examined_dirs + len(pending) + len(directories) >= max_dirs:
            truncation_reason = "MAX_DIRS"
            break
          directories.append((path, depth + 1))
          continue
        if examined_files >= max_files:
          truncation_reason = "MAX_FILES"
          break
        examined_files += 1
        lower = name.lower()
        kind = "RAW_LOG" if lower in SUFFIXES or any(lower.endswith("." + x) for x in SUFFIXES) else "METADATA" if lower in METADATA else None
        if kind is None:
          continue
        if path.is_symlink() or not path.is_file():
          entries.append({"path": str(path), "kind": "REJECTED_SYMLINK_OR_NONFILE"})
          continue
        try:
          digest, size, metadata_bytes = _read_snapshot(path, metadata=kind == "METADATA")
        except ArtifactTooLarge as exc:
          entries.append({"path": str(path), "kind": "OVERSIZE", "bytes": exc.size})
          continue
        except (OSError, ValueError):
          entries.append({"path": str(path), "kind": "UNSTABLE_OR_UNREADABLE", "identity": "UNVERIFIED"})
          continue
        item = {"path": str(path), "kind": kind, "bytes": size, "sha256": digest, "identity": "UNVERIFIED"}
        if kind == "METADATA":
          if metadata_bytes is None:
            item["parse"] = "METADATA_TOO_LARGE"
          else:
            try:
              data = load_json_bytes(metadata_bytes)
              item["fields_present"] = sorted(k for k in ("route_id", "carFingerprint", "vehicle", "ecu_firmware", "software_sha", "dbc_sha") if isinstance(data, dict) and k in data)
            except (ValueError, UnicodeError):
              item["parse"] = "INVALID_JSON"
        entries.append(item)
      pending.extend(reversed(directories))
      if truncation_reason:
        break
    if truncation_reason:
      break
  return {"schema": 1, "examined_files": examined_files, "examined_dirs": examined_dirs,
          "truncated": truncation_reason is not None, "truncation_reason": truncation_reason, "entries": entries,
          "authentic_verified_routes": 0,
          "note": "Raw bytes and matching filenames do not establish vehicle, firmware, software or DBC provenance."}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("roots", nargs="+", type=Path)
  parser.add_argument("--max-files", type=int, default=MAX_FILES, help="maximum file entries examined (1-2000)")
  parser.add_argument("--max-dirs", type=int, default=MAX_DIRS, help="maximum directories visited (1-2000)")
  args = parser.parse_args()
  print(json.dumps(inventory(args.roots, max_files=args.max_files, max_dirs=args.max_dirs), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

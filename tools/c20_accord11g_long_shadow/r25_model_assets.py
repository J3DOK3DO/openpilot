"""Verify the exact shipped C19/C20 chunked model files without materializing them.

This is an offline integrity preflight, NOT evidence of a QCOM build, inference,
installer, vehicle compatibility, or model safety qualification.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openpilot.common.file_chunker import CHUNK_SIZE
from openpilot.starpilot.models.catalog import DEFAULT_SMALL_SHA256, DEFAULT_SMALL_SIZE

MODELS = Path("openpilot/selfdrive/modeld/models")
BUNDLED = (
  ("cheddar_driving_tinygrad.pkl", 2, DEFAULT_SMALL_SHA256, DEFAULT_SMALL_SIZE),
  ("dmonitoring_model_tinygrad.pkl", 1, None, None),
)


def components(base: Path, count: int) -> tuple[Path, ...]:
  return (
    Path(str(base) + ".chunkmanifest"),
    Path(str(base) + ".chunksha256"),
    *(Path(str(base) + f".chunk{i:02d}of{count:02d}") for i in range(1, count + 1)),
  )


MODEL_COMPONENTS = tuple(component for name, count, _, _ in BUNDLED
                         for component in components(MODELS / name, count))


def sha_file(path: Path) -> tuple[int, str]:
  digest = hashlib.sha256()
  length = 0
  with path.open("rb") as stream:
    while chunk := stream.read(1024 * 1024):
      length += len(chunk)
      digest.update(chunk)
  return length, digest.hexdigest()


def verify_one(repo: Path, name: str, count: int, pinned_sha: str | None, pinned_size: int | None) -> list[str]:
  base = MODELS / name
  paths = components(base, count)
  found = [repo / path for path in paths]
  if any(path.is_symlink() or not path.is_file() for path in found):
    return [f"chunked product model components missing or symlinked: {name}"]
  try:
    manifest, sidecar, *parts = found
    if manifest.read_text().strip() != str(count):
      return [f"model part count invalid: {name}"]
    meta = json.loads(sidecar.read_text())
    if (type(meta) is not dict or set(meta) != {"bytes", "sha256", "parts"} or
        type(meta["bytes"]) is not int or meta["bytes"] <= 0 or
        type(meta["sha256"]) is not str or len(meta["sha256"]) != 64 or
        type(meta["parts"]) is not list or len(meta["parts"]) != count):
      return [f"model integrity metadata invalid: {name}"]
    if ((pinned_sha is not None and meta["sha256"] != pinned_sha) or
        (pinned_size is not None and meta["bytes"] != pinned_size)):
      return [f"model pinned identity mismatch: {name}"]
    digest = hashlib.sha256()
    total = 0
    for idx, part in enumerate(parts):
      part_digest = hashlib.sha256()
      part_size = 0
      with part.open("rb") as stream:
        while block := stream.read(1024 * 1024):
          digest.update(block)
          part_digest.update(block)
          part_size += len(block)
      if not 0 < part_size <= CHUNK_SIZE or (idx + 1 < count and part_size != CHUNK_SIZE):
        return [f"model part size invalid: {name}"]
      if meta["parts"][idx] != {"bytes": part_size, "sha256": part_digest.hexdigest()}:
        return [f"model part digest mismatch: {name}"]
      total += part_size
    if (digest.hexdigest() != meta["sha256"] or total != meta["bytes"] or
        (pinned_sha is not None and digest.hexdigest() != pinned_sha) or
        (pinned_size is not None and total != pinned_size)):
      return [f"model content digest mismatch: {name}"]
    return []
  except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError):
    return [f"model chunk validation failed: {name}"]


def verify_models(repo: Path) -> list[str]:
  findings = []
  for name, count, sha, size in BUNDLED:
    findings.extend(verify_one(repo, name, count, sha, size))
  return findings

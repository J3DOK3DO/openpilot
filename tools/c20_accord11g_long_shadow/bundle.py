"""Build and verify a deterministic, commit-pinned offline research archive."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

from .admission import load_json_bytes

PREFIX = "tools/c20_accord11g_long_shadow/"
MAX_BYTES = 5_000_000
MAX_MEMBERS = 1024
FORBIDDEN_SUFFIXES = (".pyc", ".log", ".zst", ".csv", ".rlog", ".qlog", ".mp4", ".hevc", ".mkv",
                      ".so", ".o", ".a", ".elf", ".bin", ".dll", ".dylib", ".exe")
PRIVATE_ROUTE_STEM = re.compile(rb"\b[0-9a-f]{8}--[0-9a-f]{10}\b")
VIN_VALUE = re.compile(rb"\b[A-HJ-NPR-Z0-9]{17}\b")
GPS_VALUE = re.compile(rb'''["'](?:gps|latitude|longitude|lat|lon)["']\s*:\s*(?:[-+]?\d|["'][-+]?\d)''', re.I)


def _check_public_entry(path: str, content: bytes) -> None:
  if (path.endswith(FORBIDDEN_SUFFIXES) or PRIVATE_ROUTE_STEM.search(path.encode()) or
      PRIVATE_ROUTE_STEM.search(content) or VIN_VALUE.search(content) or GPS_VALUE.search(content)):
    raise ValueError("raw data or private route detail in research archive")


def _git(repo: Path, *args: str) -> bytes:
  return subprocess.check_output(["git", "-C", str(repo), *args])


def _json(value: dict) -> bytes:
  return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def build(repo: Path, output: Path) -> dict:
  if _git(repo, "status", "--porcelain", "--untracked-files=all").strip():
    raise ValueError("repository must be clean; archive uses committed sources only")
  revision = _git(repo, "rev-parse", "HEAD").decode().strip()
  branch = _git(repo, "symbolic-ref", "--short", "HEAD").decode().strip()
  paths = sorted(p.decode() for p in _git(repo, "ls-tree", "-r", "--name-only", "HEAD", PREFIX).splitlines())
  if not paths or any(not p.startswith(PREFIX) or "__pycache__" in p or p.endswith(FORBIDDEN_SUFFIXES) for p in paths):
    raise ValueError("invalid committed research contents")
  if len(paths) + 1 > MAX_MEMBERS:
    raise ValueError("archive member limit exceeded")
  entries = {}
  total = 0
  for path in paths:
    if _git(repo, "ls-tree", "HEAD", path).split(None, 1)[0] != b"100644" and _git(repo, "ls-tree", "HEAD", path).split(None, 1)[0] != b"100755":
      raise ValueError(f"nonregular tracked entry: {path}")
    content = _git(repo, "show", f"HEAD:{path}")
    _check_public_entry(path, content)
    total += len(content)
    if total > MAX_BYTES:
      raise ValueError("uncompressed archive contents exceed 5 MB")
    entries[path] = content
  manifest = {"schema": 1, "revision": revision, "branch": branch,
              "scope": PREFIX, "active_alpha_long": "NO_GO", "road_deployment": "NO_GO",
              "files": {path: {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
                        for path, content in entries.items()}}
  entries["RESEARCH_MANIFEST.json"] = _json(manifest)
  if len(entries) > MAX_MEMBERS or total + len(entries["RESEARCH_MANIFEST.json"]) > MAX_BYTES:
    raise ValueError("uncompressed archive contents exceed 5 MB or member limit")
  output.parent.mkdir(parents=True, exist_ok=True)
  with output.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as zipped:
      with tarfile.open(fileobj=zipped, mode="w") as archive:
        for path, content in sorted(entries.items()):
          info = tarfile.TarInfo(path)
          info.size = len(content)
          info.mtime = 0
          info.mode = 0o644
          info.uid = info.gid = 0
          info.uname = info.gname = ""
          archive.addfile(info, io.BytesIO(content))
  if output.stat().st_size > MAX_BYTES:
    output.unlink()
    raise ValueError("compressed archive exceeds 5 MB")
  verify(output)
  record = {"archive": output.name, "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "revision": revision,
            "branch": branch, "files": len(paths)}
  output.with_suffix(output.suffix + ".sha256.json").write_bytes(_json(record))
  return record


def verify(path: Path) -> dict:
  with tarfile.open(path, "r:gz") as archive:
    members = {}
    total = 0
    for member in archive:
      if len(members) >= MAX_MEMBERS or member.name in members:
        raise ValueError("duplicate entry or member limit exceeded")
      parts = Path(member.name).parts
      if (not member.isfile() or member.mtime != 0 or member.size < 0
          or member.size > MAX_BYTES or member.name.startswith("/")
          or ".." in parts or member.name == "."
          or (member.name != "RESEARCH_MANIFEST.json" and not member.name.startswith(PREFIX))):
        raise ValueError("invalid archive entry")
      total += member.size
      if total > MAX_BYTES:
        raise ValueError("uncompressed archive contents exceed 5 MB")
      members[member.name] = member
    names = set(members)
    if "RESEARCH_MANIFEST.json" not in names:
      raise ValueError("duplicate or missing manifest")
    manifest_raw = archive.extractfile(members["RESEARCH_MANIFEST.json"]).read(MAX_BYTES + 1)
    _check_public_entry("RESEARCH_MANIFEST.json", manifest_raw)
    manifest = load_json_bytes(manifest_raw)
    required = {"schema", "revision", "branch", "scope", "active_alpha_long", "road_deployment", "files"}
    if (type(manifest) is not dict or set(manifest) != required or manifest["schema"] != 1
        or type(manifest["revision"]) is not str or not re.fullmatch(r"[0-9a-f]{40}", manifest["revision"])
        or type(manifest["branch"]) is not str or not manifest["branch"] or len(manifest["branch"]) > 128
        or manifest["scope"] != PREFIX or manifest["active_alpha_long"] != "NO_GO"
        or manifest["road_deployment"] != "NO_GO" or type(manifest["files"]) is not dict
        or not manifest["files"]):
      raise ValueError("manifest schema invalid")
    _check_public_entry("RESEARCH_MANIFEST.json", _json(manifest))
    for name, expected in manifest["files"].items():
      if (type(name) is not str or not name.startswith(PREFIX) or type(expected) is not dict
          or set(expected) != {"bytes", "sha256"} or type(expected["bytes"]) is not int
          or not 0 <= expected["bytes"] <= MAX_BYTES or type(expected["sha256"]) is not str
          or not re.fullmatch(r"[0-9a-f]{64}", expected["sha256"])):
        raise ValueError("manifest file schema invalid")
    if names != set(manifest["files"]) | {"RESEARCH_MANIFEST.json"}:
      raise ValueError("manifest does not cover archive")
    for name, expected in manifest["files"].items():
      data = archive.extractfile(members[name]).read(MAX_BYTES + 1)
      _check_public_entry(name, data)
      if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise ValueError(f"digest mismatch: {name}")
  return manifest


def verify_release(path: Path) -> dict:
  """Check both archive members and the adjacent whole-archive digest record."""
  manifest = verify(path)
  record = json.loads(path.with_suffix(path.suffix + ".sha256.json").read_text())
  if (record.get("archive") != path.name or record.get("revision") != manifest["revision"]
      or record.get("branch") != manifest["branch"] or record.get("files") != len(manifest["files"])
      or record.get("bytes") != path.stat().st_size
      or record.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest()):
    raise ValueError("archive digest record mismatch")
  return record


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo", type=Path, default=Path.cwd())
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("--output", type=Path)
  group.add_argument("--verify", type=Path)
  args = parser.parse_args()
  print(json.dumps(verify_release(args.verify) if args.verify else build(args.repo, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

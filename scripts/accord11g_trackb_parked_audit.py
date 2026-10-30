#!/usr/bin/env python3
"""Read-only source/host audit for the Accord 11G Track B parked branch."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

AGNOS_ROOT = Path("/AGNOS")
PROC_ROOT = Path("/proc")
TRUSTED_REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
  "opendbc_repo/opendbc/car/honda/interface.py",
  "opendbc_repo/opendbc/car/honda/values.py",
  "opendbc_repo/opendbc/car/honda/accord_mvl_stock.py",
  "opendbc_repo/opendbc/safety/modes/honda.h",
  "opendbc_repo/opendbc/safety/safety.h",
  "scripts/accord11g_trackb_parked_audit.py",
)
SOURCE_DIRECTORIES = ("openpilot", "opendbc_repo", "panda")
PROCESS_NAMES = ("manager", "pandad", "controlsd")


def _unknown(reason: str) -> dict[str, str]:
  return {"status": "unknown", "reason": reason}


def _is_sha(value: str | None) -> bool:
  return value is not None and len(value) == 40 and all(char in "0123456789abcdef" for char in value)


def _path_has_symlink(path: Path) -> bool:
  if not path.is_absolute():
    return True
  current = Path(path.anchor)
  for component in path.parts[1:]:
    current /= component
    try:
      if stat.S_ISLNK(os.lstat(current).st_mode):
        return True
    except OSError:
      return True
  return False


def _open_beneath(root: Path, relative: str, flags: int) -> int:
  """Open a whitelisted relative path without following a symlink component."""
  parts = Path(relative).parts
  if not parts or any(part in ("", ".", "..") for part in parts):
    raise OSError("invalid relative path")
  directory_flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
  root_fd = os.open(root, directory_flags)
  fd = root_fd
  try:
    for part in parts[:-1]:
      next_fd = os.open(part, directory_flags, dir_fd=fd)
      os.close(fd)
      fd = next_fd
    return os.open(parts[-1], flags | getattr(os, "O_NOFOLLOW", 0), dir_fd=fd)
  finally:
    os.close(fd)


def _sha256(root: Path, relative: str) -> dict[str, str]:
  try:
    fd = _open_beneath(root, relative, os.O_RDONLY)
  except FileNotFoundError:
    return {"status": "missing"}
  except OSError:
    return _unknown("unreadable_or_unsafe")
  try:
    with os.fdopen(fd, "rb", closefd=True) as source:
      digest = hashlib.file_digest(source, "sha256").hexdigest()
  except OSError:
    return _unknown("unreadable_or_unsafe")
  return {"status": "present", "sha256": digest}


def _safe_directory(root: Path, relative: str) -> bool:
  try:
    fd = _open_beneath(root, relative, os.O_RDONLY | os.O_DIRECTORY)
  except OSError:
    return False
  os.close(fd)
  return True


def _git_sha(root: Path) -> dict[str, str]:
  """The only subprocess is a config-free, read-only git rev-parse."""
  git_env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
             "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
  try:
    result = subprocess.run(["git", "-C", os.fspath(root), "rev-parse", "HEAD"], check=False,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=2, env=git_env)
  except (OSError, subprocess.SubprocessError):
    return _unknown("git_unavailable")
  sha = result.stdout.strip()
  if result.returncode == 0 and _is_sha(sha):
    return {"status": "present", "sha": sha}
  return _unknown("git_sha_unavailable")


def _git_clean(root: Path) -> bool:
  """Check tracked source cleanliness without returning filenames or writing an index."""
  env = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
         "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
  try:
    result = subprocess.run(["git", "-C", os.fspath(root), "status", "--porcelain", "--untracked-files=no"],
                            check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                            timeout=3, env=env)
  except (OSError, subprocess.SubprocessError):
    return False
  return result.returncode == 0 and not result.stdout.strip()


def _agnos() -> dict[str, Any]:
  if not AGNOS_ROOT.exists():
    return {"present": False, "version_marker": _unknown("agnos_absent")}
  if not AGNOS_ROOT.is_dir() or AGNOS_ROOT.is_symlink():
    return {"present": False, "version_marker": _unknown("agnos_not_directory")}
  markers = []
  for name in ("VERSION", "version"):
    marker = AGNOS_ROOT / name
    try:
      if marker.is_symlink():
        return {"present": True, "version_marker": _unknown("marker_unreadable")}
      value = marker.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
      continue
    except (OSError, UnicodeError):
      return {"present": True, "version_marker": _unknown("marker_unreadable")}
    if value and "\n" not in value and len(value) <= 128:
      markers.append(value)
  if len(markers) == 1 or (len(markers) == 2 and markers[0] == markers[1]):
    return {"present": True, "version_marker": {"status": "present", "value": markers[0]}}
  if not markers:
    return {"present": True, "version_marker": _unknown("no_unambiguous_marker")}
  return {"present": True, "version_marker": _unknown("ambiguous_marker")}


def _processes(proc_root: Path) -> dict[str, Any]:
  found = dict.fromkeys(PROCESS_NAMES, False)
  if not proc_root.is_dir() or proc_root.is_symlink():
    return {"status": "unknown", "processes": found, "reason": "proc_unavailable"}
  try:
    entries = list(proc_root.iterdir())
  except OSError:
    return {"status": "unknown", "processes": found, "reason": "proc_unreadable"}
  for entry in entries:
    if not entry.name.isdecimal():
      continue
    try:
      comm = entry / "comm"
      if comm.is_symlink():
        return {"status": "unknown", "processes": found, "reason": "proc_incomplete"}
      name = comm.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError, UnicodeError):
      return {"status": "unknown", "processes": found, "reason": "proc_incomplete"}
    if name in found:
      found[name] = True
  return {"status": "present", "processes": found}


def _trusted_root(root: Path) -> bool:
  return root.is_absolute() and root == TRUSTED_REPO_ROOT and not _path_has_symlink(root) and _safe_directory(root, ".git")


def collect(root: Path, proc_root: Path, expected_head: str | None = None) -> dict[str, Any]:
  """Collect only non-personal, non-vehicle source and host metadata."""
  result: dict[str, Any] = {"audit": "accord11g_trackb_parked_audit", "scope": "source_and_host_only",
                            "operational_claim": "No readiness-to-drive claim; status is audit completeness only.",
                            "software": {"python_version": platform.python_version(), "expected_head_supplied": expected_head is not None},
                            "host": {"architecture": platform.machine() or "unknown", "os": platform.system() or "unknown",
                                     "os_release": platform.release() or "unknown"},
                            "source_directories": {}, "source_files": {}, "processes": {}, "agnos": {}}
  if not _trusted_root(root):
    result["audit_completeness"] = "FAIL"
    result["input_error"] = "untrusted_root"
    return result
  result["software"]["source_git_sha"] = _git_sha(root)
  result["software"]["tracked_source_clean"] = _git_clean(root)
  result["source_directories"] = {directory: _safe_directory(root, directory) for directory in SOURCE_DIRECTORIES}
  result["source_files"] = {relative: _sha256(root, relative) for relative in SOURCE_FILES}
  result["processes"] = _processes(proc_root)
  result["agnos"] = _agnos()
  source_ok = all(item["status"] == "present" for item in result["source_files"].values())
  git = result["software"]["source_git_sha"]
  head_matches = expected_head is not None and git.get("status") == "present" and git.get("sha") == expected_head
  result["software"]["expected_head_match"] = head_matches if expected_head is not None else "unknown"
  agnos_marker = result["agnos"].get("version_marker", {})
  target_observed = result["host"]["architecture"] == "aarch64" and result["agnos"].get("present", False) and agnos_marker.get("status") == "present"
  if not source_ok:
    result["audit_completeness"] = "FAIL"
  elif not head_matches or not result["software"]["tracked_source_clean"] or result["processes"]["status"] != "present" or not target_observed:
    result["audit_completeness"] = "UNKNOWN"
  else:
    result["audit_completeness"] = "PASS"
  return result


def _write_output(path: Path, payload: str) -> None:
  if not path.is_absolute() or path.name in ("", ".", ".."):
    raise OSError("unsafe output")
  parts = path.parts[1:]
  directory_flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
  fd = os.open(path.anchor, directory_flags)
  try:
    for part in parts[:-1]:
      next_fd = os.open(part, directory_flags, dir_fd=fd)
      os.close(fd)
      fd = next_fd
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    output_fd = os.open(parts[-1], flags, 0o600, dir_fd=fd)
  finally:
    os.close(fd)
  with os.fdopen(output_fd, "w", encoding="utf-8") as output:
    os.fchmod(output.fileno(), 0o600)
    output.write(payload)
    output.write("\n")


def _expected_head(value: str) -> str:
  if not _is_sha(value):
    raise argparse.ArgumentTypeError("expected head must be a 40-character lowercase hexadecimal SHA")
  return value


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Strictly read-only Accord 11G Track B parked source audit")
  parser.add_argument("--root", type=Path, default=TRUSTED_REPO_ROOT, help="trusted repository root")
  parser.add_argument("--expected-head", type=_expected_head, help="published GitHub release commit SHA")
  parser.add_argument("--output", type=Path, help="absolute JSON output path (created mode 0600)")
  args = parser.parse_args(argv)
  report = collect(args.root, PROC_ROOT, args.expected_head)
  payload = json.dumps(report, sort_keys=True, indent=2)
  if args.output is None:
    print(payload)
    return 0
  try:
    _write_output(args.output, payload)
  except OSError:
    print("audit output unavailable", file=sys.stderr)
    return 1
  return 0


if __name__ == "__main__":
  sys.exit(main())

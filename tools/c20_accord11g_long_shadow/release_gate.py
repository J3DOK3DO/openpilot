"""Machine-checkable research scope audit and deliberately fail-closed release matrix."""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import stat
import subprocess

RESEARCH = "tools/c20_accord11g_long_shadow/"
BASELINE = "a32dcc0a6e62a4e2a15d9ac4425424e598313c98"
REQUIRED_CODE = ("admission.py", "policies.py", "replay.py", "inventory.py", "native_preflight.py", "native_gap.py", "historical_audit.py", "shadow_advisory.py", "bundle.py", "scenarios.py", "release_gate.py")
FORBIDDEN_IMPORT_PREFIXES = ("opendbc", "panda", "openpilot", "cereal", "socket", "can", "serial")
FORBIDDEN_ATTRS = {"send", "sendall", "transmit", "forward", "connect", "set_safety_mode", "setSafetyMode", "get_car_params", "CarParams"}


def source_audit(repo: Path) -> dict:
  root = repo / RESEARCH
  findings = []
  sources = []
  if root.is_symlink() or not root.is_dir():
    findings.append("research package missing or symlinked")
  else:
    for name in REQUIRED_CODE:
      if not (root / name).is_file():
        findings.append(f"missing {name}")
    def walk_error(exc: OSError) -> None:
      findings.append(f"unreadable source directory: {exc.filename}")

    for base, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
      for name in sorted(dirs):
        if (Path(base) / name).is_symlink():
          findings.append(f"symlinked directory {Path(base, name).relative_to(root)}")
      dirs[:] = sorted(d for d in dirs if not (Path(base) / d).is_symlink())
      for name in sorted(files):
        path = Path(base) / name
        if path.is_symlink():
          findings.append(f"symlinked file {path.relative_to(root)}")
        elif path.suffix == ".py":
          sources.append(path)
  if not sources:
    findings.append("no Python source files")
  for path in sources:
    name = str(path.relative_to(root))
    try:
      fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
      with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
          raise ValueError("not a regular file")
        source = stream.read().decode("utf-8")
        after = os.fstat(stream.fileno())
        current = path.stat(follow_symlinks=False)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if identity(before) != identity(after) or identity(before) != identity(current):
          raise ValueError("source changed while reading")
      tree = ast.parse(source, filename=name)
    except (OSError, ValueError, UnicodeError, SyntaxError) as exc:
      findings.append(f"{name}: unreadable or invalid Python: {type(exc).__name__}")
      continue
    imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    for module in imports:
      if any(module == prefix or module.startswith(prefix + ".") for prefix in FORBIDDEN_IMPORT_PREFIXES):
        findings.append(f"{name}: forbidden import {module}")
    for node in ast.walk(tree):
      if isinstance(node, ast.Name) and node.id in {"Panda", "CarParams"}:
        findings.append(f"{name}: forbidden control binding {node.id}")
      if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
        findings.append(f"{name}: forbidden attribute {node.attr}")
      if isinstance(node, ast.Call) and (isinstance(node.func, ast.Name) and node.func.id in {"__import__", "import_module"}
                                         or isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"):
        findings.append(f"{name}: dynamic import")
      if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "compile"}:
        findings.append(f"{name}: dynamic execution")
  changed = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"], text=True).splitlines()
  out_of_scope = [line for line in changed if not line[3:].startswith(RESEARCH)]
  committed = subprocess.check_output(["git", "-C", str(repo), "diff", "--name-only", BASELINE, "HEAD"], text=True).splitlines()
  out_of_scope += [name for name in committed if not name.startswith(RESEARCH)]
  if out_of_scope:
    findings.append("working tree contains out-of-scope changes")
  return {"status": "PASS" if not findings else "FAIL", "findings": findings,
          "research_only_changed_paths": [line[3:] for line in changed if line[3:].startswith(RESEARCH)],
          "committed_paths_since_c19": committed}


def gate(repo: Path) -> dict:
  audit = source_audit(repo)
  stages = {
    "R1": "BLOCKED_UNVERIFIED_VEHICLE_ROUTE", "R2": "BLOCKED_NATIVE_ARCH_AND_DEPENDENCY",
    "R3": "SYNTHETIC_AND_UNVERIFIED_HISTORICAL_ATTRIBUTION", "R4": "RISK_ACCEPTED_RESEARCH_ONLY",
    "R5": "OFFLINE_INERT_SHADOW_PROTOTYPE_ONLY", "R6": "PENDING_ARM64_HARDWARE_AND_BUILD_RECEIPT",
    "R7": "RESEARCH_CANDIDATE_ONLY", "R8": "NOT_STARTED_INDEPENDENT_QUALIFICATION",
    "A1": "NOT_VERIFIED_RADAR_CAMERA_OWNERSHIP", "A2": "NOT_VERIFIED_CAN2_STARTUP",
    "A3": "NOT_VERIFIED_PANDA_AND_BRAKE_PATH", "A4": "NOT_VERIFIED_OVERRIDE_AND_FAULTS",
    "A5": "NOT_VERIFIED_REGULATORY_INSURANCE_ROAD_RELEASE"}
  return {"schema": 1, "source_audit": audit, "gates": stages,
          "active_alpha_long": "NO_GO", "road_deployment": "NO_GO",
          "research_simulator": "ELIGIBLE_IF_TESTS_PASS_AND_COMMITTED" if audit["status"] == "PASS" else "NO_GO",
          "rollback": "NOT_VERIFIED", "independent_reproduction": "NOT_VERIFIED"}


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo", type=Path, default=Path.cwd())
  args = parser.parse_args()
  print(json.dumps(gate(args.repo), indent=2, sort_keys=True))

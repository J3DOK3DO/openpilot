"""Bounded offline rebuild and verification of C19's generated C example.

Only ``build`` invokes gcc or the synthetic example. Import and ``verify`` are
read only. This is not the C19 Python MPC or longitudinal planner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess

from .admission import load_json_bytes
from .native_preflight import elf_machine
from .platform_receipt import BASELINE

GENERATED = Path("openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/c_generated_code")
LIBS = ("libacados.so", "libhpipm.so", "libblasfeo.so", "libqpOASES_e.so.3.1")
MAX_FILE = 8 * 1024 * 1024
MAX_OUTPUT = 128 * 1024
OUTPUT_FILES = ("main_long_x86", "build_stdout.log", "build_stderr.log",
                "run_stdout.log", "run_stderr.log", "native_receipt.json")


def digest(path: Path) -> str:
  if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE:
    raise ValueError(f"missing, linked or oversized file: {path}")
  return hashlib.sha256(path.read_bytes()).hexdigest()


def sources(root: Path) -> list[Path]:
  names = [root / "main_long.c", root / "acados_solver_long.c"]
  for directory in ("long_model", "long_cost", "long_constraints"):
    names.extend(sorted((root / directory).glob("*.c")))
  if len(names) != 18 or any(not p.is_file() or p.is_symlink() for p in names):
    raise ValueError("generated source set incomplete")
  return names


def source_hashes(root: Path) -> dict[str, str]:
  paths = sources(root) + sorted(root.glob("*.h"))
  for directory in ("long_model", "long_cost", "long_constraints"):
    paths.extend(sorted((root / directory).glob("*.h")))
  if len(paths) != 23:
    raise ValueError("generated header set incomplete")
  return {str(path.relative_to(root)): digest(path) for path in paths}


def library_hashes(lib: Path) -> dict[str, str]:
  return {name: digest(lib / name) for name in LIBS}


def header_tree_digest(include: Path) -> str:
  paths = sorted(include.rglob("*.h"))
  if not paths or len(paths) > 1000:
    raise ValueError("cached header set invalid")
  record = [(str(path.relative_to(include)), digest(path)) for path in paths]
  return hashlib.sha256(json.dumps(record, separators=(",", ":")).encode()).hexdigest()


def _run(command: list[str], *, env: dict | None = None, timeout: int = 30) -> subprocess.CompletedProcess:
  result = subprocess.run(command, capture_output=True, timeout=timeout, env=env, check=False)
  if len(result.stdout) + len(result.stderr) > MAX_OUTPUT:
    raise ValueError("compiler or solver output exceeded bound")
  return result


def _revision(repo: Path) -> str:
  result = _run(["git", "-C", str(repo), "rev-parse", "HEAD"], timeout=5)
  return result.stdout.decode().strip() if result.returncode == 0 else ""


def _clean(repo: Path) -> bool:
  result = _run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"], timeout=5)
  return result.returncode == 0 and not result.stdout.strip()


def _checks(stdout: str) -> tuple[int, int] | None:
  cycles = re.findall(r"solved ocp (\d+) times, solution printed above", stdout)
  iters = re.findall(r"SQP iterations\s+(\d+)", stdout)
  if len(cycles) != 1 or len(iters) != 1 or "long_acados_solve(): SUCCESS!" not in stdout:
    return None
  return int(cycles[0]), int(iters[0])


def _safe_output(repo: Path, output: Path) -> Path:
  # Inspect the supplied spelling before resolve() can erase a linked component.
  supplied = output if output.is_absolute() else Path.cwd() / output
  current = Path(supplied.anchor)
  for part in supplied.parts[1:]:
    if part == "..":
      current = current.parent
    else:
      current /= part
      if current.is_symlink():
        raise ValueError("linked output path component")
  resolved = supplied.resolve()
  research = Path(__file__).resolve().parents[2]
  if resolved.is_relative_to(repo.resolve()) or resolved.is_relative_to(research):
    raise ValueError("output overlaps a source checkout")
  if resolved.exists() and not resolved.is_dir():
    raise ValueError("output is not a directory")
  if any((resolved / name).is_symlink() for name in OUTPUT_FILES):
    raise ValueError("linked output artifact")
  return resolved


def _build_command(repo: Path, acados: Path, output: Path, src: list[Path]) -> list[str]:
  root, include, lib = repo / GENERATED, acados / "include", acados / "lib"
  command = ["gcc", "-O0", "-std=c99"]
  command += ["-I" + str(path) for path in (include, include / "acados", include / "blasfeo/include", include / "hpipm/include", root)]
  command += ["-o", str(output / "main_long_x86")] + [str(path) for path in src]
  command += ["-L" + str(lib), "-Wl,-rpath," + str(lib), "-lacados", "-lhpipm", "-lblasfeo", "-lm"]
  return command


def build(repo: Path, acados: Path, output: Path) -> dict:
  output = _safe_output(repo, output)
  repo, acados = repo.resolve(), acados.resolve()
  if _revision(repo) != BASELINE or not _clean(repo) or platform.machine().lower() != "x86_64":
    raise ValueError("clean pinned C19 and x86_64 host required")
  root, include, lib = repo / GENERATED, acados / "include", acados / "lib"
  src = sources(root)
  src_hash = source_hashes(root)
  lib_hash = library_hashes(lib)
  include_hash = header_tree_digest(include)
  if any(elf_machine(lib / name) != "x86_64" for name in LIBS):
    raise ValueError("cached libraries are not x86_64")
  output.mkdir(parents=True, exist_ok=True)
  binary = output / "main_long_x86"
  command = _build_command(repo, acados, output, src)
  compiler = _run(["gcc", "--version"], timeout=5).stdout.decode().splitlines()[0]
  built = _run(command)
  (output / "build_stdout.log").write_bytes(built.stdout)
  (output / "build_stderr.log").write_bytes(built.stderr)
  run = None
  if built.returncode == 0 and binary.is_file() and binary.stat().st_size < MAX_FILE:
    environment = dict(os.environ, LD_LIBRARY_PATH=str(lib))
    run = _run([str(binary)], env=environment, timeout=10)
    (output / "run_stdout.log").write_bytes(run.stdout)
    (output / "run_stderr.log").write_bytes(run.stderr)
  parsed = _checks(run.stdout.decode(errors="replace")) if run else None
  success = (built.returncode == 0 and run is not None and run.returncode == 0
             and parsed is not None and parsed[0] == 1 and parsed[1] >= 1)
  receipt = {
    "schema_version": 1, "classification": "REBUILT_GENERATED_SOLVER_CYCLE" if success else "NATIVE_BUILD_OR_RUN_FAILED",
    "source_commit": BASELINE, "host_architecture": platform.machine().lower(),
    "compiler": compiler, "source_sha256": src_hash, "library_sha256": lib_hash,
    "cached_headers_tree_sha256": include_hash,
    "build_command": command, "build_exit": built.returncode,
    "run_exit": run.returncode if run else None, "cycle_count": parsed[0] if parsed else 0,
    "sqp_iterations": parsed[1] if parsed else None,
    "binary_sha256": digest(binary) if binary.is_file() and binary.stat().st_size < MAX_FILE else None,
    "log_sha256": {name: digest(output / name) for name in ("build_stdout.log", "build_stderr.log")
                   + (("run_stdout.log", "run_stderr.log") if run else ())},
    "planner_replay": "NOT_DONE", "input_classification": "SYNTHETIC_GENERATED_MAIN",
    "independent_authenticity": "UNVERIFIED",
  }
  (output / "native_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
  return receipt


def verify(repo: Path, acados: Path, output: Path, expected_sha256: str) -> dict:
  output = _safe_output(repo, output)
  repo, acados = repo.resolve(), acados.resolve()
  receipt_path = output / "native_receipt.json"
  reasons = []
  if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
    raise ValueError("expected receipt digest invalid")
  if digest(receipt_path) != expected_sha256:
    reasons.append("receipt digest mismatch")
  data = load_json_bytes(receipt_path.read_bytes())
  required = {"schema_version", "classification", "source_commit", "host_architecture", "compiler",
              "source_sha256", "library_sha256", "cached_headers_tree_sha256", "build_command", "build_exit", "run_exit",
              "cycle_count", "sqp_iterations", "binary_sha256", "log_sha256", "planner_replay",
              "input_classification", "independent_authenticity"}
  if type(data) is not dict or set(data) != required:
    raise ValueError("receipt schema mismatch")
  root, lib = repo / GENERATED, acados / "lib"
  if _revision(repo) != BASELINE or not _clean(repo) or data["source_commit"] != BASELINE:
    reasons.append("source revision mismatch")
  if data["source_sha256"] != source_hashes(root):
    reasons.append("generated source mismatch")
  if data["library_sha256"] != library_hashes(lib):
    reasons.append("cached library mismatch")
  if data["cached_headers_tree_sha256"] != header_tree_digest(acados / "include"):
    reasons.append("cached header mismatch")
  if data["build_command"] != _build_command(repo, acados, output, sources(root)):
    reasons.append("build command mismatch")
  binary = output / "main_long_x86"
  if data["binary_sha256"] != digest(binary) or elf_machine(binary) != "x86_64":
    reasons.append("binary mismatch or architecture")
  if set(data["log_sha256"]) != {"build_stdout.log", "build_stderr.log", "run_stdout.log", "run_stderr.log"}:
    reasons.append("log set mismatch")
  else:
    for name, expected in data["log_sha256"].items():
      if digest(output / name) != expected:
        reasons.append("log digest mismatch: " + name)
  stdout = (output / "run_stdout.log").read_text(errors="replace")
  parsed = _checks(stdout)
  if (data["schema_version"] != 1 or data["classification"] != "REBUILT_GENERATED_SOLVER_CYCLE"
      or data["host_architecture"] != "x86_64" or data["build_exit"] != 0 or data["run_exit"] != 0
      or parsed != (data["cycle_count"], data["sqp_iterations"]) or not parsed or parsed[0] != 1
      or parsed[1] < 1 or data["planner_replay"] != "NOT_DONE"
      or data["input_classification"] != "SYNTHETIC_GENERATED_MAIN"
      or data["independent_authenticity"] != "UNVERIFIED"):
    reasons.append("cycle claim mismatch")
  return {"status": "REJECTED" if reasons else "LOCAL_EVIDENCE_CONSISTENT_UNAUTHENTICATED",
          "reasons": reasons, "independent_authenticity_verified": False,
          "native_c19_planner_replay": "NOT_DONE"}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("operation", choices=("build", "verify"))
  parser.add_argument("--repo", type=Path, required=True)
  parser.add_argument("--acados", type=Path, required=True)
  parser.add_argument("--output", type=Path, required=True)
  parser.add_argument("--expected-sha256")
  args = parser.parse_args()
  if args.operation == "verify" and not args.expected_sha256:
    parser.error("verify requires --expected-sha256")
  result = (build(args.repo, args.acados, args.output) if args.operation == "build" else
            verify(args.repo, args.acados, args.output, args.expected_sha256))
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

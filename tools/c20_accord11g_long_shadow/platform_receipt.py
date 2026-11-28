"""Read-only C19 solver artifact inventory and bounded external receipt check.

This never loads a shared library or invokes the solver. A matching external
digest proves consistency with a reference, not who supplied that reference.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import re
import subprocess

from .admission import load_json_bytes
from .native_preflight import elf_machine

BASELINE = "a32dcc0a6e62a4e2a15d9ac4425424e598313c98"
ROOT = Path("openpilot/selfdrive/controls/lib/longitudinal_mpc_lib")
ARTIFACTS = ("c_generated_code/acados_ocp_solver_pyx.so", "c_generated_code/libacados.so",
             "c_generated_code/libacados_ocp_solver_long.so", "c_generated_code/libblasfeo.so",
             "c_generated_code/libhpipm.so", "c_generated_code/libqpOASES_e.so.3.1",
             "acados_ocp_long.json", "long_mpc.py")
PINNED_SHA256 = {
  "c_generated_code/acados_ocp_solver_pyx.so": "111ca810cbf69707124162374f3b320349afc0c039ee83d18b0949cfc4072387",
  "c_generated_code/libacados.so": "c3b25e257ed8befa95c5d56493289881c34c790f7f75deae7acfc6d6bdd60335",
  "c_generated_code/libacados_ocp_solver_long.so": "b9aa77badbc77ed6e9c86962ca6572823309f89793910b7df0eced17cf2193d3",
  "c_generated_code/libblasfeo.so": "bfa126e6d2f881be97792a1b3611c1aa786a68a7233c36f86c0091be08cf95da",
  "c_generated_code/libhpipm.so": "bc1f5825c52b53327f109821082af47c6053b49cc38381b0bd4845963a3d5075",
  "c_generated_code/libqpOASES_e.so.3.1": "36b4eb60baba69fdaa1b4ef42bcc09e7b766bbcf0b0006be8e82e3c20e8dde85",
  "long_mpc.py": "3e2689f6c6366f98b2bfcfc1946074766585ed1e353a6fa22f9054934828d1ee",
  "../longitudinal_planner.py": "5d78f335aa20f0490bb743dfc6a069317fda2eca3f6e7a5bc574578fdf3c8a7d",
  "acados_ocp_long.json": "5f86aa27d7ea70bb066eaaaa58976a7a524c5f2f8d23da04e69441f1c16a5dcd",
}
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_RECEIPT = 64 * 1024


def sha(path: Path) -> str:
  h = hashlib.sha256()
  total = 0
  with path.open("rb") as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b""):
      total += len(block)
      if total > 8 * 1024 * 1024:
        raise ValueError("artifact too large")
      h.update(block)
  return h.hexdigest()


def run_readelf(path: Path) -> dict:
  try:
    result = subprocess.run(["readelf", "-d", str(path)], capture_output=True, text=True,
                            check=False, timeout=5)
  except (OSError, subprocess.TimeoutExpired):
    return {"needed": [], "runpath": []}
  if result.returncode:
    return {"needed": [], "runpath": []}
  return {"needed": sorted(set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", result.stdout))),
          "runpath": re.findall(r"\((?:RUNPATH|RPATH)\).*?\[([^\]]+)\]", result.stdout)}


def inventory(repo: Path) -> dict:
  revision = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                            text=True, check=False, timeout=5).stdout.strip()
  try:
    version_lines = subprocess.run(["readelf", "--version"], capture_output=True, text=True,
                                   check=False, timeout=5).stdout.splitlines()
    version = version_lines[0] if version_lines else None
  except (OSError, subprocess.TimeoutExpired):
    version = None
  files = {}
  for relative in ARTIFACTS + ("../longitudinal_planner.py",):
    path = repo / ROOT / relative
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
      files[relative] = None
      continue
    item = {"sha256": sha(path), "bytes": path.stat().st_size}
    if path.suffix == ".so" or ".so." in path.name:
      item.update(architecture=elf_machine(path), **run_readelf(path))
    files[relative] = item
  try:
    model_path = repo / ROOT / "acados_ocp_long.json"
    if model_path.is_symlink() or model_path.stat().st_size > 8 * 1024 * 1024:
      raise ValueError("generated model JSON unavailable or oversized")
    with model_path.open("rb") as stream:
      model = load_json_bytes(stream.read(8 * 1024 * 1024 + 1))
    solver_options = model["solver_options"]
    model_options = {"N": model["dims"]["N"], "tf": solver_options["tf"],
                     "nlp_solver_type": solver_options["nlp_solver_type"], "qp_solver": solver_options["qp_solver"]}
  except (OSError, ValueError, KeyError, TypeError):
    model_options = None
  host = platform.machine().lower()
  compiled = files[ARTIFACTS[0]] or {}
  deps = {name: importlib.util.find_spec(name) is not None for name in ("numpy", "scipy", "casadi", "capnp")}
  reasons = []
  if revision != BASELINE:
    reasons.append("C19 source revision mismatch")
  if any((files[name] or {}).get("sha256") != digest for name, digest in PINNED_SHA256.items()):
    reasons.append("C19 pinned artifact digest mismatch")
  if compiled.get("architecture") != host:
    reasons.append("compiled solver architecture differs from host")
  if version is None:
    reasons.append("readelf unavailable")
  for name in ARTIFACTS[1:6]:
    if not files[name] or files[name].get("architecture") != compiled.get("architecture"):
      reasons.append("missing or incompatible bundled library: " + name)
  if not all(deps[name] for name in ("numpy", "casadi", "scipy", "capnp")):
    reasons.append("required Python dependencies unavailable")
  expected_links = {ARTIFACTS[0]: "libacados_ocp_solver_long.so",
                    ARTIFACTS[2]: "libacados.so", ARTIFACTS[1]: "libhpipm.so"}
  for artifact, linked in expected_links.items():
    if linked not in (files[artifact] or {}).get("needed", []):
      reasons.append("generated solver dependency tree incomplete")
      break
  if model_options != {"N": 12, "tf": 10.0, "nlp_solver_type": "SQP_RTI", "qp_solver": "PARTIAL_CONDENSING_HPIPM"}:
    reasons.append("generated model options mismatch or unavailable")
  if any(files[name] is None for name in ARTIFACTS):
    reasons.append("source or generated artifact missing")
  return {"schema_version": 1, "classification": "SOURCE_ARTIFACT_ONLY", "c19_commit": revision,
          "host_architecture": host, "python_version": platform.python_version(), "readelf_version": version,
          "python_dependencies": deps, "model_options": model_options, "artifacts": files,
          "native_execution_eligibility": "BLOCKED" if reasons else "PLATFORM_ONLY_INPUTS_PENDING",
          "reasons": reasons, "executed_solver": False}


def verify_external(repo: Path, receipt_path: Path, expected_digest: str) -> dict:
  reasons = []
  if not HEX.fullmatch(expected_digest):
    raise ValueError("expected receipt SHA-256 must be lowercase hex")
  if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > MAX_RECEIPT:
    raise ValueError("receipt missing, symlinked or oversized")
  with receipt_path.open("rb") as stream:
    raw = stream.read(MAX_RECEIPT + 1)
  if len(raw) > MAX_RECEIPT:
    raise ValueError("receipt oversized")
  if hashlib.sha256(raw).hexdigest() != expected_digest:
    reasons.append("receipt digest mismatch")
  data = load_json_bytes(raw)
  local = inventory(repo)
  solver = local["artifacts"][ARTIFACTS[0]] or {}
  required = {"schema_version", "classification", "source_commit", "solver_sha256", "solver_architecture",
              "execution_architecture", "executed_solver", "cycle_count", "input_digest_sha256"}
  if type(data) is not dict or set(data) != required:
    raise ValueError("external solver receipt schema mismatch")
  if data["schema_version"] != 1 or data["classification"] != "EXTERNAL_NATIVE_EXECUTION":
    reasons.append("external execution classification mismatch")
  if data["source_commit"] != BASELINE or local["c19_commit"] != BASELINE:
    reasons.append("C19 source revision mismatch")
  if (type(data["solver_sha256"]) is not str or not HEX.fullmatch(data["solver_sha256"])
      or type(solver.get("sha256")) is not str or not HEX.fullmatch(solver["sha256"])
      or data["solver_sha256"] != solver["sha256"]):
    reasons.append("solver artifact digest mismatch")
  if (solver.get("architecture") != "aarch64" or data["solver_architecture"] != "aarch64"
      or data["execution_architecture"] != "aarch64"):
    reasons.append("solver/execution architecture mismatch")
  if (any(local["artifacts"][name] is None for name in ARTIFACTS)
      or any(local["artifacts"][name].get("architecture") != "aarch64" for name in ARTIFACTS[:6])
      or local["model_options"] != {"N": 12, "tf": 10.0, "nlp_solver_type": "SQP_RTI", "qp_solver": "PARTIAL_CONDENSING_HPIPM"}
      or "C19 pinned artifact digest mismatch" in local["reasons"]
      or "generated solver dependency tree incomplete" in local["reasons"]):
    reasons.append("local generated source or dependency set incomplete")
  if data["executed_solver"] is not True or type(data["cycle_count"]) is not int or not 0 < data["cycle_count"] <= 100000:
    reasons.append("native execution claim absent or invalid")
  if type(data["input_digest_sha256"]) is not str or not HEX.fullmatch(data["input_digest_sha256"]):
    reasons.append("input digest invalid")
  return {"schema_version": 1, "status": "REJECTED" if reasons else "REFERENCE_MATCH_UNVERIFIED",
          "reasons": reasons, "receipt_digest_matches_supplied_reference": "receipt digest mismatch" not in reasons,
          "authenticity_verified": False, "executed_solver_verified": False}


def verify_pinned_inventory(repo: Path, receipt_path: Path) -> dict:
  if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > MAX_RECEIPT:
    raise ValueError("pinned inventory missing, symlinked or oversized")
  with receipt_path.open("rb") as stream:
    raw = stream.read(MAX_RECEIPT + 1)
  if len(raw) > MAX_RECEIPT:
    raise ValueError("pinned inventory oversized")
  expected = load_json_bytes(raw)
  actual = inventory(repo)
  return {"schema_version": 1, "status": "MATCH" if expected == actual else "MISMATCH",
          "classification": "SOURCE_ARTIFACT_ONLY", "executed_solver": False}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo", type=Path, required=True)
  parser.add_argument("--external-receipt", type=Path)
  parser.add_argument("--expected-receipt-sha256")
  parser.add_argument("--pinned-inventory", type=Path)
  args = parser.parse_args()
  if bool(args.external_receipt) != bool(args.expected_receipt_sha256):
    parser.error("external receipt and expected digest must be supplied together")
  if args.pinned_inventory and args.external_receipt:
    parser.error("choose pinned inventory or external execution receipt")
  result = (verify_pinned_inventory(args.repo, args.pinned_inventory) if args.pinned_inventory else
            verify_external(args.repo, args.external_receipt, args.expected_receipt_sha256) if args.external_receipt else inventory(args.repo))
  print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

"""Offline native C19 MPC qualification without importing solver or car code."""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
from pathlib import Path

SOLVER = Path("openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/c_generated_code/acados_ocp_solver_pyx.so")
LIBRARIES = ("libacados.so", "libacados_ocp_solver_long.so", "libblasfeo.so", "libhpipm.so")
MACHINES = {0x3e: "x86_64", 0xb7: "aarch64"}


def elf_machine(path: Path) -> str | None:
  with path.open("rb") as stream:
    header = stream.read(20)
  if len(header) < 20 or header[:4] != b"\x7fELF" or header[5] not in (1, 2):
    return None
  return MACHINES.get(int.from_bytes(header[18:20], "little" if header[5] == 1 else "big"), "OTHER")


def qualify(repo: Path) -> dict:
  solver = repo / SOLVER
  generated = solver.parent
  reasons = []
  machine = platform.machine().lower()
  solver_arch = elf_machine(solver) if solver.is_file() else None
  if solver_arch is None:
    reasons.append("compiled acados Cython solver missing or not ELF")
  elif solver_arch != machine:
    reasons.append(f"solver architecture {solver_arch} differs from host {machine}")
  libs = {}
  for name in LIBRARIES:
    path = generated / name
    libs[name] = elf_machine(path) if path.is_file() else None
    if libs[name] != solver_arch or libs[name] is None:
      reasons.append(f"{name} absent or incompatible")
  deps = {name: importlib.util.find_spec(name) is not None for name in ("numpy", "casadi")}
  for name, found in deps.items():
    if not found:
      reasons.append(f"Python dependency {name} unavailable")
  return {"label": "NATIVE_C19_MPC", "status": "READY_FOR_ISOLATED_EXECUTION" if not reasons else "BLOCKED",
          "host_arch": machine, "solver_arch": solver_arch, "libraries": libs,
          "python_dependencies": deps, "reasons": reasons,
          "executed_solver": False,
          "input_contract": "Same-cycle carState, radarState, modelV2 trajectories, controlsState, vehicleParameters, CP, cruise, personality, timebase and planner state; no interpolated or synthetic stand-ins for recorded equivalence",
          "source": "C19 a32dcc0a6e62 openpilot/selfdrive/controls/lib/longitudinal_mpc_lib/long_mpc.py and longitudinal_planner.py"}


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--repo", type=Path, default=Path.cwd())
  args = parser.parse_args()
  print(json.dumps(qualify(args.repo), indent=2, sort_keys=True))


if __name__ == "__main__":
  main()

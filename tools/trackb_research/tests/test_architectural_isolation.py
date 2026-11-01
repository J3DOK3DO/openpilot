"""Structural proof that Track B research is not imported by production code."""

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_ROOTS = (ROOT / "openpilot", ROOT / "opendbc_repo" / "opendbc", ROOT / "panda")
SOURCE_SUFFIXES = {".py", ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".sconscript"}
RESEARCH_MODULES = (
  "plan_controller_sim.py",
  "shadow_synthetic.py",
  "ownership_evidence_model.py",
  "brake_hold_contract.py",
)


def test_trackb_research_has_no_production_import_or_reference():
  hits = []
  for production_root in PRODUCTION_ROOTS:
    for path in production_root.rglob("*"):
      if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES and "/tests/" not in f"/{path.relative_to(ROOT)}":
        if "trackb_research" in path.read_text(encoding="utf-8", errors="ignore"):
          hits.append(path.relative_to(ROOT).as_posix())
  assert hits == []


def test_research_modules_have_only_standard_library_imports():
  for name in RESEARCH_MODULES:
    source = (ROOT / "tools" / "trackb_research" / name).read_text(encoding="utf-8")
    imports = []
    for node in ast.walk(ast.parse(source)):
      if isinstance(node, ast.Import):
        imports.extend(alias.name.split(".")[0] for alias in node.names)
      elif isinstance(node, ast.ImportFrom) and node.module is not None:
        imports.append(node.module.split(".")[0])
    assert set(imports) <= {"dataclasses", "math", "sys"}


def test_no_tracked_runtime_file_anywhere_references_trackb_research():
  """Whole-repository scan (starpilot, system, scripts, launchers, SConstruct included), not just three roots."""
  tracked = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True).split("\0")
  allowed_prefixes = ("docs/", "tools/trackb_research/")
  hits = []
  for name in filter(None, tracked):
    relative = f"/{name}"
    if name.startswith(allowed_prefixes) or "/tests/" in relative or "/test_" in relative:
      continue
    path = ROOT / name
    if path.is_file() and not path.is_symlink() and path.stat().st_size < 4_000_000:
      if "trackb_research" in path.read_text(encoding="utf-8", errors="ignore"):
        hits.append(name)
  assert hits == []

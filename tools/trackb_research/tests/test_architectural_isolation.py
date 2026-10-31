"""Structural proof that Track B research is not imported by production code."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_ROOTS = (ROOT / "openpilot", ROOT / "opendbc_repo" / "opendbc", ROOT / "panda")
SOURCE_SUFFIXES = {".py", ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".sconscript"}


def test_trackb_research_has_no_production_import_or_reference():
  hits = []
  for production_root in PRODUCTION_ROOTS:
    for path in production_root.rglob("*"):
      if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES and "/tests/" not in f"/{path.relative_to(ROOT)}":
        if "trackb_research" in path.read_text(encoding="utf-8", errors="ignore"):
          hits.append(path.relative_to(ROOT).as_posix())
  assert hits == []


def test_simulator_source_has_only_standard_library_imports_and_no_transport_terms():
  source = (ROOT / "tools" / "trackb_research" / "plan_controller_sim.py").read_text(encoding="utf-8")
  imports = []
  for node in ast.walk(ast.parse(source)):
    if isinstance(node, ast.Import):
      imports.extend(alias.name.split(".")[0] for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module is not None:
      imports.append(node.module.split(".")[0])
  assert set(imports) <= {"dataclasses", "math"}

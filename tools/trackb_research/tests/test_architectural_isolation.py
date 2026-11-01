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
  "mvl_retained_sim.py",
  "release_b_gate.py",
  "source_evidence_contracts.py",
  "brake_policy_model.py",
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
        imports.extend(alias.name for alias in node.names)
      elif isinstance(node, ast.ImportFrom) and node.module is not None:
        imports.append(node.module)
    # Sibling research modules are allowed; nothing else outside the standard library.
    external = {module.split(".")[0] for module in imports if not module.startswith("tools.trackb_research.")}
    assert external <= {"dataclasses", "hashlib", "math", "sys"}, name


def test_no_tracked_runtime_file_anywhere_references_trackb_research():
  """Whole-repository scan (starpilot, system, scripts, launchers, SConstruct, tests included), not just three roots."""
  tracked = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True).split("\0")
  # Only documentation and the research tree itself may mention it: no test-name or tests-directory exemption,
  # so a runtime file named like a test (e.g. starpilot/test_launcher.py) is still scanned.
  allowed_prefixes = ("docs/", "tools/trackb_research/")

  def allowed(name):
    return name.startswith(allowed_prefixes)

  hits = []
  for name in filter(None, tracked):
    if allowed(name):
      continue
    path = ROOT / name
    if path.is_file() and not path.is_symlink() and path.stat().st_size < 4_000_000:
      if "trackb_research" in path.read_text(encoding="utf-8", errors="ignore"):
        hits.append(name)
  # The working-tree pass above cannot see sparse-checkout (skip-worktree) files; search every index blob too.
  grep = subprocess.run(["git", "-C", str(ROOT), "grep", "--cached", "-l", "-z", "-I", "-e", "trackb_research"],
                        capture_output=True, text=True)
  assert grep.returncode in (0, 1), grep.stderr
  hits.extend(name for name in filter(None, grep.stdout.split("\0")) if not allowed(name))
  assert sorted(set(hits)) == []

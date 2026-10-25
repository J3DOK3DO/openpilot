"""Targeted RC3 package-planner attacks; host filesystem reads only."""
from __future__ import annotations

import json
import os
import ast
import subprocess
from pathlib import Path

import pytest

import rc3_package_planner as planner

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def unsigned_plan():
  return planner.build_plan(ROOT)


def test_exact_frozen_inventory_is_deterministic_but_unsigned(unsigned_plan):
  second = planner.build_plan(ROOT)
  assert second == unsigned_plan
  assert unsigned_plan["inventory"]["frozen_git_commit"] == planner.FROZEN_COMMIT
  assert unsigned_plan["inventory"]["frozen_git_tree"] == planner.FROZEN_TREE
  assert unsigned_plan["classification"] == "UNSIGNED DEVELOPMENT PACKAGE"
  assert unsigned_plan["package_manifest_signed"] is False
  assert unsigned_plan["external_trust"]["status"] == "MISSING_SIGNED_EXTERNAL_TRUST_POLICY"
  assert unsigned_plan["external_trust"]["independent_trust_anchor_verified"] is False
  assert unsigned_plan["external_trust"]["production_release_authority"] is False
  assert unsigned_plan["qualification"]["content_integrity_verified"] is True
  assert unsigned_plan["qualification"]["external_trust_verified"] is False
  assert unsigned_plan["qualification"]["installation_authorized"] is False


@pytest.mark.parametrize("commit,tree", [
  ("0" * 40, planner.FROZEN_TREE),
  (planner.FROZEN_COMMIT, "f" * 40),
  ("not-a-commit", planner.FROZEN_TREE),
])
def test_wrong_commit_or_tree_is_rejected(commit, tree):
  with pytest.raises(planner.PlanningError, match="Git|wrong source"):
    planner.require_frozen_identity((commit, tree))


def test_tracked_worktree_drift_is_rejected(monkeypatch):
  monkeypatch.setattr(planner, "_git", lambda *_args, **_kwargs:
                      planner.subprocess.CompletedProcess([], 1, "", ""))
  with pytest.raises(planner.PlanningError, match="tracked worktree"):
    planner.require_clean_tracked_tree(ROOT)


@pytest.mark.parametrize("relative", [
  "/etc/passwd", "../etc/passwd", "native/../../escape", "x//y", "x/./y", "x\\y", "",
])
def test_manifest_path_traversal_is_rejected(relative):
  with pytest.raises(planner.PlanningError):
    planner._safe_relative_path(relative)


def test_symlink_artifact_is_rejected(tmp_path):
  (tmp_path / "real").write_bytes(b"payload")
  (tmp_path / "link").symlink_to(tmp_path / "real")
  with pytest.raises(planner.PlanningError, match="symlink"):
    planner.read_stable_declared_bytes(tmp_path, "link")


def test_symlink_parent_is_rejected(tmp_path):
  outside = tmp_path / "outside"
  outside.mkdir()
  (outside / "payload").write_bytes(b"payload")
  (tmp_path / "parent").symlink_to(outside, target_is_directory=True)
  with pytest.raises(planner.PlanningError, match="symlink"):
    planner.read_stable_declared_bytes(tmp_path, "parent/payload")


def test_manifest_swap_after_open_is_rejected_without_parsing_replacement(tmp_path, monkeypatch):
  original = b'{"identity":"opened-before-swap"}\n'
  replacement = b'{"identity":"replacement-after-check"}\n'
  manifest = tmp_path / planner.PINNED_MANIFEST_PATH
  manifest.write_bytes(original)
  swap = tmp_path / "replacement.json"
  swap.write_bytes(replacement)
  read_descriptor = planner._read_descriptor
  calls = 0

  def swap_after_first_read(descriptor, maximum=None):
    nonlocal calls
    raw = read_descriptor(descriptor, maximum)
    calls += 1
    if calls == 1:
      os.replace(swap, manifest)
    return raw

  monkeypatch.setattr(planner, "_read_descriptor", swap_after_first_read)
  with pytest.raises(planner.PlanningError, match="changed|unstable"):
    planner.load_pinned_manifest(tmp_path)


def test_git_root_must_match_canonical_requested_root():
  with pytest.raises(planner.PlanningError, match="Git root mismatch|cannot establish local Git root"):
    planner.git_identity(ROOT / "tools")


def test_local_git_environment_drops_caller_git_controls(monkeypatch):
  observed = {}
  monkeypatch.setenv("GIT_DIR", "/tmp/attacker-git-dir")
  monkeypatch.setenv("GIT_WORK_TREE", "/tmp/attacker-work-tree")
  monkeypatch.setenv("GIT_INDEX_FILE", "/tmp/attacker-index")

  def fake_run(*args, **kwargs):
    observed.update(kwargs["env"])
    return subprocess.CompletedProcess(args[0], 0, "", "")

  monkeypatch.setattr(planner.subprocess, "run", fake_run)
  planner._git(ROOT, ["status"])
  assert "GIT_DIR" not in observed
  assert "GIT_WORK_TREE" not in observed
  assert "GIT_INDEX_FILE" not in observed
  assert observed["GIT_CONFIG_NOSYSTEM"] == "1"


def _test_git(root, *arguments):
  git = planner.shutil.which("git", path=os.defpath)
  assert git is not None
  return subprocess.run(
    [git, "-c", "user.name=RC3 Test", "-c", "user.email=rc3@example.invalid",
     "-C", os.fspath(root), *arguments],
    check=True, capture_output=True, text=True,
  ).stdout.strip()


def test_git_replace_objects_disabled_for_frozen_identity(tmp_path):
  repository = tmp_path / "replace-repo"
  repository.mkdir()
  _test_git(repository, "init")
  (repository / "payload.txt").write_text("original\n")
  _test_git(repository, "add", "payload.txt")
  _test_git(repository, "commit", "-m", "original")
  first_commit = _test_git(repository, "rev-parse", "HEAD")
  (repository / "payload.txt").write_text("newer\n")
  _test_git(repository, "commit", "-am", "newer")
  second_tree = _test_git(repository, "rev-parse", "HEAD^{tree}")
  second_commit = _test_git(repository, "rev-parse", "HEAD")
  _test_git(repository, "replace", second_commit, first_commit)
  assert planner._git_output(repository, "HEAD^{tree}") == second_tree


def test_git_grafts_are_explicitly_rejected(tmp_path):
  repository = tmp_path / "grafts-repo"
  repository.mkdir()
  _test_git(repository, "init")
  (repository / "payload.txt").write_text("original\n")
  _test_git(repository, "add", "payload.txt")
  _test_git(repository, "commit", "-m", "original")
  (repository / ".git" / "info" / "grafts").write_text(_test_git(repository, "rev-parse", "HEAD") + "\n")
  with pytest.raises(planner.PlanningError, match="grafts prohibited"):
    planner.require_safe_engineering_overlay(repository)


def test_graft_inserted_after_precheck_cannot_forge_raw_parent(tmp_path, monkeypatch):
  repository = tmp_path / "late-graft-repo"
  repository.mkdir()
  _test_git(repository, "init")
  (repository / "payload.txt").write_text("protected\n")
  _test_git(repository, "add", "payload.txt")
  _test_git(repository, "commit", "-m", "baseline")
  frozen_commit = _test_git(repository, "rev-parse", "HEAD")
  frozen_tree = _test_git(repository, "rev-parse", "HEAD^{tree}")
  monkeypatch.setattr(planner, "FROZEN_COMMIT", frozen_commit)
  monkeypatch.setattr(planner, "FROZEN_TREE", frozen_tree)
  _test_git(repository, "checkout", "--orphan", "forged-unrelated")
  _test_git(repository, "read-tree", "--empty")
  (repository / "payload.txt").write_text("protected\n")
  allowed = repository / "tools/g8_release/rc3_package_planner.py"
  allowed.parent.mkdir(parents=True)
  allowed.write_text("# engineering-only overlay\n")
  _test_git(repository, "add", "payload.txt", "tools/g8_release/rc3_package_planner.py")
  _test_git(repository, "commit", "-m", "unrelated but tree diff only allowlisted")
  unrelated_commit = _test_git(repository, "rev-parse", "HEAD")
  actual_git = planner._git
  graft_written = False

  def late_graft(root, args, **kwargs):
    nonlocal graft_written
    if not graft_written and args[:2] == ["cat-file", "-p"]:
      graft_written = True
      (repository / ".git" / "info" / "grafts").write_text(
        unrelated_commit + " " + frozen_commit + "\n"
      )
    return actual_git(root, args, **kwargs)

  monkeypatch.setattr(planner, "_git", late_graft)
  with pytest.raises(planner.PlanningError, match="single-parent descendant|not a descendant"):
    planner.require_safe_engineering_overlay(repository)
  assert graft_written


def test_engineering_overlay_accepts_only_descendant_whitelist(tmp_path, monkeypatch):
  repository = tmp_path / "overlay-repository"
  repository.mkdir()
  _test_git(repository, "init")
  (repository / "protected-payload.txt").write_text("frozen\n")
  _test_git(repository, "add", "protected-payload.txt")
  _test_git(repository, "commit", "-m", "frozen baseline")
  frozen_commit = _test_git(repository, "rev-parse", "HEAD")
  frozen_tree = _test_git(repository, "rev-parse", "HEAD^{tree}")
  monkeypatch.setattr(planner, "FROZEN_COMMIT", frozen_commit)
  monkeypatch.setattr(planner, "FROZEN_TREE", frozen_tree)

  allowed = repository / "tools/g8_release/rc3_package_planner.py"
  allowed.parent.mkdir(parents=True)
  allowed.write_text("# engineering-only overlay\n")
  _test_git(repository, "add", os.fspath(allowed.relative_to(repository)))
  _test_git(repository, "commit", "-m", "allowed engineering overlay")
  planner.require_safe_engineering_overlay(repository)
  planner.require_clean_tracked_tree(repository)

  (repository / "protected-payload.txt").write_text("changed\n")
  _test_git(repository, "add", "protected-payload.txt")
  _test_git(repository, "commit", "-m", "forbidden payload edit")
  with pytest.raises(planner.PlanningError, match="non-whitelisted"):
    planner.require_safe_engineering_overlay(repository)

  _test_git(repository, "checkout", "--orphan", "unrelated-history")
  _test_git(repository, "read-tree", "--empty")
  (repository / "unrelated.txt").write_text("unrelated\n")
  _test_git(repository, "add", "unrelated.txt")
  _test_git(repository, "commit", "-m", "unrelated root")
  with pytest.raises(planner.PlanningError, match="single-parent descendant|not a descendant"):
    planner.require_safe_engineering_overlay(repository)


def test_duplicate_key_manifest_is_rejected(tmp_path):
  (tmp_path / planner.PINNED_MANIFEST_PATH).write_text('{"id":"a","id":"b"}\n')
  with pytest.raises(planner.PlanningError, match="duplicate"):
    planner.load_pinned_manifest(tmp_path)


def test_malicious_extra_install_field_manifest_is_rejected(tmp_path):
  manifest = json.loads((ROOT / planner.PINNED_MANIFEST_PATH).read_text())
  manifest["install_now"] = True
  (tmp_path / planner.PINNED_MANIFEST_PATH).write_text(json.dumps(manifest))
  with pytest.raises(planner.PlanningError, match="schema"):
    planner.load_pinned_manifest(tmp_path)


def test_malicious_traversal_in_native_manifest_is_rejected(tmp_path):
  manifest = json.loads((ROOT / planner.PINNED_MANIFEST_PATH).read_text())
  manifest["source_built_AArch64_elfs"][0]["path"] = "../pandad"
  (tmp_path / planner.PINNED_MANIFEST_PATH).write_text(json.dumps(manifest))
  loaded = planner.load_pinned_manifest(tmp_path)
  with pytest.raises(planner.PlanningError, match="traversing"):
    planner.verify_native_components(tmp_path, loaded["source_built_AArch64_elfs"])


def test_altered_aarch64_binary_is_rejected(tmp_path):
  source = ROOT / "selfdrive/pandad/pandad"
  target = tmp_path / "pandad"
  target.write_bytes(source.read_bytes())
  with target.open("r+b") as stream:
    stream.seek(4096)
    original = stream.read(1)
    stream.seek(4096)
    stream.write(bytes([original[0] ^ 1]))
  entries = [{"path": "pandad", "sha256": planner.EXPECTED_HONDA_PANDAD_SHA256,
              "size_bytes": source.stat().st_size, "source": "TEST"}]
  with pytest.raises(planner.PlanningError, match="integrity mismatch"):
    planner.verify_native_components(tmp_path, entries)


def test_wrong_model_full_hash_is_rejected(tmp_path):
  pieces = []
  for number, payload in enumerate((b"alpha", b"beta", b"gamma"), 1):
    relative = f"chunk{number}"
    (tmp_path / relative).write_bytes(payload)
    pieces.append((relative, len(payload), planner.hashlib.sha256(payload).hexdigest()))
  with pytest.raises(planner.PlanningError, match="reconstructed model"):
    planner.verify_model_chunks(tmp_path, pieces, "0" * 64, len(b"alphabetagamma"))


@pytest.mark.parametrize("mutation", [
  lambda lines: lines.__setitem__(4, "exit 0"),
  lambda lines: lines.insert(4, "source ./launch_env.sh"),
  lambda lines: lines.__setitem__(4, "# exit 78"),
])
def test_launcher_guard_mutations_are_rejected(mutation):
  lines = (ROOT / planner.LAUNCHER_PATH).read_text().splitlines()
  mutation(lines)
  assert not planner.verify_launcher_guard("\n".join(lines) + "\n")


def test_launcher_guard_is_exact_and_early_success_remains_unreachable():
  source = (ROOT / planner.LAUNCHER_PATH).read_text()
  assert planner.verify_launcher_guard(source)
  assert source.index("exit 78") < source.index("sudo abctl --set_success")


def test_output_is_explicit_create_only(tmp_path, unsigned_plan):
  destination = tmp_path / "plan.json"
  planner.write_new_file(destination, planner.canonical_json(unsigned_plan))
  before = destination.read_bytes()
  with pytest.raises(planner.PlanningError, match="overwrite"):
    planner.write_new_file(destination, b"changed")
  assert destination.read_bytes() == before


def test_no_external_policy_pair_cannot_be_partially_supplied():
  with pytest.raises(planner.PlanningError, match="together"):
    planner.build_plan(ROOT, policy_path=Path("/tmp/absent"))


def test_planner_source_exposes_no_device_or_install_command_interface():
  source = (ROOT / "tools/g8_release/rc3_package_planner.py").read_text()
  tree = ast.parse(source)
  subprocess_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
                       isinstance(node.func, ast.Attribute) and
                       getattr(node.func.value, "id", None) == "subprocess"]
  assert len(subprocess_calls) == 1
  assert subprocess_calls[0].func.attr == "run"  # bounded local git identity query only
  command = subprocess_calls[0].args[0]
  string_literals = [node.value for node in ast.walk(command)
                     if isinstance(node, ast.Constant) and isinstance(node.value, str)]
  assert isinstance(command, ast.List) and isinstance(command.elts[0], ast.Name)
  assert command.elts[0].id == "git_binary"
  assert '"rev-parse"' in source and '"diff"' in source and '"--quiet"' in source
  assert "git fetch" not in source and "git push" not in source
  assert "os.system" not in source and "Popen" not in source and "--override" not in source

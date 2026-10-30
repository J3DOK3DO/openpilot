"""Synthetic-fixture tests for the strictly read-only Track B parked audit."""
import ast
import importlib.util
import json
import stat
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "accord11g_trackb_parked_audit.py"
SPEC = importlib.util.spec_from_file_location("accord11g_trackb_parked_audit", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit)
EXPECTED = "a" * 40


def make_root(tmp_path):
  root = tmp_path / "private-fixture-root"
  for relative in audit.SOURCE_FILES:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("public synthetic source\n", encoding="utf-8")
  for directory in audit.SOURCE_DIRECTORIES:
    (root / directory).mkdir(exist_ok=True)
  (root / ".git").mkdir()
  return root


def make_proc(tmp_path, *names):
  proc = tmp_path / "proc"
  proc.mkdir()
  for number, name in enumerate(names, start=100):
    entry = proc / str(number)
    entry.mkdir(parents=True)
    (entry / "comm").write_text(name + "\n", encoding="utf-8")
  return proc


@pytest.fixture
def trusted_root(monkeypatch, tmp_path):
  root = make_root(tmp_path)
  monkeypatch.setattr(audit, "TRUSTED_REPO_ROOT", root)
  monkeypatch.setattr(audit, "_git_clean", lambda _: True)
  return root


def target(monkeypatch):
  monkeypatch.setattr(audit.platform, "machine", lambda: "aarch64")
  monkeypatch.setattr(audit, "_agnos", lambda: {"present": True, "version_marker": {"status": "present", "value": "synthetic"}})


def test_default_stdout_is_read_only_and_requires_external_pin(trusted_root, tmp_path, monkeypatch, capsys):
  proc = make_proc(tmp_path, "manager")
  before = {path: path.stat().st_mtime_ns for path in trusted_root.rglob("*")}
  monkeypatch.setattr(audit, "PROC_ROOT", proc)
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  assert audit.main([]) == 0
  stdout = capsys.readouterr().out
  assert json.loads(stdout)["audit_completeness"] == "UNKNOWN"
  assert str(trusted_root) not in stdout
  assert before == {path: path.stat().st_mtime_ns for path in trusted_root.rglob("*")}


def test_expected_head_match_is_required_even_on_synthetic_target(trusted_root, tmp_path, monkeypatch):
  proc = make_proc(tmp_path)
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  target(monkeypatch)
  assert audit.collect(trusted_root, proc)["audit_completeness"] == "UNKNOWN"
  assert audit.collect(trusted_root, proc, "b" * 40)["audit_completeness"] == "UNKNOWN"
  report = audit.collect(trusted_root, proc, EXPECTED)
  assert report["processes"]["status"] == "present", report["processes"]
  assert all(item["status"] == "present" for item in report["source_files"].values()), report["source_files"]
  assert report["software"]["expected_head_match"] is True, report["software"]
  assert report["audit_completeness"] == "PASS", report


def test_missing_source_fails_and_unknown_git_never_passes(trusted_root, tmp_path, monkeypatch):
  proc = make_proc(tmp_path)
  (trusted_root / audit.SOURCE_FILES[0]).unlink()
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "unknown", "reason": "git_unavailable"})
  report = audit.collect(trusted_root, proc, EXPECTED)
  assert report["source_files"][audit.SOURCE_FILES[0]]["status"] == "missing"
  assert report["audit_completeness"] == "FAIL"


def test_untrusted_root_and_source_symlink_fail_redacted(trusted_root, tmp_path, monkeypatch):
  proc = make_proc(tmp_path)
  outside = tmp_path / "outside"
  outside.mkdir()
  (outside / "interface.py").write_text("outside", encoding="utf-8")
  (trusted_root / audit.SOURCE_FILES[0]).unlink()
  (trusted_root / audit.SOURCE_FILES[0]).symlink_to(outside / "interface.py")
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  report = audit.collect(trusted_root, proc, EXPECTED)
  assert report["audit_completeness"] == "FAIL"
  assert "outside" not in json.dumps(report)
  linked_root = tmp_path / "linked-root"
  linked_root.symlink_to(trusted_root, target_is_directory=True)
  linked = audit.collect(linked_root, proc, EXPECTED)
  assert linked["audit_completeness"] == "FAIL"
  assert linked["input_error"] == "untrusted_root"


def test_process_observation_unknown_for_any_unreadable_numeric_comm(trusted_root, tmp_path, monkeypatch):
  proc = make_proc(tmp_path, "manager")
  (proc / "101").mkdir()
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  report = audit.collect(trusted_root, proc, EXPECTED)
  assert report["processes"]["status"] == "unknown"
  assert report["processes"]["reason"] == "proc_incomplete"
  assert report["audit_completeness"] == "UNKNOWN"


def test_process_detection_reads_only_comm_files(trusted_root, tmp_path, monkeypatch):
  proc = make_proc(tmp_path, "manager", "pandad", "controlsd", "unrelated")
  for entry in proc.iterdir():
    (entry / "cmdline").write_text("sensitive arguments", encoding="utf-8")
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  report = audit.collect(trusted_root, proc, EXPECTED)
  assert report["processes"] == {"status": "present", "processes": dict.fromkeys(audit.PROCESS_NAMES, True)}
  assert "sensitive arguments" not in json.dumps(report)


def test_output_is_private_and_parent_symlink_or_existing_file_is_redacted(trusted_root, tmp_path, monkeypatch, capsys):
  proc = make_proc(tmp_path)
  monkeypatch.setattr(audit, "PROC_ROOT", proc)
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  output = tmp_path / "report.json"
  assert audit.main(["--expected-head", EXPECTED, "--output", str(output)]) == 0
  assert stat.S_IMODE(output.stat().st_mode) == 0o600
  assert json.loads(output.read_text(encoding="utf-8"))["audit"] == "accord11g_trackb_parked_audit"
  assert audit.main(["--expected-head", EXPECTED, "--output", str(output)]) == 1
  assert capsys.readouterr().err == "audit output unavailable\n"
  linked_parent = tmp_path / "linked-parent"
  linked_parent.symlink_to(tmp_path, target_is_directory=True)
  assert audit.main(["--expected-head", EXPECTED, "--output", str(linked_parent / "new.json")]) == 1
  assert str(linked_parent) not in capsys.readouterr().err


def test_source_uses_no_network_or_device_interfaces_or_proc_cli_option():
  source = MODULE_PATH.read_text(encoding="utf-8")
  imports = {node.names[0].name.split(".")[0] for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Import)}
  imports.update(node.module.split(".")[0] for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom) and node.module)
  assert not imports & {"can", "panda", "socket", "usb"}
  assert '"cmdline"' not in source
  assert "--proc-root" not in source
  assert "/dev/" not in source


def test_expected_head_parser_requires_exact_lowercase_sha():
  assert audit._expected_head(EXPECTED) == EXPECTED
  with pytest.raises(SystemExit):
    audit.main(["--expected-head", "A" * 40])

def test_dirty_tracked_source_can_never_be_approved(trusted_root, tmp_path, monkeypatch):
  proc = make_proc(tmp_path)
  monkeypatch.setattr(audit, "_git_sha", lambda _: {"status": "present", "sha": EXPECTED})
  monkeypatch.setattr(audit, "_git_clean", lambda _: False)
  target(monkeypatch)
  report = audit.collect(trusted_root, proc, EXPECTED)
  assert report["software"]["expected_head_match"] is True
  assert report["software"]["tracked_source_clean"] is False
  assert report["audit_completeness"] == "UNKNOWN"

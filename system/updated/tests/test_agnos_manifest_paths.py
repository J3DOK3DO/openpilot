import json
from pathlib import Path

import pytest

from openpilot.system.updated.updated import AGNOS_MANIFEST_PATHS, get_agnos_manifest_path


REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "system/hardware/tici/agnos.json"


def test_compat_manifest_paths():
  real_manifest = MANIFEST.resolve()
  for relative_path in AGNOS_MANIFEST_PATHS:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"{relative_path} missing or dangling"
    assert path.resolve() == real_manifest
    json.loads(path.read_text())


def test_manifest_resolver_uses_first_available_layout(tmp_path):
  first = tmp_path / AGNOS_MANIFEST_PATHS[2]
  second = tmp_path / AGNOS_MANIFEST_PATHS[4]
  first.parent.mkdir(parents=True)
  second.parent.mkdir(parents=True)
  first.write_text("[]")
  second.write_text("[]")

  assert get_agnos_manifest_path(tmp_path) == str(first)


def test_manifest_resolver_fails_closed(tmp_path):
  with pytest.raises(FileNotFoundError, match="no agnos.json found"):
    get_agnos_manifest_path(tmp_path)

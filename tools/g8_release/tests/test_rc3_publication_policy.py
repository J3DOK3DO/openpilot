"""RC3 engineering policy tests — no boot-slot access, CAN or device startup."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rc3_publication_policy import (check_tree, _declared_file, HARDWARE_GATES,
                                     EXPECTED_MODEL_SHA256)

ROOT = Path(__file__).resolve().parents[3]


def test_exact_offline_RC3_artifact_integrity():
    status = check_tree(ROOT)
    assert status["engineering_integrity_pass"]
    assert status["checked_source_built_native_components"] == 14
    assert status["honda_pandad_digest_match"]
    assert status["tracked_model_chunk_reconstruction_sha256_matches"]


def test_policy_never_authorizes_installation():
    status = check_tree(ROOT)
    assert status["installation_authorized"] is False
    assert status["road_use_authorized"] is False
    assert status["production_approved"] is False
    assert status["github_install_url_authorized"] is False
    assert status["disposition"] == "OFFLINE_INTEGRITY_ONLY_PRODUCTION_HOLD"


def test_guard_preserved_and_early_boot_success_still_unresolved():
    status = check_tree(ROOT)
    assert status["fail_closed_launch_guard_ahead_of_init"]
    assert status["early_abctl_boot_success_unresolved"]


@pytest.mark.parametrize("relative", [
    "/etc/passwd", "../etc/passwd", "some/../../secret", "x//y",
    "x/./y", "x\\y", "",
])
def test_rejects_noncanonical_attestation_paths(relative):
    with pytest.raises(ValueError):
        _declared_file(ROOT, relative)


def test_agnos_slot_not_mistaken_for_openpilot_application_slot():
    status = check_tree(ROOT)
    assert status["inactive_agnos_boot_slot_is_NOT_an_application_slot"] is True
    assert len(HARDWARE_GATES) == 4
    assert "rolling" not in status["disposition"].lower()


def test_model_manifest_and_chunks_do_not_require_oversized_git_blob():
    assert EXPECTED_MODEL_SHA256 == "27969d9da00f74ba0c1f56de575665121a967528753500cd2f809b61664e0e3f"
    assert not (ROOT / "selfdrive/modeld/models/driving_tinygrad.pkl").exists()
    assert all((ROOT / f"selfdrive/modeld/models/driving_tinygrad.pkl.chunk{i:02}of03").is_file()
               for i in (1, 2, 3))


def test_offline_policy_contains_no_privileged_action_interface():
    src = (ROOT / "tools/g8_release/rc3_publication_policy.py").read_text()
    for disallowed in ("subprocess.", "os.system(", "abctl --set_active",
                       "ssh ", "can_send(", "reboot("):
        assert disallowed not in src

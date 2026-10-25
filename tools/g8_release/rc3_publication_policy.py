"""Offline RC3 integrity/admission check, never an installer or safety approval.

Reads a source tree, hashes native components and the model's three tracked
chunks, and asserts the release guard remains ahead of any hardware startup.
Runs no subprocess, network, device command, privileged operation or CAN.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

MAX_MANIFEST_SIZE = 1_048_576
MODEL_CHUNK_COUNT = 3
EXPECTED_MODEL_SHA256 = "27969d9da00f74ba0c1f56de575665121a967528753500cd2f809b61664e0e3f"
EXPECTED_HONDA_PANDAD_SHA256 = "6fec6261fae4a84de75ef16f6fa604df01cd66f56e6ccea596fdfd890698d671"

HARDWARE_GATES = (
    "Independent OEM-rooted AGNOS verified-boot and image trust evidence",
    "Independent immutable health supervisor, qualified A/B rollback and witnessed power loss",
    "Signed recoverable installation artifact, tested off-road app startup and component provenance",
    "Honda Panda/CAN and disengagement bench evidence, independent safety release approval",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _declared_file(root: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
        raise ValueError("invalid manifest path")
    parts = rel.split("/")
    if any(item in ("", ".", "..") for item in parts):
        raise ValueError("noncanonical manifest path")
    root = root.resolve(strict=True)
    file = root.joinpath(*parts)
    if file.is_symlink() or not file.is_file():
        raise ValueError(f"not a regular declared artifact: {rel}")
    if not file.resolve(strict=True).is_relative_to(root):
        raise ValueError("artifact escapes source tree")
    return file


def verify_tracked_model_chunks(root: Path) -> bool:
    h = hashlib.sha256()
    for i in range(1, MODEL_CHUNK_COUNT + 1):
        rel = f"selfdrive/modeld/models/driving_tinygrad.pkl.chunk{i:02}of03"
        with _declared_file(root, rel).open("rb") as f:
            for part in iter(lambda: f.read(1024 * 1024), b""):
                h.update(part)
    return h.hexdigest() == EXPECTED_MODEL_SHA256


def check_tree(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    manifest_path = _declared_file(root, "G8_F12_RC3_PINNED_COMPONENTS.json")
    if manifest_path.stat().st_size > MAX_MANIFEST_SIZE:
        raise ValueError("oversized release manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("invalid release manifest")
    component_list = manifest.get("source_built_AArch64_elfs")
    if not isinstance(component_list, list) or len(component_list) != 14:
        raise ValueError("expected 14 source-built ARM64 components")
    seen = set()
    checks = []
    for x in component_list:
        rel = x["path"]
        if rel in seen:
            raise ValueError("duplicate native artifact")
        seen.add(rel)
        path = _declared_file(root, rel)
        valid = sha256_file(path) == x["sha256"]
        checks.append({"path": rel, "matches": valid})
    if not any(x["path"] == "selfdrive/pandad/pandad"
               and x["sha256"] == EXPECTED_HONDA_PANDAD_SHA256
               for x in component_list):
        raise ValueError("Honda-only pandad digest absent")
    source = _declared_file(root, "launch_chffrplus.sh").read_text(encoding="utf-8")
    # Require a real, top-level shell exit, not a substring in a comment.
    lines = source.splitlines()
    guard_valid = (
        len(lines) >= 8
        and lines[0] == "#!/usr/bin/env bash"
        and lines[4] == "exit 78"
        and source.find('source "$DIR/launch_env.sh"') > source.index("\nexit 78\n")
        and "sudo abctl --set_success" not in "\n".join(lines[:5])
    )
    # The original slot success call is intentionally unreachable, but NOT fixed.
    early_slot_success_unresolved = "sudo abctl --set_success" in source
    model_ok = verify_tracked_model_chunks(root)
    sha_ok = all(x["matches"] for x in checks)
    good = all((guard_valid, early_slot_success_unresolved, model_ok, sha_ok))
    return {
        "schema": "G8_F12_RC3_ENGINEERING_ADMISSION_V1",
        "engineering_integrity_pass": good,
        "checked_source_built_native_components": len(checks),
        "native_component_digests_match": sha_ok,
        "honda_pandad_digest_match": next(x["matches"] for x in checks
                                           if x["path"] == "selfdrive/pandad/pandad"),
        "tracked_model_chunk_reconstruction_sha256_matches": model_ok,
        "fail_closed_launch_guard_ahead_of_init": guard_valid,
        "early_abctl_boot_success_unresolved": early_slot_success_unresolved,
        "inactive_agnos_boot_slot_is_NOT_an_application_slot": True,
        "mandatory_hardware_gates": list(HARDWARE_GATES),
        "installation_authorized": False,
        "road_use_authorized": False,
        "github_install_url_authorized": False,
        "production_approved": False,
        "disposition": "OFFLINE_INTEGRITY_ONLY_PRODUCTION_HOLD",
    }

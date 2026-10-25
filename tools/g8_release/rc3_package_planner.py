#!/usr/bin/env python3
"""Deterministic, read-only-by-default RC3 development package planner.

The planner verifies the frozen Git identity, pinned RC3 component manifest,
14 native AArch64 artifacts, all three model chunks and their reconstructed
digest, plus the launcher's fail-closed exit-78 guard.  It does not create an
archive, sign anything, install anything, start openpilot, access a device, or
authorize production.  An output file is written only with explicit --output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from rc3_external_trust import ExternalTrustVerifier, TrustError, canonical_json

FROZEN_COMMIT = "bbb771a2fadf5af96f532e798846ba8171483e50"
FROZEN_TREE = "fcd3142e877a165911a677f9361c6594f3eecf6b"
PINNED_MANIFEST_PATH = "G8_F12_RC3_PINNED_COMPONENTS.json"
PINNED_MANIFEST_SHA256 = "93456212b73126671089eaf9b30c54dd245c16ac7d8f3de8f8405c6ede2c7aae"
LAUNCHER_PATH = "launch_chffrplus.sh"
LAUNCHER_SHA256 = "dba70ac885eee3a98f19a3830660e365f764b6970c69c3d1bf2b3d28c8be5284"
EXPECTED_MODEL_SHA256 = "27969d9da00f74ba0c1f56de575665121a967528753500cd2f809b61664e0e3f"
EXPECTED_MODEL_BYTES = 126_302_979
EXPECTED_HONDA_PANDAD_SHA256 = "6fec6261fae4a84de75ef16f6fa604df01cd66f56e6ccea596fdfd890698d671"
MAX_MANIFEST_BYTES = 1_048_576

# A future engineering publication may be a descendant of the immutable RC3
# HOLD baseline, but only these non-payload additions may differ from it.  This
# is deliberately an exact list, not a directory-prefix allowlist.
ENGINEERING_OVERLAY_PATHS = frozenset({
  "RC3_CODEX_EXIT.rc",
  "RC3_CODEX_HANDOFF.txt",
  "RC3_CODEX_RUN.log",
  "RC3_DEVELOPMENT_PACKAGE_PLAN.json",
  "RC3_INDEPENDENT_REVIEW.log",
  "RC3_INDEPENDENT_REVIEW.rc",
  "RC3_INDEPENDENT_SAFETY_REVIEW.txt",
  "RC3_REMEDIATION_CODEX_RUN.log",
  "RC3_SAFE_STAGING_ENGINEERING_HANDOFF.md",
  "RC3_SAFE_STAGING_ENGINEERING_REPORT.md",
  "RC3_SAFE_STAGING_GATECARD.json",
  "RC3_RAW_PARENT_INDEPENDENT_REVIEW.txt",
  "RC3_TEST_LOGS/README.md",
  "RC3_TEST_LOGS/ubuntu_rc3_RAW_PARENT_FINAL.log",
  "RC3_TEST_LOGS/ubuntu_rc3_RAW_PARENT_FINAL.xml",
  "RC3_TEST_LOGS/ubuntu_rc3_RAW_PARENT_FINAL.rc",
  "RC3_TEST_LOGS/rc3_RAW_PARENT_QEMU_FINAL.log",
  "RC3_TEST_LOGS/rc3_RAW_PARENT_QEMU_FINAL.xml",
  "RC3_TEST_LOGS/rc3_RAW_PARENT_QEMU_FINAL.rc",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU.log",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU.rc",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU.xml",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_CORRECTED.log",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_CORRECTED.rc",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_CORRECTED.xml",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_FULL.log",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_FULL.rc",
  "RC3_TEST_LOGS/RC3_SAFE_STAGING_QEMU_FULL.xml",
  "RC3_TEST_LOGS/ubuntu_baseline_without_new_tests.xml",
  "RC3_TEST_LOGS/ubuntu_tools_g8_release.xml",
  "tools/g8_release/rc3_external_trust.py",
  "tools/g8_release/rc3_host_staging.py",
  "tools/g8_release/rc3_package_planner.py",
  "tools/g8_release/tests/test_rc3_host_staging.py",
  "tools/g8_release/tests/test_rc3_package_planner.py",
})

MODEL_CHUNKS = (
  ("selfdrive/modeld/models/driving_tinygrad.pkl.chunk01of03", 47_185_920,
   "1f562cd72273e1c670e9fc79eb3dc5dc78abd0842a918c222991e0eb62429ed5"),
  ("selfdrive/modeld/models/driving_tinygrad.pkl.chunk02of03", 47_185_920,
   "97ee0e75752193102192d7513486aa964838f14f41673db7c4b45c9e6617720f"),
  ("selfdrive/modeld/models/driving_tinygrad.pkl.chunk03of03", 31_931_139,
   "76e8660b09c859e39682738f82e100ea271a7339d212fabba9534442aa94a976"),
)

_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")


class PlanningError(ValueError):
  """Malformed or integrity-invalid package input."""


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for key, value in pairs:
    if key in result:
      raise PlanningError(f"duplicate JSON key: {key}")
    result[key] = value
  return result


def _safe_relative_path(relative: Any) -> tuple[str, ...]:
  if type(relative) is not str or not relative or relative.startswith("/") or "\\" in relative:
    raise PlanningError("invalid declared path")
  parts = tuple(relative.split("/"))
  if any(part in ("", ".", "..") for part in parts):
    raise PlanningError("noncanonical or traversing declared path")
  return parts


@contextmanager
def _open_declared_regular(root: Path, relative: Any) -> Iterator[tuple[int, os.stat_result]]:
  """Open a declared file beneath root without ever re-resolving its path.

  Every component is opened relative to an already-open directory descriptor
  with O_NOFOLLOW.  Callers hash, parse, or decode through the yielded final
  descriptor, so a path substitution cannot switch the verified byte stream.
  """
  root = root.resolve(strict=True)
  parts = _safe_relative_path(relative)
  nofollow = getattr(os, "O_NOFOLLOW", 0)
  cloexec = getattr(os, "O_CLOEXEC", 0)
  directory = getattr(os, "O_DIRECTORY", 0)
  parent_fd: int | None = None
  final_fd: int | None = None
  try:
    try:
      parent_fd = os.open(root, os.O_RDONLY | directory | nofollow | cloexec)
    except OSError as error:
      raise PlanningError("cannot open canonical source root") from error
    for part in parts[:-1]:
      try:
        next_fd = os.open(part, os.O_RDONLY | directory | nofollow | cloexec,
                          dir_fd=parent_fd)
      except OSError as error:
        raise PlanningError(
          f"missing, symlinked, or non-directory declared artifact parent: {relative}") from error
      os.close(parent_fd)
      parent_fd = next_fd
    try:
      final_fd = os.open(parts[-1], os.O_RDONLY | os.O_NONBLOCK | nofollow | cloexec,
                         dir_fd=parent_fd)
    except OSError as error:
      raise PlanningError(f"missing or symlinked declared artifact: {relative}") from error
    info = os.fstat(final_fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink < 1:
      raise PlanningError(f"declared artifact is not a linked regular file: {relative}")
    yield final_fd, info
  finally:
    if final_fd is not None:
      os.close(final_fd)
    if parent_fd is not None:
      os.close(parent_fd)


def _stat_identity(info: os.stat_result) -> tuple[int, ...]:
  return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size,
          info.st_mtime_ns, info.st_ctime_ns)


def _read_descriptor(descriptor: int, maximum: int | None = None) -> bytes:
  os.lseek(descriptor, 0, os.SEEK_SET)
  chunks: list[bytes] = []
  total = 0
  while chunk := os.read(descriptor, 1024 * 1024):
    total += len(chunk)
    if maximum is not None and total > maximum:
      raise PlanningError("declared artifact exceeds bounded read size")
    chunks.append(chunk)
  return b"".join(chunks)


def read_stable_declared_bytes(root: Path, relative: Any, *, maximum: int | None = None,
                               repeat: bool = True) -> bytes:
  """Read bytes from one pinned descriptor and detect concurrent mutation."""
  with _open_declared_regular(root, relative) as (descriptor, opened):
    if opened.st_size <= 0 or (maximum is not None and opened.st_size > maximum):
      raise PlanningError("declared artifact has invalid size")
    raw = _read_descriptor(descriptor, maximum)
    after_first = os.fstat(descriptor)
    if len(raw) != opened.st_size or _stat_identity(opened) != _stat_identity(after_first):
      raise PlanningError(f"declared artifact changed while read: {relative}")
    if repeat:
      repeated = _read_descriptor(descriptor, maximum)
      after_second = os.fstat(descriptor)
      if raw != repeated or _stat_identity(opened) != _stat_identity(after_second):
        raise PlanningError(f"declared artifact was unstable across repeated reads: {relative}")
    return raw


def _hash_declared_file(root: Path, relative: Any, *, aggregate: Any = None) -> tuple[int, str]:
  """Hash one pinned regular-file descriptor with before/after fstat checks."""
  with _open_declared_regular(root, relative) as (descriptor, opened):
    digest = hashlib.sha256()
    size = 0
    while part := os.read(descriptor, 1024 * 1024):
      digest.update(part)
      if aggregate is not None:
        aggregate.update(part)
      size += len(part)
    closed_read = os.fstat(descriptor)
    if size != opened.st_size or _stat_identity(opened) != _stat_identity(closed_read):
      raise PlanningError(f"declared artifact changed while hashed: {relative}")
    return size, digest.hexdigest()


def load_pinned_manifest(root: Path, relative: str = PINNED_MANIFEST_PATH, *,
                         expected_sha256: str | None = None) -> dict[str, Any]:
  raw = read_stable_declared_bytes(root, relative, maximum=MAX_MANIFEST_BYTES)
  if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256:
    raise PlanningError("pinned component manifest digest mismatch")
  try:
    manifest = json.loads(raw, object_pairs_hook=_reject_duplicate_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                            PlanningError(f"invalid JSON constant: {value}")))
  except (UnicodeDecodeError, json.JSONDecodeError) as error:
    raise PlanningError("malformed pinned component manifest JSON") from error
  expected_keys = {
    "id", "parent_RC2_commit", "branch", "components_unchanged_from_RC2",
    "reconstructed_model_SHA256", "model_bytes", "source_built_AArch64_elfs",
    "regenerated_localization_source", "tests", "Sol_HIGH_boot_architecture_review",
    "boot_integrity", "root_of_trust", "trusted_boot_health_supervisor",
    "physical_AB_power_loss_recovery", "panda_honda_real_CAN_bench",
    "production_install_authorized", "road_use_authorized", "launcher_exit_code",
    "device_changed", "github_pushed",
  }
  if type(manifest) is not dict or set(manifest) != expected_keys:
    raise PlanningError("pinned component manifest has an unexpected schema")
  if (manifest["id"] != "G8-F12-RC3-HONDA-ENGINEERING-HOLD-20261025" or
      manifest["reconstructed_model_SHA256"] != EXPECTED_MODEL_SHA256 or
      manifest["model_bytes"] != EXPECTED_MODEL_BYTES or
      manifest["launcher_exit_code"] != 78 or
      manifest["production_install_authorized"] is not False or
      manifest["road_use_authorized"] is not False or manifest["device_changed"] is not False or
      manifest["github_pushed"] is not False):
    raise PlanningError("pinned manifest identity or safety disposition mismatch")
  components = manifest["source_built_AArch64_elfs"]
  if type(components) is not list or len(components) != 14:
    raise PlanningError("pinned manifest must contain exactly 14 native components")
  return manifest


def _git(root: Path, arguments: list[str], *, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
  root = root.resolve(strict=True)
  git_binary = shutil.which("git", path=os.defpath)
  if git_binary is None or not Path(git_binary).is_absolute():
    raise PlanningError("trusted host Git executable is unavailable")
  environment = {
    "PATH": os.defpath,
    "LC_ALL": "C",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_NO_REPLACE_OBJECTS": "1",  # signed release objects must not be rewritten by refs/replace
  }
  try:
    return subprocess.run(
      [git_binary, "--no-optional-locks", "-c", f"safe.directory={root}",
       "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}",
       "-c", "diff.external=",
       "-C", os.fspath(root), *arguments],
      check=False, capture_output=capture_output, text=True, timeout=10, env=environment,
    )
  except (OSError, subprocess.SubprocessError) as error:
    raise PlanningError("bounded local Git identity check failed") from error


def _git_output(root: Path, argument: str) -> str:
  result = _git(root, ["rev-parse", "--verify", argument])
  if result.returncode != 0:
    raise PlanningError(f"cannot resolve frozen Git identity: {argument}")
  return result.stdout.strip()


def git_identity(root: Path) -> tuple[str, str]:
  canonical = root.resolve(strict=True)
  top = _git(root, ["rev-parse", "--show-toplevel"])
  if top.returncode != 0:
    raise PlanningError("cannot establish local Git root")
  try:
    observed_top = Path(top.stdout.strip()).resolve(strict=True)
  except (OSError, RuntimeError) as error:
    raise PlanningError("local Git reported an invalid top-level path") from error
  if observed_top != canonical:
    raise PlanningError(f"Git root mismatch: expected {canonical}, got {observed_top}")
  return _git_output(canonical, "HEAD"), _git_output(canonical, "HEAD^{tree}")


def require_frozen_identity(identity: tuple[str, str]) -> None:
  commit, tree = identity
  if not _HEX40.fullmatch(commit) or not _HEX40.fullmatch(tree):
    raise PlanningError("malformed Git commit/tree identity")
  if commit != FROZEN_COMMIT:
    raise PlanningError(f"wrong source commit: expected {FROZEN_COMMIT}, got {commit}")
  if tree != FROZEN_TREE:
    raise PlanningError(f"wrong source tree: expected {FROZEN_TREE}, got {tree}")


def require_safe_engineering_overlay(root: Path) -> tuple[str, str]:
  """Accept the frozen baseline or a descendant containing only listed evidence/tooling."""
  root = root.resolve(strict=True)
  common = _git(root, ["rev-parse", "--path-format=absolute", "--git-common-dir"])
  if common.returncode != 0:
    raise PlanningError("cannot resolve Git common directory for graft rejection")
  common_path = Path(common.stdout.strip())
  if not common_path.is_absolute():
    raise PlanningError("Git common directory is not absolute")
  grafts = common_path / "info" / "grafts"
  if os.path.lexists(grafts):
    raise PlanningError("Git grafts prohibited for frozen release identity")
  head, head_tree = git_identity(root)
  if not _HEX40.fullmatch(head) or not _HEX40.fullmatch(head_tree):
    raise PlanningError("malformed Git HEAD identity")
  frozen_commit = _git_output(root, f"{FROZEN_COMMIT}^{{commit}}")
  frozen_tree = _git_output(root, f"{FROZEN_COMMIT}^{{tree}}")
  if frozen_commit != FROZEN_COMMIT or frozen_tree != FROZEN_TREE:
    raise PlanningError("frozen RC3 commit/tree object identity mismatch")
  # Read immutable raw commit parent records, not rev-list or merge-base.
  # Git's legacy info/grafts can rewrite revision-walking ancestry between
  # successive subprocesses; cat-file commit bytes are unaffected by grafts.
  # GIT_NO_REPLACE_OBJECTS=1 is always set in _git for every raw object read.
  current = head
  seen: set[str] = set()
  for _ in range(1024):
    if current == FROZEN_COMMIT:
      break
    if current in seen:
      raise PlanningError("cyclic raw Git commit ancestry")
    seen.add(current)
    raw = _git(root, ["cat-file", "-p", current])
    if raw.returncode != 0:
      raise PlanningError("cannot read raw Git commit parent record")
    header = raw.stdout.split("\n\n", 1)[0].splitlines()
    trees = [line[5:] for line in header if line.startswith("tree ")]
    parents = [line[7:] for line in header if line.startswith("parent ")]
    if len(trees) != 1 or not _HEX40.fullmatch(trees[0]):
      raise PlanningError("malformed raw Git commit tree")
    if len(parents) != 1 or not _HEX40.fullmatch(parents[0]):
      raise PlanningError("Git HEAD is not a single-parent descendant of frozen RC3")
    current = parents[0]
  else:
    raise PlanningError("raw Git ancestry exceeds bounded depth")
  if current != FROZEN_COMMIT:
    raise PlanningError("Git HEAD is not a descendant of the frozen RC3 baseline")
  changed = _git(root, ["diff", "--no-ext-diff", "--name-only", "--diff-filter=ACDMRTUXB", "-z",
                        FROZEN_COMMIT, "HEAD", "--"])
  if changed.returncode != 0:
    raise PlanningError("cannot enumerate engineering overlay")
  paths = {item for item in changed.stdout.split("\0") if item}
  disallowed = sorted(paths - ENGINEERING_OVERLAY_PATHS)
  if disallowed:
    raise PlanningError(f"engineering overlay modifies non-whitelisted path: {disallowed[0]}")
  return head, head_tree


def require_clean_tracked_tree(root: Path) -> None:
  result = _git(root, ["diff", "--no-ext-diff", "--quiet", "--ignore-submodules=none",
                       "HEAD", "--"])
  if result.returncode == 1:
    raise PlanningError("tracked worktree or submodule content differs from Git HEAD")
  if result.returncode != 0:
    raise PlanningError("cannot verify tracked worktree against Git HEAD")


def verify_launcher_guard(source: str) -> bool:
  lines = source.splitlines()
  return (
    len(lines) >= 8 and lines[0] == "#!/usr/bin/env bash" and
    lines[1] == "# G8-F12 RC2 HONDA ENGINEERING HOLD: non-installable, non-actuating snapshot." and
    lines[4] == "exit 78" and lines[2].startswith("# Hardware and boot-health") and
    lines[3].startswith("printf ") and
    source.find('source "$DIR/launch_env.sh"') > source.index("\nexit 78\n") and
    "sudo " not in "\n".join(lines[:5]) and "abctl " not in "\n".join(lines[:5])
  )


def verify_native_components(root: Path, components: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
  results: list[dict[str, Any]] = []
  seen: set[str] = set()
  for item in components:
    if type(item) is not dict or set(item) != {"path", "sha256", "size_bytes", "source"}:
      raise PlanningError("malformed native component entry")
    relative = item["path"]
    _safe_relative_path(relative)
    if relative in seen:
      raise PlanningError("duplicate native component path")
    seen.add(relative)
    if (type(item["sha256"]) is not str or not _HEX64.fullmatch(item["sha256"]) or
        type(item["size_bytes"]) is not int or item["size_bytes"] <= 0 or
        type(item["source"]) is not str or not item["source"]):
      raise PlanningError("malformed native component metadata")
    actual_size, actual_sha256 = _hash_declared_file(root, relative)
    if actual_size != item["size_bytes"] or actual_sha256 != item["sha256"]:
      raise PlanningError(f"native component integrity mismatch: {relative}")
    results.append({"path": relative, "size_bytes": actual_size, "sha256": actual_sha256})
  if len(results) != 14:
    raise PlanningError("native component inventory count mismatch")
  pandad = [item for item in results if item["path"] == "selfdrive/pandad/pandad"]
  if len(pandad) != 1 or pandad[0]["sha256"] != EXPECTED_HONDA_PANDAD_SHA256:
    raise PlanningError("pinned Honda pandad is missing or altered")
  return results


def verify_model_chunks(root: Path, chunks: Iterable[tuple[str, int, str]] = MODEL_CHUNKS,
                        expected_full_sha256: str = EXPECTED_MODEL_SHA256,
                        expected_full_bytes: int = EXPECTED_MODEL_BYTES) -> dict[str, Any]:
  full = hashlib.sha256()
  results: list[dict[str, Any]] = []
  total = 0
  for relative, expected_size, expected_sha256 in chunks:
    size, digest = _hash_declared_file(root, relative, aggregate=full)
    if size != expected_size or digest != expected_sha256:
      raise PlanningError(f"model chunk integrity mismatch: {relative}")
    results.append({"path": relative, "size_bytes": size, "sha256": digest})
    total += size
  if len(results) != 3 or total != expected_full_bytes or full.hexdigest() != expected_full_sha256:
    raise PlanningError("reconstructed model size or digest mismatch")
  return {"chunks": results, "reconstructed_size_bytes": total,
          "reconstructed_sha256": full.hexdigest()}


def build_inventory(root: Path) -> dict[str, Any]:
  root = root.resolve(strict=True)
  require_safe_engineering_overlay(root)
  require_clean_tracked_tree(root)
  manifest = load_pinned_manifest(root, expected_sha256=PINNED_MANIFEST_SHA256)
  launcher_raw = read_stable_declared_bytes(root, LAUNCHER_PATH, maximum=1024 * 1024)
  launcher_sha = hashlib.sha256(launcher_raw).hexdigest()
  try:
    launcher_source = launcher_raw.decode("utf-8")
  except UnicodeDecodeError as error:
    raise PlanningError("launcher is not valid UTF-8") from error
  if launcher_sha != LAUNCHER_SHA256 or not verify_launcher_guard(launcher_source):
    raise PlanningError("launcher digest or fail-closed exit-78 guard mismatch")
  native = verify_native_components(root, manifest["source_built_AArch64_elfs"])
  model = verify_model_chunks(root)
  return {
    "schema": "G8_F12_RC3_DEVELOPMENT_INVENTORY_V1",
    "frozen_git_commit": FROZEN_COMMIT,
    "frozen_git_tree": FROZEN_TREE,
    "pinned_component_manifest": {"path": PINNED_MANIFEST_PATH,
                                  "sha256": PINNED_MANIFEST_SHA256},
    "launcher": {"path": LAUNCHER_PATH, "sha256": launcher_sha,
                 "exit_78_guard_verified": True},
    "native_AArch64_components": native,
    "model": model,
  }


def inventory_sha256(inventory: dict[str, Any]) -> str:
  return hashlib.sha256(canonical_json(inventory)).hexdigest()


def build_plan(root: Path, *, policy_path: Path | None = None,
               keyring_path: Path | None = None) -> dict[str, Any]:
  if (policy_path is None) != (keyring_path is None):
    raise PlanningError("external policy and keyring must be supplied together")
  root = root.resolve(strict=True)
  inventory = build_inventory(root)
  digest = inventory_sha256(inventory)
  trust = {
    "caller_supplied_signature_verified": False,
    "independent_trust_anchor_verified": False,
    "production_release_authority": False,
    "status": "MISSING_SIGNED_EXTERNAL_TRUST_POLICY",
    "policy_id": None,
    "scope": None,
  }
  if policy_path is not None and keyring_path is not None:
    try:
      policy = ExternalTrustVerifier(root, policy_path, keyring_path).verify_policy(
        frozen_commit=FROZEN_COMMIT, frozen_tree=FROZEN_TREE, inventory_sha256=digest)
    except TrustError as error:
      raise PlanningError(f"external trust verification failed: {error}") from error
    trust = {
      "caller_supplied_signature_verified": True,
      "independent_trust_anchor_verified": False,
      "production_release_authority": False,
      "status": "CALLER_SUPPLIED_HOST_SIMULATION_KEY_CRYPTOGRAPHICALLY_VERIFIED",
      "policy_id": policy["policy_id"],
      "scope": policy["scope"],
    }
  return {
    "schema": "G8_F12_RC3_DEVELOPMENT_PACKAGE_PLAN_V1",
    "classification": "UNSIGNED DEVELOPMENT PACKAGE",
    "deterministic": True,
    "package_manifest_signed": False,
    "inventory_sha256": digest,
    "inventory": inventory,
    "external_trust": trust,
    "qualification": {
      "content_integrity_verified": True,
      "external_trust_verified": False,
      "caller_supplied_host_simulation_signature_verified":
        trust["caller_supplied_signature_verified"],
      "host_trial_simulation_eligible": trust["caller_supplied_signature_verified"],
      "production_approved": False,
      "installation_authorized": False,
      "device_operations_authorized": False,
      "road_use_authorized": False,
      "disposition": "HOST_ONLY_DEVELOPMENT_HOLD",
    },
  }


def write_new_file(path: Path, payload: bytes) -> None:
  if not path.is_absolute():
    path = Path.cwd() / path
  path.parent.resolve(strict=True)
  flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
  if hasattr(os, "O_NOFOLLOW"):
    flags |= os.O_NOFOLLOW
  try:
    descriptor = os.open(path, flags, 0o644)
  except OSError as error:
    raise PlanningError(f"refusing to overwrite or follow output path: {path}") from error
  try:
    with os.fdopen(descriptor, "wb", closefd=False) as stream:
      stream.write(payload)
      stream.flush()
      os.fsync(stream.fileno())
  finally:
    os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
  parser.add_argument("--external-policy", type=Path)
  parser.add_argument("--external-keyring", type=Path)
  parser.add_argument("--output", type=Path,
                      help="explicitly write a new canonical plan file; existing paths are refused")
  arguments = parser.parse_args(argv)
  try:
    plan = build_plan(arguments.root, policy_path=arguments.external_policy,
                      keyring_path=arguments.external_keyring)
    payload = canonical_json(plan)
    if arguments.output is not None:
      write_new_file(arguments.output, payload)
    else:
      sys.stdout.buffer.write(payload)
    return 0 if plan["external_trust"]["caller_supplied_signature_verified"] else 78
  except PlanningError as error:
    print(f"RC3 package planning rejected: {error}", file=sys.stderr)
    return 2


if __name__ == "__main__":
  raise SystemExit(main())

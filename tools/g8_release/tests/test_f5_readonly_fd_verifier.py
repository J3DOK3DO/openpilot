import base64
import errno
import fcntl
import hashlib
import json
import os
from dataclasses import replace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import g8_manifest as gm
import g8_slot_supervisor as sv
from g8_protected_authority import CandidateIdentity, MockProtectedAuthority, SIMULATED_TRUST_LABEL
from g8_readonly_fd_verifier import (
  PinningCrash,
  PinningError,
  PinningFaults,
  ReadOnlyFdVerifier,
)


COMMIT = "d" * 40


def _public_raw(private_key):
  return private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _public_b64(private_key):
  return base64.b64encode(_public_raw(private_key)).decode()


def _identity(app, slot_id):
  directory = app / "slots" / slot_id
  manifest_bytes = (directory / sv.MANIFEST_NAME).read_bytes()
  manifest = json.loads(manifest_bytes)
  signature = json.loads((directory / sv.SIGNATURE_NAME).read_bytes())
  return CandidateIdentity(
    slot_id, hashlib.sha256(manifest_bytes).hexdigest(), manifest["source_commit"],
    manifest["release_sequence"], signature["key_id"],
  )


def _package(path, tag):
  path.mkdir()
  launcher = path / sv.LAUNCHER
  launcher.write_text(f"#!/bin/sh\necho {tag}\n")
  launcher.chmod(0o755)
  (path / "version.txt").write_text(tag)
  data = path / "data"
  data.mkdir()
  (data / "config.txt").write_text(f"config={tag}\n")
  (path / "config-link").symlink_to("data/config.txt")


@pytest.fixture
def f5(tmp_path):
  release_key = Ed25519PrivateKey.generate()
  trust_key = {
    "key_id": gm.key_id(_public_raw(release_key)),
    "pubkey_b64": _public_b64(release_key),
    "purpose": "production",
  }
  trust = {"trusted_keys": [trust_key]}
  app = tmp_path / "mutable_app"
  app.mkdir()
  supervisor = sv.Supervisor(app, trust=trust, expected_commit=COMMIT, minimum_release_sequence=10)
  slots = {}
  identities = {}
  for sequence, tag in ((10, "old-release"), (11, "current-release")):
    source = tmp_path / f"package_{tag}"
    _package(source, tag)
    manifest = gm.build_manifest(source, COMMIT, with_elf_detail=False, release_sequence=sequence)
    signature = gm.sign_manifest(manifest, release_key, SIMULATED_TRUST_LABEL)
    slot_id = supervisor.stage(source, manifest, COMMIT, signature)
    slots[tag] = slot_id
    identities[tag] = _identity(app, slot_id)
  protected = tmp_path / "mock_protected_authority"
  authority = MockProtectedAuthority.create(
    protected,
    recovery=identities["current-release"],
    expected_commit=COMMIT,
    minimum_release_sequence=11,
    signing_keys=[trust_key],
    decision_pubkey_b64=_public_b64(Ed25519PrivateKey.generate()),
    health_pubkey_b64=_public_b64(Ed25519PrivateKey.generate()),
  )
  return type("F5", (), {
    "app": app,
    "slots": slots,
    "ids": identities,
    "policy": authority.policy_snapshot(),
  })()


def _current_launcher(env):
  return env.app / "slots" / env.slots["current-release"] / sv.LAUNCHER


def _fd_count():
  return len(os.listdir("/proc/self/fd"))


@pytest.mark.SIMULATED_TEST_TRUST
def test_signed_exact_candidate_returns_only_readonly_noninheritable_descriptors(f5):
  verifier = ReadOnlyFdVerifier(f5.app, f5.policy)
  expected = _current_launcher(f5).read_bytes()
  with verifier.pin(f5.ids["current-release"]) as pinned:
    descriptor = pinned.fileno()
    assert pinned.candidate == f5.ids["current-release"]
    assert pinned.policy_generation == f5.policy.generation
    assert pinned.policy_epoch == f5.policy.epoch
    assert pinned.executed is False
    assert fcntl.fcntl(descriptor, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY
    assert os.get_inheritable(descriptor) is False
    assert pinned.read_file() == expected
    pinned.revalidate()
  assert pinned.closed is True
  assert pinned.descriptor_count == 0
  with pytest.raises(OSError) as raised:
    os.fstat(descriptor)
  assert raised.value.errno == errno.EBADF


@pytest.mark.SIMULATED_TEST_TRUST
def test_launcher_symlink_replacement_between_lstat_and_open_fails_closed(f5):
  launcher = _current_launcher(f5)
  outside = f5.app.parent / "outside-launcher"
  outside.write_bytes(launcher.read_bytes())
  outside.chmod(0o755)

  def replace_with_symlink():
    launcher.unlink()
    launcher.symlink_to(outside)

  faults = PinningFaults(action_at={f"entry_before_open:{sv.LAUNCHER}": replace_with_symlink})
  before = _fd_count()
  with pytest.raises(OSError):
    ReadOnlyFdVerifier(f5.app, f5.policy, faults=faults).pin(f5.ids["current-release"])
  assert _fd_count() == before


@pytest.mark.SIMULATED_TEST_TRUST
def test_regular_file_inode_replacement_during_open_is_rejected_and_cleaned(f5):
  version = f5.app / "slots" / f5.slots["current-release"] / "version.txt"

  def replace_inode():
    replacement = version.with_name("replacement.tmp")
    replacement.write_bytes(version.read_bytes())
    os.replace(replacement, version)

  faults = PinningFaults(action_at={"entry_before_open:version.txt": replace_inode})
  before = _fd_count()
  with pytest.raises(PinningError, match="inode changed"):
    ReadOnlyFdVerifier(f5.app, f5.policy, faults=faults).pin(f5.ids["current-release"])
  assert _fd_count() == before


@pytest.mark.SIMULATED_TEST_TRUST
def test_path_replacement_after_pin_cannot_retarget_pinned_launcher(f5):
  launcher = _current_launcher(f5)
  original = launcher.read_bytes()
  with ReadOnlyFdVerifier(f5.app, f5.policy).pin(f5.ids["current-release"]) as pinned:
    pinned_inode = os.fstat(pinned.fileno()).st_ino
    replacement = launcher.with_name("forged-launcher.tmp")
    replacement.write_bytes(b"X" * len(original))
    replacement.chmod(0o755)
    os.replace(replacement, launcher)
    assert os.lstat(launcher).st_ino != pinned_inode
    assert pinned.read_file() == original
    pinned.revalidate()


@pytest.mark.SIMULATED_TEST_TRUST
def test_same_size_hash_mismatch_is_rejected(f5):
  version = f5.app / "slots" / f5.slots["current-release"] / "version.txt"
  version.write_bytes(b"X" * len(version.read_bytes()))
  with pytest.raises(PinningError, match="hash mismatch"):
    ReadOnlyFdVerifier(f5.app, f5.policy).pin(f5.ids["current-release"])


@pytest.mark.SIMULATED_TEST_TRUST
def test_in_place_mutation_of_pinned_inode_is_detected_but_not_prevented(f5):
  verifier = ReadOnlyFdVerifier(f5.app, f5.policy)
  with verifier.pin(f5.ids["current-release"]) as pinned:
    launcher = _current_launcher(f5)
    original = launcher.read_bytes()
    with launcher.open("r+b") as stream:
      stream.write(b"Z" * len(original))
      stream.flush()
      os.fsync(stream.fileno())
    with pytest.raises(PinningError, match="pinned inode changed|pinned content hash changed"):
      pinned.revalidate()


@pytest.mark.SIMULATED_TEST_TRUST
def test_replayed_older_signed_release_is_rejected_by_current_protected_floor(f5):
  with pytest.raises(PinningError, match="below protected minimum"):
    ReadOnlyFdVerifier(f5.app, f5.policy).pin(f5.ids["old-release"])


@pytest.mark.SIMULATED_TEST_TRUST
def test_exact_candidate_identity_blocks_other_valid_signed_slot(f5):
  old = f5.ids["old-release"]
  forged_expectation = replace(
    f5.ids["current-release"],
    slot_id=old.slot_id,
    release_sequence=11,
  )
  with pytest.raises(PinningError, match="exact protected candidate"):
    ReadOnlyFdVerifier(f5.app, f5.policy).pin(forged_expectation)


@pytest.mark.SIMULATED_TEST_TRUST
def test_bad_signature_fails_before_any_descriptor_set_is_returned(f5):
  directory = f5.app / "slots" / f5.slots["current-release"]
  signature_path = directory / sv.SIGNATURE_NAME
  signature = json.loads(signature_path.read_bytes())
  signature["signature"] = base64.b64encode(b"x" * 64).decode()
  signature_bytes = gm.canonical(signature)
  signature_path.write_bytes(signature_bytes)
  seal_path = directory / sv.SEAL_NAME
  seal = json.loads(seal_path.read_bytes())
  seal["signature_sha256"] = hashlib.sha256(signature_bytes).hexdigest()
  seal_path.write_bytes(gm.canonical(seal))
  with pytest.raises(PinningError, match="signature is not trusted"):
    ReadOnlyFdVerifier(f5.app, f5.policy).pin(f5.ids["current-release"])


@pytest.mark.SIMULATED_TEST_TRUST
@pytest.mark.parametrize("point", ["root_opened", "signature_verified", "entry_opened:version.txt", "before_return"])
def test_injected_crash_closes_every_owned_descriptor(f5, point):
  before = _fd_count()
  faults = PinningFaults(crash_at=point)
  with pytest.raises(PinningCrash):
    ReadOnlyFdVerifier(f5.app, f5.policy, faults=faults).pin(f5.ids["current-release"])
  assert point in faults.points_seen
  assert _fd_count() == before


@pytest.mark.SIMULATED_TEST_TRUST
@pytest.mark.parametrize("number", [errno.EIO, errno.EMFILE, errno.ENOSPC])
def test_injected_oserror_closes_every_owned_descriptor(f5, number):
  before = _fd_count()
  faults = PinningFaults(oserror_at={"entry_before_open:version.txt": number})
  with pytest.raises(OSError) as raised:
    ReadOnlyFdVerifier(f5.app, f5.policy, faults=faults).pin(f5.ids["current-release"])
  assert raised.value.errno == number
  assert _fd_count() == before


@pytest.mark.SIMULATED_TEST_TRUST
def test_context_exception_and_repeated_close_release_resources(f5):
  before = _fd_count()
  pinned = ReadOnlyFdVerifier(f5.app, f5.policy).pin(f5.ids["current-release"])
  assert _fd_count() > before
  with pytest.raises(RuntimeError, match="consumer failed"):
    with pinned:
      raise RuntimeError("consumer failed")
  pinned.close()
  assert pinned.closed is True
  assert _fd_count() == before


@pytest.mark.SIMULATED_TEST_TRUST
def test_unexpected_hook_error_is_fail_closed_and_leak_free(f5):
  before = _fd_count()

  def fail_unexpectedly():
    raise ValueError("hostile callback")

  faults = PinningFaults(action_at={"signature_verified": fail_unexpectedly})
  with pytest.raises(PinningError, match="unexpected pinning failure"):
    ReadOnlyFdVerifier(f5.app, f5.policy, faults=faults).pin(f5.ids["current-release"])
  assert _fd_count() == before

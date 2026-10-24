#!/usr/bin/env python3
"""OFFLINE, NON-DEPLOYABLE read-only descriptor verification reference.

This module never executes a descriptor or pathname.  It opens a sealed F1 slot
relative to pinned directory descriptors, verifies its canonical Ed25519-signed
manifest against an exact F4 ``CandidateIdentity`` and policy snapshot, and
retains read-only, non-inheritable descriptors for regular manifest files.

The implementation is a host experiment, not an immutable filesystem or a
trusted boot component.  A pinned descriptor survives pathname replacement,
but it does not stop another writer from modifying the same inode.  Filesystem
lookup/enumeration is not an atomic snapshot.  Production still requires a
separate hardware/OS-rooted authority plus immutable or verified storage.
"""
from __future__ import annotations

import copy
import errno
import fnmatch
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from typing import Callable

import g8_manifest as gm
import g8_slot_supervisor as sv
from g8_protected_authority import AuthorityError, CandidateIdentity, PolicySnapshot


MAX_PINNED_FILES = 4096
_READ_FLAGS = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | \
              getattr(os, "O_NONBLOCK", 0)
_DIR_FLAGS = _READ_FLAGS | getattr(os, "O_DIRECTORY", 0)


class PinningError(Exception):
  """Fail-closed verification error; no descriptor set is authorized."""


class PinningCrash(BaseException):
  """Deterministic host-only process-death injection."""


class PinningFaults:
  """Named crash, errno and mutation hooks for disposable-host tests."""

  def __init__(self, crash_at: str | None = None, oserror_at: dict[str, int] | None = None,
               action_at: dict[str, Callable[[], None]] | None = None):
    self.crash_at = crash_at
    self.oserror_at = dict(oserror_at or {})
    self.action_at = dict(action_at or {})
    self.points_seen: list[str] = []

  def hit(self, point: str) -> None:
    self.points_seen.append(point)
    action = self.action_at.get(point)
    if action is not None:
      action()
    if point in self.oserror_at:
      number = self.oserror_at[point]
      raise OSError(number, os.strerror(number), point)
    if point == self.crash_at:
      raise PinningCrash(point)


@dataclass(frozen=True)
class _Fingerprint:
  device: int
  inode: int
  mode: int
  size: int
  mtime_ns: int
  ctime_ns: int

  @classmethod
  def from_stat(cls, value: os.stat_result) -> "_Fingerprint":
    return cls(value.st_dev, value.st_ino, value.st_mode, value.st_size,
               value.st_mtime_ns, value.st_ctime_ns)


def _close_all(descriptors: list[int]) -> None:
  first_error = None
  while descriptors:
    descriptor = descriptors.pop()
    try:
      os.close(descriptor)
    except OSError as error:
      if error.errno != errno.EBADF and first_error is None:
        first_error = error
  if first_error is not None:
    raise first_error


def _sha256_fd(descriptor: int, size: int) -> str:
  digest = hashlib.sha256()
  offset = 0
  while offset < size:
    chunk = os.pread(descriptor, min(1 << 20, size - offset), offset)
    if not chunk:
      raise PinningError("regular file became short while hashing")
    digest.update(chunk)
    offset += len(chunk)
  if os.pread(descriptor, 1, size):
    raise PinningError("regular file grew while hashing")
  return digest.hexdigest()


def _read_bounded_fd(descriptor: int, limit: int) -> bytes:
  data = bytearray()
  offset = 0
  while len(data) <= limit:
    chunk = os.pread(descriptor, min(1 << 20, limit + 1 - len(data)), offset)
    if not chunk:
      break
    data.extend(chunk)
    offset += len(chunk)
  if len(data) > limit:
    raise PinningError("metadata exceeds the bounded read limit")
  return bytes(data)


def _elf_machine_fd(descriptor: int) -> str | None:
  header = os.pread(descriptor, 20, 0)
  if len(header) < 20 or header[:4] != b"\x7fELF":
    return None
  if header[5] not in (1, 2):
    return "MALFORMED_ENDIAN"
  order = "little" if header[5] == 1 else "big"
  machine = int.from_bytes(header[18:20], order)
  return gm.EM_NAMES.get(machine, f"EM_{machine}")


def _parts(path: str) -> tuple[str, ...]:
  if not gm._safe_rel(path):
    raise PinningError(f"manifest path is unsafe: {path!r}")
  parts = tuple(path.split("/"))
  if any(not part or part in (".", "..") for part in parts):
    raise PinningError(f"manifest path is unsafe: {path!r}")
  return parts


class PinnedRelease:
  """Owned verified descriptors.  The object has no execution primitive.

  ``fileno`` returns a borrowed descriptor owned by this object.  Callers must
  not close it.  Use this object as a context manager and call ``revalidate``
  immediately before any read-only consumer action.  Even revalidation cannot
  make a mutable inode immutable or close a post-check race.
  """

  def __init__(self, candidate: CandidateIdentity, generation: int, epoch: int,
               file_descriptors: dict[str, int], fingerprints: dict[str, _Fingerprint],
               expected_hashes: dict[str, str], owned_descriptors: list[int]):
    self.candidate = candidate
    self.policy_generation = generation
    self.policy_epoch = epoch
    self.executed = False
    self._files = file_descriptors
    self._fingerprints = fingerprints
    self._hashes = expected_hashes
    self._owned = owned_descriptors
    self._closed = False

  @property
  def closed(self) -> bool:
    return self._closed

  @property
  def descriptor_count(self) -> int:
    return 0 if self._closed else len(self._owned)

  def fileno(self, relative_path: str = sv.LAUNCHER) -> int:
    if self._closed:
      raise PinningError("pinned release is closed")
    try:
      return self._files[relative_path]
    except KeyError as error:
      raise PinningError(f"no pinned regular file: {relative_path!r}") from error

  def read_file(self, relative_path: str = sv.LAUNCHER) -> bytes:
    descriptor = self.fileno(relative_path)
    current = os.fstat(descriptor)
    expected = self._fingerprints[relative_path]
    if ((current.st_dev, current.st_ino, current.st_mode, current.st_size) !=
        (expected.device, expected.inode, expected.mode, expected.size)):
      raise PinningError(f"pinned inode changed: {relative_path}")
    data = _read_bounded_fd(descriptor, expected.size)
    if hashlib.sha256(data).hexdigest() != self._hashes[relative_path]:
      raise PinningError(f"pinned content hash changed: {relative_path}")
    return data

  def revalidate(self) -> None:
    if self._closed:
      raise PinningError("pinned release is closed")
    for path in sorted(self._files):
      descriptor = self._files[path]
      current = os.fstat(descriptor)
      expected = self._fingerprints[path]
      if ((current.st_dev, current.st_ino, current.st_mode, current.st_size) !=
          (expected.device, expected.inode, expected.mode, expected.size)):
        raise PinningError(f"pinned inode changed: {path}")
      if _sha256_fd(descriptor, current.st_size) != self._hashes[path]:
        raise PinningError(f"pinned content hash changed: {path}")

  def close(self) -> None:
    if self._closed:
      return
    self._closed = True
    _close_all(self._owned)
    self._files.clear()

  def __enter__(self) -> "PinnedRelease":
    if self._closed:
      raise PinningError("pinned release is closed")
    return self

  def __exit__(self, *_exc: object) -> bool:
    self.close()
    return False

  def __del__(self) -> None:
    try:
      self.close()
    except Exception:
      pass


class ReadOnlyFdVerifier:
  """Verify and pin one exact authority-selected F1 slot without execution."""

  def __init__(self, app_root: str | os.PathLike[str], policy: PolicySnapshot,
               *, faults: PinningFaults | None = None):
    if type(policy) is not PolicySnapshot:
      raise PinningError("F5 host reference requires an exact policy snapshot")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "pread"):
      raise PinningError("platform lacks required descriptor-relative safety primitives")
    self.app_root = os.path.abspath(os.fspath(app_root))
    self.policy = copy.deepcopy(policy)
    self.faults = faults or PinningFaults()

  @staticmethod
  def _open_verified(parent: int, name: str, flags: int, expected_kind: str,
                     faults: PinningFaults, point: str) -> tuple[int, _Fingerprint]:
    before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    faults.hit(point)
    descriptor = os.open(name, flags, dir_fd=parent)
    try:
      after = os.fstat(descriptor)
      before_fp = _Fingerprint.from_stat(before)
      after_fp = _Fingerprint.from_stat(after)
      if before_fp != after_fp:
        raise PinningError(f"inode changed while opening {name!r}")
      is_expected = stat.S_ISDIR(after.st_mode) if expected_kind == "dir" else stat.S_ISREG(after.st_mode)
      if not is_expected:
        raise PinningError(f"expected {expected_kind} while opening {name!r}")
      if os.get_inheritable(descriptor):
        os.set_inheritable(descriptor, False)
      return descriptor, after_fp
    except BaseException:
      os.close(descriptor)
      raise

  def _read_metadata(self, slot_fd: int, name: str, owned: list[int]) -> tuple[int, bytes, _Fingerprint]:
    descriptor, fingerprint = self._open_verified(
      slot_fd, name, _READ_FLAGS, "file", self.faults, f"metadata_before_open:{name}")
    owned.append(descriptor)
    if fingerprint.size > sv.MAX_METADATA_BYTES:
      raise PinningError(f"metadata is too large: {name}")
    self.faults.hit(f"metadata_opened:{name}")
    data = _read_bounded_fd(descriptor, sv.MAX_METADATA_BYTES)
    if _Fingerprint.from_stat(os.fstat(descriptor)) != fingerprint:
      raise PinningError(f"metadata changed while reading: {name}")
    return descriptor, data, fingerprint

  def pin(self, candidate: CandidateIdentity) -> PinnedRelease:
    """Return a read-only descriptor set or fail with every opened FD closed."""
    owned: list[int] = []
    file_descriptors: dict[str, int] = {}
    fingerprints: dict[str, _Fingerprint] = {}
    expected_hashes: dict[str, str] = {}
    try:
      try:
        candidate.validate()
      except AuthorityError as error:
        raise PinningError(f"candidate identity is malformed: {error}") from error
      if candidate.source_commit != self.policy.expected_commit:
        raise PinningError("candidate source commit does not match protected policy")
      if candidate.release_sequence < self.policy.minimum_release_sequence:
        raise PinningError("candidate release sequence is below protected minimum")

      self.faults.hit("root_before_open")
      root_fd = os.open(self.app_root, _DIR_FLAGS)
      owned.append(root_fd)
      self.faults.hit("root_opened")
      slots_fd, _ = self._open_verified(root_fd, "slots", _DIR_FLAGS, "dir", self.faults,
                                         "slots_before_open")
      owned.append(slots_fd)
      slot_fd, _ = self._open_verified(slots_fd, candidate.slot_id, _DIR_FLAGS, "dir", self.faults,
                                       "slot_before_open")
      owned.append(slot_fd)

      _, manifest_bytes, _ = self._read_metadata(slot_fd, sv.MANIFEST_NAME, owned)
      _, signature_bytes, _ = self._read_metadata(slot_fd, sv.SIGNATURE_NAME, owned)
      _, seal_bytes, _ = self._read_metadata(slot_fd, sv.SEAL_NAME, owned)
      try:
        manifest = json.loads(manifest_bytes)
        signature = json.loads(signature_bytes)
        seal = json.loads(seal_bytes)
      except (UnicodeDecodeError, ValueError, TypeError) as error:
        raise PinningError("slot metadata is malformed JSON") from error
      if gm.canonical(manifest) != manifest_bytes:
        raise PinningError("manifest is not canonical")
      if gm.canonical(signature) != signature_bytes or gm.canonical(seal) != seal_bytes:
        raise PinningError("signature or seal metadata is not canonical")
      manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
      expected_seal = {
        "schema": "c7-g8-slotseal/1",
        "slot": candidate.slot_id,
        "manifest_sha256": manifest_hash,
        "signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
      }
      if seal != expected_seal or candidate.slot_id[7:] != manifest_hash[:12]:
        raise PinningError("slot seal, metadata, and slot identity do not match")
      try:
        trust = {"trusted_keys": [dict(item) for item in self.policy.signing_keys]}
        gm.verify_signature(manifest, signature, trust, allow_dev=False)
      except Exception as error:
        raise PinningError(f"manifest signature is not trusted: {error}") from error
      self.faults.hit("signature_verified")

      actual = CandidateIdentity(
        slot_id=candidate.slot_id,
        manifest_sha256=manifest_hash,
        source_commit=manifest.get("source_commit"),
        release_sequence=manifest.get("release_sequence"),
        signing_key_id=signature.get("key_id"),
      )
      try:
        actual.validate()
      except AuthorityError as error:
        raise PinningError(f"signed manifest identity is malformed: {error}") from error
      if actual != candidate:
        raise PinningError("signed manifest does not match exact protected candidate identity")
      if actual.source_commit != self.policy.expected_commit:
        raise PinningError("signed source commit does not match protected policy")
      if actual.release_sequence < self.policy.minimum_release_sequence:
        raise PinningError("signed release sequence is below protected minimum")

      structure = gm.check_manifest_structure(manifest)
      if structure:
        raise PinningError(f"signed manifest structure is invalid: {structure[:3]}")
      entries = manifest.get("entries")
      if not isinstance(entries, list) or len(entries) > MAX_PINNED_FILES:
        raise PinningError("signed manifest has an unsupported entry count")
      by_path = {entry["path"]: entry for entry in entries}
      if len(by_path) != len(entries) or set(by_path) & sv.METADATA_NAMES:
        raise PinningError("signed manifest has duplicate or reserved paths")

      directories: dict[tuple[str, ...], int] = {(): slot_fd}
      expected_children: dict[tuple[str, ...], set[str]] = {(): set(sv.METADATA_NAMES)}
      for path in by_path:
        parts = _parts(path)
        expected_children.setdefault(parts[:-1], set()).add(parts[-1])
        if by_path[path].get("type") == "dir":
          expected_children.setdefault(parts, set())

      for path in sorted(by_path, key=lambda item: (len(_parts(item)), item)):
        entry = by_path[path]
        parts = _parts(path)
        parent = directories.get(parts[:-1])
        if parent is None:
          raise PinningError(f"manifest parent directory is missing: {path}")
        kind = entry.get("type")
        if kind == "dir":
          descriptor, fingerprint = self._open_verified(
            parent, parts[-1], _DIR_FLAGS, "dir", self.faults, f"entry_before_open:{path}")
          owned.append(descriptor)
          directories[parts] = descriptor
          if format(stat.S_IMODE(fingerprint.mode), "04o") != entry.get("mode"):
            raise PinningError(f"directory mode mismatch: {path}")
        elif kind == "file":
          descriptor, fingerprint = self._open_verified(
            parent, parts[-1], _READ_FLAGS, "file", self.faults, f"entry_before_open:{path}")
          owned.append(descriptor)
          file_descriptors[path] = descriptor
          fingerprints[path] = fingerprint
          expected_hashes[path] = entry.get("sha256")
          self.faults.hit(f"entry_opened:{path}")
          if (format(stat.S_IMODE(fingerprint.mode), "04o") != entry.get("mode") or
              fingerprint.size != entry.get("size")):
            raise PinningError(f"regular file metadata mismatch: {path}")
          if _sha256_fd(descriptor, fingerprint.size) != entry.get("sha256"):
            raise PinningError(f"regular file hash mismatch: {path}")
          machine = _elf_machine_fd(descriptor)
          if machine != entry.get("elf_machine"):
            raise PinningError(f"ELF machine mismatch: {path}")
          foreign = manifest.get("foreign_elf_allow", {})
          if (machine and machine != manifest.get("target_machine") and
              not any(fnmatch.fnmatch(path, pattern) for pattern in foreign)):
            raise PinningError(f"foreign ELF architecture is not allowed: {path}")
          if _Fingerprint.from_stat(os.fstat(descriptor)) != fingerprint:
            raise PinningError(f"regular file changed while hashing: {path}")
        elif kind == "symlink":
          before = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
          self.faults.hit(f"symlink_before_read:{path}")
          if not stat.S_ISLNK(before.st_mode):
            raise PinningError(f"expected symlink: {path}")
          target = os.readlink(parts[-1], dir_fd=parent)
          after = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
          if _Fingerprint.from_stat(before) != _Fingerprint.from_stat(after):
            raise PinningError(f"symlink changed while reading: {path}")
          if target != entry.get("target") or gm._link_escapes(self.app_root, path, target):
            raise PinningError(f"symlink target mismatch or escape: {path}")
          try:
            os.stat(parts[-1], dir_fd=parent)
          except OSError:
            if path not in manifest.get("dangling_symlink_allow", {}):
              raise PinningError(f"dangling symlink is not allowed: {path}")
        else:
          raise PinningError(f"unsupported manifest entry type: {path}")

      for parts, descriptor in sorted(directories.items()):
        label = "/".join(parts) or "."
        self.faults.hit(f"directory_before_enumerate:{label}")
        if set(os.listdir(descriptor)) != expected_children.get(parts, set()):
          raise PinningError(f"directory membership mismatch: {label}")

      if sv.LAUNCHER not in file_descriptors:
        raise PinningError("signed manifest does not pin a regular launcher")
      launcher_mode = fingerprints[sv.LAUNCHER].mode
      if not stat.S_IMODE(launcher_mode) & 0o111:
        raise PinningError("pinned launcher is not executable in the signed mode")

      self.faults.hit("before_final_revalidation")
      for path, descriptor in sorted(file_descriptors.items()):
        fingerprint = fingerprints[path]
        if (_Fingerprint.from_stat(os.fstat(descriptor)) != fingerprint or
            _sha256_fd(descriptor, fingerprint.size) != expected_hashes[path]):
          raise PinningError(f"regular file changed before return: {path}")
      self.faults.hit("before_return")
      return PinnedRelease(
        candidate, self.policy.generation, self.policy.epoch,
        file_descriptors, fingerprints, expected_hashes, owned,
      )
    except BaseException as error:
      try:
        _close_all(owned)
      except OSError as cleanup_error:
        raise PinningError(f"descriptor cleanup failed: {cleanup_error}") from error
      if isinstance(error, (PinningError, PinningCrash, OSError)):
        raise
      raise PinningError(f"unexpected pinning failure: {error!r}") from error

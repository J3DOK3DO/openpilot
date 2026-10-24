#!/usr/bin/env python3
"""C7 G8 slot supervisor: host-only security and fault-injection reference.

Every slot decision is authorized from caller-pinned policy, never from mutable
``state.json``: an Ed25519 manifest signature must chain to ``trust`` with
production purpose, ``source_commit`` must equal ``expected_commit``, and an
optional signed ``release_sequence`` must meet ``minimum_release_sequence``.
The signature is persisted beside each slot and rechecked with a full tree hash
before activation, recovery, rollback, confirmation, or returning a launcher.

This is not deployed or integrated with AGNOS. The supervisor must run outside
the replaceable tree. Tests model process death at syscall boundaries, not block
device power loss, hostile concurrent filesystem mutation, or secure key-store
and early-boot integration.
"""
import copy
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g8_manifest as gm  # noqa: E402

LAUNCHER = "launch_chffrplus.sh"
MANIFEST_NAME = ".g8_manifest.json"
SIGNATURE_NAME = ".g8_signature.json"
SEAL_NAME = ".g8_sealed"
METADATA_NAMES = frozenset({MANIFEST_NAME, SIGNATURE_NAME, SEAL_NAME})
SLOT_RE = re.compile(r"^[0-9]{6}-[0-9a-f]{12}$")
MAX_METADATA_BYTES = 16 << 20


class SimulatedCrash(BaseException):
  """Models abrupt process death at a named point."""


class LockBusy(Exception):
  pass


class InsufficientSpace(Exception):
  pass


class SlotInvalid(Exception):
  pass


class Faults:
  def __init__(self, crash_at=None, oserror_at=None):
    self.crash_at = crash_at
    self.oserror_at = oserror_at or {}
    self.points_seen = []

  def hit(self, name):
    self.points_seen.append(name)
    if name in self.oserror_at:
      e = self.oserror_at[name]
      raise OSError(e, os.strerror(e), name)
    if self.crash_at == name:
      raise SimulatedCrash(name)


def _fsync_dir(path):
  fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
  try:
    os.fsync(fd)
  finally:
    os.close(fd)


def _atomic_write(path, data: bytes, faults):
  tmp = path + ".tmp"
  with open(tmp, "wb") as f:
    f.write(data)
    f.flush()
    os.fsync(f.fileno())
  faults.hit("state_tmp_written")
  os.replace(tmp, path)
  _fsync_dir(os.path.dirname(path))


class Supervisor:
  def __init__(self, base, faults=None, max_boot_attempts=3, min_free_bytes=0, keep_slots=3,
               trust=None, expected_commit=None, minimum_release_sequence=None):
    self.base = os.path.abspath(base)
    self.f = faults or Faults()
    self.max_attempts = max_boot_attempts
    self.min_free = min_free_bytes
    self.keep = keep_slots
    # Snapshot policy so mutation of a caller-owned dictionary cannot silently
    # change decisions made by this supervisor instance.
    self._trust = copy.deepcopy(trust)
    self._expected_commit = expected_commit
    self._minimum_release_sequence = minimum_release_sequence
    for d in ("slots", "staging"):
      os.makedirs(os.path.join(self.base, d), exist_ok=True)
    self._lock_fd = None
    self._copy_errno = None

  def p(self, *a):
    return os.path.join(self.base, *a)

  def _require_policy(self):
    keys = self._trust.get("trusted_keys") if isinstance(self._trust, dict) else None
    if not isinstance(keys, list) or not keys:
      raise SlotInvalid("trusted production-key policy is not configured")
    if not isinstance(self._expected_commit, str) or not self._expected_commit:
      raise SlotInvalid("expected source commit is not configured")
    minimum = self._minimum_release_sequence
    if minimum is not None and (isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0):
      raise SlotInvalid("minimum release sequence policy is malformed")

  @staticmethod
  def _valid_sid(sid):
    return isinstance(sid, str) and SLOT_RE.fullmatch(sid) is not None

  @classmethod
  def _require_sid(cls, sid):
    if not cls._valid_sid(sid):
      raise SlotInvalid(f"malformed slot id: {sid!r}")

  @classmethod
  def _slot_sequence(cls, sid):
    cls._require_sid(sid)
    return int(sid[:6])

  def _authorize_manifest(self, manifest, signature):
    self._require_policy()
    try:
      gm.verify_signature(manifest, signature, self._trust, allow_dev=False)
    except Exception as e:
      raise SlotInvalid(f"manifest signature is not trusted: {e}") from e
    if manifest.get("source_commit") != self._expected_commit:
      raise SlotInvalid("source commit does not match pinned policy")
    minimum = self._minimum_release_sequence
    if minimum is not None:
      sequence = manifest.get("release_sequence")
      if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < minimum:
        raise SlotInvalid("release sequence is missing, malformed, or below pinned minimum")

  def __enter__(self):
    fd = os.open(self.p("lock"), os.O_RDWR | os.O_CREAT, 0o600)
    try:
      fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
      os.close(fd)
      raise LockBusy(self.base)
    self._lock_fd = fd
    return self

  def __exit__(self, *exc):
    if self._lock_fd is not None:
      os.close(self._lock_fd)
      self._lock_fd = None
    return False

  # Append-only diagnostics; never an authorization source.
  def journal(self, event, **kw):
    rec = json.dumps({"ev": event, **kw}, sort_keys=True)
    line = f"{zlib.crc32(rec.encode()):08x} {rec}\n"
    fd = os.open(self.p("journal.log"), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
      os.write(fd, line.encode())
      os.fsync(fd)
    finally:
      os.close(fd)

  def read_journal(self):
    out = []
    try:
      with open(self.p("journal.log"), "rb") as f:
        for raw in f.read().split(b"\n"):
          try:
            crc, rec = raw.decode().split(" ", 1)
            if int(crc, 16) == zlib.crc32(rec.encode()):
              obj = json.loads(rec)
              if isinstance(obj, dict):
                out.append(obj)
          except (ValueError, UnicodeDecodeError):
            continue
    except OSError:
      pass
    return out

  # Mutable availability state, explicitly not a release authorization anchor.
  @classmethod
  def _state_valid(cls, state):
    if not isinstance(state, dict) or set(state) != {"schema", "seq", "last_good", "pending"}:
      return False
    if state.get("schema") != "c7-g8-slotstate/1":
      return False
    sequence = state.get("seq")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence <= 999999:
      return False
    if state.get("last_good") is not None and not cls._valid_sid(state["last_good"]):
      return False
    pending = state.get("pending")
    if pending is None:
      return True
    if not isinstance(pending, dict) or set(pending) != {"slot", "from", "attempts_left"}:
      return False
    attempts = pending.get("attempts_left")
    return (cls._valid_sid(pending.get("slot")) and
            (pending.get("from") is None or cls._valid_sid(pending.get("from"))) and
            isinstance(attempts, int) and not isinstance(attempts, bool) and 0 <= attempts <= 1000000)

  def load_state(self):
    try:
      with open(self.p("state.json"), encoding="utf-8") as f:
        state = json.load(f)
      return state if self._state_valid(state) else None
    except (OSError, ValueError, TypeError):
      return None

  def save_state(self, state):
    if not self._state_valid(state):
      raise SlotInvalid("refusing to persist malformed state")
    _atomic_write(self.p("state.json"), json.dumps(state, sort_keys=True).encode(), self.f)

  @staticmethod
  def new_state():
    return {"schema": "c7-g8-slotstate/1", "seq": 0, "last_good": None, "pending": None}

  # Slot verification.
  def slot_dir(self, sid):
    self._require_sid(sid)
    return self.p("slots", sid)

  @staticmethod
  def _read_regular(path):
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_METADATA_BYTES:
      raise SlotInvalid(f"metadata is not a bounded regular file: {os.path.basename(path)}")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
      opened = os.fstat(fd)
      if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
        raise SlotInvalid(f"metadata changed while opening: {os.path.basename(path)}")
      data = bytearray()
      while len(data) <= MAX_METADATA_BYTES:
        chunk = os.read(fd, min(1 << 20, MAX_METADATA_BYTES + 1 - len(data)))
        if not chunk:
          break
        data.extend(chunk)
      if len(data) > MAX_METADATA_BYTES:
        raise SlotInvalid(f"metadata too large: {os.path.basename(path)}")
      return bytes(data)
    finally:
      os.close(fd)

  def verify_slot(self, sid, deep=True):
    self._require_policy()
    self._require_sid(sid)
    directory = self.slot_dir(sid)
    try:
      if not stat.S_ISDIR(os.lstat(directory).st_mode):
        raise SlotInvalid(f"{sid}: not a real directory")
      manifest_bytes = self._read_regular(os.path.join(directory, MANIFEST_NAME))
      signature_bytes = self._read_regular(os.path.join(directory, SIGNATURE_NAME))
      seal_bytes = self._read_regular(os.path.join(directory, SEAL_NAME))
      manifest = json.loads(manifest_bytes)
      signature = json.loads(signature_bytes)
      seal = json.loads(seal_bytes)
      manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
      expected_seal = {
        "schema": "c7-g8-slotseal/1", "slot": sid,
        "manifest_sha256": manifest_hash,
        "signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
      }
      if seal != expected_seal or sid[7:] != manifest_hash[:12]:
        raise SlotInvalid(f"{sid}: seal/metadata/slot mismatch")
      self._authorize_manifest(manifest, signature)
      # Security invariant: caller-supplied deep=False must NEVER bypass file hashes.
      # A same-size launcher modification must be rejected even during recovery.
      findings = gm.verify_tree_ignoring(directory, manifest, METADATA_NAMES, deep=True)
      if findings:
        raise SlotInvalid(f"{sid}: {findings[:3]}")
      launcher = os.path.join(directory, LAUNCHER)
      launcher_stat = os.lstat(launcher)
      if not stat.S_ISREG(launcher_stat.st_mode) or not (stat.S_IMODE(launcher_stat.st_mode) & 0o111):
        raise SlotInvalid(f"{sid}: launcher missing, linked, or not executable")
      return manifest
    except SlotInvalid:
      raise
    except (OSError, ValueError, KeyError, TypeError) as e:
      raise SlotInvalid(f"{sid}: {e!r}") from e

  def slot_ok(self, sid, deep=True):
    try:
      self.verify_slot(sid, deep=deep)
      return True
    except SlotInvalid:
      return False

  def live_slot(self):
    try:
      target = os.readlink(self.p("live"))
    except OSError:
      return None
    prefix = "slots/"
    sid = target[len(prefix):] if target.startswith(prefix) else None
    return sid if self._valid_sid(sid) and target == prefix + sid else None

  def sealed_slots(self):
    try:
      names = [entry.name for entry in os.scandir(self.p("slots")) if self._valid_sid(entry.name)]
    except OSError:
      return []
    return sorted(names, key=self._slot_sequence)

  def _switch_live(self, sid):
    self.verify_slot(sid, deep=True)
    temporary = self.p(f"live.tmp.{os.getpid()}")
    try:
      os.unlink(temporary)
    except FileNotFoundError:
      pass
    os.symlink(os.path.join("slots", sid), temporary)
    self.f.hit("before_switch_rename")
    os.replace(temporary, self.p("live"))
    self.f.hit("after_switch_rename")
    _fsync_dir(self.base)

  def stage(self, src, manifest, expected_commit=None, signature=None):
    """Copy and seal a package only after trusted signature and identity checks."""
    self._require_policy()
    if expected_commit is not None and expected_commit != self._expected_commit:
      raise SlotInvalid("stage commit pin differs from supervisor policy")
    self._authorize_manifest(manifest, signature)
    findings = gm.verify_tree(src, manifest, expected_commit=self._expected_commit, deep=True)
    if findings:
      raise SlotInvalid(f"source package failed verification: {findings[:3]}")
    need = sum(entry["size"] for entry in manifest["entries"] if entry["type"] == "file")
    fs = os.statvfs(self.base)
    available = fs.f_bavail * fs.f_frsize
    if available < need * 1.05 + self.min_free:
      raise InsufficientSpace(f"need {need} + reserve {self.min_free}, have {available}")
    manifest_bytes = gm.canonical(manifest)
    signature_bytes = gm.canonical(signature)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    next_sequence = max([self._slot_sequence(n) for n in self.sealed_slots()] + [0]) + 1
    if next_sequence > 999999:
      raise SlotInvalid("slot sequence exhausted")
    sid = f"{next_sequence:06d}-{manifest_hash[:12]}"
    temporary = self.p("staging", f"{sid}.{os.getpid()}")
    final = self.slot_dir(sid)
    self.journal("stage_begin", slot=sid)
    try:
      if os.path.lexists(final):
        raise SlotInvalid("slot id exists")
      shutil.copytree(src, temporary, symlinks=True, copy_function=self._copy)
      for name, data in ((MANIFEST_NAME, manifest_bytes), (SIGNATURE_NAME, signature_bytes)):
        with open(os.path.join(temporary, name), "wb") as metadata:
          metadata.write(data)
          metadata.flush()
          os.fsync(metadata.fileno())
      self.f.hit("stage_copied")
      findings = gm.verify_tree_ignoring(temporary, manifest, {MANIFEST_NAME, SIGNATURE_NAME}, deep=True)
      if findings:
        raise SlotInvalid(f"staged copy failed verification: {findings[:3]}")
      seal_bytes = gm.canonical({
        "schema": "c7-g8-slotseal/1", "slot": sid,
        "manifest_sha256": manifest_hash,
        "signature_sha256": hashlib.sha256(signature_bytes).hexdigest(),
      })
      with open(os.path.join(temporary, SEAL_NAME), "wb") as seal:
        seal.write(seal_bytes)
        seal.flush()
        os.fsync(seal.fileno())
      for directory, _dirs, _files in os.walk(temporary, followlinks=False):
        _fsync_dir(directory)
      self.f.hit("stage_sealed")
      os.rename(temporary, final)
      _fsync_dir(self.p("slots"))
      self.f.hit("stage_renamed")
    except SimulatedCrash:
      raise
    except BaseException as error:
      try:
        if os.path.lexists(temporary):
          shutil.rmtree(temporary)
      except OSError as cleanup_error:
        self.journal("cleanup_failed", path=os.path.basename(temporary), error=repr(cleanup_error))
      self.journal("stage_failed", slot=sid)
      if isinstance(error, shutil.Error) and self._copy_errno:
        raise OSError(self._copy_errno, os.strerror(self._copy_errno), "stage copy") from error
      raise
    state = self.load_state()
    if state is None:
      if os.path.lexists(self.p("state.json")):
        raise SlotInvalid("state is malformed; recover before staging")
      state = self.new_state()
    state["seq"] = next_sequence
    self.save_state(state)
    self.verify_slot(sid, deep=True)
    self.journal("staged", slot=sid)
    return sid

  def _copy(self, source, destination, *, follow_symlinks=True):
    try:
      self.f.hit("copy_file")
      result = shutil.copy2(source, destination, follow_symlinks=follow_symlinks)
    except OSError as error:
      self._copy_errno = error.errno
      raise
    if not os.path.islink(destination):
      fd = os.open(destination, os.O_RDONLY)
      try:
        os.fsync(fd)
      finally:
        os.close(fd)
    return result

  def activate(self, sid):
    self.verify_slot(sid, deep=True)
    state = self.load_state()
    if state is None:
      raise SlotInvalid("state missing or malformed; recover before activation")
    current = self.live_slot()
    if state["pending"] is not None:
      raise SlotInvalid("previous activation is unconfirmed; confirm or roll back first")
    if current == sid:
      return
    self.journal("activate_intent", frm=current, to=sid)
    state["pending"] = {"slot": sid, "from": current, "attempts_left": self.max_attempts}
    state["last_good"] = state["last_good"] if state["last_good"] else current
    self.save_state(state)
    self.f.hit("after_intent_state")
    self._switch_live(sid)
    self.journal("activated", slot=sid)

  def boot(self):
    """Recover, consume an attempt, deep-verify again, then return a launcher."""
    report = self.recover()
    state = self.load_state()
    if state is None:
      raise SlotInvalid("state unavailable after recovery")
    pending = state["pending"]
    if pending and self.live_slot() == pending["slot"]:
      if pending["attempts_left"] <= 0:
        self._rollback(state, "boot attempts exhausted")
      else:
        pending["attempts_left"] -= 1
        self.save_state(state)
    sid = self.live_slot()
    if sid is None:
      raise SlotInvalid("no bootable slot")
    self.verify_slot(sid, deep=True)
    if self.live_slot() != sid:
      raise SlotInvalid("live slot changed during boot verification")
    return os.path.join(self.p("live"), LAUNCHER), report

  def confirm(self):
    self._require_policy()
    state = self.load_state()
    if state is None:
      raise SlotInvalid("state missing or malformed")
    sid = self.live_slot()
    if sid is None:
      raise SlotInvalid("live slot is malformed")
    self.verify_slot(sid, deep=True)
    pending = state["pending"]
    if pending is None or pending["slot"] != sid:
      raise SlotInvalid("nothing to confirm for live slot")
    state["last_good"], state["pending"] = sid, None
    self.save_state(state)
    self.f.hit("after_confirm_state")
    self.journal("confirmed", slot=sid)
    return self._prune(state)

  def rollback(self, sid=None, why="caller requested rollback"):
    """Manual rollback constrained by signature, identity, and minimum policy."""
    self._require_policy()
    state = self.load_state()
    if state is None:
      raise SlotInvalid("state missing or malformed; recover first")
    if sid is not None:
      self.verify_slot(sid, deep=True)
      target = sid
    else:
      pending = state.get("pending") or {}
      target = self._best_slot([pending.get("from"), state.get("last_good")], {self.live_slot()})
    if target is None:
      raise SlotInvalid("no policy-authorized rollback target")
    self.journal("rollback", to=target, why=why)
    self._switch_live(target)
    state["pending"] = None
    state["last_good"] = target
    self.save_state(state)
    self.f.hit("rollback_state_saved")
    return target

  @staticmethod
  def _remove_entry(path):
    current = os.lstat(path)
    if stat.S_ISLNK(current.st_mode) or not stat.S_ISDIR(current.st_mode):
      os.unlink(path)
    else:
      shutil.rmtree(path)

  def _cleanup(self, path, description, report):
    try:
      self._remove_entry(path)
      report["actions"].append(f"removed {description}")
    except FileNotFoundError:
      return
    except OSError as error:
      message = f"could not remove {description}: {error!r}"
      report["errors"].append(message)
      self.journal("cleanup_failed", path=os.path.basename(path), error=repr(error))

  def _prune(self, state):
    report = {"actions": [], "errors": []}
    keep = {state["last_good"], self.live_slot()}
    spare = [name for name in self.sealed_slots() if name not in keep]
    room = max(0, self.keep - len({name for name in keep if name}))
    victims = spare[:len(spare) - room] if room else spare
    for sid in victims:
      self._cleanup(self.slot_dir(sid), f"pruned slot {sid}", report)
    return report

  def _rollback(self, state, why):
    pending = state.get("pending") or {}
    target = self._best_slot([state.get("last_good"), pending.get("from")], {pending.get("slot")})
    if target is None:
      raise SlotInvalid("no policy-authorized verified rollback target")
    self.journal("rollback", to=target, why=why)
    self._switch_live(target)
    state["pending"] = None
    state["last_good"] = target
    self.save_state(state)
    self.f.hit("rollback_state_saved")

  def _best_slot(self, prefer, exclude=()):
    seen = set()
    candidates = [item for item in prefer if item] + list(reversed(self.sealed_slots()))
    for sid in candidates:
      if sid in seen or sid in exclude or not self._valid_sid(sid):
        continue
      seen.add(sid)
      if self.slot_ok(sid, deep=True):
        return sid
    return None

  def recover(self):
    """Idempotently recover from supported syscall-boundary crash points."""
    self._require_policy()
    report = {"actions": [], "errors": []}
    try:
      staging = list(os.scandir(self.p("staging")))
    except OSError as error:
      raise SlotInvalid(f"cannot inspect staging: {error!r}") from error
    for entry in staging:
      self._cleanup(entry.path, f"staging {entry.name}", report)
    try:
      base_entries = list(os.scandir(self.base))
    except OSError as error:
      raise SlotInvalid(f"cannot inspect supervisor base: {error!r}") from error
    for entry in base_entries:
      if entry.name.startswith("live.tmp."):
        self._cleanup(entry.path, entry.name, report)
    try:
      slot_entries = list(os.scandir(self.p("slots")))
    except OSError as error:
      raise SlotInvalid(f"cannot inspect slots: {error!r}") from error
    for entry in slot_entries:
      sealed = (self._valid_sid(entry.name) and entry.is_dir(follow_symlinks=False) and
                os.path.isfile(os.path.join(entry.path, SEAL_NAME)))
      if not sealed:
        self._cleanup(entry.path, f"invalid or unsealed slot {entry.name}", report)

    state = self.load_state()
    if state is None:
      state = self.new_state()
      state["seq"] = max([self._slot_sequence(name) for name in self.sealed_slots()] + [0])
      self.save_state(state)
      report["actions"].append("state rebuilt")
      self.journal("state_rebuilt")
    sequences = [self._slot_sequence(name) for name in self.sealed_slots()]
    if sequences and max(sequences) > state["seq"]:
      state["seq"] = max(sequences)
      self.save_state(state)
      report["actions"].append("seq caught up with slots")
    live = self.live_slot()
    pending = state["pending"]
    if pending and live != pending["slot"]:
      state["pending"] = None
      self.save_state(state)
      report["actions"].append("dropped unswitched pending activation")
      pending = None
    live_ok = live is not None and self.slot_ok(live, deep=True)
    if pending is None and state["last_good"] is None and live_ok:
      state["last_good"] = live
      self.save_state(state)
    if not live_ok:
      if pending:
        self._rollback(state, "live slot invalid")
      else:
        target = self._best_slot([state["last_good"]])
        if target is None:
          raise SlotInvalid("no policy-authorized verified slot available for recovery")
        self.journal("recovered_live", to=target)
        state["last_good"] = target
        self.save_state(state)
        self._switch_live(target)
      report["actions"].append("restored live")
    final = self.live_slot()
    if final is None:
      raise SlotInvalid("recovery did not establish a valid live slot")
    self.verify_slot(final, deep=True)
    return report

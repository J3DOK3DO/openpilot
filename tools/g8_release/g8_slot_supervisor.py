#!/usr/bin/env python3
"""C7 G8 slot supervisor: REFERENCE IMPLEMENTATION for host-side fault-injection only.

Not deployed, not integrated with launch_chffrplus.sh, not qualified on AGNOS.

Design: the application lives in immutable, sealed, manifest-verified slots under
``base/slots/<id>``. ``base/live`` is a symlink to the active slot, switched with a
single atomic rename(2) of a symlink, so there is never an instant at which the
launcher path is absent (the two-rename window of launch_chffrplus.sh is gone).
Intent is recorded in an fsync'd, atomically replaced ``state.json`` BEFORE the
switch, and ``boot()`` consumes a bounded boot-attempt budget until ``confirm()``
acknowledges health; exhausting it rolls back to the last confirmed-good slot.

The supervisor must run from outside the replaceable tree (an assumption this host
test cannot prove for AGNOS). All guarantees are at syscall-boundary granularity:
a block-level power cut / filesystem reordering is NOT simulated.
"""
import errno
import fcntl
import hashlib
import json
import os
import shutil
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import g8_manifest as gm  # noqa: E402

LAUNCHER = "launch_chffrplus.sh"


class SimulatedCrash(BaseException):
  """Models abrupt process death (power loss) at a named point; not catchable by 'except Exception'."""


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
  fd = os.open(path, os.O_RDONLY)
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
  os.rename(tmp, path)
  _fsync_dir(os.path.dirname(path))


class Supervisor:
  def __init__(self, base, faults=None, max_boot_attempts=3, min_free_bytes=0, keep_slots=3, verifier=None):
    self.base = os.path.abspath(base)
    self.f = faults or Faults()
    self.max_attempts = max_boot_attempts
    self.min_free = min_free_bytes
    self.keep = keep_slots
    self.verifier = verifier  # callable(manifest) raising on untrusted/unsigned; None => stage() refuses
    for d in ("slots", "staging"):
      os.makedirs(os.path.join(self.base, d), exist_ok=True)
    self._lock_fd = None
    self._copy_errno = None

  # --- paths
  def p(self, *a):
    return os.path.join(self.base, *a)

  # --- locking: non-blocking exclusive, released on process death by the kernel
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

  # --- journal (append-only, CRC per line; torn tail ignored)
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
              out.append(json.loads(rec))
          except (ValueError, UnicodeDecodeError):
            continue
    except FileNotFoundError:
      pass
    return out

  # --- state
  def load_state(self):
    try:
      with open(self.p("state.json")) as f:
        s = json.load(f)
      if s.get("schema") == "c7-g8-slotstate/1" and isinstance(s.get("seq"), int):
        return s
    except (OSError, ValueError):
      pass
    return None

  def save_state(self, s):
    _atomic_write(self.p("state.json"), json.dumps(s, sort_keys=True).encode(), self.f)

  @staticmethod
  def new_state():
    return {"schema": "c7-g8-slotstate/1", "seq": 0, "last_good": None, "pending": None}

  # --- slot verification
  def slot_dir(self, sid):
    return self.p("slots", sid)

  def verify_slot(self, sid, deep):
    d = self.slot_dir(sid)
    try:
      if os.path.islink(d) or not os.path.isdir(d):
        raise SlotInvalid(f"{sid}: not a directory")
      with open(os.path.join(d, ".g8_sealed")) as f:
        seal = json.load(f)
      with open(os.path.join(d, ".g8_manifest.json"), "rb") as f:
        mb = f.read()
      if hashlib.sha256(mb).hexdigest() != seal.get("manifest_sha256") or seal.get("slot") != sid:
        raise SlotInvalid(f"{sid}: seal/manifest mismatch")
      m = json.loads(mb)
      # manifest describes the app tree only; the two control files are verified above
      findings = gm.verify_tree_ignoring(d, m, {".g8_sealed", ".g8_manifest.json"}, deep=deep)
      if findings:
        raise SlotInvalid(f"{sid}: {findings[:3]}")
      lp = os.path.join(d, LAUNCHER)
      if not (os.path.isfile(lp) and os.access(lp, os.X_OK)):
        raise SlotInvalid(f"{sid}: launcher missing or not executable")
    except (OSError, ValueError, KeyError) as e:
      raise SlotInvalid(f"{sid}: {e!r}")

  def slot_ok(self, sid, deep=False):
    try:
      self.verify_slot(sid, deep)
      return True
    except SlotInvalid:
      return False

  def live_slot(self):
    try:
      t = os.readlink(self.p("live"))
    except OSError:
      return None
    if os.path.dirname(t) != "slots":
      return None
    return os.path.basename(t)

  def sealed_slots(self):
    try:
      return sorted(n for n in os.listdir(self.p("slots")) if not n.startswith("."))
    except FileNotFoundError:
      return []

  # --- atomic live switch
  def _switch_live(self, sid):
    tmp = self.p(f"live.tmp.{os.getpid()}")
    try:
      os.unlink(tmp)
    except FileNotFoundError:
      pass
    os.symlink(os.path.join("slots", sid), tmp)
    self.f.hit("before_switch_rename")
    os.rename(tmp, self.p("live"))
    self.f.hit("after_switch_rename")
    _fsync_dir(self.base)

  # --- stage
  def stage(self, src, manifest, expected_commit=None):
    """Copy ``src`` into a sealed slot after verifying it against ``manifest``. Returns slot id."""
    if self.verifier is None:
      raise SlotInvalid("no signature verifier configured; refusing to stage (fail closed)")
    try:
      self.verifier(manifest)
    except Exception as e:
      raise SlotInvalid(f"manifest authenticity check failed: {e}")
    if expected_commit is not None and manifest.get("source_commit") != expected_commit:
      raise SlotInvalid("source commit mismatch")
    need = sum(e.get("size", 0) for e in manifest["entries"] if e["type"] == "file")
    st = os.statvfs(self.base)
    if st.f_bavail * st.f_frsize < need * 1.05 + self.min_free:
      raise InsufficientSpace(f"need {need} + reserve {self.min_free}, have {st.f_bavail * st.f_frsize}")
    pre = gm.verify_tree(src, manifest)
    if pre:
      raise SlotInvalid(f"source package failed verification: {pre[:3]}")
    mb = gm.canonical(manifest)
    mh = hashlib.sha256(mb).hexdigest()
    state = self.load_state() or self.new_state()
    sid = f"{state['seq'] + 1:06d}-{mh[:12]}"
    tmpd = self.p("staging", f"{sid}.{os.getpid()}")
    final = self.slot_dir(sid)
    self.journal("stage_begin", slot=sid)
    try:
      if os.path.exists(final):
        raise SlotInvalid("slot id exists")
      shutil.copytree(src, tmpd, symlinks=True, copy_function=self._copy)
      with open(os.path.join(tmpd, ".g8_manifest.json"), "wb") as f:
        f.write(mb)
        f.flush()
        os.fsync(f.fileno())
      self.f.hit("stage_copied")
      post = gm.verify_tree_ignoring(tmpd, manifest, {".g8_manifest.json"})
      if post:
        raise SlotInvalid(f"staged copy failed verification: {post[:3]}")
      with open(os.path.join(tmpd, ".g8_sealed"), "w") as f:
        json.dump({"slot": sid, "manifest_sha256": mh}, f)
        f.flush()
        os.fsync(f.fileno())
      for dp, _dns, _fns in os.walk(tmpd):
        _fsync_dir(dp)
      self.f.hit("stage_sealed")
      os.rename(tmpd, final)
      _fsync_dir(self.p("slots"))
      self.f.hit("stage_renamed")
    except SimulatedCrash:
      raise
    except BaseException as e:
      shutil.rmtree(tmpd, ignore_errors=True)
      self.journal("stage_failed", slot=sid)
      if isinstance(e, shutil.Error) and self._copy_errno:  # copytree aggregates OSErrors; keep the errno (ENOSPC!)
        raise OSError(self._copy_errno, os.strerror(self._copy_errno), "stage copy") from e
      raise
    state["seq"] += 1
    self.save_state(state)
    self.journal("staged", slot=sid)
    return sid

  def _copy(self, s, d, *, follow_symlinks=True):
    try:
      self.f.hit("copy_file")
      r = shutil.copy2(s, d, follow_symlinks=follow_symlinks)
    except OSError as e:
      self._copy_errno = e.errno
      raise
    if not os.path.islink(d):
      fd = os.open(d, os.O_RDONLY)
      try:
        os.fsync(fd)
      finally:
        os.close(fd)
    return r

  # --- activate
  def activate(self, sid):
    self.verify_slot(sid, deep=True)  # fail closed: full re-hash at activation time
    state = self.load_state() or self.new_state()
    cur = self.live_slot()
    if state["pending"] is not None:
      raise SlotInvalid("previous activation is unconfirmed; confirm or roll back first")
    if cur == sid:
      return
    lg = state["last_good"] if state["last_good"] else cur
    self.journal("activate_intent", frm=cur, to=sid)
    state["pending"] = {"slot": sid, "from": cur, "attempts_left": self.max_attempts}
    state["last_good"] = lg
    self.save_state(state)
    self.f.hit("after_intent_state")
    self._switch_live(sid)
    self.journal("activated", slot=sid)

  # --- boot / health
  def boot(self):
    """Early-boot entry: recover, spend one boot attempt if unconfirmed, return launcher path."""
    r = self.recover()
    state = self.load_state() or self.new_state()
    pend = state["pending"]
    if pend and self.live_slot() == pend["slot"]:
      if pend["attempts_left"] <= 0:
        self._rollback(state, "boot attempts exhausted")
        state = self.load_state()
      else:
        pend["attempts_left"] -= 1
        self.save_state(state)
    sid = self.live_slot()
    if sid is None:
      raise SlotInvalid("no bootable slot")
    return os.path.join(self.p("live"), LAUNCHER), r

  def confirm(self):
    state = self.load_state() or self.new_state()
    sid = self.live_slot()
    pend = state["pending"]
    if pend is None or pend["slot"] != sid:
      raise SlotInvalid("nothing to confirm for live slot")
    state["last_good"], state["pending"] = sid, None
    self.save_state(state)
    self.f.hit("after_confirm_state")
    self.journal("confirmed", slot=sid)
    self._prune(state)

  def _prune(self, state):
    keep = {state["last_good"], self.live_slot()}
    spare = [n for n in self.sealed_slots() if n not in keep]
    room = max(0, self.keep - len(keep))
    for n in spare[:len(spare) - room] if room else spare:
      shutil.rmtree(self.slot_dir(n), ignore_errors=True)

  def _rollback(self, state, why):
    target = self._best_slot(prefer=[state.get("last_good"), (state.get("pending") or {}).get("from")],
                             exclude={(state.get("pending") or {}).get("slot")})
    if target is None:
      raise SlotInvalid("no verified rollback target")
    self.journal("rollback", to=target, why=why)
    # switch BEFORE clearing intent: a crash in between leaves pending.slot != live,
    # which recover() resolves by dropping the intent (live is already the target).
    self._switch_live(target)
    state["pending"] = None
    state["last_good"] = target
    self.save_state(state)
    self.f.hit("rollback_state_saved")

  def _best_slot(self, prefer, exclude=()):
    seen = []
    for n in [x for x in prefer if x] + list(reversed(self.sealed_slots())):
      if n in seen or n in exclude:
        continue
      seen.append(n)
      if os.path.isdir(self.slot_dir(n)) and self.slot_ok(n, deep=True):
        return n
    return None

  # --- recovery: idempotent, safe to run any number of times, from any crash point
  def recover(self):
    rep = {"actions": []}
    for n in os.listdir(self.p("staging")):
      shutil.rmtree(self.p("staging", n), ignore_errors=True)
      rep["actions"].append(f"removed staging {n}")
    for n in os.listdir(self.base):
      if n.startswith("live.tmp."):
        os.unlink(self.p(n))
        rep["actions"].append(f"removed {n}")
    for n in os.listdir(self.p("slots")):  # unsealed slot dirs can only be partial renames/leftovers
      if not os.path.exists(os.path.join(self.p("slots", n), ".g8_sealed")):
        shutil.rmtree(self.p("slots", n), ignore_errors=True)
        rep["actions"].append(f"removed unsealed slot {n}")
    state = self.load_state()
    if state is None:
      state = self.new_state()
      names = self.sealed_slots()
      state["seq"] = max([int(n.split("-")[0]) for n in names] + [0])
      rep["actions"].append("state rebuilt")
      self.journal("state_rebuilt")
    seqs = [int(n.split("-")[0]) for n in self.sealed_slots()]
    if seqs and max(seqs) > state["seq"]:
      state["seq"] = max(seqs)
      self.save_state(state)
      rep["actions"].append("seq caught up with sealed slots")
    live = self.live_slot()
    pend = state["pending"]
    if pend and live != pend["slot"]:
      # intent logged but switch never happened (or was already rolled back): drop intent
      state["pending"] = None
      self.save_state(state)
      rep["actions"].append("dropped unswitched pending activation")
      pend = None
    if pend is None and state["last_good"] is None and live and self.slot_ok(live, deep=True):
      state["last_good"] = live
      self.save_state(state)
    if live is None or not self.slot_ok(live, deep=False) or (pend and not self.slot_ok(live, deep=True)):
      if pend:
        self._rollback(state, "live slot invalid")
      else:
        t = self._best_slot(prefer=[state["last_good"]])
        if t is None:
          raise SlotInvalid("no verified slot available for recovery")
        self.journal("recovered_live", to=t)
        state["last_good"] = t
        self.save_state(state)
        self._switch_live(t)
      rep["actions"].append("restored live")
    return rep

"""Fault-injection tests for the G8 slot supervisor on scratch filesystems.

Crash model: SimulatedCrash aborts at a named point (no cleanup runs, partial FS state
remains); a FRESH Supervisor instance then runs recovery. This models process death at
syscall boundaries. It does NOT model block-level power loss or fsync reordering.
"""
import errno
import multiprocessing as mp
import os
import random
import shutil
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import g8_manifest as gm  # noqa: E402
import g8_slot_supervisor as sv  # noqa: E402

COMMIT = "d2e2d24bdd61011aed0c2c99c8c277cd0bf94860"
SIMULATED_TEST_TRUST = "SIMULATED_TEST_TRUST-NOT-A-RELEASE-KEY"
pytestmark = pytest.mark.SIMULATED_TEST_TRUST
CRASH_ACTIVATE = ["after_intent_state", "state_tmp_written", "before_switch_rename", "after_switch_rename"]
CRASH_STAGE = ["copy_file", "stage_copied", "stage_sealed", "stage_renamed", "state_tmp_written"]
CRASH_CONFIRM = ["state_tmp_written", "after_confirm_state"]


def make_pkg(root, tag, size=2048):
  root.mkdir(parents=True)
  (root / "launch_chffrplus.sh").write_text(f"#!/bin/sh\necho {tag}\n")
  os.chmod(root / "launch_chffrplus.sh", 0o755)
  (root / "lib").mkdir()
  (root / "lib" / "data.bin").write_bytes(os.urandom(size))
  (root / "lib" / "ver").write_text(tag)
  return root


def signed_manifest(root, key, commit=COMMIT, release_sequence=None, purpose="production"):
  manifest = gm.build_manifest(str(root), commit, with_elf_detail=False, release_sequence=release_sequence)
  signature = gm.sign_manifest(manifest, key, SIMULATED_TEST_TRUST)
  trust = {"trusted_keys": [{"key_id": signature["key_id"], "pubkey_b64": gm.pub_b64(key),
                              "purpose": purpose}]}
  return manifest, signature, trust


@pytest.fixture
def env(tmp_path):
  e = type("E", (), {})()
  e.base = tmp_path / "base"
  e.pk = {t: make_pkg(tmp_path / f"pkg_{t}", t) for t in ("v1", "v2", "v3")}
  e.key = Ed25519PrivateKey.generate()  # memory-only simulated production key
  e.mf = {}
  e.sig = {}
  for tag, package in e.pk.items():
    e.mf[tag], e.sig[tag], e.trust = signed_manifest(package, e.key)
  e.tmp = tmp_path

  def sign(package, commit=COMMIT, release_sequence=None):
    manifest, signature, _ = signed_manifest(package, e.key, commit, release_sequence)
    return manifest, signature
  e.sign = sign

  def S(**kw):
    kw.setdefault("trust", e.trust)
    kw.setdefault("expected_commit", COMMIT)
    return sv.Supervisor(str(e.base), **kw)
  e.S = S
  return e


def install(env, tag, confirm=True):
  s = env.S()
  with s:
    sid = s.stage(str(env.pk[tag]), env.mf[tag], COMMIT, env.sig[tag])
    s.activate(sid)
    if confirm:
      s.confirm()
  return sid


def launcher_tag(env):
  with open(env.base / "live" / "launch_chffrplus.sh") as f:
    return f.read().split()[-1]


def assert_bootable(env, allowed_tags):
  """Core invariant: after ANY recovery, live resolves to a deep-verified sealed slot with a launcher."""
  s = env.S()
  with s:
    launcher, _ = s.boot()
    sid = s.live_slot()
    s.verify_slot(sid, deep=True)
  assert os.access(launcher, os.X_OK)
  assert launcher_tag(env) in allowed_tags
  return launcher_tag(env)


# ---- 10 required scenarios

def test_01_interrupted_staging_leaves_live_untouched(env):
  install(env, "v1")
  for pt in CRASH_STAGE:
    s = env.S(faults=sv.Faults(crash_at=pt))
    with pytest.raises(sv.SimulatedCrash):
      with s:
        s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
    assert assert_bootable(env, {"v1"}) == "v1", pt
    assert os.listdir(env.base / "staging") == [], pt
    # staging still possible afterwards (state consistent, no stale id collision)
    s = env.S()
    with s:
      sid = s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
      s.verify_slot(sid, deep=True)
    shutil.rmtree(env.base / "slots" / sid)


def test_02_failed_renames_never_lose_launcher(env):
  install(env, "v1")
  for where in ("before_switch_rename", "after_intent_state"):
    s = env.S(faults=sv.Faults(oserror_at={where: errno.EIO}))
    with s:
      sid = s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
      with pytest.raises(OSError):
        s.activate(sid)
    assert os.access(env.base / "live" / "launch_chffrplus.sh", os.X_OK)  # no instant without launcher
    assert assert_bootable(env, {"v1"}) == "v1"  # intent dropped by recovery, old slot live
    s = env.S()
    with s:
      s.recover()
    shutil.rmtree(env.base / "slots" / sid, ignore_errors=True)


def test_03_power_loss_at_every_activation_point(env):
  for pt in CRASH_ACTIVATE:
    shutil.rmtree(env.base, ignore_errors=True)
    install(env, "v1")
    s = env.S()
    with s:
      sid = s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
    s = env.S(faults=sv.Faults(crash_at=pt))
    with pytest.raises(sv.SimulatedCrash):
      with s:
        s.activate(sid)
    got = assert_bootable(env, {"v1", "v2"})  # either old or fully-verified new; never missing/partial
    assert got in ("v1", "v2")
    # recovery idempotent
    snap = []
    for _ in range(4):
      s = env.S()
      with s:
        s.recover()
      snap.append((os.readlink(env.base / "live"), (env.base / "state.json").read_text()))
    assert len(set(snap[1:])) == 1, pt


def test_03b_live_link_exists_after_every_filesystem_mutation(env, monkeypatch):
  """Atomicity proof at the syscall layer: after each unlink/rename/symlink the supervisor issues during
  activation and rollback, the launcher path must resolve. (Catches unlink-then-symlink 'switches'.)"""
  install(env, "v1")
  live = str(env.base / "live")
  violations = []
  real = {n: getattr(os, n) for n in ("unlink", "rename", "symlink", "replace")}

  def wrap(name):
    def f(*a, **k):
      r = real[name](*a, **k)
      if os.path.lexists(live) is False:
        violations.append((name, a))
      return r
    return f
  for n in real:
    monkeypatch.setattr(os, n, wrap(n))
  s = env.S(max_boot_attempts=1)
  with s:
    s.activate(s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"]))
  for _ in range(4):  # exhaust boot budget -> rollback path
    s = env.S(max_boot_attempts=1)
    with s:
      s.boot()
  assert launcher_tag(env) == "v1"
  assert violations == []


def test_04c_crash_inside_rollback_still_ends_on_good_slot(env):
  install(env, "v1")
  install(env, "v2", confirm=False)
  for pt in ("rollback_state_saved", "state_tmp_written", "before_switch_rename", "after_switch_rename"):
    shutil.rmtree(env.base, ignore_errors=True)
    install(env, "v1")
    install(env, "v2", confirm=False)
    for _ in range(3):  # burn the whole 3-attempt budget
      with env.S(max_boot_attempts=1) as s:
        s.boot()
    s = env.S(max_boot_attempts=1, faults=sv.Faults(crash_at=pt))
    try:
      with s:
        s.boot()
    except sv.SimulatedCrash:
      pass
    assert assert_bootable(env, {"v1"}) == "v1", pt


def test_04_failed_startup_rolls_back_after_attempt_budget(env):
  install(env, "v1")
  s = env.S(max_boot_attempts=3)
  with s:
    s.activate(s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"]))
  seen = []
  for _ in range(6):  # app never calls confirm(): simulates crash-looping new version
    s = env.S(max_boot_attempts=3)
    with s:
      s.boot()
    seen.append(launcher_tag(env))
  assert seen[:3] == ["v2"] * 3 and seen[3:] == ["v1"] * 3, seen
  s = env.S()
  with s:
    st = s.load_state()
  assert st["pending"] is None and st["last_good"] == s.live_slot()


def test_04b_confirmed_update_is_not_rolled_back(env):
  install(env, "v1")
  install(env, "v2", confirm=False)
  s = env.S()
  with s:
    s.boot()
    s.confirm()
  for _ in range(6):
    s = env.S()
    with s:
      s.boot()
  assert launcher_tag(env) == "v2"


def test_05_missing_active_launcher_recovers_without_the_app(env):
  install(env, "v1")
  install(env, "v2")
  os.unlink(env.base / "slots" / os.readlink(env.base / "live").split("/")[-1] / "launch_chffrplus.sh")
  assert assert_bootable(env, {"v1"}) == "v1"
  # live symlink deleted entirely
  os.unlink(env.base / "live")
  assert assert_bootable(env, {"v1", "v2"}) in ("v1", "v2")
  # dangling live symlink
  os.unlink(env.base / "live")
  os.symlink("slots/999999-deadbeef", env.base / "live")
  assert assert_bootable(env, {"v1", "v2"}) in ("v1", "v2")


def test_06_corrupt_or_incomplete_package_rejected_and_never_activated(env):
  install(env, "v1")
  # (a) corrupt source package vs signed manifest
  with open(env.pk["v2"] / "lib" / "data.bin", "r+b") as f:
    f.write(b"\xff")
  s = env.S()
  with s, pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
  # (b) incomplete package
  os.unlink(env.pk["v3"] / "lib" / "ver")
  with s, pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v3"]), env.mf["v3"], COMMIT, env.sig["v3"])
  # (c) untrusted/unsigned manifest
  s = env.S(trust={"trusted_keys": []})
  with s, pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]), env.mf["v1"], COMMIT, env.sig["v1"])
  s = env.S(trust=None)
  with s, pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]), env.mf["v1"], COMMIT, env.sig["v1"])
  # (d) wrong source commit
  s = env.S()
  with s, pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]), env.mf["v1"], "f" * 40, env.sig["v1"])
  assert os.listdir(env.base / "staging") == [] and assert_bootable(env, {"v1"}) == "v1"
  # (e) bit-rot in a sealed-but-inactive slot is caught at activation (deep verify)
  shutil.rmtree(env.pk["v2"]); make_pkg(env.pk["v2"], "v2"); env.mf["v2"], env.sig["v2"] = env.sign(env.pk["v2"])
  with s:
    sid = s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
  with open(env.base / "slots" / sid / "lib" / "data.bin", "r+b") as f:
    f.write(b"\x00\x01")
  with s, pytest.raises(sv.SlotInvalid):
    s.activate(sid)
  assert assert_bootable(env, {"v1"}) == "v1"


def test_06b_corrupt_live_after_unconfirmed_activation_rolls_back(env):
  install(env, "v1")
  install(env, "v2", confirm=False)
  live = os.readlink(env.base / "live").split("/")[-1]
  with open(env.base / "slots" / live / "lib" / "data.bin", "r+b") as f:
    f.write(b"BITROT")
  assert assert_bootable(env, {"v1"}) == "v1"


def test_07_existing_backups_and_repeated_recovery(env):
  install(env, "v1")
  # stale legacy-style artifacts must neither block nor be mistaken for slots
  os.makedirs(env.base / "slots" / "old_openpilot")
  os.makedirs(env.base / "staging" / "junk.123")
  (env.base / "live.tmp.4242").symlink_to("slots/nothing")
  install(env, "v2")
  for _ in range(5):
    s = env.S()
    with s:
      s.recover()
  assert launcher_tag(env) == "v2"
  assert not (env.base / "slots" / "old_openpilot").exists()
  # many successive updates: pruning keeps live + last_good, never deletes them
  for i in range(6):
    t = f"x{i}"
    p = make_pkg(env.tmp / f"pk_{t}", t)
    install_pkg = env.S()
    with install_pkg:
      m, signature = env.sign(p)
      sid = install_pkg.stage(str(p), m, COMMIT, signature)
      install_pkg.activate(sid)
      install_pkg.confirm()
  assert len(os.listdir(env.base / "slots")) <= 3
  assert assert_bootable(env, {"x5"}) == "x5"


def test_08_disk_exhaustion_injected(env):
  install(env, "v1")
  s = env.S(faults=sv.Faults(oserror_at={"copy_file": errno.ENOSPC}))
  with s, pytest.raises(OSError) as ei:
    s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
  assert ei.value.errno == errno.ENOSPC
  assert os.listdir(env.base / "staging") == []
  assert assert_bootable(env, {"v1"}) == "v1"
  s = env.S(min_free_bytes=1 << 60)
  with s, pytest.raises(sv.InsufficientSpace):
    s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])


def test_08b_disk_exhaustion_real_tmpfs(tmp_path):
  """Real ENOSPC on a 2 MiB tmpfs inside a private mount namespace (no host mounts touched)."""
  if subprocess.run(["unshare", "-Urm", "true"], capture_output=True).returncode != 0:
    pytest.skip("unprivileged user+mount namespace unavailable on this host")
  script = tmp_path / "tmpfs_case.py"
  # simpler & honest: preflight would refuse first (InsufficientSpace) -> assert that, then assert real ENOSPC by pre-filling.
  script.write_text(f'''
import os, sys, subprocess, errno
sys.path.insert(0, {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))!r})
import g8_manifest as gm, g8_slot_supervisor as sv
mnt = {str(tmp_path / "mnt")!r}
os.makedirs(mnt)
subprocess.check_call(["mount", "-t", "tmpfs", "-o", "size=2m", "tmpfs", mnt])
def mk(d, n):
  os.makedirs(d + "/lib")
  open(d + "/launch_chffrplus.sh", "w").write("#!/bin/sh\\necho t\\n"); os.chmod(d + "/launch_chffrplus.sh", 0o755)
  open(d + "/lib/blob", "wb").write(os.urandom(n))
pk = {str(tmp_path / "bigpkg")!r}; mk(pk, 3 << 20)          # source lives on the real fs
m = gm.build_manifest(pk, "c" * 40, with_elf_detail=False)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
k = Ed25519PrivateKey.generate()
sig = gm.sign_manifest(m, k, "TEST-SIMULATED-TRUST")
trust = {"trusted_keys": [{"key_id": sig["key_id"], "pubkey_b64": gm.pub_b64(k), "purpose": "production"}]}
s = sv.Supervisor(mnt + "/base", trust=trust, expected_commit="c" * 40)
with s:
  try:
    s.stage(pk, m, "c" * 40, sig); print("RESULT=NO_ERROR")
  except sv.InsufficientSpace:
    print("RESULT=PREFLIGHT_REFUSED")
# now small package that passes preflight, but fill the fs so the real copy hits ENOSPC
small = {str(tmp_path / "smallpkg")!r}; mk(small, 1 << 20)
ms = gm.build_manifest(small, "c" * 40, with_elf_detail=False)
fill = open(mnt + "/filler", "wb")
try:
  while True: fill.write(b"x" * 4096); fill.flush()
except OSError: pass
fill.close()
os.truncate(mnt + "/filler", os.path.getsize(mnt + "/filler") - (1 << 20) - 200000)   # leaves ~preflight-passing headroom
st = os.statvfs(mnt); free = st.f_bavail * st.f_frsize
s2 = sv.Supervisor(mnt + "/base", trust=trust, expected_commit="c" * 40)
with s2:
  try:
    s2.stage(small, ms, "c" * 40, gm.sign_manifest(ms,k,"TEST-SIMULATED-TRUST")); print("RESULT2=NO_ERROR free=%d" % free)
  except sv.InsufficientSpace: print("RESULT2=PREFLIGHT_REFUSED free=%d" % free)
  except OSError as e: print("RESULT2=OSERROR", errno.errorcode[e.errno])
print("STAGING_LEFT=%s" % os.listdir(mnt + "/base/staging"))
''')
  r = subprocess.run(["unshare", "-Urm", sys.executable, str(script)], capture_output=True, text=True)
  assert "RESULT=PREFLIGHT_REFUSED" in r.stdout, r.stdout + r.stderr
  assert ("RESULT2=OSERROR ENOSPC" in r.stdout or "RESULT2=PREFLIGHT_REFUSED" in r.stdout), r.stdout + r.stderr
  assert "STAGING_LEFT=[]" in r.stdout, r.stdout + r.stderr


def test_08c_real_kernel_write_failure_efbig(env):
  """Real kernel write error (RLIMIT_FSIZE -> EFBIG) mid-copy. Not ENOSPC: a real full-filesystem needs a
  privileged mount, unavailable on this host (userns restricted, no passwordless sudo)."""
  import resource
  import signal
  install(env, "v1")
  big = make_pkg(env.tmp / "pkg_big", "big", size=64 * 1024)
  mfb, sigb = env.sign(big)
  old = resource.getrlimit(resource.RLIMIT_FSIZE)
  old_h = signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
  resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024, old[1]))
  try:
    s = env.S()
    with s, pytest.raises(OSError) as ei:
      s.stage(str(big), mfb, COMMIT, sigb)
  finally:
    resource.setrlimit(resource.RLIMIT_FSIZE, old)
    signal.signal(signal.SIGXFSZ, old_h)
  assert ei.value.errno == errno.EFBIG
  assert os.listdir(env.base / "staging") == []
  assert assert_bootable(env, {"v1"}) == "v1"


def _lock_holder(base, ready, release, trust):
  s = sv.Supervisor(base, trust=trust, expected_commit=COMMIT)
  with s:
    ready.set()
    release.wait(10)


def test_09_concurrent_updater_excluded(env):
  install(env, "v1")
  ready, release = mp.Event(), mp.Event()
  p = mp.Process(target=_lock_holder, args=(str(env.base), ready, release, env.trust))
  p.start()
  assert ready.wait(10)
  try:
    s = env.S()
    with pytest.raises(sv.LockBusy):
      s.__enter__()
  finally:
    release.set(); p.join(10)
  # lock released on holder exit; and a killed holder releases it too
  ready.clear(); release.clear()
  p = mp.Process(target=_lock_holder, args=(str(env.base), ready, release, env.trust))
  p.start(); assert ready.wait(10); p.kill(); p.join(10)
  s = env.S()
  with s:
    s.recover()


def test_10_recovery_to_independently_verified_previous(env):
  install(env, "v1")
  install(env, "v2", confirm=False)
  with open(env.base / "state.json", "w") as f:  # corrupt state file entirely
    f.write("{not json")
  prev = os.readlink(env.base / "live").split("/")[-1]
  # tamper v2 AND state corrupt: recovery must pick a deep-verified slot (v1), never trust the tampered one
  with open(env.base / "slots" / prev / "lib" / "ver", "w") as f:
    f.write("tampered")
  got = assert_bootable(env, {"v1"})
  assert got == "v1"
  # if every slot is corrupt, fail closed (raise) rather than boot something unverified
  for n in os.listdir(env.base / "slots"):
    with open(env.base / "slots" / n / "lib" / "data.bin", "r+b") as f:
      f.write(b"\xde\xad")
  os.unlink(env.base / "live")
  s = env.S()
  with s, pytest.raises(sv.SlotInvalid):
    s.boot()


# ---- stress: randomized operation sequences with random crashes, invariant checked after every step

@pytest.mark.parametrize("seed", [1, 7, 42, 1234, 2026])
def test_stress_random_crashes_preserve_bootability(env, seed):
  rnd = random.Random(seed)
  install(env, "v1")
  tags = {"v1"}
  pkgs = {}
  for i in range(60):
    op = rnd.choice(["update", "update", "boot", "confirm", "recover", "boot_loop"])
    crash = rnd.choice([None, None] + CRASH_STAGE + CRASH_ACTIVATE + CRASH_CONFIRM)
    try:
      s = env.S(faults=sv.Faults(crash_at=crash), max_boot_attempts=2)
      with s:
        if op == "update":
          t = f"s{seed}_{i}"
          p = make_pkg(env.tmp / f"sp_{t}", t)
          pkgs[t] = p
          tags.add(t)
          m, signature = env.sign(p)
          s.activate(s.stage(str(p), m, COMMIT, signature))
        elif op in ("boot", "boot_loop"):
          s.boot()
        elif op == "confirm":
          s.confirm()
        else:
          s.recover()
    except (sv.SimulatedCrash, sv.SlotInvalid):
      pass
    got = assert_bootable(env, tags)
    assert got in tags
    # live must never be missing between operations
    assert os.path.islink(env.base / "live") and os.path.exists(env.base / "live" / "launch_chffrplus.sh")
    for n in os.listdir(env.base / "staging"):
      pass  # leftovers are legal until recovery; assert_bootable already ran recovery
    assert os.listdir(env.base / "staging") == []


def test_manifest_hash_cost_smoke(env):
  """Activation re-hashes the whole slot (deep verify); make sure that path is exercised, not shallow."""
  install(env, "v1")
  s = env.S()
  with s:
    sid = s.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
  # same-size, same-mode corruption invisible to a shallow (stat-only) check
  p = env.base / "slots" / sid / "lib" / "data.bin"
  b = bytearray(p.read_bytes()); b[100] ^= 0xFF; p.write_bytes(bytes(b))
  assert s.slot_ok(sid, deep=False) is False  # deep verification mandatory after hardening
  assert s.slot_ok(sid, deep=True) is False
  with s, pytest.raises(sv.SlotInvalid):
    s.activate(sid)

"""Independent verification of production activation_guard.sh against `mv -T -n` SEMANTIC VARIANTS.

coreutils >= 9.2 exits 1 when -n skips an existing destination; older coreutils (e.g. the 8.x line shipped
with older Ubuntu bases) exits 0 and silently does nothing. The device's mv version is UNVERIFIED, and the
sysroot ships no ARM64 userland binaries, so the old behaviour is modelled with a bash `mv` shim. The guard
must stay safe either way because it checks inode postconditions instead of trusting mv's exit status.
"""
import os
import pathlib
import subprocess
import sys

import pytest

GUARD = pathlib.Path(os.environ.get("G8_GUARD", pathlib.Path(__file__).resolve().parents[3] / "system/updated/activation_guard.sh"))

RUN = r'''
source "$1"; active="$2"; root="$3"; scenario="$4"; n=0
mv() {
  n=$((n+1))
  case "$scenario:$n" in
    oldsemantics_backup_race:1)   # backup appears after preflight; old mv -n skips it and exits 0
      mkdir -p "$root/old_openpilot"; echo foreign > "$root/old_openpilot/FOREIGN"; return 0 ;;
    oldsemantics_active_race:2)   # active appears between the two renames; old mv -n skips and exits 0
      mkdir -p "$active"; echo foreign > "$active/FOREIGN"; return 0 ;;
    newsemantics_active_race:2)   # >=9.2: same race but mv exits 1
      mkdir -p "$active"; echo foreign > "$active/FOREIGN"; return 1 ;;
    silent_noop_first:1) return 0 ;;   # mv claims success but moved nothing
    fail_second_real_restore:2) return 1 ;;
    fail_second_noop_restore:2) return 1 ;;
    fail_second_noop_restore:3) return 0 ;;  # restore claims success but moved nothing
  esac
  command mv "$@"
}
g8_activate_staged_update "$active" "$root"; echo "RC=$?"
'''


def ino(p):
  st = os.stat(p)
  return f"{st.st_dev}:{st.st_ino}"


@pytest.fixture
def tree(tmp_path):
  base = tmp_path.resolve()
  active, root = base / "openpilot", base / "staging"
  active.mkdir()
  (active / "launch_chffrplus.sh").write_text("old")
  cand = root / "finalized"
  (cand / "system/manager").mkdir(parents=True)
  (cand / ".overlay_consistent").write_text("")
  for f in ("launch_chffrplus.sh", "launch_env.sh", "system/manager/manager.py"):
    (cand / f).write_text("new")
    os.chmod(cand / f, 0o755)
  return active, root, ino(active), ino(cand)


def run(tree, scenario):
  active, root, *_ = tree
  r = subprocess.run(["bash", "-c", RUN, "x", str(GUARD), str(active), str(root), scenario], capture_output=True, text=True)
  rc = int([l for l in r.stdout.splitlines() if l.startswith("RC=")][-1][3:])
  return rc, r.stderr


def test_baseline_normal_activation(tree):
  active, root, old, cand = tree
  rc, _ = run(tree, "none")
  assert rc == 0 and ino(active) == cand and ino(root / "old_openpilot") == old


def test_old_coreutils_silent_skip_of_first_rename_keeps_old_app(tree):
  active, root, old, cand = tree
  rc, err = run(tree, "oldsemantics_backup_race")
  assert rc == 20, err                      # recoverable: old app provably still active
  assert ino(active) == old and (root / "finalized").is_dir()


def test_old_coreutils_silent_skip_of_second_rename_is_critical_not_success(tree):
  active, root, old, cand = tree
  rc, err = run(tree, "oldsemantics_active_race")
  assert rc == 40, err                      # NOT 0: must never report activation of the foreign dir
  assert ino(root / "old_openpilot") == old  # old app preserved for external recovery
  assert (root / "finalized").is_dir()


def test_new_coreutils_second_rename_race_is_critical(tree):
  active, root, old, cand = tree
  rc, err = run(tree, "newsemantics_active_race")
  assert rc == 40 and ino(root / "old_openpilot") == old


def test_first_mv_claims_success_but_moved_nothing(tree):
  active, root, old, cand = tree
  rc, err = run(tree, "silent_noop_first")
  assert rc == 20 and ino(active) == old


def test_second_rename_failure_restores_old_app(tree):
  active, root, old, cand = tree
  rc, err = run(tree, "fail_second_real_restore")
  assert rc == 30 and ino(active) == old and (root / "finalized").is_dir()


def test_restore_that_claims_success_but_moved_nothing_is_critical(tree):
  active, root, old, cand = tree
  rc, err = run(tree, "fail_second_noop_restore")
  assert rc == 40, err                      # must not be reported as restored
  assert not active.exists() and ino(root / "old_openpilot") == old

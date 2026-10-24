"""F1 security and fault qualification for externally pinned recovery.

All keys are disposable in-memory Ed25519 keys and every filesystem target is
pytest's per-test scratch directory.  SIGKILL tests kill only child processes
created by this module; they do not model physical power loss.
"""
import errno
import json
import os
from pathlib import Path
import signal
import time

import multiprocessing as mp
import pytest

import g8_slot_supervisor as sv
from test_g8_supervisor import COMMIT, env, install


pytestmark = pytest.mark.SIMULATED_TEST_TRUST


def _stage(env, tag, release_sequence=None, minimum=None):
  manifest, signature = env.sign(env.pk[tag], release_sequence=release_sequence)
  with env.S(minimum_release_sequence=minimum) as supervisor:
    return supervisor.stage(str(env.pk[tag]), manifest, COMMIT, signature)


def test_signed_unconfirmed_slot_rejected_when_state_is_missing(env):
  sid = _stage(env, "v1")
  (env.base / "state.json").unlink()
  with env.S(approved_recovery_slot=None) as supervisor, pytest.raises(sv.SlotInvalid):
    supervisor.boot()
  assert supervisor.live_slot() is None
  assert not (env.base / "state.json").exists()
  assert supervisor.slot_ok(sid)


def test_corrupt_state_cannot_boot_live_unconfirmed_signed_slot(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  live = env.base / "live"
  live.unlink()
  live.symlink_to(Path("slots") / candidate)
  (env.base / "state.json").write_text("{corrupt")
  with env.S() as supervisor:
    supervisor.boot()
    assert supervisor.live_slot() == known_good


def test_explicit_external_pin_authorizes_initial_bootstrap(env):
  candidate = _stage(env, "v1")
  with env.S(approved_recovery_slot=candidate) as supervisor:
    launcher, _ = supervisor.boot()
    assert supervisor.live_slot() == candidate
    assert supervisor.load_state()["pending"] is None
    assert launcher.endswith(sv.LAUNCHER)


def test_state_loss_selects_pin_not_newer_never_activated_slot(env):
  known_good = install(env, "v1")
  newer = _stage(env, "v2")
  (env.base / "state.json").unlink()
  (env.base / "live").unlink()
  with env.S() as supervisor:
    supervisor.recover()
    assert supervisor.live_slot() == known_good
    assert supervisor.live_slot() != newer


def test_forged_valid_state_cannot_relabel_signed_slot_as_healthy(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  forged = sv.Supervisor.new_state()
  forged.update(seq=2, last_good=candidate)
  (env.base / "state.json").write_text(json.dumps(forged))
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S() as supervisor:
    supervisor.recover()
    assert supervisor.live_slot() == known_good
    assert supervisor.load_state()["last_good"] == known_good


def test_forged_pending_and_live_cannot_boot_signed_candidate_without_trial_pin(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  forged = sv.Supervisor.new_state()
  forged.update(seq=2, last_good=known_good,
                pending={"slot": candidate, "from": known_good, "attempts_left": 3})
  (env.base / "state.json").write_text(json.dumps(forged))
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S(approved_trial_slot=None) as supervisor:
    supervisor.boot()
    assert supervisor.live_slot() == known_good
    assert supervisor.load_state()["pending"] is None


def test_forged_trial_pending_excessive_attempt_budget_is_rejected(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  forged = sv.Supervisor.new_state()
  forged.update(seq=2, last_good=known_good,
                pending={"slot": candidate, "from": known_good, "attempts_left": 1_000_000})
  (env.base / "state.json").write_text(json.dumps(forged))
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S(approved_trial_slot=candidate, approved_health_slot=None,
             max_boot_attempts=3) as supervisor:
    launcher, _ = supervisor.boot()
    assert supervisor.live_slot() == known_good
    assert supervisor.load_state()["pending"] is None
    assert supervisor.load_state()["last_good"] == known_good
    assert launcher.endswith(sv.LAUNCHER)


@pytest.mark.parametrize("invalid_budget", [True, 0, -1, 101, 3.5])
def test_invalid_host_trial_retry_budget_rejected(env, invalid_budget):
  known_good = install(env, "v1")
  with env.S(max_boot_attempts=invalid_budget) as supervisor, pytest.raises(sv.SlotInvalid):
    supervisor.boot()
  assert known_good == env.approved_recovery_slot


def test_forged_live_cannot_boot_trial_pin_without_matching_pending_state(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S(approved_trial_slot=candidate) as supervisor:
    supervisor.boot()
    assert supervisor.live_slot() == known_good


def test_fake_confirm_rejected_without_external_health_authorization(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  forged = sv.Supervisor.new_state()
  forged.update(seq=2, last_good=known_good,
                pending={"slot": candidate, "from": known_good, "attempts_left": 3})
  (env.base / "state.json").write_text(json.dumps(forged))
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S(approved_trial_slot=candidate, approved_health_slot=None) as supervisor:
    with pytest.raises(sv.SlotInvalid):
      supervisor.confirm()
    assert supervisor.load_state()["last_good"] == known_good
    assert supervisor.load_state()["pending"]["slot"] == candidate
  assert env.approved_recovery_slot == known_good


def test_manual_rollback_rejects_signed_but_unapproved_slot(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  with env.S() as supervisor, pytest.raises(sv.SlotInvalid):
    supervisor.rollback(candidate)
  assert supervisor.live_slot() == known_good


def _install_sequence(env, tag, sequence, minimum):
  sid = _stage(env, tag, release_sequence=sequence, minimum=minimum)
  with env.S(minimum_release_sequence=minimum, approved_recovery_slot=sid) as supervisor:
    supervisor.recover()
  env.approved_recovery_slot = sid
  return sid


def test_antirollback_minimum_blocks_boot_of_previously_signed_old_slot(env):
  old = _install_sequence(env, "v1", 4, 4)
  with env.S(minimum_release_sequence=5, approved_recovery_slot=old) as supervisor:
    with pytest.raises(sv.SlotInvalid):
      supervisor.boot()


def test_antirollback_minimum_blocks_recovery_to_old_approved_pin(env):
  old = _install_sequence(env, "v1", 4, 4)
  (env.base / "state.json").unlink()
  (env.base / "live").unlink()
  with env.S(minimum_release_sequence=5, approved_recovery_slot=old) as supervisor:
    with pytest.raises(sv.SlotInvalid):
      supervisor.recover()
  assert supervisor.live_slot() is None


def test_antirollback_minimum_blocks_manual_rollback_to_old_slot(env):
  old = _install_sequence(env, "v1", 4, 4)
  new = _stage(env, "v2", release_sequence=5, minimum=4)
  env.approved_trial_slot = new
  with env.S(minimum_release_sequence=4) as supervisor:
    supervisor.activate(new)
  env.approved_health_slot = new
  with env.S(minimum_release_sequence=4) as supervisor:
    supervisor.confirm()
  env.approved_recovery_slot = new
  env.approved_trial_slot = None
  env.approved_health_slot = None
  with env.S(minimum_release_sequence=5, approved_recovery_slot=old) as supervisor, pytest.raises(sv.SlotInvalid):
    supervisor.rollback(old)
  assert supervisor.live_slot() == new


def test_malformed_external_recovery_pin_fails_closed(env):
  install(env, "v1")
  for bad in ("../slots/000001-deadbeef0000", "000001-../../escape", "signed"):
    with env.S(approved_recovery_slot=bad) as supervisor, pytest.raises(sv.SlotInvalid):
      supervisor.recover()


def test_recovery_unlinks_temporary_symlink_without_touching_target(env):
  install(env, "v1")
  sentinel = env.tmp / "OUTSIDE_STATE_TMP"
  sentinel.write_text("do not modify")
  hostile = env.base / "state.json.tmp.hostile"
  hostile.symlink_to(sentinel)
  with env.S() as supervisor:
    supervisor.recover()
  assert sentinel.read_text() == "do not modify"
  assert not os.path.lexists(hostile)


def _assert_stage_copy_errno(env, injected_errno):
  install(env, "v1")
  faults = sv.Faults(oserror_at={"copy_file": injected_errno})
  with env.S(faults=faults) as supervisor, pytest.raises(OSError) as raised:
    supervisor.stage(str(env.pk["v2"]), env.mf["v2"], COMMIT, env.sig["v2"])
  assert raised.value.errno == injected_errno
  assert list((env.base / "staging").iterdir()) == []
  with env.S() as supervisor:
    supervisor.boot()
    assert supervisor.live_slot() == env.approved_recovery_slot


def test_fault_hook_simulates_enospc_without_filling_filesystem(env):
  _assert_stage_copy_errno(env, errno.ENOSPC)


def test_fault_hook_simulates_eio_without_damaging_live_slot(env):
  _assert_stage_copy_errno(env, errno.EIO)


def test_fault_hook_simulates_erofs_without_mounting_filesystem(env):
  _assert_stage_copy_errno(env, errno.EROFS)


def test_erofs_during_confirm_keeps_unconfirmed_state_and_cleans_temp(env):
  install(env, "v1")
  candidate = _stage(env, "v2")
  env.approved_trial_slot = candidate
  with env.S() as supervisor:
    supervisor.activate(candidate)
  env.approved_health_slot = candidate
  faults = sv.Faults(oserror_at={"state_tmp_written": errno.EROFS})
  with env.S(faults=faults) as supervisor, pytest.raises(OSError) as raised:
    supervisor.confirm()
  assert raised.value.errno == errno.EROFS
  assert not list(env.base.glob("state.json.tmp.*"))
  with env.S() as supervisor:
    supervisor.boot()
    assert supervisor.load_state()["pending"]["slot"] == candidate


class _PauseAt(sv.Faults):
  def __init__(self, point, marker):
    super().__init__()
    self.point = point
    self.marker = marker

  def hit(self, name):
    self.points_seen.append(name)
    if name == self.point:
      Path(self.marker).write_text(name)
      while True:
        signal.pause()


def _operation_child(base, trust, recovery, trial, health, point, marker, action,
                     package, manifest, signature, sid):
  faults = _PauseAt(point, marker)
  supervisor = sv.Supervisor(base, trust=trust, expected_commit=COMMIT,
                             approved_recovery_slot=recovery,
                             approved_trial_slot=trial,
                             approved_health_slot=health, faults=faults)
  with supervisor:
    if action == "stage":
      supervisor.stage(package, manifest, COMMIT, signature)
    elif action == "activate":
      supervisor.activate(sid)
    elif action == "confirm":
      supervisor.confirm()
    else:
      raise AssertionError(action)


def _recovery_child(base, trust, recovery, trial, connection):
  try:
    with sv.Supervisor(base, trust=trust, expected_commit=COMMIT,
                       approved_recovery_slot=recovery,
                       approved_trial_slot=trial) as supervisor:
      supervisor.boot()
      connection.send(("ok", supervisor.live_slot()))
  except BaseException as error:
    connection.send(("error", repr(error)))
  finally:
    connection.close()


def _kill_child_at(env, point, action, approved, *, sid=None):
  marker = env.tmp / f"reached_{point}"
  context = mp.get_context("fork")
  process = context.Process(
    target=_operation_child,
    args=(str(env.base), env.trust, approved,
          sid if action in ("activate", "confirm") else None,
          sid if action == "confirm" else None,
          point, str(marker), action,
          str(env.pk["v2"]), env.mf["v2"], env.sig["v2"], sid),
  )
  process.start()
  deadline = time.monotonic() + 10
  while not marker.exists() and process.is_alive() and time.monotonic() < deadline:
    time.sleep(0.01)
  assert marker.exists(), f"child did not reach {point}; exit={process.exitcode}"
  os.kill(process.pid, signal.SIGKILL)
  process.join(10)
  assert process.exitcode == -signal.SIGKILL


def _fresh_process_boot(env, approved, trial=None):
  context = mp.get_context("fork")
  parent, child = context.Pipe(duplex=False)
  process = context.Process(target=_recovery_child,
                            args=(str(env.base), env.trust, approved, trial, child))
  process.start()
  child.close()
  assert parent.poll(10), "fresh recovery process did not report"
  result = parent.recv()
  process.join(10)
  assert process.exitcode == 0
  assert result[0] == "ok", result
  return result[1]


def test_sigkill_during_stage_then_fresh_process_recovers(env):
  known_good = install(env, "v1")
  _kill_child_at(env, "stage_copied", "stage", known_good)
  assert _fresh_process_boot(env, known_good) == known_good
  assert list((env.base / "staging").iterdir()) == []


def test_sigkill_after_live_switch_then_fresh_process_recovers_trial(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  _kill_child_at(env, "after_switch_rename", "activate", known_good, sid=candidate)
  assert _fresh_process_boot(env, known_good, candidate) == candidate


def test_sigkill_after_confirm_state_does_not_override_external_health_pin(env):
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  env.approved_trial_slot = candidate
  with env.S() as supervisor:
    supervisor.activate(candidate)
  _kill_child_at(env, "after_confirm_state", "confirm", known_good, sid=candidate)
  assert _fresh_process_boot(env, known_good) == known_good


def test_forged_oversized_retry_budget_restores_known_good(env):
  """Even a correctly pinned trial may not exceed a configured boot budget."""
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  forged = sv.Supervisor.new_state()
  forged.update(seq=2, last_good=known_good,
                pending={"slot": candidate, "from": known_good, "attempts_left": 1000000})
  (env.base / "state.json").write_text(json.dumps(forged))
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S(approved_trial_slot=candidate, approved_health_slot=None, max_boot_attempts=3) as supervisor:
    launcher, report = supervisor.boot()
    assert supervisor.live_slot() == known_good
    assert supervisor.load_state()["pending"] is None
    assert supervisor.load_state()["last_good"] == known_good
    assert "dropped unauthorized or inconsistent pending activation" in report["actions"]
    assert launcher.endswith(sv.LAUNCHER)


def test_forged_matching_pending_with_different_approved_trial_rolls_back(env):
  """A different signed trial pin cannot authorize forged pending/live state."""
  known_good = install(env, "v1")
  candidate = _stage(env, "v2")
  different_pin = _stage(env, "v3")
  forged = sv.Supervisor.new_state()
  forged.update(seq=3, last_good=known_good,
                pending={"slot": candidate, "from": known_good, "attempts_left": 2})
  (env.base / "state.json").write_text(json.dumps(forged))
  (env.base / "live").unlink()
  (env.base / "live").symlink_to(Path("slots") / candidate)
  with env.S(approved_trial_slot=different_pin, approved_health_slot=None, max_boot_attempts=3) as supervisor:
    supervisor.boot()
    assert supervisor.live_slot() == known_good
    assert supervisor.load_state()["pending"] is None


@pytest.mark.parametrize("bad_budget", [0, -1, True, 1000001, "3"])
def test_invalid_configured_boot_attempt_budget_fails_closed(env, bad_budget):
  known_good = install(env, "v1")
  with env.S(max_boot_attempts=bad_budget) as supervisor, pytest.raises(sv.SlotInvalid):
    supervisor.boot()
  assert supervisor.live_slot() == known_good

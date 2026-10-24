"""Negative host-only tests of signed slot enforcement and anti-forgery invariants.

All packages, keys and filesystem paths are temporary test fixtures. No comma use.
The in-memory "production"-purpose test key is only SIMULATED_TEST_TRUST,
never a real release signing authority.
"""
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from test_g8_supervisor import COMMIT, env, install, make_pkg
import g8_slot_supervisor as sv
import g8_manifest as gm

pytestmark = pytest.mark.SIMULATED_TEST_TRUST


def forged_slot(env, sid="000001-aaaaaaaaaaaa", commit="FABRICATED_UNTRUSTED", signature=None):
  """Forge a self-consistent unsigned slot without invoking production stage()."""
  root=env.base/"slots"/sid
  root.mkdir(parents=True,exist_ok=True)
  (root/"launch_chffrplus.sh").write_text("#!/bin/sh\n# NOT EXECUTED\nexit 1\n")
  (root/"launch_chffrplus.sh").chmod(0o755)
  manifest=gm.build_manifest(str(root), commit, with_elf_detail=False)
  b=gm.canonical(manifest)
  root_id=f"000001-{hashlib.sha256(b).hexdigest()[:12]}"
  correct=env.base/"slots"/root_id
  root.rename(correct)
  (correct/".g8_manifest.json").write_bytes(b)
  if signature is not None:
    (correct/".g8_signature.json").write_bytes(gm.canonical(signature))
  sigsha=hashlib.sha256(gm.canonical(signature)).hexdigest() if signature is not None else "0"*64
  seal={"schema":"c7-g8-slotseal/1","slot":root_id,
        "manifest_sha256":hashlib.sha256(b).hexdigest(),"signature_sha256":sigsha}
  (correct/".g8_sealed").write_bytes(gm.canonical(seal))
  return root_id,correct


def test_recovery_refuses_unsigned_fabricated_slot_with_valid_seal(env):
  sid,_=forged_slot(env)
  s=env.S()
  with s, pytest.raises(sv.SlotInvalid):
    s.boot()
  assert s.live_slot() is None
  assert not s.slot_ok(sid,deep=True)


def test_absent_trust_policy_refuses_boot_of_previously_valid_slot(env):
  install(env,"v1")
  s=env.S(trust=None)
  with s, pytest.raises(sv.SlotInvalid):
    s.boot()


def test_empty_trust_policy_refuses_earlier_signed_slot(env):
  install(env,"v1")
  s=env.S(trust={"trusted_keys":[]})
  with s, pytest.raises(sv.SlotInvalid):
    s.boot()


def test_recover_does_not_resurrect_slot_after_key_revocation(env):
  install(env,"v1")
  (env.base/"live").unlink()
  s=env.S(trust={"trusted_keys":[]})
  with s, pytest.raises(sv.SlotInvalid):
    s.recover()
  assert s.live_slot() is None


def test_dev_purpose_key_rejected_for_stage(env):
  dev={"trusted_keys":[dict(env.trust["trusted_keys"][0],purpose="dev-disposable")]}
  s=env.S(trust=dev)
  with s,pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]),env.mf["v1"],COMMIT,env.sig["v1"])


def test_wrong_key_signature_rejected_even_with_correct_source_commit(env):
  import cryptography.hazmat.primitives.asymmetric.ed25519 as ed
  wrong=ed.Ed25519PrivateKey.generate()
  sig=gm.sign_manifest(env.mf["v1"],wrong,"UNTRUSTED_TEST")
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]),env.mf["v1"],COMMIT,sig)


def test_missing_signature_rejected_before_staging(env):
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]),env.mf["v1"],COMMIT,None)


def test_wrong_signed_commit_is_rejected(env):
  m,sig=env.sign(env.pk["v1"],commit="f"*40)
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]),m,COMMIT,sig)


def test_pinned_minimum_release_sequence_requires_signed_metadata(env):
  s=env.S(minimum_release_sequence=5)
  with s,pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]),env.mf["v1"],COMMIT,env.sig["v1"])
  m,sig=env.sign(env.pk["v1"],release_sequence=4)
  with s,pytest.raises(sv.SlotInvalid):
    s.stage(str(env.pk["v1"]),m,COMMIT,sig)
  m,sig=env.sign(env.pk["v1"],release_sequence=5)
  with s:
    sid=s.stage(str(env.pk["v1"]),m,COMMIT,sig)
    assert s.slot_ok(sid,deep=True)


def test_same_size_live_launcher_tampering_rejected_at_boot(env):
  install(env,"v1")
  current=env.base/"live"/"launch_chffrplus.sh"
  old=current.read_bytes()
  current.write_bytes(bytes([old[0]^1])+old[1:])
  assert current.stat().st_size==len(old)
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.boot()


def test_shallow_flag_cannot_bypass_modified_file_hash(env):
  sid=install(env,"v1")
  target=env.base/"slots"/sid/"lib"/"ver"
  before=target.read_bytes()
  target.write_bytes(b"x"*len(before))
  s=env.S()
  assert not s.slot_ok(sid,deep=False)
  assert not s.slot_ok(sid,deep=True)


def test_unsigned_arbitrary_slot_never_manual_rollback_target(env):
  install(env,"v1")
  sid,_=forged_slot(env, sid="000050-aaaaaaaaaaaa")
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.rollback(sid)
  assert s.live_slot() is not None


def test_forged_metadata_signature_and_resealed_hash_rejected(env):
  sid=install(env,"v1")
  root=env.base/"slots"/sid
  sig=root/".g8_signature.json"
  bad=dict(json.loads(sig.read_text()))
  bad["signature"]="not_a_real_signature"
  contents=gm.canonical(bad)
  sig.write_bytes(contents)
  seal=json.loads((root/".g8_sealed").read_text())
  seal["signature_sha256"]=hashlib.sha256(contents).hexdigest()
  (root/".g8_sealed").write_bytes(gm.canonical(seal))
  s=env.S()
  assert not s.slot_ok(sid,deep=True)
  with s,pytest.raises(sv.SlotInvalid):
    s.boot()


def test_malformed_slot_id_and_traversal_never_authorized(env):
  install(env,"v1")
  s=env.S()
  for bad in ("../../bad","abc", "000001-z"*8, "000001-0123456789ab/../../"):
    assert not s.slot_ok(bad)
    with s,pytest.raises(sv.SlotInvalid):
      s.rollback(bad)


def test_malformed_state_does_not_make_unsigned_slot_bootable(env):
  sid,_=forged_slot(env)
  (env.base/"state.json").write_text('{"schema":"c7-g8-slotstate/1","seq":"not_an_int","last_good":"'+sid+'","pending":null}')
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.boot()
  assert s.live_slot() is None


def test_staging_symlink_cleanup_does_not_delete_outside_target(env):
  install(env,"v1")
  sentinel=env.tmp/"OUTSIDE_SENTINEL"
  sentinel.mkdir()
  (sentinel/"DO_NOT_REMOVE").write_bytes(b"outside")
  (env.base/"staging"/"hostile").symlink_to(sentinel,target_is_directory=True)
  s=env.S()
  with s:
    s.recover()
  assert (sentinel/"DO_NOT_REMOVE").read_bytes()==b"outside"
  assert not os.path.lexists(env.base/"staging"/"hostile")


def test_corrupted_manifest_cannot_be_fixed_by_rehashing_seal(env):
  sid=install(env,"v1")
  root=env.base/"slots"/sid
  data=json.loads((root/".g8_manifest.json").read_text())
  data["source_commit"]="attacker_unsigned"
  mb=gm.canonical(data)
  (root/".g8_manifest.json").write_bytes(mb)
  seal=json.loads((root/".g8_sealed").read_text())
  seal["manifest_sha256"]=hashlib.sha256(mb).hexdigest()
  (root/".g8_sealed").write_bytes(gm.canonical(seal))
  s=env.S()
  with s,pytest.raises(sv.SlotInvalid):
    s.boot()


def test_previous_valid_slot_recovery_with_signature(env):
  old=install(env,"v1")
  sid=install(env,"v2",confirm=False)
  (env.base/"slots"/sid/"lib"/"data.bin").write_bytes(b"x"*2048)
  s=env.S()
  with s:
    launcher,_=s.boot()
    assert launcher.endswith("launch_chffrplus.sh")
    assert s.live_slot()==old
    assert s.slot_ok(old,deep=True)

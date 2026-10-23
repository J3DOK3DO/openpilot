"""Fail-closed artifact verification tests. Keys here are DISPOSABLE DEV KEYS generated per test."""
import base64
import copy
import json
import os
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import g8_manifest as gm  # noqa: E402

COMMIT = "d2e2d24bdd61011aed0c2c99c8c277cd0bf94860"


def elf(machine):
  return b"\x7fELF\x02\x01\x01" + b"\x00" * 11 + machine.to_bytes(2, "little") + b"\x00" * 44


@pytest.fixture
def pkg(tmp_path):
  r = tmp_path / "pkg"
  (r / "bin").mkdir(parents=True)
  (r / "assets").mkdir()
  (r / "launch_chffrplus.sh").write_text("#!/bin/sh\n")
  os.chmod(r / "launch_chffrplus.sh", 0o755)
  (r / "bin" / "good_arm64").write_bytes(elf(183) + b"payload")
  (r / "bin" / "mcu_fw").write_bytes(elf(40) + b"fw")
  (r / "assets" / "a.txt").write_text("asset")
  os.symlink("a.txt", r / "assets" / "link")
  os.symlink("missing_dir", r / "assets" / "optional")
  return r


def make(pkg, dev=True, **kw):
  m = gm.build_manifest(str(pkg), COMMIT, foreign_elf_globs={"bin/mcu_fw": "MCU firmware, not executed on host"},
                        dangling_symlink_allow={"assets/optional": "runtime-managed optional link"},
                        with_elf_detail=False, **kw)
  k = Ed25519PrivateKey.generate()
  sig = gm.sign_manifest(m, k, "DEV-DISPOSABLE-NOT-A-RELEASE-KEY")
  trust = {"trusted_keys": [{"key_id": sig["key_id"], "pubkey_b64": gm.pub_b64(k),
                             "purpose": "dev-disposable" if dev else "production"}]}
  return m, sig, trust, k


def codes(res):
  return {c for c, _, _ in res["findings"]}


def test_valid_dev_signed_package_is_dev_only(pkg):
  m, sig, trust, _ = make(pkg)
  r = gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True)
  assert r["ok"] and r["trust_level"] == "DEV_ONLY", r


def test_default_policy_rejects_dev_key(pkg):
  m, sig, trust, _ = make(pkg)
  assert "SIG_DEV_KEY_NOT_ALLOWED" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT))


def test_production_purpose_key_accepted_only_if_trust_store_says_so(pkg):
  m, sig, trust, _ = make(pkg, dev=False)  # simulated trust-store entry in a test fixture only
  r = gm.verify_package(str(pkg), m, sig, trust, COMMIT)
  assert r["ok"] and r["trust_level"] == "PRODUCTION"


def test_unsigned_fails_closed(pkg):
  m, _, trust, _ = make(pkg)
  for bad in (None, {}, {"alg": "none"}):
    assert not gm.verify_package(str(pkg), m, bad, trust, COMMIT, allow_dev=True)["ok"]


def test_empty_or_missing_trust_store_fails_closed(pkg):
  m, sig, _, _ = make(pkg)
  for t in (None, {}, {"trusted_keys": []}):
    assert "SIG_KEY_UNTRUSTED" in codes(gm.verify_package(str(pkg), m, sig, t, COMMIT, allow_dev=True))


def test_wrong_key_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  other = Ed25519PrivateKey.generate()
  sig2 = gm.sign_manifest(m, other, "other")
  assert not gm.verify_package(str(pkg), m, sig2, trust, COMMIT, allow_dev=True)["ok"]


def test_key_id_spoof_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  other = Ed25519PrivateKey.generate()
  sig2 = gm.sign_manifest(m, other, "x")
  sig2["key_id"] = sig["key_id"]  # claims to be the trusted key
  assert "SIG_INVALID" in codes(gm.verify_package(str(pkg), m, sig2, trust, COMMIT, allow_dev=True))


def test_signature_bitflip_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  raw = bytearray(base64.b64decode(sig["signature"]))
  raw[0] ^= 1
  sig["signature"] = base64.b64encode(bytes(raw)).decode()
  assert "SIG_INVALID" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_garbage_signature_encoding_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  sig["signature"] = "!!!notbase64"
  assert not gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True)["ok"]


def test_domain_separation(pkg):
  m, sig, trust, _ = make(pkg)
  sig["domain"] = "some-other-protocol"
  assert "SIG_DOMAIN_MISMATCH" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_manifest_tamper_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  m2 = copy.deepcopy(m)
  next(e for e in m2["entries"] if e["path"] == "assets/a.txt")["sha256"] = "0" * 64
  assert not gm.verify_package(str(pkg), m2, sig, trust, COMMIT, allow_dev=True)["ok"]


def test_corrupted_file(pkg):
  m, sig, trust, _ = make(pkg)
  (pkg / "assets" / "a.txt").write_text("assex")
  assert "HASH_MISMATCH" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_truncated_incomplete_file(pkg):
  m, sig, trust, _ = make(pkg)
  with open(pkg / "bin" / "good_arm64", "r+b") as f:
    f.truncate(30)
  assert "SIZE_MISMATCH" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_missing_file_incomplete_package(pkg):
  m, sig, trust, _ = make(pkg)
  os.unlink(pkg / "assets" / "a.txt")
  assert "MISSING_PATH" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_extra_file_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  (pkg / "evil.py").write_text("x")
  assert "EXTRA_PATH" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_mode_change_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  os.chmod(pkg / "launch_chffrplus.sh", 0o644)
  assert "MODE_CHANGED" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_symlink_retarget_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  os.unlink(pkg / "assets" / "link")
  os.symlink("../launch_chffrplus.sh", pkg / "assets" / "link")
  assert "SYMLINK_TARGET_CHANGED" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_symlink_escape_rejected(pkg):
  os.symlink("../../etc/passwd", pkg / "assets" / "esc")
  m, sig, trust, _ = make(pkg)
  assert "SYMLINK_ESCAPES_ROOT" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_absolute_symlink_rejected(pkg):
  os.symlink("/etc/passwd", pkg / "assets" / "abs")
  m, sig, trust, _ = make(pkg)
  assert "SYMLINK_ESCAPES_ROOT" in codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_unallowlisted_dangling_symlink_rejected(pkg):
  os.symlink("nowhere", pkg / "assets" / "dangling2")
  m, sig, trust, _ = make(pkg)
  r = gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True)
  assert [p for c, p, _ in r["findings"] if c == "SYMLINK_DANGLING_UNALLOWED"] == ["assets/dangling2"]


def test_foreign_arch_elf_rejected_unless_allowlisted(pkg):
  (pkg / "bin" / "x86_tool").write_bytes(elf(62) + b"x")
  m, sig, trust, _ = make(pkg)
  r = gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True)
  assert [p for c, p, _ in r["findings"] if c == "ELF_FOREIGN_ARCH_UNALLOWED"] == ["bin/x86_tool"]


def test_elf_arch_swap_detected(pkg):
  m, sig, trust, _ = make(pkg)
  (pkg / "bin" / "good_arm64").write_bytes(elf(62) + b"payload")
  assert {"ELF_MACHINE_CHANGED", "HASH_MISMATCH"} <= codes(gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True))


def test_source_commit_mismatch(pkg):
  m, sig, trust, _ = make(pkg)
  assert "SOURCE_COMMIT_MISMATCH" in codes(gm.verify_package(str(pkg), m, sig, trust, "f1dced93dd3596d62a03299478ea582517802177", allow_dev=True))


@pytest.mark.parametrize("bad", ["../x", "/abs", "a/../../b", "", "a//b", "a/./b"])
def test_manifest_path_traversal_rejected(pkg, bad):
  m, _, _, _ = make(pkg)
  m["entries"].append({"path": bad, "type": "file", "mode": "0644", "size": 0, "sha256": "0" * 64})
  assert "MANIFEST_BAD_PATH" in {c for c, _, _ in gm.verify_tree(str(pkg), m)}


def test_duplicate_manifest_path_rejected(pkg):
  m, _, _, _ = make(pkg)
  m["entries"].append(copy.deepcopy(m["entries"][0]))
  assert "MANIFEST_DUPLICATE_PATH" in {c for c, _, _ in gm.verify_tree(str(pkg), m)}


def test_unknown_schema_rejected(pkg):
  m, _, _, _ = make(pkg)
  m["schema"] = "c7-g8-manifest/999"
  assert gm.verify_tree(str(pkg), m)[0][0] == "SCHEMA_UNKNOWN"


def test_special_file_rejected(pkg):
  m, sig, trust, _ = make(pkg)
  os.mkfifo(pkg / "fifo")
  r = gm.verify_package(str(pkg), m, sig, trust, COMMIT, allow_dev=True)
  assert "EXTRA_PATH" in codes(r)
  m2 = gm.build_manifest(str(pkg), COMMIT, with_elf_detail=False)
  assert any(e["type"] == "special" for e in m2["entries"])
  assert "MANIFEST_BAD_TYPE" in {c for c, _, _ in gm.verify_tree(str(pkg), m2)}


def test_cli_fails_closed_without_trusted_production_key(pkg, tmp_path):
  m, sig, trust, _ = make(pkg)
  for n, o in (("m", m), ("s", sig), ("t", trust)):
    (tmp_path / f"{n}.json").write_text(json.dumps(o))
  base = [sys.executable, gm.__file__, "verify", str(pkg), "--manifest", str(tmp_path / "m.json"),
          "--sig", str(tmp_path / "s.json"), "--trust", str(tmp_path / "t.json"), "--commit", COMMIT]
  assert subprocess.run(base, capture_output=True).returncode == 2
  assert subprocess.run(base + ["--allow-dev-key"], capture_output=True).returncode == 10
  missing = list(base)
  missing[5] = "/nonexistent"
  assert subprocess.run(missing, capture_output=True).returncode == 2


def test_real_readelf_dynamic_extraction():
  d = gm.elf_dynamic(sys.executable)
  if d is None:
    pytest.skip("readelf unavailable")
  assert any(n.startswith("libc.so") for n in d["needed"])

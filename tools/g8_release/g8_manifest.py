#!/usr/bin/env python3
"""C7 G8 release manifest builder and fail-closed verifier (host-side, not deployed).

A tree is accepted only if EVERY check passes: the manifest is signed by a trusted
key, the signature covers the exact canonical manifest bytes, and the tree on disk
matches the manifest exactly (no missing, extra, modified, re-moded or re-linked
entries; no unexpected ELF architecture; no unallowlisted dangling symlink).

Trust model: ``trust.json`` lists keys with purpose "production" or
"dev-disposable". By default ONLY production keys are accepted. Dev keys verify
only with allow_dev=True and the result is labelled DEV_ONLY. No production key
exists in this repository, so default verification of any package fails closed.
"""
import argparse
import base64
import fnmatch
import hashlib
import json
import os
import stat
import subprocess
import sys

SCHEMA = "c7-g8-manifest/1"
SIG_DOMAIN = b"c7-g8-release-manifest/v1"
EM_NAMES = {183: "AArch64", 62: "x86_64", 40: "ARM", 3: "x86", 243: "RISC-V"}
MAX_FILE_SIZE = 1 << 33


class VerifyError(Exception):
  pass


def canonical(obj) -> bytes:
  return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_file(path, bufsize=1 << 20):
  h = hashlib.sha256()
  with open(path, "rb") as f:
    while chunk := f.read(bufsize):
      h.update(chunk)
  return h.hexdigest()


def elf_machine(path):
  """Return machine name for an ELF file, None if not ELF."""
  try:
    with open(path, "rb") as f:
      hdr = f.read(20)
  except OSError:
    return None
  if len(hdr) < 20 or hdr[:4] != b"\x7fELF":
    return None
  order = "little" if hdr[5] == 1 else "big"
  m = int.from_bytes(hdr[18:20], order)
  return EM_NAMES.get(m, f"EM_{m}")


def elf_dynamic(path):
  """NEEDED/SONAME/RPATH via readelf; None if unavailable."""
  try:
    out = subprocess.run(["readelf", "-d", path], capture_output=True, text=True, timeout=30).stdout
  except (OSError, subprocess.SubprocessError):
    return None
  d = {"needed": [], "soname": None, "runpath": None}
  for line in out.splitlines():
    if "(NEEDED)" in line:
      d["needed"].append(line.split("[")[1].split("]")[0])
    elif "(SONAME)" in line:
      d["soname"] = line.split("[")[1].split("]")[0]
    elif "(RUNPATH)" in line or "(RPATH)" in line:
      d["runpath"] = line.split("[")[1].split("]")[0]
  return d


def _safe_rel(p):
  return p and not p.startswith("/") and ".." not in p.split("/") and "\x00" not in p and p == os.path.normpath(p)


def _link_escapes(root, rel, target):
  """True if symlink at rel with target resolves (lexically) outside root."""
  if target.startswith("/"):
    return True
  base = os.path.dirname(rel)
  res = os.path.normpath(os.path.join(base, target))
  return res == ".." or res.startswith("../")


def scan_tree(root, with_elf_detail=True):
  entries = []
  for dp, dns, fns in os.walk(root, followlinks=False):
    dns.sort()
    for name in sorted(dns + fns):
      full = os.path.join(dp, name)
      rel = os.path.relpath(full, root)
      st = os.lstat(full)
      mode = format(stat.S_IMODE(st.st_mode), "04o")
      if stat.S_ISLNK(st.st_mode):
        tgt = os.readlink(full)
        entries.append({"path": rel, "type": "symlink", "target": tgt,
                        "target_exists": os.path.exists(full), "escapes_root": _link_escapes(root, rel, tgt)})
      elif stat.S_ISDIR(st.st_mode):
        entries.append({"path": rel, "type": "dir", "mode": mode})
      elif stat.S_ISREG(st.st_mode):
        e = {"path": rel, "type": "file", "mode": mode, "size": st.st_size, "sha256": sha256_file(full)}
        m = elf_machine(full)
        if m:
          e["elf_machine"] = m
          if with_elf_detail:
            e["elf_dynamic"] = elf_dynamic(full)
        entries.append(e)
      else:
        entries.append({"path": rel, "type": "special", "mode": mode})
  entries.sort(key=lambda e: e["path"])
  return entries


def build_manifest(root, source_commit, target_machine="AArch64", foreign_elf_globs=(),
                   dangling_symlink_allow=None, provenance=None, with_elf_detail=True):
  """dangling_symlink_allow: {path: reason}. foreign_elf_globs: {glob: reason}."""
  entries = scan_tree(root, with_elf_detail)
  return {
    "schema": SCHEMA, "source_commit": source_commit, "target_machine": target_machine,
    "foreign_elf_allow": dict(foreign_elf_globs), "dangling_symlink_allow": dict(dangling_symlink_allow or {}),
    "provenance": provenance or {}, "entries": entries,
  }


# ----------------------------------------------------------------------- signing
def key_id(pub_raw: bytes) -> str:
  return hashlib.sha256(pub_raw).hexdigest()[:16]


def sign_manifest(manifest, private_key, label):
  """private_key: cryptography Ed25519PrivateKey. Caller owns key custody."""
  from cryptography.hazmat.primitives import serialization
  pub = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
  mb = canonical(manifest)
  sig = private_key.sign(SIG_DOMAIN + b"\x00" + mb)
  return {"alg": "ed25519", "key_id": key_id(pub), "key_label": label, "domain": SIG_DOMAIN.decode(),
          "manifest_sha256": hashlib.sha256(mb).hexdigest(), "signature": base64.b64encode(sig).decode()}


def pub_b64(private_key):
  from cryptography.hazmat.primitives import serialization
  return base64.b64encode(private_key.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()


def verify_signature(manifest, sig, trust, allow_dev=False):
  """Returns trust level string ('PRODUCTION' or 'DEV_ONLY'); raises VerifyError."""
  from cryptography.exceptions import InvalidSignature
  from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
  if not isinstance(sig, dict) or sig.get("alg") != "ed25519":
    raise VerifyError("SIG_MISSING_OR_BAD_ALG")
  if sig.get("domain") != SIG_DOMAIN.decode():
    raise VerifyError("SIG_DOMAIN_MISMATCH")
  keys = {k.get("key_id"): k for k in (trust or {}).get("trusted_keys", [])}
  k = keys.get(sig.get("key_id"))
  if k is None:
    raise VerifyError("SIG_KEY_UNTRUSTED")
  purpose = k.get("purpose")
  if purpose == "dev-disposable" and not allow_dev:
    raise VerifyError("SIG_DEV_KEY_NOT_ALLOWED")
  if purpose not in ("production", "dev-disposable"):
    raise VerifyError("SIG_KEY_PURPOSE_UNKNOWN")
  try:
    pub = base64.b64decode(k["pubkey_b64"], validate=True)
    if key_id(pub) != k["key_id"]:
      raise VerifyError("SIG_KEY_ID_MISMATCH")
    mb = canonical(manifest)
    if hashlib.sha256(mb).hexdigest() != sig.get("manifest_sha256"):
      raise VerifyError("SIG_MANIFEST_DIGEST_MISMATCH")
    Ed25519PublicKey.from_public_bytes(pub).verify(base64.b64decode(sig["signature"], validate=True),
                                                   SIG_DOMAIN + b"\x00" + mb)
  except InvalidSignature:
    raise VerifyError("SIG_INVALID")
  except (KeyError, ValueError, TypeError):
    raise VerifyError("SIG_MALFORMED")
  return "PRODUCTION" if purpose == "production" else "DEV_ONLY"


# ----------------------------------------------------------------------- verification
def check_manifest_structure(m):
  f = []
  if not isinstance(m, dict) or m.get("schema") != SCHEMA:
    return [("SCHEMA_UNKNOWN", "", str(m.get("schema") if isinstance(m, dict) else m))]
  seen = set()
  for e in m.get("entries", []):
    p = e.get("path")
    if not _safe_rel(p):
      f.append(("MANIFEST_BAD_PATH", str(p), ""))
      continue
    if p in seen:
      f.append(("MANIFEST_DUPLICATE_PATH", p, ""))
    seen.add(p)
    if e.get("type") not in ("file", "symlink", "dir"):
      f.append(("MANIFEST_BAD_TYPE", p, str(e.get("type"))))
  if not m.get("source_commit"):
    f.append(("MANIFEST_NO_SOURCE_COMMIT", "", ""))
  return f


def verify_tree_ignoring(root, manifest, ignore, deep=True):
  return verify_tree(root, manifest, deep=deep, ignore=frozenset(ignore))


def verify_tree(root, manifest, expected_commit=None, deep=True, with_elf=True, ignore=frozenset()):
  """Return list of (code, path, detail) findings; empty list means tree matches."""
  f = check_manifest_structure(manifest)
  if f:
    return f
  if expected_commit is not None and manifest["source_commit"] != expected_commit:
    f.append(("SOURCE_COMMIT_MISMATCH", "", f"{manifest['source_commit']} != {expected_commit}"))
  want = {e["path"]: e for e in manifest["entries"]}
  have = {}
  for dp, dns, fns in os.walk(root, followlinks=False):
    for name in dns + fns:
      full = os.path.join(dp, name)
      rp = os.path.relpath(full, root)
      if rp not in ignore:
        have[rp] = full
  for p in sorted(set(have) - set(want)):
    f.append(("EXTRA_PATH", p, ""))
  for p in sorted(set(want) - set(have)):
    f.append(("MISSING_PATH", p, ""))
  tm = manifest.get("target_machine")
  foreign = manifest.get("foreign_elf_allow", {})
  dang = manifest.get("dangling_symlink_allow", {})
  for p in sorted(set(want) & set(have)):
    e, full = want[p], have[p]
    st = os.lstat(full)
    kind = "symlink" if stat.S_ISLNK(st.st_mode) else "dir" if stat.S_ISDIR(st.st_mode) else \
           "file" if stat.S_ISREG(st.st_mode) else "special"
    if kind != e["type"]:
      f.append(("TYPE_CHANGED", p, f"{e['type']}->{kind}"))
      continue
    if kind == "symlink":
      t = os.readlink(full)
      if t != e["target"]:
        f.append(("SYMLINK_TARGET_CHANGED", p, f"{e['target']}->{t}"))
      if _link_escapes(root, p, t):
        f.append(("SYMLINK_ESCAPES_ROOT", p, t))
      elif not os.path.exists(full) and p not in dang:
        f.append(("SYMLINK_DANGLING_UNALLOWED", p, t))
    elif kind == "dir":
      if format(stat.S_IMODE(st.st_mode), "04o") != e["mode"]:
        f.append(("MODE_CHANGED", p, ""))
    else:
      if format(stat.S_IMODE(st.st_mode), "04o") != e["mode"]:
        f.append(("MODE_CHANGED", p, f"{e['mode']}->{format(stat.S_IMODE(st.st_mode), '04o')}"))
      if st.st_size != e["size"]:
        f.append(("SIZE_MISMATCH", p, f"{e['size']}->{st.st_size}"))
      elif deep and sha256_file(full) != e["sha256"]:
        f.append(("HASH_MISMATCH", p, ""))
      if with_elf:
        m = elf_machine(full)
        if m != e.get("elf_machine"):
          f.append(("ELF_MACHINE_CHANGED", p, f"{e.get('elf_machine')}->{m}"))
        if m and m != tm and not any(fnmatch.fnmatch(p, g) for g in foreign):
          f.append(("ELF_FOREIGN_ARCH_UNALLOWED", p, f"{m} (target {tm})"))
  return f


def verify_package(root, manifest, sig, trust, expected_commit=None, allow_dev=False, deep=True):
  """Full fail-closed gate. Returns dict(ok, trust_level, findings)."""
  findings = []
  level = None
  try:
    level = verify_signature(manifest, sig, trust, allow_dev)
  except VerifyError as e:
    findings.append((str(e), "", ""))
  except Exception as e:  # never let an unexpected error read as success
    findings.append(("SIG_UNEXPECTED_ERROR", "", repr(e)))
  try:
    findings += verify_tree(root, manifest, expected_commit, deep)
  except Exception as e:
    findings.append(("TREE_VERIFY_UNEXPECTED_ERROR", "", repr(e)))
  return {"ok": not findings, "trust_level": level if not findings else None, "findings": findings}


def _load(p):
  with open(p) as f:
    return json.load(f)


def main(argv=None):
  ap = argparse.ArgumentParser()
  sp = ap.add_subparsers(dest="cmd", required=True)
  v = sp.add_parser("verify")
  v.add_argument("root"); v.add_argument("--manifest", required=True); v.add_argument("--sig", required=True)
  v.add_argument("--trust", required=True); v.add_argument("--commit"); v.add_argument("--allow-dev-key", action="store_true")
  a = ap.parse_args(argv)
  try:
    r = verify_package(a.root, _load(a.manifest), _load(a.sig), _load(a.trust), a.commit, a.allow_dev_key)
  except (OSError, ValueError) as e:
    print(json.dumps({"ok": False, "findings": [("INPUT_ERROR", "", repr(e))]}))
    return 2
  print(json.dumps(r, indent=1))
  if not r["ok"]:
    return 2
  return 0 if r["trust_level"] == "PRODUCTION" else 10


if __name__ == "__main__":
  sys.exit(main())

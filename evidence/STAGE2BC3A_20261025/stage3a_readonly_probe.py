#!/usr/bin/env python3
"""Read-only remote comma capability inquiry; no device filesystem writes."""
from __future__ import annotations
import datetime
import json
import pathlib
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"evidence/STAGE2BC3A_20261025/STAGE3A_COMMA_READONLY_DEVICE_AUDIT.json"

REMOTE = r'''
from __future__ import annotations
import json, os, pathlib, subprocess, platform, hashlib, stat, re

def safe_run(*args, timeout=12):
  try:
    r=subprocess.run(args,check=False,text=True,capture_output=True,timeout=timeout)
    return r.stdout.strip() if r.returncode==0 else None
  except Exception:
    return None

def digest(path):
  h=hashlib.sha256()
  with pathlib.Path(path).open("rb") as f:
    for b in iter(lambda:f.read(1048576),b""):
      h.update(b)
  return h.hexdigest()

def modes(path):
  x=os.lstat(path)
  return {"mode":format(stat.S_IMODE(x.st_mode),"04o"),
          "type": ("symlink" if stat.S_ISLNK(x.st_mode) else
                   "directory" if stat.S_ISDIR(x.st_mode) else
                   "regular" if stat.S_ISREG(x.st_mode) else "other")}

rootfs=None; datamount=None
for line in pathlib.Path("/proc/self/mounts").read_text().splitlines():
  parts=line.split()
  if len(parts)<4:continue
  if parts[1]=="/":rootfs={"fstype":parts[2],"is_ro":"ro" in parts[3].split(",")}
  if parts[1]=="/data":datamount={"fstype":parts[2],"is_ro":"ro" in parts[3].split(",")}
cmdline=pathlib.Path("/proc/cmdline").read_text().split()
keys=set(x.split("=",1)[0] for x in cmdline)
selinux=[x.split("=",1)[1] for x in cmdline if x.startswith("androidboot.selinux=")]
stage=pathlib.Path("/data/g8_rc3_inert_qualification_20261025")
archive=stage/"G8_F12_RC3_FROZEN_UNSIGNED_HOLD_20261025.tar.gz"
vfs=os.statvfs("/data")
unit_text=safe_run("systemctl","list-unit-files","--type=service","--no-legend","--no-pager") or ""
services=sorted(set(x.split()[0] for x in unit_text.splitlines()
                    if x and re.search(r"openpilot|manager|supervisor|agnos|panda",x,re.I)))[:35]
print(json.dumps({
 "schema":"G8_F12_RC3_AGNOS_READONLY_QUALIFICATION_V1",
 "platform_arch":platform.machine(),
 "agnos_version":pathlib.Path("/VERSION").read_text().strip(),
 "kernel_release":platform.release(),
 "glibc_version":(safe_run("ldd","--version") or "").splitlines()[0:1],
 "boot_slot":safe_run("abctl","--boot_slot"),
 "active_openpilot_commit":safe_run("git","-C","/data/openpilot","rev-parse","HEAD"),
 "active_openpilot_launcher_sha256":digest("/data/openpilot/launch_chffrplus.sh"),
 "active_application_is_shared_data":os.path.realpath("/data/openpilot")=="/data/openpilot",
 "root_mount":rootfs,
 "data_mount":datamount,
 "data_free_bytes":vfs.f_bavail*vfs.f_frsize,
 "selinux_cmdline_mode":selinux if selinux else ["UNDETERMINED"],
 "cmdline_names_indicate_verity":any("verity" in k.lower() for k in keys),
 "verified_boot_independently_proven":False,
 "tee_device_present":bool(list(pathlib.Path("/dev").glob("tee*"))),
 "tpm_device_present":bool(list(pathlib.Path("/dev").glob("tpm*"))),
 "rpmb_device_present":bool(list(pathlib.Path("/dev").glob("*rpmb*"))),
 "rpmb_hardware_attestation_proven":False,
 "systemd_candidate_services":services,
 "staging_directory":str(stage),
 "staging_directory_mode":modes(stage),
 "archive_mode":modes(archive),
 "archive_size_bytes":archive.stat().st_size,
 "staged_archive_sha256":digest(archive),
 "device_app_supervisor_cryptographically_verified":False,
 "physical_panda_can_isolation_evidenced":False,
 "powercut_recovery_evidenced":False,
 "ssh_check_is_not_hardware_safety_signoff":True,
 "device_mutations_performed":False,
 "launch_install_or_can_attempted":False,
},sort_keys=True))
'''
def main():
  r=subprocess.run(
    ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=7","comma","python3 -"],
    input=REMOTE,text=True,capture_output=True,timeout=75)
  if r.returncode:
    raise SystemExit("READONLY_DEVICE_CHECK_FAILED: "+r.stderr[:400])
  result=json.loads(r.stdout)
  assert result["platform_arch"]=="aarch64"
  assert result["agnos_version"]=="19.8.1"
  assert result["active_openpilot_commit"]=="7b4db9a26010ba9899eef242d3ca49b33cbcca9c"
  assert result["boot_slot"]=="_a"
  assert result["active_openpilot_launcher_sha256"]=="b70486dd999cd7e60ed27c09a643dfb3d28ebc74f3cc11e02dac01e1468ec98e"
  assert result["staged_archive_sha256"]=="a0bec9fcba3a38de40daf0928e714a8e877565e438b311fdd37fab67e8e30b9b"
  result["checked_at_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
  result["stage3a_disposition"]="READONLY_DEVICE_INVENTORY_PASS_PROTECTED_SUPERVISOR_HOLD"
  result["installation_authorized"]=False
  OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
  for key in ("platform_arch","agnos_version","boot_slot","data_free_bytes",
              "root_mount","data_mount","selinux_cmdline_mode","tee_device_present",
              "tpm_device_present","rpmb_device_present","systemd_candidate_services",
              "stage3a_disposition"):
    print(key,":",result[key])
  print("REPORT",OUTPUT)
if __name__=="__main__":
  main()

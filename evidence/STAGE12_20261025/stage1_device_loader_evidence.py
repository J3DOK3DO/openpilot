#!/usr/bin/env python3
"""Read-only per-library device hashes and ELF headers for referenced cache libs."""
import pathlib,hashlib,json,subprocess,datetime
root=pathlib.Path(__file__).resolve().parents[2]
out=root/"evidence/STAGE12_20261025"
stage1=json.loads((out/"STAGE1_AGNOS_ARM64_STATIC_COMPATIBILITY.json").read_text())
libs=stage1["device_standard_library_cache_hits"]
remote=r'''
import json,hashlib,pathlib,subprocess,re,stat,sys
requested=json.load(sys.stdin)
def h(path):
 sha=hashlib.sha256(); p=pathlib.Path(path)
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):sha.update(b)
 return sha.hexdigest()
checks={}
for soname, candidates in requested.items():
 resolved=[]
 for candidate in candidates:
  p=pathlib.Path(candidate)
  try:
   absolute=p.resolve(strict=True)
   ret=subprocess.run(["readelf","-h",str(absolute)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=12)
   valid=ret.returncode==0 and bool(re.search(r"Machine:\s*AArch64",ret.stdout))
   resolved.append({"cache_path":candidate,"resolved_path":str(absolute),"byte_size":absolute.stat().st_size,
                    "sha256":h(absolute) if valid else None,"native_aarch64_elf":valid})
  except (OSError,subprocess.TimeoutExpired) as e:
   resolved.append({"cache_path":candidate,"read_error":type(e).__name__})
 checks[soname]=resolved
print(json.dumps(checks,sort_keys=True))
'''
# Ship the code and its input via one read-only inline SSH Python -c script.
import base64
payload=base64.b64encode(json.dumps(libs,sort_keys=True).encode()).decode()
wrapped="import base64,io,sys\n"+remote.replace("requested=json.load(sys.stdin)","requested=json.loads(base64.b64decode("+repr(payload)+"))")
r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=7","comma","python3 -"],input=wrapped,text=True,capture_output=True,timeout=75)
if r.returncode:raise RuntimeError(r.stderr[:500])
actual=json.loads(r.stdout)
miss=[k for k,v in actual.items() if not v or not any(x.get("native_aarch64_elf") for x in v)]
report={"schema":"G8_F12_RC3_DEVICE_LOADER_CACHE_COMPONENT_DIGESTS_V1",
        "utc":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "stage1_standard_dependency_hashes":actual,"all_cache_hits_have_aarch64_elf":not miss,
        "unverified_libraries":miss,"source_executables_loaded":False,
        "device_state_modified":False,"production_authorized":False}
f=out/"STAGE1_DEVICE_LOADER_LIB_SHA256.json";f.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
print("TARGET_LIBRARIES",len(libs),"HARD_CHECK_PASS",not miss,"UNVERIFIED",miss)
print("DEVICE_EVIDENCE",f)

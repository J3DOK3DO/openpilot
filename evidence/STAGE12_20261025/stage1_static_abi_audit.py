#!/usr/bin/env python3
"""Offline ELF and read-only remote AGNOS inventory; never loads RC3 code."""
import hashlib,json,pathlib,re,subprocess,sys,datetime
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/"evidence/STAGE12_20261025"
PINNED=ROOT/"G8_F12_RC3_PINNED_COMPONENTS.json"
def run(args,timeout=40):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout)
 if p.returncode: raise RuntimeError("failed "+str(args)+" "+p.stderr[:220])
 return p.stdout
manifest=json.loads(PINNED.read_text())
items=manifest["source_built_AArch64_elfs"]
inventory=[]
for item in items:
 f=ROOT/item["path"]; raw=f.read_bytes()
 actual=hashlib.sha256(raw).hexdigest()
 if len(raw)!=item["size_bytes"] or actual!=item["sha256"]: raise RuntimeError("PINNED_DIGEST_MISMATCH:"+item["path"])
 header=run(["readelf","-h",str(f)])
 dyn=run(["readelf","-d",str(f)])
 ph=run(["readelf","-l",str(f)])
 versions=run(["readelf","--version-info",str(f)])
 machine=re.search(r"Machine:\s*(.*)",header)
 if machine is None or "AArch64" not in machine.group(1): raise RuntimeError("WRONG_ARCH:"+item["path"])
 needed=re.findall(r"\(NEEDED\).*?\[([^]]+)\]",dyn)
 runpath=re.findall(r"\((?:RUNPATH|RPATH)\).*?\[([^]]+)\]",dyn)
 interpreter=re.findall(r"Requesting program interpreter: ([^\]]+)\]",ph)
 glibc=sorted(set(re.findall(r"\bGLIBC_\d+(?:\.\d+)+\b",versions)))
 cpp=sorted(set(re.findall(r"\b(?:GLIBCXX|CXXABI)_\d+(?:\.\d+)+\b",versions)))
 inventory.append({"path":item["path"],"sha256":actual,"size_bytes":len(raw),"machine":"AArch64","dynamic_dependencies":needed,"embedded_search_paths":runpath,"elf_interpreter":interpreter,"version_requirements":{"glibc":glibc,"cpp_abi":cpp}})
remote=r'''
import json,os,re,platform,subprocess,sys,glob
def call(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=12)
 return p.stdout if p.returncode==0 else ""
cache=call(["ldconfig","-p"])
entries={}
for line in cache.splitlines():
 m=re.match(r"\s*([^\s]+)\s+\(([^)]*)\)\s+=>\s+(\S+)",line)
 if m and "AArch64" in m.group(2):
  entries.setdefault(m.group(1),[]).append(m.group(3))
print(json.dumps({
 "uname_machine":platform.machine(),
 "kernel":platform.release(),
 "agnos":open("/VERSION").read().strip(),
 "python_version":platform.python_version(),
 "glibc":call(["ldd","--version"]).splitlines()[0:1],
 "ldconfig_aarch64":entries,
 "venv_ffmpeg_library_search_path_present":os.path.isdir("/usr/local/venv/lib/python3.12/site-packages/ffmpeg/install/lib"),
 "usr_local_lib_present":os.path.isdir("/usr/local/lib"),
 "loader_path_present":os.path.exists("/lib/ld-linux-aarch64.so.1"),
 "driver_nodes":{name:bool(glob.glob(name)) for name in ["/dev/kgsl*","/dev/adsprpc*","/dev/dri/renderD*","/dev/spidev*"]},
 "app_commit":call(["git","-C","/data/openpilot","rev-parse","HEAD"]).strip(),
 "os_boot_slot":call(["abctl","--boot_slot"]).strip(),
},sort_keys=True))
'''
p=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=8","comma","python3 -"],input=remote,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
if p.returncode:raise RuntimeError("DEVICE_READONLY_QUERY_FAILED: "+p.stderr[:450])
device=json.loads(p.stdout)
needs=sorted(set(n for i in inventory for n in i["dynamic_dependencies"]))
cache=device["ldconfig_aarch64"]
missing=[name for name in needs if name not in cache]
# A missing cache hit is not proof of a missing library: app-local files may supply it.
unresolved=[{"name":n,"classification":"NOT_IN_STANDARD_DEVICE_LOADER_CACHE_REQUIRES_APP_LOCAL_OR_VENDOR_LOOKUP"} for n in missing]
rpaths=sorted(set(path for item in inventory for path in item["embedded_search_paths"]))
status="STATIC_ABI_REVIEW_HOLD" if missing else "STATIC_ABI_INVENTORY_PASS_RUNTIME_UNVERIFIED"
evidence={
 "schema":"G8_F12_RC3_STAGE1_STATIC_ABI_AGNOS_READONLY_V1",
 "generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
 "source_frozen_commit":"bbb771a2fadf5af96f532e798846ba8171483e50",
 "pinned_component_count":len(items),"verified_component_count":len(inventory),
 "unique_needed_shared_libraries":needs,
 "device_ldconfig_cache_missing_names":missing,
 "device_standard_library_cache_hits":{n:cache[n] for n in needs if n in cache},
 "unresolved_library_queries":unresolved,
 "device":device,
 "embedded_search_paths":rpaths,
 "components":inventory,
 "result":status,
 "device_elf_load_performed":False,
 "device_app_runtime_qualified":False,
 "device_files_modified":False,
 "Panda_CAN_operations":False,
 "production_install_authorized":False,
 "notes":["Readelf on Ubuntu scanned pinned ARM64 files; device only reported loader configuration.", "ldconfig cache absence is not authoritative for app-local or vendor library paths.", "ELF headers and library name checks do not prove Python extension ABI/runtime compatibility or Honda hardware safety.", "DO NOT load pandad or model shared object on a device connected to a vehicle without physical CAN isolation."]
}
path=OUT/"STAGE1_AGNOS_ARM64_STATIC_COMPATIBILITY.json"
path.write_text(json.dumps(evidence,sort_keys=True,indent=2)+"\n")
print("STATIC_COMPONENTS",len(items),"VERIFIED",len(inventory))
print("UNIQUE_DEPENDENCIES",needs)
print("NEEDS_APP_OR_VENDOR_RESOLUTION",missing)
print("EMBEDDED_SEARCH_PATHS",rpaths)
print("DEVICE_ARCH",device["uname_machine"],"AGNOS",device["agnos"],"GLIBC",device["glibc"])
print("STATUS",status)
print("REPORT",path)

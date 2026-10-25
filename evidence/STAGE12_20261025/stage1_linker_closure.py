#!/usr/bin/env python3
"""Static RPATH/RUNPATH dependency closure, host-only; never dlopen or run payload."""
import hashlib,json,pathlib,re,subprocess,tarfile,datetime,sys
root=pathlib.Path(__file__).resolve().parents[2]
out=root/"evidence/STAGE12_20261025"
source=json.loads((out/"STAGE1_AGNOS_ARM64_STATIC_COMPATIBILITY.json").read_text())
cache=source["device"]["ldconfig_aarch64"]
roots=[x["path"] for x in source["components"]]
assets=root/"third_party/acados/larch64/lib"
seen=set(); closure=[]; unresolved=[]; malformed=[]; maxdepth=16
def metadata(relative):
 p=root/relative
 if not p.exists() or not p.is_file():raise RuntimeError("ABSENT "+relative)
 if p.suffix!=".so" and ".so." not in p.name and p.name!="pandad": pass
 cp=subprocess.run(["readelf","-d",str(p)],capture_output=True,text=True)
 hp=subprocess.run(["readelf","-h",str(p)],capture_output=True,text=True)
 if cp.returncode or hp.returncode or "AArch64" not in hp.stdout:
  raise RuntimeError("INVALID_ELF "+relative)
 dyn=cp.stdout
 needed=re.findall(r"\(NEEDED\).*?\[([^]]+)\]",dyn)
 soname=re.findall(r"\(SONAME\).*?\[([^]]+)\]",dyn)
 legacy=re.findall(r"\(RPATH\).*?\[([^]]+)\]",dyn)
 runpath=re.findall(r"\(RUNPATH\).*?\[([^]]+)\]",dyn)
 return {"needed":needed,"soname":soname,"rpath":legacy,"runpath":runpath}
def expand(entries,origin):
 candidates=[]
 for entry in entries:
  for segment in entry.split(":"):
   if segment.startswith("/"):
    continue # OS location is handled by cache rather than assuming host path
   if "$ORIGIN" not in segment:
    continue
   candidate=segment.replace("${ORIGIN}",str(origin)).replace("$ORIGIN",str(origin))
   absolute=(root/candidate).resolve()
   if not absolute.is_relative_to(root):
    malformed.append(str(segment));continue
   candidates.append(absolute)
 return candidates
def walk(relative, inherited, origin_parent=None,depth=0):
 if depth>maxdepth:raise RuntimeError("dependency recursion depth exceeded")
 key=(relative,tuple(inherited))
 if key in seen:return
 seen.add(key)
 meta=metadata(relative)
 parent=(root/relative).parent
 direct_paths=expand(meta["rpath"]+meta["runpath"],parent)
 next_inherit=inherited+expand(meta["rpath"],parent) if meta["rpath"] and not meta["runpath"] else inherited
 for name in meta["needed"]:
  if name in cache or name=="ld-linux-aarch64.so.1":
   closure.append({"from":relative,"needed":name,"resolution":"DEVICE_STANDARD_LOADER_CACHE_OR_INTERPRETER"})
   continue
  resolved=None
  for directory in direct_paths+inherited:
   potential=directory/name
   if potential.exists() and potential.is_file() and potential.resolve().is_relative_to(root):
    resolved=potential.resolve().relative_to(root).as_posix()
    break
  if not resolved:
   # relative lookup for DT_NEEDED may rely on LD_LIBRARY_PATH: DO NOT ASSUME.
   unresolved.append({"from":relative,"needed":name,"searched_rpath_roots":list(map(str,direct_paths+inherited))})
   continue
  closure.append({"from":relative,"needed":name,"resolution":"BUNDLED_RELATIVE_RPATH","resolved_relative_path":resolved})
  walk(resolved,next_inherit,depth=depth+1)
for rootlib in roots:
 walk(rootlib,[])
needed_archive={x["resolved_relative_path"] for x in closure if x["resolution"]=="BUNDLED_RELATIVE_RPATH"}
archive=pathlib.Path("/mnt/commadrive/g8-f12-rc3-owner-authorized-preflight-20261025/output/G8_F12_RC3_FROZEN_UNSIGNED_HOLD_20261025.tar.gz")
with tarfile.open(archive,"r:gz") as tf:
 members={x.name[len("g8-f12-rc3/"):]:x for x in tf if x.name.startswith("g8-f12-rc3/")}
archive_verified={}
for x in sorted(needed_archive):
 t=members.get(x)
 if t is None or not t.isfile():
  unresolved.append({"from":"ARCHIVE","needed":x,"reason":"PACKAGED_LIBRARY_MISSING_OR_NONREGULAR"})
 else:
  digest=hashlib.sha256()
  with tarfile.open(archive,"r:gz") as tar:
   f=tar.extractfile("g8-f12-rc3/"+x)
   for b in iter(lambda:f.read(1048576),b""):digest.update(b)
  localhash=hashlib.sha256((root/x).read_bytes()).hexdigest()
  if digest.hexdigest()!=localhash:unresolved.append({"from":"ARCHIVE","needed":x,"reason":"GIT_ARCHIVE_HASH_MISMATCH"})
  else:archive_verified[x]={"sha256":localhash,"bytes":t.size}
report={
 "schema":"G8_F12_RC3_STAGE1_STATIC_LINKER_CLOSURE_V1",
 "timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
 "source_commit":"bbb771a2fadf5af96f532e798846ba8171483e50",
 "host_reviewed_ELF_count":len(roots),
 "archive_bundled_dependencies_verified":len(archive_verified),
 "archive_bundled_files":archive_verified,
 "device_standard_cache_dependency_occurrences":sum(x["resolution"]=="DEVICE_STANDARD_LOADER_CACHE_OR_INTERPRETER" for x in closure),
 "bundled_dependency_occurrences":sum(x["resolution"]=="BUNDLED_RELATIVE_RPATH" for x in closure),
 "resolved_edges":closure,
 "unresolved_edges":unresolved,
 "malformed_path_segments":malformed,
 "stage1_static_linker_closure_pass":not unresolved and not malformed,
 "native_runtime_executed":False,
 "runtime_compatibility_proven":False,
 "device_system_modified":False,
 "Panda_CAN_accessed":False,
 "installation_authorized":False,
 "physical_test_status":"HOLD",
 "notes":["Calculated using static DT_RPATH/DT_RUNPATH and the existing device loader cache, not a live dlopen.","Each app-local library is independently checked against the frozen archive.","Transitive DT_RPATH is modeled; host review does not reproduce the production launcher environment.","Compatible ELF dependency names are insufficient to prove ABI or runtime behavior."]
}
path=out/"STAGE1_STATIC_LINKER_CLOSURE.json"
path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print("LINKER_STATIC_CLOSURE_PASS",report["stage1_static_linker_closure_pass"])
print("BUNDLED_LIBRARY_FILES",len(archive_verified))
print("UNRESOLVED",unresolved[:15])
print("MALFORMED",malformed[:10])
print("OUTPUT",path)

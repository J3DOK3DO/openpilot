"""F12 offline release-integrity assessment.

This module is deliberately denial-only.  It validates bounded, canonical caller
evidence and reports engineering blockers; it has no device, command, install,
publish, or production-authorization interface.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any


SCHEMA = "G8_F12_RELEASE_EVIDENCE_V1"
MAX_JSON_BYTES = 1_048_576
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
F8_COMMIT = "dbe8565d1ede8f16844fc4d79a68844cc8e7629a"
F8_GATECARD_SHA256 = "a7ff9dc300bc83d341557155fdaf83492f423e1f87710d7c0486281cf49150e1"


class EvidenceError(ValueError):
  """Evidence is malformed, non-canonical, oversized, or semantically false."""


@dataclass(frozen=True)
class ReleaseAssessment:
  schema_valid: bool
  offline_integrity_controls_exercised: bool
  disposition: str
  production_go: bool
  installation_authorized: bool
  device_action_authorized: bool
  panda_can_authorized: bool
  hardware_qualified: bool
  native_agnos_qualified: bool
  evidence_label: str
  blockers: tuple[str, ...]

  def __post_init__(self) -> None:
    # A forged advisory result must never acquire release authority, even by direct construction.
    required_true = ("schema_valid", "offline_integrity_controls_exercised")
    required_false = ("production_go", "installation_authorized", "device_action_authorized",
                      "panda_can_authorized", "hardware_qualified", "native_agnos_qualified")
    if (any(type(getattr(self, field)) is not bool or not getattr(self, field) for field in required_true)
        or any(type(getattr(self, field)) is not bool or getattr(self, field) for field in required_false)
        or self.disposition != "SIMULATED_OFFLINE_ASSESSMENT_HOLD"
        or self.evidence_label != "CALLER_SUPPLIED_JSON_PLUS_UNKEYED_HASHES_NOT_ATTESTATION"
        or type(self.blockers) is not tuple
        or not self.blockers
        or not all(type(reason) is str and reason for reason in self.blockers)):
      raise EvidenceError("advisory result cannot grant release or device authority")

  def to_dict(self) -> dict[str, Any]:
    return asdict(self)


def _no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
  result: dict[str, Any] = {}
  for key, value in pairs:
    if key in result:
      raise EvidenceError(f"duplicate JSON key: {key}")
    result[key] = value
  return result


def canonical_json(value: Any) -> bytes:
  return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def read_canonical_json(raw: bytes, *, max_bytes: int = MAX_JSON_BYTES) -> dict[str, Any]:
  if type(raw) is not bytes:
    raise EvidenceError("input must be bytes")
  if not raw or len(raw) > max_bytes:
    raise EvidenceError("JSON byte length outside bound")
  try:
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
                       parse_constant=lambda value: (_ for _ in ()).throw(EvidenceError(f"invalid constant: {value}")))
  except EvidenceError:
    raise
  except (UnicodeDecodeError, ValueError, RecursionError) as exc:
    # ValueError covers json.JSONDecodeError and the interpreter's integer-digit limit.
    raise EvidenceError("invalid UTF-8 JSON") from exc
  if type(value) is not dict:
    raise EvidenceError("top-level JSON must be an object")
  try:
    canonical = canonical_json(value)
  except (UnicodeEncodeError, RecursionError, ValueError) as exc:
    raise EvidenceError("JSON cannot be canonicalized") from exc
  if raw != canonical:
    raise EvidenceError("JSON is not canonical")
  return value


def sha256_canonical(value: Any) -> str:
  return hashlib.sha256(canonical_json(value)).hexdigest()


def _exact(obj: Any, keys: set[str], label: str) -> dict[str, Any]:
  if type(obj) is not dict or set(obj) != keys:
    raise EvidenceError(f"{label} has wrong schema")
  return obj


def _text(value: Any, label: str) -> str:
  if type(value) is not str or not value:
    raise EvidenceError(f"{label} must be non-empty text")
  return value


def _bool(value: Any, label: str) -> bool:
  if type(value) is not bool:
    raise EvidenceError(f"{label} must be boolean")
  return value


def _integer(value: Any, label: str) -> int:
  if type(value) is not int or value < 0:
    raise EvidenceError(f"{label} must be a nonnegative integer")
  return value


def _digest(value: Any, label: str) -> str:
  value = _text(value, label)
  if SHA256_RE.fullmatch(value) is None:
    raise EvidenceError(f"{label} must be lowercase SHA-256")
  return value


def _commit(value: Any, label: str) -> str:
  value = _text(value, label)
  if COMMIT_RE.fullmatch(value) is None:
    raise EvidenceError(f"{label} must be a full lowercase commit")
  return value


def assess_release(evidence: dict[str, Any]) -> ReleaseAssessment:
  top = _exact(evidence, {"schema", "release_provenance", "essential_binaries", "abi",
                          "device_identity", "prior_f8", "f7a_trust", "regression",
                          "compiler_artifacts", "platform_evidence"}, "evidence")
  if top["schema"] != SCHEMA:
    raise EvidenceError("unknown schema")

  provenance = _exact(top["release_provenance"], {"source_commit", "tree_clean", "bundle_sha256",
                      "provenance_kind", "keyed_signature_verified"}, "release_provenance")
  source_commit = _commit(provenance["source_commit"], "source_commit")
  if source_commit != F8_COMMIT or not _bool(provenance["tree_clean"], "tree_clean"):
    raise EvidenceError("source freeze is not the pinned clean F8 commit")
  _digest(provenance["bundle_sha256"], "bundle_sha256")
  if provenance["provenance_kind"] != "UNKEYED_SHA256_ONLY":
    raise EvidenceError("unsupported provenance label")
  if _bool(provenance["keyed_signature_verified"], "keyed_signature_verified"):
    raise EvidenceError("no keyed production signature is established")

  binaries = top["essential_binaries"]
  if type(binaries) is not list or not binaries:
    raise EvidenceError("essential_binaries must be a non-empty list")
  required = {"pandad", "pandad_api_impl", "lateral_mpc", "longitudinal_mpc", "ipc_pyx", "params_pyx"}
  names: set[str] = set()
  for index, entry in enumerate(binaries):
    item = _exact(entry, {"name", "path", "sha256", "architecture", "source_commit",
                         "source_paths", "built_from_pinned_source"}, f"binary[{index}]")
    name = _text(item["name"], "binary name")
    if name in names:
      raise EvidenceError("duplicate essential binary")
    names.add(name)
    path = _text(item["path"], "binary path")
    if path.startswith("/") or ".." in path.split("/"):
      raise EvidenceError("binary path must be repository-relative")
    _digest(item["sha256"], "binary sha256")
    if item["architecture"] != "AARCH64":
      raise EvidenceError("essential binary is not AARCH64")
    _commit(item["source_commit"], "binary source_commit")
    if type(item["source_paths"]) is not list or not item["source_paths"] or not all(type(p) is str and p for p in item["source_paths"]):
      raise EvidenceError("binary source_paths are missing")
    _bool(item["built_from_pinned_source"], "built_from_pinned_source")
  if names != required:
    raise EvidenceError("essential binary allowlist is incomplete or expanded")

  abi = _exact(top["abi"], {"target_arch", "python_abi", "elf_interpreter", "agnos_version",
               "native_agnos", "qemu_userland_only", "dependency_closure_complete",
               "pinned_sysroot_sha256", "rpath_policy_pass"}, "abi")
  if abi["target_arch"] != "AARCH64" or abi["python_abi"] != "CPython-3.12" or abi["elf_interpreter"] != "/lib/ld-linux-aarch64.so.1" or abi["agnos_version"] != "19.8.1":
    raise EvidenceError("ABI target identity mismatch")
  _bool(abi["native_agnos"], "native_agnos")
  _bool(abi["qemu_userland_only"], "qemu_userland_only")
  _bool(abi["dependency_closure_complete"], "dependency_closure_complete")
  sysroot = abi["pinned_sysroot_sha256"]
  if sysroot is not None:
    _digest(sysroot, "pinned_sysroot_sha256")
  _bool(abi["rpath_policy_pass"], "rpath_policy_pass")
  if abi["native_agnos"] and abi["qemu_userland_only"]:
    raise EvidenceError("QEMU evidence cannot be native AGNOS evidence")

  device = _exact(top["device_identity"], {"hardware", "agnos_version", "app_commit",
                  "independently_authenticated"}, "device_identity")
  _text(device["hardware"], "hardware")
  if device["agnos_version"] != "19.8.1":
    raise EvidenceError("device AGNOS mismatch")
  _commit(device["app_commit"], "device app_commit")
  _bool(device["independently_authenticated"], "independently_authenticated")

  prior = _exact(top["prior_f8"], {"gatecard_sha256", "source_commit", "offline_disposition",
                 "hardware_trust"}, "prior_f8")
  if _digest(prior["gatecard_sha256"], "F8 gatecard digest") != F8_GATECARD_SHA256 or _commit(prior["source_commit"], "F8 commit") != F8_COMMIT:
    raise EvidenceError("prior F8 evidence is not the frozen artifact")
  if prior["offline_disposition"] != "CONDITIONALLY_PASS_PREPARED_NOT_HARDWARE_QUALIFIED" or prior["hardware_trust"] != "UNKNOWN_NOT_DEMONSTRATED_HOLD":
    raise EvidenceError("F8 offline status is being overstated")

  f7a = _exact(top["f7a_trust"], {"inventory_pass", "hardware_trust", "installation"}, "f7a_trust")
  if _bool(f7a["inventory_pass"], "F7A inventory_pass") is not True or f7a["hardware_trust"] != "UNKNOWN_HOLD" or f7a["installation"] != "NO_GO":
    raise EvidenceError("F7A trust status is being overstated")

  regression = _exact(top["regression"], {"passed", "failed", "skipped", "unwaived_failures"}, "regression")
  if (_integer(regression["passed"], "passed"), _integer(regression["failed"], "failed"),
      _integer(regression["skipped"], "skipped")) != (3661, 2, 72):
    raise EvidenceError("inherited broad regression counts changed")
  if regression["unwaived_failures"] != ["Chevrolet Bolt", "Hyundai Palisade"]:
    raise EvidenceError("inherited failures are missing or altered")

  compiler = _exact(top["compiler_artifacts"], {"full_clean_build", "build_source_commit",
                    "compiler_identity_pinned", "artifacts_match_source"}, "compiler_artifacts")
  _bool(compiler["full_clean_build"], "full_clean_build")
  _commit(compiler["build_source_commit"], "build_source_commit")
  _bool(compiler["compiler_identity_pinned"], "compiler_identity_pinned")
  _bool(compiler["artifacts_match_source"], "artifacts_match_source")

  platform = _exact(top["platform_evidence"], {"production_health_signer", "protected_monotonic_state",
                    "authenticated_boot_measurement", "panda_can_hardware_qualified",
                    "independent_production_review_go"}, "platform_evidence")
  for key, value in platform.items():
    _bool(value, key)

  blockers: list[str] = []
  if not all(item["built_from_pinned_source"] and item["source_commit"] == source_commit for item in binaries):
    blockers.append("essential binaries lack pinned-source build provenance")
  if not compiler["full_clean_build"] or compiler["build_source_commit"] != source_commit or not compiler["compiler_identity_pinned"] or not compiler["artifacts_match_source"]:
    blockers.append("full clean compiler artifact reconciliation is absent")
  if not abi["native_agnos"] or abi["qemu_userland_only"] or not abi["dependency_closure_complete"] or sysroot is None or not abi["rpath_policy_pass"]:
    blockers.append("native AGNOS 19.8.1 ABI and dependency closure are unqualified")
  if not device["independently_authenticated"]:
    blockers.append("device identity and active runtime are not independently authenticated")
  if not platform["production_health_signer"] or not platform["protected_monotonic_state"] or not platform["authenticated_boot_measurement"]:
    blockers.append("platform-rooted health, monotonic state, and boot measurement are absent")
  if not platform["panda_can_hardware_qualified"]:
    blockers.append("Panda/CAN hardware safety qualification is absent")
  if regression["failed"] or regression["skipped"]:
    blockers.append("broad regressions retain failures and skips")
  if not platform["independent_production_review_go"]:
    blockers.append("independent production review GO is absent")

  # An immutable invariant: this host-only parser cannot confer release authority,
  # even if every caller-controlled boolean is true.
  return ReleaseAssessment(
    schema_valid=True,
    offline_integrity_controls_exercised=True,
    disposition="SIMULATED_OFFLINE_ASSESSMENT_HOLD",
    production_go=False,
    installation_authorized=False,
    device_action_authorized=False,
    panda_can_authorized=False,
    hardware_qualified=False,
    native_agnos_qualified=False,
    evidence_label="CALLER_SUPPLIED_JSON_PLUS_UNKEYED_HASHES_NOT_ATTESTATION",
    blockers=tuple(blockers) or ("host-only assessment is intrinsically non-authorizing",),
  )

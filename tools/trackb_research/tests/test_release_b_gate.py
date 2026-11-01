"""Release B qualification gate: no proposal unless every B1-B6 requirement passed with the right evidence."""
import copy
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tools.trackb_research.ownership_evidence_model import STATE_OBSERVED_STOCK, STATE_UNKNOWN, OwnershipEvidence
from tools.trackb_research.plan_controller_sim import MODE_TRACKING, PlanSnapshot, SimulationPolicy, VehicleObservation
from tools.trackb_research.release_b_gate import (
  PHYSICAL_IDS, REQUIRED_IDS, REQUIRED_KINDS, STATUSES, SubordinateReleaseBGate, TargetIdentity, assess_register,
)

ROOT = Path(__file__).resolve().parents[3]
REGISTER_PATH = ROOT / "docs" / "accord11g_trackb" / "RELEASE_B_EVIDENCE_REGISTER.json"
POLICY = SimulationPolicy(2.0, 2.0, -3.0, 2.0, 0.1)  # Symbolic test values, not vehicle calibration.
PANDA, AGNOS = "a" * 64, "b" * 64
TARGET = TargetIdentity(PANDA, AGNOS)
STOCK = OwnershipEvidence(STATE_OBSERVED_STOCK, "stock_ownership_retained_source_only", 1)


def committed_register():
  return json.loads(REGISTER_PATH.read_text(encoding="utf-8"))


ALL_KINDS = sorted(set().union(*REQUIRED_KINDS.values()) | {"historical_log"})


def synthetic_all_pass():
  """Hypothetical fully-qualified register and artifacts; exist only in this test to prove the gate can open at all."""
  requirements, artifacts = [], {}
  for rid in REQUIRED_IDS:
    path = f"synthetic/{rid}.record"
    artifacts[path] = f"synthetic evidence for {rid}".encode()
    item = {"kind": sorted(REQUIRED_KINDS[rid])[0], "path": path, "sha256": hashlib.sha256(artifacts[path]).hexdigest()}
    entry = {"id": rid, "status": "PASS", "author": "synthetic author", "independent_reviewer": "synthetic reviewer", "evidence": [item]}
    for identity_rid, value in (("B3-TARGET-PANDA-RELEASE-IDENTITY", PANDA), ("B4-INSTALLED-DEVICE-IDENTITY", AGNOS)):
      if rid == identity_rid:
        entry["qualified_identity"] = item["measured_sha256"] = value
    requirements.append(entry)
  return {"requirements": requirements}, artifacts


def committed_artifacts(register):
  return {item["path"]: (ROOT / item["path"]).read_bytes() for entry in register["requirements"] for item in entry["evidence"]
          if isinstance(item, dict) and isinstance(item.get("path"), str) and (ROOT / item["path"]).is_file()}


def plan(identity=20, published=10.0, target=0.5, **changes):
  base = PlanSnapshot(identity, identity - 1, published, target, False, True, True, False, False, "cruise", (1.0,), (0.5,), (0.0,))
  return replace(base, **changes)


def observation(identity=30, observed=10.0, token="token-a", **changes):
  base = VehicleObservation(identity, observed, 5.0, 0.0, False, False, False, False, "clear", token, True, False, True)
  return replace(base, **changes)


def test_committed_register_is_well_formed_and_complete():
  register = committed_register()
  ids = [entry["id"] for entry in register["requirements"]]
  assert sorted(ids) == sorted(REQUIRED_IDS)
  assert all(entry["status"] in STATUSES for entry in register["requirements"])


def test_committed_register_has_no_pass_and_holds_every_requirement():
  # Release B stays non-operational: nothing is PASS, so in particular no OEM, target-firmware, installed-device,
  # bench or vehicle requirement is, and the gate (fed every committed evidence file that exists) holds all twelve.
  register = committed_register()
  assert [e["id"] for e in register["requirements"] if e["status"] == "PASS"] == []
  authorization = assess_register(register, committed_artifacts(register))
  assert not authorization.eligible
  assert set(authorization.holds) == set(REQUIRED_IDS) and set(PHYSICAL_IDS) <= set(authorization.holds)


def test_committed_register_marks_b5_b6_out_of_scope_not_passed():
  # Owner scope change 2026-11-01: B5/B6 are excluded from this campaign. That is recorded, never treated as evidence.
  statuses = {e["id"]: e["status"] for e in committed_register()["requirements"]}
  assert statuses["B5-ISOLATED-BENCH"] == statuses["B6-CONTROLLED-VEHICLE"] == "OUT_OF_SCOPE"


@pytest.mark.parametrize("rid", ("B5-ISOLATED-BENCH", "B6-CONTROLLED-VEHICLE"))
def test_out_of_scope_holds_even_when_everything_else_passes(rid):
  register, artifacts = synthetic_all_pass()
  entry = next(e for e in register["requirements"] if e["id"] == rid)
  entry["status"] = "OUT_OF_SCOPE"
  authorization = assess_register(register, artifacts)
  assert not authorization.eligible and authorization.holds == (rid,)


def arm(gate):
  # Cold-start arming of the composed simulation: one current, valid, disengaged observation.
  record = gate.step(plan(2), observation(2, token=None), POLICY, 10.0, STOCK, TARGET)
  assert record.proposal is None and record.shadow.reason == "engagement_token_missing"


def test_fresh_gate_withdraws_an_engagement_it_did_not_see_begin():
  gate = SubordinateReleaseBGate(*synthetic_all_pass())
  record = gate.step(plan(), observation(), POLICY, 10.5, STOCK, TARGET)
  assert record.proposal is None and record.shadow.reason == "cold_start_engagement_not_observed"


def test_committed_register_withdraws_even_a_valid_tracking_shadow():
  register = committed_register()
  gate = SubordinateReleaseBGate(register, committed_artifacts(register))
  arm(gate)
  record = gate.step(plan(), observation(), POLICY, 10.5, STOCK, TARGET)
  assert record.shadow.mode == MODE_TRACKING  # the simulation itself would track ...
  assert record.proposal is None              # ... but Release B holds suppress any proposal
  assert record.reason.startswith("release_b_qualification_hold:B1-")


def test_synthetic_fully_qualified_register_yields_only_an_abstract_record():
  gate = SubordinateReleaseBGate(*synthetic_all_pass())
  assert gate.authorization.eligible
  arm(gate)
  record = gate.step(plan(), observation(), POLICY, 10.5, STOCK, TARGET)
  assert record.reason == "release_b_gates_passed_abstract_only"
  assert record.proposal is record.shadow and record.proposal.acceleration_request == 0.5


MUTATIONS = ("status_hold", "no_reviewer", "reviewer_is_author", "no_author", "no_evidence", "bad_hash", "missing",
             "fabricated_hash_no_artifact", "artifact_hash_mismatch", "empty_artifact", "no_path")


@pytest.mark.parametrize("rid", REQUIRED_IDS)
@pytest.mark.parametrize("mutation", MUTATIONS)
def test_any_single_unmet_requirement_holds(rid, mutation):
  register, artifacts = synthetic_all_pass()
  entry = next(e for e in register["requirements"] if e["id"] == rid)
  item = entry["evidence"][0]
  if mutation == "status_hold":
    entry["status"] = "HOLD"
  elif mutation == "no_reviewer":
    entry["independent_reviewer"] = "  "
  elif mutation == "reviewer_is_author":
    entry["independent_reviewer"] = entry["author"]
  elif mutation == "no_author":
    del entry["author"]
  elif mutation == "no_evidence":
    entry["evidence"] = []
  elif mutation == "bad_hash":
    item["sha256"] = item["sha256"].upper()
  elif mutation == "missing":
    register["requirements"].remove(entry)
  elif mutation == "fabricated_hash_no_artifact":
    item.update(path="synthetic/never-supplied.record", sha256="c" * 64)
  elif mutation == "artifact_hash_mismatch":
    artifacts[item["path"]] = b"different bytes"
  elif mutation == "empty_artifact":
    artifacts[item["path"]] = b""
    item["sha256"] = hashlib.sha256(b"").hexdigest()
  else:
    del item["path"]
  authorization = assess_register(register, artifacts)
  assert not authorization.eligible and rid in authorization.holds


@pytest.mark.parametrize("rid", REQUIRED_IDS)
@pytest.mark.parametrize("kind", ALL_KINDS)
def test_each_requirement_accepts_only_its_own_evidence_kind(rid, kind):
  # Closes the review finding that one generic physical kind (e.g. bench_record) satisfied every physical row.
  register, artifacts = synthetic_all_pass()
  next(e for e in register["requirements"] if e["id"] == rid)["evidence"][0]["kind"] = kind
  assert (rid in assess_register(register, artifacts).holds) == (kind not in REQUIRED_KINDS[rid])


@pytest.mark.parametrize("rid", sorted(PHYSICAL_IDS))
def test_physical_requirements_accept_no_source_host_image_or_historical_kind(rid):
  assert REQUIRED_KINDS[rid].isdisjoint({"source_test", "host_test", "source_review", "image_hash", "historical_log"})


@pytest.mark.parametrize("rid", ("B3-TARGET-PANDA-RELEASE-IDENTITY", "B4-INSTALLED-DEVICE-IDENTITY"))
@pytest.mark.parametrize("mutation", ("measured_differs", "measured_missing", "qualified_missing", "qualified_malformed"))
def test_identity_must_equal_the_measured_hash_in_its_evidence(rid, mutation):
  register, artifacts = synthetic_all_pass()
  entry = next(e for e in register["requirements"] if e["id"] == rid)
  if mutation == "measured_differs":
    entry["evidence"][0]["measured_sha256"] = "d" * 64
  elif mutation == "measured_missing":
    del entry["evidence"][0]["measured_sha256"]
  elif mutation == "qualified_missing":
    del entry["qualified_identity"]
  else:
    entry["qualified_identity"] = entry["evidence"][0]["measured_sha256"] = "not-a-hash"
  assert rid in assess_register(register, artifacts).holds


@pytest.mark.parametrize("register", (None, [], {}, {"requirements": {}}, {"requirements": [1]},
                                      {"requirements": [{"id": "B5-ISOLATED-BENCH"}, {"id": "B5-ISOLATED-BENCH"}]}))
def test_malformed_register_fails_closed(register):
  assert assess_register(register, {}).holds == ("register_invalid",)


@pytest.mark.parametrize("artifacts", (None, [], "synthetic"))
def test_malformed_artifacts_fail_closed(artifacts):
  assert assess_register(synthetic_all_pass()[0], artifacts).holds == ("register_invalid",)


@pytest.mark.parametrize("target", (TargetIdentity(PANDA, "d" * 64), TargetIdentity("d" * 64, AGNOS), None, (PANDA, AGNOS)))
def test_firmware_identity_mismatch_withdraws(target):
  record = SubordinateReleaseBGate(*synthetic_all_pass()).step(plan(), observation(), POLICY, 10.5, STOCK, target)
  assert record.proposal is None and record.reason == "target_identity_mismatch"


@pytest.mark.parametrize("ownership", (OwnershipEvidence(STATE_UNKNOWN, "aeb_cmbs_not_clear", 1), None, "observed_stock"))
def test_oem_protection_state_not_observed_withdraws(ownership):
  record = SubordinateReleaseBGate(*synthetic_all_pass()).step(plan(), observation(), POLICY, 10.5, ownership, TARGET)
  assert record.proposal is None and record.reason == "oem_protection_state_not_observed"


@pytest.mark.parametrize(("changes", "reason"), (
  ({"aeb_cmbs_state": "active"}, "aeb_cmbs_not_clear"),
  ({"brake_pressed": True}, "driver_pedal_override"),
  ({"accelerator_pressed": True}, "driver_pedal_override"),
  ({"cancel_pressed": True}, "driver_cancel"),
  ({"stock_acc_enabled": False}, "stock_acc_disengaged"),
  ({"valid": False}, "observation_invalid"),
))
def test_shadow_withdrawal_reasons_propagate_through_a_fully_qualified_gate(changes, reason):
  record = SubordinateReleaseBGate(*synthetic_all_pass()).step(plan(), observation(**changes), POLICY, 10.5, STOCK, TARGET)
  assert record.proposal is None and record.reason == f"shadow_withdrawn:{reason}"


def test_plan_fcw_and_stale_plan_withdraw_through_gate():
  gate = SubordinateReleaseBGate(*synthetic_all_pass())
  assert gate.step(plan(fcw=True), observation(), POLICY, 10.5, STOCK, TARGET).reason == "shadow_withdrawn:plan_fcw_active"
  assert gate.step(plan(21, published=1.0), observation(31), POLICY, 10.5, STOCK, TARGET).reason == "shadow_withdrawn:stale_plan"


def test_gate_does_not_reread_register_or_artifacts_after_construction():
  register, artifacts = synthetic_all_pass()
  gate = SubordinateReleaseBGate(copy.deepcopy(register), dict(artifacts))
  register["requirements"][0]["status"] = "HOLD"
  artifacts.clear()
  assert gate.authorization.eligible
  held = committed_register()
  gate_held = SubordinateReleaseBGate(held, {})
  for entry in held["requirements"]:
    entry.update(status="PASS", author="a", independent_reviewer="late edit", evidence=[{"kind": "bench_record", "path": "x", "sha256": "e" * 64}])
  assert not gate_held.authorization.eligible

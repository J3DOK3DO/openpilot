"""Numeric DRV-001..010 policy model: unit cases, seeded property sweep, and a Dom hysteresis equivalence check."""

import dataclasses
import random

import pytest

from tools.trackb_research.brake_policy_model import (BRAKE, COAST, PROPEL, WITHDRAWN, BrakePolicyModel,
                                                     PolicyConfig, PolicyInput, config_valid)

CFG = PolicyConfig(accel_min=-3.5, accel_max=2.0, brake_entry=-0.12, brake_release=-0.02, meaningful_brake=-0.8,
                   release_steps=3, low_speed=3.0, integrator_gain=0.05, integrator_floor=-0.5,
                   integrator_relax=0.02, brake_relax_step=0.05, standstill_tolerance=0.01)


def inp(step, req=0.0, v=10.0, a=None, **kw):
  base = {"step": step, "requested_accel": req, "measured_accel": req if a is None else a, "v_ego": v,
          "stopping": False, "driver_brake": False, "driver_gas": False, "fault": False,
          "stock_acc_disengaged": False}
  return PolicyInput(**(base | kw))


def armed(cfg=CFG):
  m = BrakePolicyModel(cfg)
  assert m.step(inp(0, stock_acc_disengaged=True)).reason == "rearmed_pending"
  return m


def test_starts_latched_until_rearm_evidence():
  m = BrakePolicyModel(CFG)
  assert m.step(inp(0, req=1.0)).mode == WITHDRAWN
  assert m.step(inp(1, req=1.0)).reason == "awaiting_rearm"
  assert m.step(inp(2, req=1.0, stock_acc_disengaged=True)).mode == WITHDRAWN
  assert m.step(inp(3, req=1.0)).mode == PROPEL


@pytest.mark.parametrize("field,value", [("accel_min", 0.0), ("brake_release", 0.1), ("release_steps", 0),
                                         ("meaningful_brake", -0.05), ("integrator_floor", 0.1),
                                         ("brake_relax_step", 0.0), ("low_speed", float("nan")),
                                         ("release_steps", True)])
def test_invalid_config_rejected(field, value):
  bad = dataclasses.replace(CFG, **{field: value})
  assert not config_valid(bad)
  with pytest.raises(ValueError):
    BrakePolicyModel(bad)


def test_drv001_hysteresis_and_drv004_debounce():
  m = armed()
  assert m.step(inp(1, req=-0.10)).mode == COAST          # inside the hysteresis band, not braking
  d = m.step(inp(2, req=-0.13))
  assert d.mode == BRAKE and d.reason == "brake_entry"
  assert m.step(inp(3, req=-0.05)).reason == "braking"     # still braking inside the band
  for step in (4, 5):
    assert m.step(inp(step, req=-0.01)).reason == "brake_release_debounce"
  assert m.step(inp(6, req=-0.01)).reason in ("brake_released", "brake_relaxing")


def test_drv004_debounce_counter_resets_on_renewed_demand():
  m = armed()
  m.step(inp(1, req=-0.5))
  m.step(inp(2, req=-0.01))
  m.step(inp(3, req=-0.01))
  assert m.step(inp(4, req=-0.3)).reason == "braking"
  assert m.step(inp(5, req=-0.01)).reason == "brake_release_debounce"


def test_drv002_meaningful_brake_enters_immediately():
  m = armed()
  d = m.step(inp(1, req=-1.0))
  assert d.mode == BRAKE and d.reason == "meaningful_brake_immediate" and d.brake == pytest.approx(1.0)


def test_drv003_positive_request_never_enters_brake_even_with_negative_correction():
  m = armed()
  # Build a negative integrator at low speed, then ask for positive accel.
  for step in range(1, 40):
    m.step(inp(step, req=-0.5, v=2.0, a=0.5))
  m.step(inp(40, req=0.0, v=2.0))  # release path
  last = m.step(inp(41, req=-0.5, v=2.0, a=0.5)).brake
  assert last > 0.0
  saw_release = False
  for step in range(42, 120):
    d = m.step(inp(step, req=0.05, v=2.0))
    # The brake fades at exactly the relaxation rate: the integrator contributes no brake target.
    assert d.brake == pytest.approx(max(0.0, last - CFG.brake_relax_step))
    if d.mode != BRAKE:
      saw_release = saw_release or d.corrected_accel < 0.0  # released while the integrator still pulls negative
      assert d.reason == "positive_request_no_brake_entry" and d.brake == 0.0
    last = d.brake
  assert saw_release


def test_drv003_integrator_adds_no_brake_target_during_long_release_debounce():
  # A long debounce keeps the selector braking while the request is positive; the brake must still only fade.
  m = armed(dataclasses.replace(CFG, release_steps=40))
  for step in range(1, 60):
    last = m.step(inp(step, req=-0.15, v=2.0, a=0.5)).brake
  for step in range(60, 90):
    d = m.step(inp(step, req=0.05, v=2.0))
    assert d.brake == pytest.approx(max(0.0, last - CFG.brake_relax_step)), step
    last = d.brake
  assert last == 0.0


def test_drv005_driver_inputs_withdraw_without_latch():
  for kw in ({"driver_brake": True}, {"driver_gas": True}):
    m = armed()
    m.step(inp(1, req=-1.0))
    d = m.step(inp(2, req=-1.0, **kw))
    assert (d.mode, d.propulsion, d.brake) == (WITHDRAWN, 0.0, 0.0) and d.reason == "driver_override"
    # Override does not latch: the next clean step acts again from a reset state.
    assert m.step(inp(3, req=0.5)).mode == PROPEL


def test_drv006_integrator_bounded_and_only_in_low_speed_window():
  m = armed()
  for step in range(1, 200):
    d = m.step(inp(step, req=-0.5, v=2.0, a=1.0))
    assert CFG.integrator_floor <= d.integrator <= 0.0
  assert d.integrator == pytest.approx(CFG.integrator_floor)
  m2 = armed()
  for step in range(1, 50):
    assert m2.step(inp(step, req=-0.5, v=10.0, a=1.0)).integrator == 0.0


def test_drv007_integrator_relaxes_and_fault_requires_rearm():
  m = armed()
  for step in range(1, 100):
    m.step(inp(step, req=-0.5, v=2.0, a=1.0))
  prev = m.step(inp(100, req=-0.5, v=10.0)).integrator
  cur = m.step(inp(101, req=-0.5, v=10.0)).integrator
  assert cur == pytest.approx(min(0.0, prev + CFG.integrator_relax))
  assert m.step(inp(102, req=-0.5, fault=True)).reason == "fault_latched"
  assert m.step(inp(103, req=-0.5)).reason == "awaiting_rearm"
  assert m.step(inp(104, req=-0.5, stock_acc_disengaged=True)).reason == "rearmed_pending"
  d = m.step(inp(105, req=-0.5))
  assert d.mode == BRAKE and d.integrator == 0.0


def test_drv008_corrected_never_exceeds_requested():
  m = armed()
  for step in range(1, 60):
    d = m.step(inp(step, req=-0.4, v=1.5, a=0.2))
    assert d.corrected_accel <= d.requested_accel
    assert d.requested_accel == -0.4


def test_drv009_one_sided_relaxation():
  m = armed()
  assert m.step(inp(1, req=-2.0)).brake == pytest.approx(2.0)
  d = m.step(inp(2, req=-0.5))
  assert d.brake == pytest.approx(2.0 - CFG.brake_relax_step)
  assert m.step(inp(3, req=-3.0)).brake == pytest.approx(3.0)   # rises at once


def test_drv010_near_zero_negative_speed():
  m = armed()
  assert m.step(inp(1, req=-0.5, v=-0.005)).mode == BRAKE
  d = m.step(inp(2, req=-0.5, v=-0.02))
  assert d.reason == "negative_speed_beyond_tolerance"
  assert m.step(inp(3, req=-0.5)).reason == "awaiting_rearm"


@pytest.mark.parametrize("bad", [None, inp(1, req=float("nan")), inp(1, v=float("inf")),
                                 dataclasses.replace(inp(1), stopping=1), dataclasses.replace(inp(1), step=-1)])
def test_invalid_input_withdraws_and_latches(bad):
  m = armed()
  assert m.step(bad).reason == "input_invalid"
  assert m.step(inp(5)).reason == "awaiting_rearm"


def test_step_must_increase():
  m = armed()
  m.step(inp(5, req=0.5))
  assert m.step(inp(5, req=0.5)).reason == "step_not_increasing"
  assert m.step(inp(6, req=0.5)).reason == "awaiting_rearm"


@pytest.mark.parametrize("seed", range(20))
def test_seeded_property_sweep(seed):
  rng = random.Random(seed)
  m = armed()
  last_brake = 0.0
  trace = []
  for step in range(1, 600):
    kw = {}
    roll = rng.random()
    if roll < 0.01:
      kw["fault"] = True
    elif roll < 0.03:
      kw["driver_brake" if rng.random() < 0.5 else "driver_gas"] = True
    if rng.random() < 0.05:
      kw["stock_acc_disengaged"] = True
    x = inp(step, req=rng.uniform(-4.0, 2.5), v=rng.choice((rng.uniform(-0.03, 0.03), rng.uniform(0.0, 35.0))),
            a=rng.uniform(-4.0, 2.5), stopping=rng.random() < 0.05, **kw)
    d = m.step(x)
    trace.append(d)
    assert d.propulsion >= 0.0 and d.brake >= 0.0 and not (d.propulsion > 0.0 and d.brake > 0.0)
    assert CFG.integrator_floor <= d.integrator <= 0.0
    if d.mode == WITHDRAWN:
      assert (d.propulsion, d.brake, d.corrected_accel) == (0.0, 0.0, 0.0)
      last_brake = 0.0
      continue
    assert not (x.fault or x.driver_brake or x.driver_gas)
    assert CFG.accel_min <= d.corrected_accel <= min(x.requested_accel, CFG.accel_max) or \
      d.corrected_accel == CFG.accel_min
    assert d.brake >= last_brake - CFG.brake_relax_step - 1e-12
    if d.mode == PROPEL:
      assert d.propulsion == d.corrected_accel > 0.0
    last_brake = d.brake
  # Determinism: an identical sequence reproduces the identical trace.
  rng = random.Random(seed)
  m2 = armed()
  for step, expected in enumerate(trace, start=1):
    kw = {}
    roll = rng.random()
    if roll < 0.01:
      kw["fault"] = True
    elif roll < 0.03:
      kw["driver_brake" if rng.random() < 0.5 else "driver_gas"] = True
    if rng.random() < 0.05:
      kw["stock_acc_disengaged"] = True
    x = inp(step, req=rng.uniform(-4.0, 2.5), v=rng.choice((rng.uniform(-0.03, 0.03), rng.uniform(0.0, 35.0))),
            a=rng.uniform(-4.0, 2.5), stopping=rng.random() < 0.05, **kw)
    assert m2.step(x) == expected


def test_stopping_semantics_are_aligned_with_dom():
  # Both selectors treat stopping as braking whatever the force; the equivalence sweep below relies on this.
  from opendbc.car.honda.bosch_longitudinal import update_honda_bosch_braking
  for prev in (False, True):
    for force in (-1.0, -0.05, 0.0, 0.5):
      assert update_honda_bosch_braking(prev, force, True, True) is True
      m = armed()
      m.step(inp(1, req=-1.0 if prev else 0.0))
      assert m.step(inp(2, req=force, stopping=True)).reason == "stopping" and m._braking


def test_selection_matches_dom_classic_bosch_hysteresis():
  """With debounce, integrator, relaxation and the immediate threshold neutralised, DRV-001 equals Dom's native
  update_honda_bosch_braking for the same force sequence (source equivalence, not 11G evidence)."""
  from opendbc.car.honda.bosch_longitudinal import (BOSCH_BRAKE_FORCE_ON, BOSCH_BRAKE_FORCE_RELEASE,
                                                    update_honda_bosch_braking)
  cfg = dataclasses.replace(CFG, brake_entry=BOSCH_BRAKE_FORCE_ON, brake_release=BOSCH_BRAKE_FORCE_RELEASE,
                            meaningful_brake=CFG.accel_min, release_steps=1, integrator_gain=0.0,
                            brake_relax_step=1e9)
  rng = random.Random(7)
  for _ in range(20):
    m = armed(cfg)
    dom = False
    for step in range(1, 300):
      force = rng.choice((rng.uniform(-0.3, 0.1), BOSCH_BRAKE_FORCE_ON, BOSCH_BRAKE_FORCE_RELEASE))
      stopping = rng.random() < 0.05
      dom = update_honda_bosch_braking(dom, force, stopping, True)
      d = m.step(inp(step, req=force, v=10.0, stopping=stopping))
      assert m._braking == dom, (step, force, stopping)
      assert (d.mode == BRAKE) == (dom and force < 0)

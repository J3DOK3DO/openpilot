"""Opt-in, read-only Accord 11G native MPC diagnostic. Never a planner or controller.

Launch manually with --shadow-only. This module intentionally has no manager entry,
Params switch, publisher, CAN, Panda, or car controller binding. Import is inert.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from types import SimpleNamespace

SOURCES = ('carState', 'radarState', 'modelV2', 'controlsState', 'deviceState')
MAX_AGE_NS = 150_000_000
# deviceState is a 2 Hz service; permit up to two missed updates in a diagnostic
# without falsely forcing the 20/100 Hz streams to align to its slow cadence.
MAX_DEVICE_AGE_NS = 1_250_000_000
MAX_SKEW_NS = 75_000_000


def _number(value, low, high):
  return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def _lead(lead):
  if type(lead.present) is not bool:
    raise ValueError('lead presence invalid')
  if not lead.present:
    return SimpleNamespace(present=False, dRel=50.0, vLead=0.0, aLeadK=0.0,
                           aLeadTau=1.5, modelProb=0.0, radar=False)
  fields = (('dRel', 0, 300), ('vLead', 0, 70), ('aLeadK', -10, 5),
            ('aLeadTau', 0.1, 10), ('modelProb', 0, 1))
  values = {name: getattr(lead, name) for name, _, _ in fields}
  if any(not _number(values[name], low, high) for name, low, high in fields) or type(lead.radar) is not bool:
    raise ValueError('lead values invalid')
  return SimpleNamespace(present=True, radar=lead.radar, **values)


def admit(sm, now_ns: int, floor_ns: int, expected_fingerprint: str):
  """Return an immutable-enough scalar snapshot; any uncertainty rejects the cycle."""
  try:
    if type(now_ns) is not int or type(floor_ns) is not int or now_ns <= floor_ns:
      return None
    if not sm.valid['carParams'] or sm['carParams'].carFingerprint != expected_fingerprint or sm['carParams'].openpilotLongitudinalControl:
      return None
    stamps = []
    for name in SOURCES:
      stamp, receipt = sm.logMonoTime[name], sm.recv_time[name]
      if (sm.valid[name] is not True or sm.alive[name] is not True or
          type(stamp) is not int or type(receipt) not in (int, float) or not math.isfinite(receipt)):
        return None
      receipt_ns = int(receipt * 1e9)
      limit = MAX_DEVICE_AGE_NS if name == 'deviceState' else MAX_AGE_NS
      if not floor_ns < stamp <= receipt_ns <= now_ns or now_ns - stamp > limit:
        return None
      if name != 'deviceState':
        stamps.append(stamp)
    if max(stamps) - min(stamps) > MAX_SKEW_NS:
      return None
    car, radar, model, controls, device = (sm[name] for name in SOURCES)
    if (not car.canValid or car.canTimeout or car.accFaulted or not car.cruiseState.enabled or
        car.gasPressed or car.brakePressed or car.stockAeb or car.stockFcw or
        any(radar.radarErrors.to_dict().values()) or controls.forceDecel or not device.started or
        type(device.startedMonoTime) is not int or not 0 < device.startedMonoTime <= floor_ns or
        type(radar.mdMonoTime) is not int or radar.mdMonoTime != sm.logMonoTime['modelV2'] or
        len(model.velocity.x) < 1 or not _number(model.velocity.x[0], 0, 70)):
      return None
    if not _number(car.vEgo, 0, 70) or not _number(car.aEgo, -8, 5):
      return None
    first, second = _lead(radar.leadOne), _lead(radar.leadTwo)
    if not first.present and not second.present:
      return None  # lead loss invalidates this lead-only diagnostic
    return SimpleNamespace(v=float(car.vEgo), a=float(car.aEgo),
                           radar=SimpleNamespace(leadOne=first, leadTwo=second))
  except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
    return None


class _ObservedSolver:
  def __init__(self, native):
    self.native = native
    self.statuses = []

  def __getattr__(self, name):
    return getattr(self.native, name)

  def solve(self):
    status = self.native.solve()
    self.statuses.append(status)
    return status


class Shadow:
  def __init__(self, expected_fingerprint: str, floor_ns: int):
    self.expected_fingerprint = expected_fingerprint
    self.floor_ns = floor_ns
    self.mpc = None
    self.observed = None
    self.cycles = 0

  def _clear(self):
    self.mpc = None
    self.observed = None

  def step(self, sm, now_ns: int) -> dict:
    snapshot = admit(sm, now_ns, self.floor_ns, self.expected_fingerprint)
    if snapshot is None:
      self._clear()
      return {'status': 'REJECTED_INPUT', 'execution': 'NONE'}
    try:
      if self.mpc is None:
        # Missing native artifacts or optional dependencies fail closed here.
        from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.long_mpc import LongitudinalMpc
        self.mpc = LongitudinalMpc()
        self.observed = _ObservedSolver(self.mpc.solver)
        self.mpc.solver = self.observed
      before = len(self.observed.statuses)
      self.mpc.set_cur_state(snapshot.v, snapshot.a)
      self.mpc.update(snapshot.radar)
      if len(self.observed.statuses) != before + 1 or type(self.observed.statuses[-1]) is not int or self.observed.statuses[-1] != 0:
        raise ValueError('native solver failed')
      import numpy as np
      if not all(np.all(np.isfinite(a)) for a in (self.mpc.x_sol, self.mpc.v_solution, self.mpc.a_solution, self.mpc.j_solution)):
        raise ValueError('nonfinite native output')
      self.cycles += 1
      return {'status': 'HYPOTHETICAL_STOCK_ACC_UNCHANGED', 'execution': 'PRODUCT_NATIVE_MPC_ONLY',
              'cycle': self.cycles, 'first_accel_mps2': round(float(self.mpc.a_solution[1]), 4)}
    except Exception:
      self._clear()
      return {'status': 'NATIVE_UNAVAILABLE_OR_FAILED', 'execution': 'NONE'}


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--shadow-only', action='store_true', help='required explicit opt-in')
  parser.add_argument('--max-cycles', type=int, default=300)
  args = parser.parse_args()
  if not args.shadow_only or not 1 <= args.max_cycles <= 6000:
    parser.error('--shadow-only and 1..6000 max-cycles required')
  try:
    from opendbc.car.honda.values import CAR
    import openpilot.cereal.messaging as messaging
    floor = time.monotonic_ns()
    sm = messaging.SubMaster([*SOURCES, 'carParams'], poll='modelV2')
  except (ImportError, OSError, RuntimeError):
    print(json.dumps({'status': 'PRODUCT_IPC_UNAVAILABLE', 'execution': 'NONE'}, sort_keys=True))
    return
  shadow = Shadow(CAR.HONDA_ACCORD_11G, floor)
  try:
    for _ in range(args.max_cycles):
      try:
        sm.update(200)
        if sm.updated['modelV2']:
          # Allowlisted diagnostic output only: no VIN, route, timestamps, positions or raw messages.
          print(json.dumps(shadow.step(sm, time.monotonic_ns()), sort_keys=True), flush=True)
      except Exception:
        print(json.dumps({'status': 'PRODUCT_IPC_FAILED', 'execution': 'NONE'}, sort_keys=True), flush=True)
        break
  finally:
    shadow._clear()


if __name__ == '__main__':
  main()

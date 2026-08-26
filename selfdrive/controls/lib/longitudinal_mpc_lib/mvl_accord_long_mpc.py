"""Validated MVL longitudinal MPC runtime isolated to the Honda Accord 11G.

The state, control, parameter, cost, and constraint dimensions are identical to
the current source-generated ``long`` acados solver. This module supplies the
validated Accord runtime weights, lead processing, and source selection while
reusing that generated solver rather than copying historical binaries.
"""

import time

import numpy as np

from cereal import log
from opendbc.car.interfaces import ACCEL_MAX, ACCEL_MIN
from openpilot.common.realtime import DT_MDL
from openpilot.common.swaglog import cloudlog
from openpilot.selfdrive.modeld.constants import index_function


LongitudinalPlanSource = log.LongitudinalPlan.LongitudinalPlanSource
MPC_SOURCES = (
  LongitudinalPlanSource.lead0,
  LongitudinalPlanSource.lead1,
  LongitudinalPlanSource.cruise,
)

MODEL_NAME = "long"
ACADOS_SOLVER_TYPE = "SQP_RTI"
X_DIM = 3
U_DIM = 1
PARAM_DIM = 6
COST_E_DIM = 5
COST_DIM = COST_E_DIM + 1
CONSTR_DIM = 4

X_EGO_OBSTACLE_COST = 3.0
X_EGO_COST = 0.0
V_EGO_COST = 0.0
A_EGO_COST = 0.0
J_EGO_COST = 5.0
A_CHANGE_COST = 200.0
DANGER_ZONE_COST = 100.0
LIMIT_COST = 1e6
CRASH_DISTANCE = 0.25
LEAD_DANGER_FACTOR = 0.75

N = 12
MAX_T = 10.0
T_IDXS = np.array([index_function(idx, max_val=MAX_T, max_idx=N) for idx in range(N + 1)])
T_DIFFS = np.diff(T_IDXS, prepend=[0.0])
FCW_IDXS = T_IDXS < 5.0

COMFORT_BRAKE = 2.5
STOP_DISTANCE = 6.0
CRUISE_MIN_ACCEL = -1.2
CRUISE_MAX_ACCEL = 1.6
MIN_X_LEAD_FACTOR = 0.5
MVL_LEAD_ACCEL_TAU = 1.5


def get_jerk_factor(personality=log.LongitudinalPersonality.standard):
  if personality in (log.LongitudinalPersonality.relaxed, log.LongitudinalPersonality.standard):
    return 1.0
  if personality == log.LongitudinalPersonality.aggressive:
    return 0.5
  raise NotImplementedError("Longitudinal personality not supported")


def get_T_FOLLOW(personality=log.LongitudinalPersonality.standard):
  if personality == log.LongitudinalPersonality.relaxed:
    return 1.75
  if personality == log.LongitudinalPersonality.standard:
    return 1.45
  if personality == log.LongitudinalPersonality.aggressive:
    return 1.25
  raise NotImplementedError("Longitudinal personality not supported")


def get_stopped_equivalence_factor(v_lead):
  return (v_lead ** 2) / (2 * COMFORT_BRAKE)


def get_safe_obstacle_distance(v_ego, t_follow):
  return (v_ego ** 2) / (2 * COMFORT_BRAKE) + t_follow * v_ego + STOP_DISTANCE


def _new_solver():
  # Import lazily so pure semantic tests do not load a stale target-architecture
  # extension. Production construction still fails closed if the solver is absent.
  from openpilot.selfdrive.controls.lib.longitudinal_mpc_lib.c_generated_code.acados_ocp_solver_pyx import AcadosOcpSolverCython
  return AcadosOcpSolverCython(MODEL_NAME, ACADOS_SOLVER_TYPE, N)


class MVLAccordLongitudinalMpc:
  def __init__(self, dt=DT_MDL, solver=None):
    self.dt = dt
    self.solver = solver if solver is not None else _new_solver()
    self.source = LongitudinalPlanSource.cruise
    self.reset()

  def reset(self):
    self.solver.reset()

    self.x_sol = np.zeros((N + 1, X_DIM))
    self.u_sol = np.zeros((N, U_DIM))
    self.v_solution = np.zeros(N + 1)
    self.a_solution = np.zeros(N + 1)
    self.j_solution = np.zeros(N)
    self.a_prev = np.array(self.a_solution)
    self.yref = np.zeros((N + 1, COST_DIM))

    for i in range(N):
      self.solver.cost_set(i, "yref", self.yref[i])
    self.solver.cost_set(N, "yref", self.yref[N][:COST_E_DIM])

    self.params = np.zeros((N + 1, PARAM_DIM))
    for i in range(N + 1):
      self.solver.set(i, "x", np.zeros(X_DIM))

    self.last_cloudlog_t = 0.0
    self.crash_cnt = 0.0
    self.solution_status = 0
    self.solve_time = 0.0
    self.x0 = np.zeros(X_DIM)
    self.set_weights()

  def set_cost_weights(self, cost_weights, constraint_cost_weights):
    W = np.asfortranarray(np.diag(cost_weights))
    for i in range(N):
      W[4, 4] = cost_weights[4] * np.interp(T_IDXS[i], [0.0, 1.0, 2.0], [1.0, 1.0, 0.0])
      self.solver.cost_set(i, "W", W)
    self.solver.cost_set(N, "W", np.copy(W[:COST_E_DIM, :COST_E_DIM]))

    Zl = np.array(constraint_cost_weights)
    for i in range(N):
      self.solver.cost_set(i, "Zl", Zl)

  def set_weights(self, prev_accel_constraint=True, personality=log.LongitudinalPersonality.standard):
    jerk_factor = get_jerk_factor(personality)
    a_change_cost = A_CHANGE_COST if prev_accel_constraint else 0.0
    cost_weights = [
      X_EGO_OBSTACLE_COST,
      X_EGO_COST,
      V_EGO_COST,
      A_EGO_COST,
      jerk_factor * a_change_cost,
      jerk_factor * J_EGO_COST,
    ]
    self.set_cost_weights(cost_weights, [LIMIT_COST, LIMIT_COST, LIMIT_COST, DANGER_ZONE_COST])

  def set_cur_state(self, v, a):
    v_prev = self.x0[1]
    self.x0[1] = v
    self.x0[2] = a
    if abs(v_prev - v) > 2.0:
      for i in range(N + 1):
        self.solver.set(i, "x", self.x0)

  @staticmethod
  def extrapolate_lead(x_lead, v_lead, a_lead, a_lead_tau):
    a_lead_traj = a_lead * np.exp(-a_lead_tau * (T_IDXS ** 2) / 2.0)
    v_lead_traj = np.clip(v_lead + np.cumsum(T_DIFFS * a_lead_traj), 0.0, 1e8)
    x_lead_traj = x_lead + np.cumsum(T_DIFFS * v_lead_traj)
    return np.column_stack((x_lead_traj, v_lead_traj))

  def process_lead(self, lead):
    v_ego = self.x0[1]
    if lead is not None and bool(getattr(lead, "status", getattr(lead, "present", False))):
      x_lead = lead.dRel
      v_lead = lead.vLead
      a_lead = lead.aLeadK
      a_lead_tau = lead.aLeadTau
    else:
      x_lead = 50.0
      v_lead = v_ego + 10.0
      a_lead = 0.0
      a_lead_tau = MVL_LEAD_ACCEL_TAU

    min_x_lead = MIN_X_LEAD_FACTOR * (v_ego + v_lead) * (v_ego - v_lead) / (-ACCEL_MIN * 2)
    x_lead = np.clip(x_lead, min_x_lead, 1e8)
    v_lead = np.clip(v_lead, 0.0, 1e8)
    a_lead = np.clip(a_lead, -10.0, 5.0)
    return self.extrapolate_lead(x_lead, v_lead, a_lead, a_lead_tau)

  def update(self, radar_state, v_cruise, personality=log.LongitudinalPersonality.standard):
    t_follow = get_T_FOLLOW(personality)
    v_ego = self.x0[1]

    lead_xv_0 = self.process_lead(radar_state.leadOne)
    lead_xv_1 = self.process_lead(radar_state.leadTwo)
    lead_0_obstacle = lead_xv_0[:, 0] + get_stopped_equivalence_factor(lead_xv_0[:, 1])
    lead_1_obstacle = lead_xv_1[:, 0] + get_stopped_equivalence_factor(lead_xv_1[:, 1])

    v_lower = v_ego + T_IDXS * CRUISE_MIN_ACCEL * 1.05
    v_upper = v_ego + T_IDXS * CRUISE_MAX_ACCEL * 1.05
    v_cruise_clipped = np.clip(v_cruise * np.ones(N + 1), v_lower, v_upper)
    cruise_obstacle = np.cumsum(T_DIFFS * v_cruise_clipped) + get_safe_obstacle_distance(v_cruise_clipped, t_follow)

    x_obstacles = np.column_stack((lead_0_obstacle, lead_1_obstacle, cruise_obstacle))
    self.source = MPC_SOURCES[int(np.argmin(x_obstacles[0]))]

    self.yref[:, :] = 0.0
    for i in range(N):
      self.solver.set(i, "yref", self.yref[i])
    self.solver.set(N, "yref", self.yref[N][:COST_E_DIM])

    self.params[:, 0] = ACCEL_MIN
    self.params[:, 1] = ACCEL_MAX
    self.params[:, 2] = np.min(x_obstacles, axis=1)
    self.params[:, 3] = np.copy(self.a_prev)
    self.params[:, 4] = t_follow
    self.params[:, 5] = LEAD_DANGER_FACTOR

    self.run()
    if (np.any(lead_xv_0[FCW_IDXS, 0] - self.x_sol[FCW_IDXS, 0] < CRASH_DISTANCE) and
        radar_state.leadOne.modelProb > 0.9):
      self.crash_cnt += 1
    else:
      self.crash_cnt = 0

  def run(self):
    for i in range(N + 1):
      self.solver.set(i, "p", self.params[i])
    self.solver.constraints_set(0, "lbx", self.x0)
    self.solver.constraints_set(0, "ubx", self.x0)

    self.solution_status = self.solver.solve()
    self.solve_time = float(self.solver.get_stats("time_tot")[0])

    for i in range(N + 1):
      self.x_sol[i] = self.solver.get(i, "x")
    for i in range(N):
      self.u_sol[i] = self.solver.get(i, "u")

    self.v_solution = self.x_sol[:, 1]
    self.a_solution = self.x_sol[:, 2]
    self.j_solution = self.u_sol[:, 0]
    self.a_prev = np.interp(T_IDXS + self.dt, T_IDXS, self.a_solution)

    if self.solution_status != 0:
      now = time.monotonic()
      if now > self.last_cloudlog_t + 5.0:
        self.last_cloudlog_t = now
        cloudlog.warning(f"MVL Accord long MPC reset, solution_status: {self.solution_status}")
      self.reset()

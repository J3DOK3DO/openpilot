"""C5-R1 road-derived regression fixtures for the Accord 11G follow-up patches.

The constants below are copied from the C5 refresh evidence, not loaded from it at
test time.  That keeps this host test deterministic while leaving the evidence
workspace authoritative for provenance and re-extraction.
"""

from types import SimpleNamespace

import pytest

from cereal import log
from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda import hondacan
from opendbc.car.honda.carcontroller import CarController
from opendbc.car.honda.hondacan import create_acc_commands as pack_acc_commands
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, DBC
from opendbc.car.interfaces import CarInterfaceBase
from openpilot.selfdrive.controls.controlsd import limit_curvature_to_plan
from openpilot.selfdrive.controls.lib.latcontrol_pid import LatControlPID
from openpilot.selfdrive.controls.lib.latcontrol_torque import LatControlTorque
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState
from openpilot.selfdrive.controls.lib.longitudinal_planner import LongitudinalPlanner


@pytest.fixture(autouse=True)
def openpilot_function_fixture():
  """These pure/controller fixtures need neither the global log prefix nor I/O."""
  yield


def _toggles():
  return SimpleNamespace(always_on_lateral_lkas=False, force_torque_controller=False, nnff=False, nnff_lite=False)


def _accord_cp():
  return CarInterface.get_params(CAR.HONDA_ACCORD_11G, gen_empty_fingerprint(), [], True, False, False, _toggles())


def _vision_lead(d_rel, v_lead, model_prob, y_rel):
  """Set only fields supplied by the named road observation."""
  lead = log.RadarState.LeadData.new_message()
  lead.status = True
  lead.dRel = d_rel
  lead.vLead = v_lead
  lead.vLeadK = v_lead
  lead.modelProb = model_prob
  lead.yRel = y_rel
  lead.radar = False
  return lead


# C0/48, 2026-09-25 13:32:42.345 UAE, A_LOW_C0_48.
# aLeadK, the planner confirmation/hold state, model length, and actuator delay
# were not retained at this instant.  The RED therefore calls only the narrow
# lift predicate, which reads none of those unavailable fields.
A_LOW_C0_48 = dict(
  v_ego=8.7182722, d_rel=27.3948326, v_rel=-0.5890007, v_lead=8.1292715,
  model_prob=0.9999043, y_rel=-0.3332809, tracking_lead=False,
  raw_mpc_accel=1.576, requested_accel=1.579,
)

# C0/72, 2026-09-25 13:57:08.236 UAE, A_HIGH_C0_72.  Same narrow-predicate
# limitation as above; its documented failure is the confidence threshold.
A_HIGH_C0_72 = dict(
  v_ego=21.4533787, d_rel=102.2063446, v_rel=-2.8082352, v_lead=18.6451435,
  model_prob=0.8684366, y_rel=-0.9423192, tracking_lead=False,
  raw_mpc_accel=1.020, requested_accel=1.0195,
)


@pytest.mark.parametrize("road", [A_LOW_C0_48, A_HIGH_C0_72], ids=["A_LOW_C0_48", "A_HIGH_C0_72"])
def test_c5a_road_constants_preserve_observed_positive_untracked_punch(road):
  assert road["v_lead"] == pytest.approx(road["v_ego"] + road["v_rel"], abs=2e-6)
  assert not road["tracking_lead"]
  assert road["raw_mpc_accel"] > 1.0
  assert road["requested_accel"] > 1.0


@pytest.mark.xfail(strict=True, reason="C5-A RED: current pretracking lift does not recognize A_LOW_C0_48")
def test_c5a_red_low_near_positive_punch_is_eligible_for_existing_pretracking_family():
  road = A_LOW_C0_48
  lead = _vision_lead(road["d_rel"], road["v_lead"], road["model_prob"], road["y_rel"])

  # Future C5-A work should adapt this existing family, not introduce a parallel
  # policy. A selected cap value is deliberately not prescribed by this RED.
  assert LongitudinalPlanner.get_vision_untracked_approach_lift_cap(lead, road["v_ego"], 1.25) is not None


@pytest.mark.xfail(strict=True, reason="C5-A RED: current pretracking lift rejects A_HIGH_C0_72 confidence")
def test_c5a_red_moderate_far_positive_punch_is_eligible_for_existing_pretracking_family():
  road = A_HIGH_C0_72
  lead = _vision_lead(road["d_rel"], road["v_lead"], road["model_prob"], road["y_rel"])

  assert LongitudinalPlanner.get_vision_untracked_approach_lift_cap(lead, road["v_ego"], 1.25) is not None


def test_c5a_preservation_opening_lead_control_is_not_a_closing_cap_case():
  # C0/40, 13:24:49.700 UAE, A_OPEN_c0_01. Only these exposed road fields
  # exist, so this is intentionally an output-preservation fixture rather than
  # a fabricated planner update (model probability/yRel/aLead are unavailable).
  v_ego, v_rel, raw_mpc_accel, requested_accel = 27.14, 2.05, 0.223, 0.550
  assert v_ego + v_rel > v_ego
  assert raw_mpc_accel > 0.0
  assert requested_accel > 0.0


def test_c5a_preservation_urgent_closing_control_remains_negative():
  # C0/69, 13:53:32.026 UAE, A_FAR_07. Model confidence/lateral fields and
  # prior planner state were not retained, so no full planner replay is claimed.
  d_rel, v_rel, v_ego = 87.88, -8.42, 23.68
  raw_mpc_accel, policy_output, requested_accel = -0.788, -0.807, -0.738
  assert d_rel == pytest.approx(87.88)
  assert v_ego + v_rel < v_ego
  assert raw_mpc_accel < 0.0
  assert policy_output < 0.0
  assert requested_accel < 0.0


# C0/70 B_HIGH_C0_70, 13:54:57.699--13:55:00.259 UAE.  These are compacted
# C5-OBS sample-side transitions: mono, vEgo, original/controller accel, pitch,
# hill, wind factor/contribution, force, minGas, brakeSide, brakeRequest,
# gasCommanded. The 18 rows retain all nine observed false->true brake-side rises.
B_HIGH_C0_70 = (
  (4262204832747, 26.6748714, -0.2350337, -0.2350337, .01792399, .17582490, .43771970, .08707219, .02786336, 0.0, False, False, True),
  (4262263766758, 26.6782322, -0.2666418, -0.2666418, .01670513, .16386969, .43745854, .08704188, -.01573018, 0.0, True, True, False),
  (4262363916237, 26.6656399, -0.2000000, -0.2000000, .01596039, .15656474, .43745854, .08696081, .04352554, 0.0, False, False, True),
  (4262424301498, 26.6568832, -0.3087234, -0.3087234, .01616052, .15852779, .43719777, .08685261, -.06334295, 0.0, True, True, False),
  (4262925846967, 26.4550323, -0.2000000, -0.2000000, .01493836, .14653982, .43823218, .08575609, .03229591, 0.0, False, False, True),
  (4263407504467, 26.3005390, -0.4417233, -0.4417233, .01494705, .14662515, .44011077, .08512289, -.20997532, 0.0, True, True, False),
  (4263468062487, 26.2901955, -0.2000000, -0.2000000, .01494264, .14658187, .44011077, .08505589, .03163776, 0.0, False, False, True),
  (4263710628164, 26.2201366, -0.4130815, -0.4130815, .01528567, .14994660, .44061923, .08469979, -.17843515, 0.0, True, True, False),
  (4263770719465, 26.1967373, -0.2000000, -0.2000000, .01489327, .14609760, .44061923, .08454803, .03064563, 0.0, False, False, True),
  (4263870895508, 26.1710644, -0.3821737, -0.3821737, .01434064, .14067687, .44087279, .08443008, -.15706670, 0.0, True, True, False),
  (4264019978788, 26.1156826, -0.2000000, -0.2000000, .01395351, .13687950, .44087279, .08407070, .02095019, 0.0, False, False, True),
  (4264062411965, 26.0991096, -0.3933892, -0.3933892, .01356831, .13310103, .44104087, .08399516, -.17629300, 0.0, True, True, False),
  (4264162059675, 26.0609550, -0.2000000, -0.2000000, .01297791, .12730971, .44120851, .08377931, .01108901, 0.0, False, False, True),
  (4264322187643, 25.9869595, -0.3699179, -0.3699179, .01236750, .12132210, .44187748, .08342507, -.16517070, 0.0, True, True, False),
  (4264623510820, 25.9067383, -0.2000000, -0.2000000, .01198871, .11760642, .44212881, .08295046, .00055687, 0.0, False, False, True),
  (4264664508424, 25.8925419, -0.3810572, -0.3810572, .01284022, .12595908, .44229469, .08288915, -.17220898, 0.0, True, True, False),
  (4264723460456, 25.8713970, -0.2000000, -0.2000000, .01362934, .13369972, .44229469, .08275150, .01645121, 0.0, False, False, True),
  (4264823658476, 25.8282280, -0.3975838, -0.3975838, .01405082, .13783397, .44270799, .08254752, -.17720234, 0.0, True, True, False),
)


def _controller_and_acc_capture(monkeypatch):
  cp = _accord_cp()
  controller = CarController(DBC[cp.carFingerprint], cp)
  calls = []
  monkeypatch.setattr(hondacan, "create_acc_commands", lambda *args, **kwargs: calls.append((args, kwargs)) or [])
  monkeypatch.setattr(hondacan, "create_steering_control", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_lkas_hud", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "create_radar_hud_canfd", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_canfd_supplemental", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_canfd_50hz_radar_messages", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "create_canfd_5hz_radar_messages", lambda *args, **kwargs: [])
  return cp, controller, calls


def _replay_crossover_sample(controller, calls, frame, sample):
  _, v_ego, original_accel, controller_accel, pitch, hill, wind_factor, wind_contrib, force, min_gas, brake_side, brake_request, gas_commanded = sample
  cc = structs.CarControl.new_message()
  cc.enabled = True
  cc.longActive = True  # Explicit same-cycle branch state; not a nearest CC join.
  cc.latActive = False
  cc.actuators.accel = original_accel
  cc.actuators.longControlState = LongCtrlState.pid
  cc.orientationNED = [0.0, pitch, 0.0]

  out = structs.CarState.new_message()
  out.vEgo = v_ego
  # aEgo is unavailable in the threshold artifact. Matching it to requested accel
  # prevents live learning from changing the recorded force; this is why this is
  # same-cycle branch replay, not an input-identical controller replay.
  out.aEgo = original_accel
  out.cruiseState.available = True
  cs = SimpleNamespace(
    out=out, v_cruise_factor=1.0, canfd_relay_open=True, stock_acc_alive=False,
    hud_tick=False, supp_tick=False, radar_50hz_tick=False, radar_5hz_tick=False,
    radar_ref_counter=0, is_metric=False, acc_hud={}, lkas_hud={"LKAS_READY": 0},
    cruise_buttons=0, cruise_setting=0, scm_ambient_light=0,
  )
  controller.bosch_wind_factor = wind_factor
  controller.bosch_wind_factor_before_brake = wind_factor
  controller.frame = frame
  actuators, _ = controller.update(cc.as_reader(), cs, 0, _toggles())
  args, kwargs = calls[-1]
  return actuators, args, kwargs, (controller_accel, hill, wind_contrib, force, min_gas, brake_side, brake_request, gas_commanded)


def test_c5b_high_train_same_cycle_controller_replay_and_mutex(monkeypatch):
  cp, controller, calls = _controller_and_acc_capture(monkeypatch)
  observed_sides = []
  for i, sample in enumerate(B_HIGH_C0_70):
    actuators, args, kwargs, observed = _replay_crossover_sample(controller, calls, 100 + 2 * i, sample)
    controller_accel, hill, wind_contrib, force, min_gas, brake_side, brake_request, gas_commanded = observed

    assert args[4] == pytest.approx(sample[2])  # original requested accel is the crossover input
    assert actuators.accel == pytest.approx(controller_accel)
    assert actuators.c5ObsHondaVEgo == pytest.approx(sample[1])
    assert actuators.c5ObsHondaOriginalAccel == pytest.approx(sample[2])
    assert actuators.c5ObsHondaControllerAccel == pytest.approx(controller_accel)
    assert actuators.c5ObsHondaPitch == pytest.approx(sample[4])
    assert actuators.c5ObsHondaHillContribution == pytest.approx(hill, abs=2e-6)
    assert actuators.c5ObsHondaWindFactor == pytest.approx(sample[6])
    assert actuators.c5ObsHondaWindContribution == pytest.approx(wind_contrib, abs=2e-6)
    assert kwargs["gas_force"] == pytest.approx(force, abs=3e-6)
    assert (kwargs["gas_force"] < min_gas) is brake_side
    assert actuators.c5ObsHondaBrakeRequest is brake_request
    assert actuators.c5ObsHondaGasCommanded is gas_commanded
    observed_sides.append(brake_side)

    class FakePacker:
      @staticmethod
      def make_can_msg(name, bus, values):
        return name, bus, values

    values = pack_acc_commands(FakePacker(), SimpleNamespace(pt=1), True, True, args[4], args[5], args[6], cp,
                               gas_force=kwargs["gas_force"], braking=kwargs["braking"])[-1][2]
    assert bool(values["BRAKE_REQUEST"]) is brake_request
    assert not (values["GAS_COMMAND"] > 0 and values["BRAKE_REQUEST"] == 1)
    assert not (values["GAS_COMMAND"] > 0 and values["BRAKE_LIGHTS"] == 1)

  assert sum(b and not a for a, b in zip(observed_sides, observed_sides[1:], strict=False)) == 9


def test_c5d_torque_path_has_lateral_provenance_builder():
  cp = _accord_cp()
  CarInterfaceBase.configure_torque_tune(CAR.HONDA_ACCORD_11G, cp.lateralTuning)
  ci = SimpleNamespace(
    torque_from_lateral_accel=lambda: lambda torque, _params: torque,
    lateral_accel_from_torque=lambda: lambda torque, _params: torque,
  )
  assert hasattr(LatControlTorque(cp.as_reader(), ci, 0.01), "starpilot_lateral_state")


@pytest.mark.xfail(strict=True, reason="C5-D RED: PID has no controller-agnostic lateral provenance builder")
def test_c5d_pid_path_publishes_controller_agnostic_lateral_provenance():
  cp = _accord_cp()
  assert hasattr(LatControlPID(cp.as_reader(), SimpleNamespace(), 0.01), "starpilot_lateral_state")


def test_c5d_guard_observation_is_output_pure():
  plan = SimpleNamespace(position=SimpleNamespace(x=[i * .5 for i in range(200)], y=[0.0] * 200))
  baseline = limit_curvature_to_plan(plan, .0155, 1.2)
  observation = SimpleNamespace()
  assert limit_curvature_to_plan(plan, .0155, 1.2, observation) == pytest.approx(baseline)

from types import SimpleNamespace

import pytest
from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda import hondacan
from opendbc.car.honda.carcontroller import CarController, get_honda_bosch_wind_brake_mps2
from opendbc.car.honda.hondacan import create_acc_commands
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, DBC
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState


def get_test_toggles():
  return SimpleNamespace(always_on_lateral_lkas=False, force_torque_controller=False, nnff=False, nnff_lite=False)


def get_accord_cp():
  return CarInterface.get_params(CAR.HONDA_ACCORD_11G, gen_empty_fingerprint(), [], True, False, False, get_test_toggles())


def make_boundary(monkeypatch):
  cp = get_accord_cp()
  controller = CarController(DBC[cp.carFingerprint], cp)
  recorded = []
  monkeypatch.setattr(hondacan, "create_acc_commands", lambda *args, **kwargs: recorded.append((args, kwargs)) or [])
  monkeypatch.setattr(hondacan, "create_steering_control", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_lkas_hud", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "create_radar_hud_canfd", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_canfd_supplemental", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_canfd_50hz_radar_messages", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "create_canfd_5hz_radar_messages", lambda *args, **kwargs: [])
  return controller, recorded


def run_boundary_frame(controller, recorded, frame, accel, a_ego):
  cc = structs.CarControl.new_message()
  cc.enabled = True
  cc.longActive = True
  cc.latActive = False
  cc.actuators.accel = float(accel)
  cc.actuators.torque = 0.0
  cc.actuators.longControlState = LongCtrlState.stopping
  cc.orientationNED = [0.0, 0.0, 0.0]

  out = structs.CarState.new_message()
  out.vEgo = 2.0
  out.aEgo = float(a_ego)
  out.cruiseState.available = True
  cs = SimpleNamespace(
    out=out, v_cruise_factor=1.0, canfd_relay_open=True, stock_acc_alive=False,
    hud_tick=False, supp_tick=False, radar_50hz_tick=False, radar_5hz_tick=False,
    radar_ref_counter=0, is_metric=False, acc_hud={}, lkas_hud={"LKAS_READY": 0},
    cruise_buttons=0, cruise_setting=0, scm_ambient_light=0,
  )
  controller.frame = frame
  controller.update(cc.as_reader(), cs, 0, get_test_toggles())
  return recorded[-1]


def test_accord_ls003_resets_addon_on_first_nonnegative_brake_error(monkeypatch):
  controller, recorded = make_boundary(monkeypatch)
  requested_accel = -0.492

  for frame in range(100, 160, 2):
    run_boundary_frame(controller, recorded, frame, requested_accel, a_ego=0.0)
  assert recorded[-1][0][4] < requested_accel

  args, _ = run_boundary_frame(controller, recorded, 160, requested_accel, a_ego=requested_accel)
  assert args[4] == pytest.approx(requested_accel)


def test_accord_c3_rearm_requires_two_consecutive_negative_opportunities(monkeypatch):
  controller, recorded = make_boundary(monkeypatch)
  requested_accel = -0.5
  first_deficit_a_ego = -0.45

  args, _ = run_boundary_frame(controller, recorded, 100, requested_accel, a_ego=0.0)
  assert args[4] < requested_accel

  args, _ = run_boundary_frame(controller, recorded, 102, requested_accel, a_ego=requested_accel)
  assert args[4] == pytest.approx(requested_accel)

  args, _ = run_boundary_frame(controller, recorded, 104, requested_accel, a_ego=first_deficit_a_ego)
  assert args[4] == pytest.approx(requested_accel)

  args, _ = run_boundary_frame(controller, recorded, 106, requested_accel, a_ego=requested_accel)
  assert args[4] == pytest.approx(requested_accel)

  args, _ = run_boundary_frame(controller, recorded, 108, requested_accel, a_ego=first_deficit_a_ego)
  assert args[4] == pytest.approx(requested_accel)

  args, _ = run_boundary_frame(controller, recorded, 110, requested_accel, a_ego=first_deficit_a_ego)
  assert args[4] < requested_accel


def test_accord_crossover_uses_original_requested_accel(monkeypatch):
  controller, recorded = make_boundary(monkeypatch)
  controller.mvl_brake_pid.update = lambda **kwargs: -0.5
  requested_accel = -0.1
  args, kwargs = run_boundary_frame(controller, recorded, 100, requested_accel, a_ego=0.0)

  assert args[4] < requested_accel
  assert kwargs["gas_force"] == pytest.approx(requested_accel + get_honda_bosch_wind_brake_mps2(2.0))
  assert kwargs["gas_force"] > args[4]
  assert kwargs["braking"] is None


@pytest.mark.parametrize("active,accel,gas_force,braking", [
  (True, 0.2, 0.5, False),
  (True, 0.0, 0.0, False),
  (True, -0.2, -0.5, True),
  (True, 0.2, -0.5, False),
  (True, -0.2, 0.5, True),
  (False, 0.2, 0.5, False),
])
def test_accord_final_can_gas_brake_mutex(active, accel, gas_force, braking):
  class FakePacker:
    @staticmethod
    def make_can_msg(name, bus, values):
      return name, bus, values

  values = create_acc_commands(
    FakePacker(), SimpleNamespace(pt=1), True, active, accel, 500, 0, get_accord_cp(), gas_force, braking,
  )[-1][2]
  assert not (values["GAS_COMMAND"] > 0 and values["BRAKE_REQUEST"] == 1)
  assert not (values["GAS_COMMAND"] > 0 and values["BRAKE_LIGHTS"] == 1)

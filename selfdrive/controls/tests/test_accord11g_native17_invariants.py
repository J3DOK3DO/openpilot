from pathlib import Path
from types import SimpleNamespace

import pytest
from opendbc.car import gen_empty_fingerprint, structs
from opendbc.car.honda import carcontroller as hcc
from opendbc.car.honda import hondacan
from opendbc.car.honda.carcontroller import CarController, get_honda_bosch_wind_brake_mps2, update_honda_bosch_braking
from opendbc.car.honda.hondacan import create_acc_commands
from opendbc.car.honda.interface import CarInterface
from opendbc.car.honda.values import CAR, DBC, HONDA_BOSCH_A, HONDA_BOSCH_CANFD, HondaSafetyFlags
from openpilot.selfdrive.controls.lib.longcontrol import LongCtrlState
from openpilot.selfdrive.controls.lib.longitudinal_vehicle_tunes import get_honda_accord_11g_reduction_only_v_cruise


def get_test_toggles():
  return SimpleNamespace(
    always_on_lateral_lkas=False,
    force_torque_controller=False,
    nnff=False,
    nnff_lite=False,
  )


def get_accord_cp():
  return CarInterface.get_params(
    CAR.HONDA_ACCORD_11G,
    gen_empty_fingerprint(),
    [],
    True,
    False,
    False,
    get_test_toggles(),
  )


def test_accord_11g_reduction_only_cruise_authority():
  """Planner policy can lower, but never raise, the live stock cruise target."""
  cp = get_accord_cp()
  assert cp.carFingerprint == CAR.HONDA_ACCORD_11G

  assert get_honda_accord_11g_reduction_only_v_cruise(cp, 25.0, 25.0) == pytest.approx(25.0)
  assert get_honda_accord_11g_reduction_only_v_cruise(cp, 25.0, 19.0) == pytest.approx(19.0)
  assert get_honda_accord_11g_reduction_only_v_cruise(cp, 25.0, 31.0) == pytest.approx(25.0)
  assert get_honda_accord_11g_reduction_only_v_cruise(cp, 25.0, float("nan")) == pytest.approx(25.0)
  assert get_honda_accord_11g_reduction_only_v_cruise(cp, 25.0, -1.0) == pytest.approx(25.0)

  planner_source = Path(__file__).resolve().parents[1] / "lib" / "longitudinal_planner.py"
  source = planner_source.read_text()
  assert "get_honda_accord_11g_reduction_only_v_cruise(" in source
  assert "stock_v_cruise = min(float(sm['carState'].vCruise), V_CRUISE_MAX) * CV.KPH_TO_MS" in source


def test_accord_11g_platform_tune_and_bosch_c_identity():
  cp = get_accord_cp()

  assert cp.longitudinalActuatorDelay == pytest.approx(0.05)
  assert cp.steerActuatorDelay == pytest.approx(0.3)
  assert cp.lateralParams.torqueBP == pytest.approx([0.0, 12789.0])
  assert cp.lateralParams.torqueV == pytest.approx([0.0, 12789.0])
  assert cp.lateralTuning.pid.kf == pytest.approx(0.000035)
  assert cp.lateralTuning.pid.kpV == pytest.approx([0.115])
  assert cp.lateralTuning.pid.kiV == pytest.approx([0.052])
  assert CarController(DBC[cp.carFingerprint], cp).params.BOSCH_GAS_LOOKUP_BP[0] == pytest.approx(0.0)

  assert CAR.HONDA_ACCORD_11G in HONDA_BOSCH_CANFD
  assert CAR.HONDA_ACCORD_11G not in HONDA_BOSCH_A
  assert cp.safetyConfigs[-1].safetyParam & HondaSafetyFlags.BOSCH_CANFD.value
  assert cp.safetyConfigs[-1].safetyParam & HondaSafetyFlags.BOSCH_CANFD_MVL.value


def test_low_speed_brake_correction_preserves_requested_force_for_crossover(monkeypatch):
  """The Accord-only correction can only lower final accel, never redefine gas crossover."""
  cp = get_accord_cp()
  controller = CarController(DBC[cp.carFingerprint], cp)
  controller.mvl_brake_pid.update = lambda **kwargs: -0.5

  recorded = []
  monkeypatch.setattr(hondacan, "create_acc_commands", lambda *args, **kwargs: recorded.append((args, kwargs)) or [])
  monkeypatch.setattr(hondacan, "create_steering_control", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_lkas_hud", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "create_radar_hud_canfd", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_canfd_supplemental", lambda *args, **kwargs: (0, b"", 0))
  monkeypatch.setattr(hondacan, "create_canfd_50hz_radar_messages", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "create_canfd_5hz_radar_messages", lambda *args, **kwargs: [])

  cc = structs.CarControl.new_message()
  cc.enabled = True
  cc.longActive = True
  cc.latActive = False
  cc.actuators.accel = -0.1
  cc.actuators.torque = 0.0
  cc.actuators.longControlState = LongCtrlState.pid
  cc.orientationNED = [0.0, 0.0, 0.0]

  out = structs.CarState.new_message()
  out.vEgo = 2.0
  out.aEgo = 0.0
  out.cruiseState.available = True
  cs = SimpleNamespace(
    out=out,
    v_cruise_factor=1.0,
    canfd_relay_open=True,
    stock_acc_alive=False,
    hud_tick=False,
    supp_tick=False,
    radar_50hz_tick=False,
    radar_5hz_tick=False,
    radar_ref_counter=0,
    is_metric=False,
    acc_hud={},
    lkas_hud={"LKAS_READY": 0},
    cruise_buttons=0,
    cruise_setting=0,
    scm_ambient_light=0,
  )

  controller.frame = 100
  controller.update(cc.as_reader(), cs, 0, get_test_toggles())

  assert len(recorded) == 1
  args, kwargs = recorded[0]
  final_accel = args[4]
  original_force = kwargs["gas_force"]
  expected_force = cc.actuators.accel + get_honda_bosch_wind_brake_mps2(out.vEgo)
  assert final_accel <= cc.actuators.accel
  assert original_force == pytest.approx(expected_force)
  assert original_force > final_accel
  assert kwargs["braking"] is None


def test_accord_bypasses_generic_bosch_brake_hysteresis_owner():
  cp = get_accord_cp()
  controller = CarController(DBC[cp.carFingerprint], cp)
  assert controller.mvl_accord_mode

  # Generic hysteresis remains a utility, but Accord deliberately leaves its final
  # braking decision to the original road-load crossover in create_acc_commands.
  assert update_honda_bosch_braking(False, -0.2, False, True)
  source = Path(hcc.__file__).read_text()
  assert "if not self.mvl_accord_mode:" in source
  assert "bosch_braking = self.bosch_braking" in source
  assert "braking=bosch_braking" in source


@pytest.mark.parametrize("active,accel,gas_force,braking", [
  (True, 0.2, 0.5, False),
  (True, 0.0, 0.0, False),
  (True, -0.2, -0.5, True),
  (True, 0.2, -0.5, False),
  (True, -0.2, 0.5, True),
  (False, 0.2, 0.5, False),
])
def test_bosch_acc_command_never_combines_gas_and_braking(active, accel, gas_force, braking):
  class FakePacker:
    @staticmethod
    def make_can_msg(name, bus, values):
      return name, bus, values

  values = create_acc_commands(
    FakePacker(), SimpleNamespace(pt=1), True, active, accel, 500, 0, get_accord_cp(), gas_force, braking,
  )[-1][2]
  assert not (values["GAS_COMMAND"] > 0 and values["BRAKE_REQUEST"] == 1)
  assert not (values["GAS_COMMAND"] > 0 and values["BRAKE_LIGHTS"] == 1)


def test_canfd_replacement_acc_requires_deferred_accord_ownership(monkeypatch):
  """No replacement ACC/radar messages until relay is open and stock ACC is gone."""
  cp = get_accord_cp()
  controller = CarController(DBC[cp.carFingerprint], cp)
  calls = []

  def single(name):
    def fn(*args, **kwargs):
      del args, kwargs
      calls.append(name)
      return (0x700, b"\\x00" * 8, 0)
    return fn

  def multiple(name):
    def fn(*args, **kwargs):
      del args, kwargs
      calls.append(name)
      return [(0x701, b"\\x00" * 8, 0)]
    return fn

  monkeypatch.setattr(hondacan, "create_acc_commands", multiple("ACC_COMMANDS"))
  monkeypatch.setattr(hondacan, "create_acc_hud", single("ACC_HUD"))
  monkeypatch.setattr(hondacan, "create_radar_hud_canfd", single("RADAR_HUD_CANFD"))
  monkeypatch.setattr(hondacan, "create_canfd_supplemental", single("RADAR_SUPPLEMENTAL"))
  monkeypatch.setattr(hondacan, "create_canfd_50hz_radar_messages", multiple("RADAR_50HZ"))
  monkeypatch.setattr(hondacan, "create_canfd_5hz_radar_messages", multiple("RADAR_5HZ"))
  monkeypatch.setattr(hondacan, "create_steering_control", single("STEERING"))
  monkeypatch.setattr(hondacan, "create_lkas_hud", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "spam_buttons_command", single("SCM_BUTTONS"))

  replacement = {"ACC_COMMANDS", "ACC_HUD", "RADAR_HUD_CANFD", "RADAR_SUPPLEMENTAL", "RADAR_50HZ", "RADAR_5HZ"}

  def make_cc():
    cc = structs.CarControl.new_message()
    cc.enabled = False
    cc.longActive = False
    cc.latActive = False
    cc.actuators.accel = 0.0
    cc.actuators.torque = 0.0
    return cc.as_reader()

  def make_cs(relay_open, stock_alive):
    out = structs.CarState.new_message()
    out.vEgo = 10.0
    out.aEgo = 0.0
    out.cruiseState.available = True
    return SimpleNamespace(
      out=out,
      v_cruise_factor=1.0,
      canfd_relay_open=relay_open,
      stock_acc_alive=stock_alive,
      hud_tick=True,
      supp_tick=True,
      radar_50hz_tick=True,
      radar_5hz_tick=True,
      radar_ref_counter=0,
      is_metric=False,
      acc_hud={},
      lkas_hud={"LKAS_READY": 0},
      cruise_buttons=0,
      cruise_setting=0,
      scm_ambient_light=0,
    )

  def run_state(relay_open, stock_alive):
    calls.clear()
    controller.frame = 100
    controller.update(make_cc(), make_cs(relay_open, stock_alive), 0, get_test_toggles())
    return set(calls) & replacement

  assert run_state(False, True) == set()
  assert run_state(True, True) == set()
  assert run_state(True, False) == replacement
  assert run_state(True, True) == set()
  assert run_state(False, False) == set()

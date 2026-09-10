from pathlib import Path


SRC = (
  Path(__file__).resolve().parents[1] /
  "carcontroller.py"
).read_text()


def test_ownership_expression_is_deferred():
  assert (
    "mvl_radar_owned = self.mvl_accord_mode and "
    "CS.canfd_relay_open and not CS.stock_acc_alive"
  ) in SRC


def test_replacement_acc_is_behind_ownership_gate():
  gate = SRC.index(
    "if not self.mvl_accord_mode or mvl_radar_owned:"
  )

  command = SRC.index(
    "hondacan.create_acc_commands(",
    gate,
  )

  assert gate < command


def test_radar_disable_requires_open_relay():
  stock = SRC.index(
    "if self.mvl_accord_mode and CS.stock_acc_alive:"
  )

  relay = SRC.index(
    "if CS.canfd_relay_open:",
    stock,
  )

  diagnostic = SRC.index(
    "self.radar_disable_counter",
    relay,
  )

  assert stock < relay < diagnostic


def test_owned_radar_streams_start_only_after_ownership():
  owned = SRC.index(
    "if mvl_radar_owned and self.CP.openpilotLongitudinalControl:"
  )

  radar = SRC.index(
    "radar_msgs = []",
    owned,
  )

  assert owned < radar


def test_dynamic_canfd_ownership_sequence(monkeypatch):
  """Replacement ACC/radar traffic exists only while Accord CAN-FD ownership is valid."""
  from types import SimpleNamespace

  from opendbc.car import gen_empty_fingerprint, structs
  from opendbc.car.honda import carcontroller as hcc
  from opendbc.car.honda import hondacan
  from opendbc.car.honda.carcontroller import CarController
  from opendbc.car.honda.interface import CarInterface
  from opendbc.car.honda.values import CAR, DBC

  class FakeParams:
    def get_float(self, key, block=False, return_default=False, default=0.0):
      del key, block, return_default
      return default

  monkeypatch.setattr(hcc, "Params", lambda: FakeParams())

  toggles = SimpleNamespace(
    always_on_lateral_lkas=False,
    force_torque_controller=False,
    nnff=False,
    nnff_lite=False,
  )

  CP = CarInterface.get_params(
    CAR.HONDA_ACCORD_11G,
    gen_empty_fingerprint(),
    [],
    True,
    False,
    False,
    toggles,
  )

  assert CP.carFingerprint == CAR.HONDA_ACCORD_11G
  assert CP.openpilotLongitudinalControl

  controller = CarController(DBC[CP.carFingerprint], CP)
  calls = []

  def single(name):
    def fn(*args, **kwargs):
      del args, kwargs
      calls.append(name)
      return (0x700, b"\x00" * 8, 0)
    return fn

  def multiple(name):
    def fn(*args, **kwargs):
      del args, kwargs
      calls.append(name)
      return [(0x701, b"\x00" * 8, 0)]
    return fn

  monkeypatch.setattr(hondacan, "create_acc_commands", multiple("ACC_COMMANDS"))
  monkeypatch.setattr(hondacan, "create_acc_hud", single("ACC_HUD"))
  monkeypatch.setattr(hondacan, "create_radar_hud_canfd", single("RADAR_HUD_CANFD"))
  monkeypatch.setattr(hondacan, "create_canfd_supplemental", single("RADAR_SUPPLEMENTAL"))
  monkeypatch.setattr(hondacan, "create_canfd_50hz_radar_messages", multiple("RADAR_50HZ"))
  monkeypatch.setattr(hondacan, "create_canfd_5hz_radar_messages", multiple("RADAR_5HZ"))

  # These are outside the longitudinal/radar ownership domain.
  monkeypatch.setattr(hondacan, "create_steering_control", single("STEERING"))
  monkeypatch.setattr(hondacan, "create_lkas_hud", lambda *args, **kwargs: [])
  monkeypatch.setattr(hondacan, "spam_buttons_command", single("SCM_BUTTONS"))

  replacement = {
    "ACC_COMMANDS",
    "ACC_HUD",
    "RADAR_HUD_CANFD",
    "RADAR_SUPPLEMENTAL",
    "RADAR_50HZ",
    "RADAR_5HZ",
  }

  def make_cc():
    CC = structs.CarControl.new_message()
    CC.enabled = False
    CC.longActive = False
    CC.latActive = False
    CC.actuators.accel = 0.0
    CC.actuators.torque = 0.0
    return CC.as_reader()

  def make_cs(relay_open, stock_alive):
    out = structs.CarState.new_message()
    out.vEgo = 10.0
    out.aEgo = 0.0
    out.steeringPressed = False
    out.gasPressed = False
    out.brakePressed = False
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

    # Exercise all relevant periodic cadence gates.
    controller.frame = 100

    _, can_sends = controller.update(
      make_cc(),
      make_cs(relay_open, stock_alive),
      0,
      toggles,
    )

    return set(calls) & replacement, can_sends

  # 1. Relay closed and stock ACC alive: stock still owns longitudinal.
  seen, _ = run_state(False, True)
  assert seen == set()

  # 2. Relay open but stock ACC still alive:
  # diagnostics may begin, replacement traffic may not.
  seen, can_sends = run_state(True, True)
  assert seen == set()
  assert any(msg[0] == 0x18DAB0F1 for msg in can_sends)

  # 3. Relay open and stock ACC gone: ownership acquired.
  seen, _ = run_state(True, False)
  assert seen == replacement

  # 4. Stock ACC returns: ownership revoked immediately.
  seen, _ = run_state(True, True)
  assert seen == set()

  # 5. Relay closes: ownership is also revoked.
  seen, _ = run_state(False, False)
  assert seen == set()

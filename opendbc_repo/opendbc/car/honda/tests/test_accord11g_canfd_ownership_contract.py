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

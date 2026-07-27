import json
import pytest
import pyray as rl
from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.onroad.starpilot.widgets.favorites_dock import FavoritesDockWidget
from openpilot.starpilot.common.favorite_slots import (
  FAVORITE_SLOTS_PARAM, default_favorite_slots, save_favorite_slots, toggle_favorite_slot
)
from openpilot.system.ui.lib.application import MousePos


@pytest.fixture(autouse=True)
def setup_params():
  params = Params()
  params_memory = Params(memory=True)

  # Populate default slots in params
  slots = default_favorite_slots()
  slots[0] = {"enabled": True, "show_onroad": True, "key": "ExperimentalMode", "label": "Chill / Exp"}
  slots[1] = {"enabled": True, "show_onroad": True, "key": "__starpilot_favorite_action__:distance_increase", "label": "Distance +"}
  save_favorite_slots(slots, params)
  ui_state.started = True
  yield params, params_memory


def test_favorites_dock_initialization(setup_params):
  dock = FavoritesDockWidget()

  assert dock.name == "favorites_dock"
  assert dock.priority == 3
  assert dock.pinned is False
  assert dock.is_expanded is False
  assert dock.is_visible is True


def test_favorites_dock_size_calculation(setup_params):
  dock = FavoritesDockWidget()
  width, height = dock.get_size()

  assert width == dock.HANDLE_WIDTH
  assert height == dock.HANDLE_HEIGHT  # when collapsed


def test_favorites_dock_pin_toggle(setup_params):
  dock = FavoritesDockWidget()
  dock.is_expanded = True
  dock._pin_rect = rl.Rectangle(10, 10, 80, 80)

  # Simulate pin button press & release
  dock._pressed_pin = True
  dock._handle_mouse_release(MousePos(15, 15))

  assert dock.pinned is True
  assert dock.is_expanded is True


def test_favorites_dock_handle_toggle(setup_params):
  dock = FavoritesDockWidget()
  initial_expanded = dock.is_expanded
  dock._handle_rect = rl.Rectangle(10, 10, 100, 30)

  # Press handle
  dock._pressed_handle = True
  dock._handle_mouse_release(MousePos(15, 15))

  assert dock.is_expanded == (not initial_expanded)


def test_favorites_dock_slot_toggle_bool(setup_params):
  params, params_memory = setup_params
  dock = FavoritesDockWidget()
  dock.is_expanded = True

  # Press & release slot #0
  dock._pressed_slot = 0
  dock._slot_rects = [(0, rl.Rectangle(10, 10, 100, 100))]
  dock._handle_mouse_release(MousePos(15, 15))

  assert dock._feedback_slot == 0


def test_aethergrid_favorite_slot_display(setup_params, monkeypatch):
  from openpilot.system.ui.lib.application import gui_app
  monkeypatch.setattr(gui_app, "font", lambda weight=None: None)

  from openpilot.selfdrive.ui.layouts.settings.starpilot.appearance import StarPilotAppearanceLayout
  params, _ = setup_params

  layout = StarPilotAppearanceLayout()
  disp0 = layout._get_favorite_slot_display(0)
  disp1 = layout._get_favorite_slot_display(1)
  disp2 = layout._get_favorite_slot_display(2)

  assert disp0 == "Chill / Exp"
  assert disp1 == "Distance + / RES"
  assert disp2 == "Disabled"


def test_slot_visual_spec(setup_params):
  from openpilot.selfdrive.ui.onroad.starpilot.widgets.favorites_dock import SlotVisualSpec
  params, _ = setup_params

  # 1. ExperimentalMode = False (Chill Mode)
  params.put_bool("ExperimentalMode", False)
  spec_chill = SlotVisualSpec("ExperimentalMode", "Chill / Exp", params)
  assert spec_chill.title == "CHILL MODE"
  assert spec_chill.status_badge == "CHILL"

  # 2. ExperimentalMode = True (Experimental Mode)
  params.put_bool("ExperimentalMode", True)
  spec_exp = SlotVisualSpec("ExperimentalMode", "Chill / Exp", params)
  assert spec_exp.title == "EXPERIMENTAL"
  assert spec_exp.status_badge == "EXP"

  # 3. Virtual Cruise Action Slot
  spec_action = SlotVisualSpec("__starpilot_favorite_action__:distance_increase", "Distance +", params)
  assert spec_action.mode_type == "action"
  assert spec_action.status_badge == "ACTION"

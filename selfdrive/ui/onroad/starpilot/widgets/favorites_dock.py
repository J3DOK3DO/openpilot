from __future__ import annotations

import pyray as rl

from openpilot.common.params import Params
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.layouts.settings.starpilot.aethergrid import AetherListColors
from openpilot.starpilot.common.favorite_slots import (
  load_favorite_slots, toggle_favorite_slot, is_favorite_action_key
)
from openpilot.system.ui.lib.application import gui_app, FontWeight, MousePos
from openpilot.system.ui.lib.text_measure import measure_text_cached

try:
  from openpilot.selfdrive.ui.layouts.settings.starpilot.aethergrid import (
    draw_constellation_nodes, _get_or_create_toggle_constellation
  )
except Exception:
  draw_constellation_nodes = None
  _get_or_create_toggle_constellation = None


def _measure(font, text: str, size: int) -> rl.Vector2:
  return measure_text_cached(font, text, size) if font else rl.Vector2(0, 0)


def _draw(font, text: str, pos: rl.Vector2, size: int, color: rl.Color) -> None:
  if font:
    rl.draw_text_ex(font, text, pos, size, 0, color)


def _draw_perfect_card(
  rect: rl.Rectangle,
  roundness: float,
  segments: int,
  bg_color: rl.Color,
  border_color: rl.Color,
  thickness: float = 1.5,
) -> None:
  """Draws a pixel-perfect rounded card fill and border stroke with zero anti-aliasing edge bleed."""
  # 1. Fill solid card area
  rl.draw_rectangle_rounded(rect, roundness, segments, bg_color)
  # 2. Draw border stroke inset by 1px so stroke anti-aliasing sits 100% inside filled background
  stroke_rect = rl.Rectangle(rect.x + 1.0, rect.y + 1.0, max(1.0, rect.width - 2.0), max(1.0, rect.height - 2.0))
  rl.draw_rectangle_rounded_lines_ex(stroke_rect, roundness, segments, thickness, border_color)


class SlotVisualSpec:
  """Extensible visual state resolver for favorite slot tiles using AetherListColors."""

  def __init__(self, key: str | None, custom_label: str, params: Params):
    self.key = key
    self.custom_label = custom_label
    self.is_action = is_favorite_action_key(key)

    if self.is_action:
      self.mode_type = "action"
      self.symbol = "+" if key == "__starpilot_favorite_action__:distance_increase" else "-"
      self.title = custom_label or ("Distance +" if self.symbol == "+" else "Distance -")
      self.status_badge = "ACTION"
      self.accent_color = AetherListColors.PRIMARY
      self.bg_color = AetherListColors.CURRENT_BG
    elif key == "ExperimentalMode":
      self.mode_type = "mode_switch"
      is_exp = params.get_bool(key)
      if is_exp:
        self.title = "EXPERIMENTAL"
        self.status_badge = "EXP"
        self.accent_color = AetherListColors.WARNING
        self.bg_color = rl.Color(48, 32, 14, 215)
      else:
        self.title = "CHILL MODE"
        self.status_badge = "CHILL"
        self.accent_color = AetherListColors.PRIMARY
        self.bg_color = AetherListColors.CURRENT_BG
    else:
      self.mode_type = "toggle"
      val = params.get_bool(key) if key else False
      self.title = custom_label or key or "Toggle"
      if val:
        self.status_badge = "ON"
        self.accent_color = AetherListColors.PRIMARY
        self.bg_color = AetherListColors.CURRENT_BG
      else:
        self.status_badge = "OFF"
        self.accent_color = AetherListColors.MUTED
        self.bg_color = rl.Color(22, 20, 32, 210)


class FavoritesDockWidget(LayoutWidget):
  """Modern floating, pinnable Favorites Dock widget expanding vertically downward beneath left-side widgets."""

  AUTO_HIDE_TIMEOUT = 4.0      # Seconds of inactivity before auto-collapsing
  HANDLE_HEIGHT = 38.0         # Height of top pull tab header bar
  HANDLE_WIDTH = 176.0         # Width of header bar and dock for zero-collision layout
  SLOT_HEIGHT = 76.0
  SLOT_WIDTH = 152.0           # HANDLE_WIDTH - (PADDING * 2)
  GAP = 10.0
  PADDING = 12.0

  def __init__(self):
    super().__init__("favorites_dock", priority=3)
    self._params = Params()
    self._params_memory = Params(memory=True)
    self.pinned = False
    self.is_expanded = False
    self.anim_progress = 0.0

    self._last_interaction_time = rl.get_time()
    self._pressed_slot: int | None = None
    self._pressed_pin = False
    self._pressed_handle = False
    self._feedback_slot: int | None = None
    self._feedback_start_time = 0.0

    # Layout Rect Cache
    self._handle_rect = rl.Rectangle(0, 0, 0, 0)
    self._dock_rect = rl.Rectangle(0, 0, 0, 0)
    self._pin_rect = rl.Rectangle(0, 0, 0, 0)
    self._slot_rects: list[tuple[int, rl.Rectangle]] = []

  @property
  def font_bold(self):
    try:
      return gui_app.font(FontWeight.BOLD)
    except Exception:
      return None

  @property
  def font_semi(self):
    try:
      return gui_app.font(FontWeight.SEMI_BOLD)
    except Exception:
      return None

  @property
  def is_visible(self) -> bool:
    if not ui_state.started:
      return False
    return len(self._visible_slots()) > 0

  def _visible_slots(self) -> list[tuple[int, dict]]:
    slots = load_favorite_slots(self._params)
    return [
      (index, slot) for index, slot in enumerate(slots)
      if slot.get("enabled") and slot.get("show_onroad") and slot.get("key")
    ]

  def get_size(self) -> tuple[float, float]:
    num_slots = max(1, len(self._visible_slots()))
    body_h = (
      self.PADDING * 2 +
      (num_slots * self.SLOT_HEIGHT) +
      ((num_slots - 1) * self.GAP)
    )
    total_h = self.HANDLE_HEIGHT + (body_h if self.is_expanded else 0.0)
    return self.HANDLE_WIDTH, total_h

  def _fit_label(self, label: str, max_width: float) -> tuple[str, int]:
    label = label or "Favorite"
    font = self.font_bold
    if font is not None:
      for font_size in range(22, 15, -1):
        if _measure(font, label, font_size).x <= max_width:
          return label, font_size
      for i in range(len(label) - 1, 3, -1):
        trunc = label[:i] + "..."
        if _measure(font, trunc, 16).x <= max_width:
          return trunc, 16
    return (label[:10] + "...") if len(label) > 10 else label, 16

  def _update_state(self):
    now = rl.get_time()

    # Auto-hide evaluation when unpinned
    if not self.pinned and self.is_expanded:
      if now - self._last_interaction_time > self.AUTO_HIDE_TIMEOUT:
        self.is_expanded = False

    # Instant expand/collapse without animation delay
    self.anim_progress = 1.0 if self.is_expanded else 0.0

  def _render(self, rect: rl.Rectangle) -> None:
    slots = self._visible_slots()
    if not slots:
      return

    body_h = (
      self.PADDING * 2 +
      (len(slots) * self.SLOT_HEIGHT) +
      ((len(slots) - 1) * self.GAP)
    )
    dock_y = rect.y + self.HANDLE_HEIGHT

    # Main header bar target
    self._handle_rect = rl.Rectangle(rect.x, rect.y, self.HANDLE_WIDTH, self.HANDLE_HEIGHT)

    # 1. Container Background Surface (Pixel-perfect inset stroke rendering)
    if self.is_expanded:
      self._dock_rect = rl.Rectangle(rect.x, dock_y, self.HANDLE_WIDTH, body_h)
      unified_rect = rl.Rectangle(rect.x, rect.y, self.HANDLE_WIDTH, self.HANDLE_HEIGHT + body_h)
      dock_bg = rl.Color(18, 14, 28, 240)

      _draw_perfect_card(unified_rect, roundness=0.08, segments=12, bg_color=dock_bg, border_color=AetherListColors.PRIMARY, thickness=2.0)

      # Subtle hairline separator under header tab
      rl.draw_line(
        int(rect.x + 20),
        int(dock_y),
        int(rect.x + self.HANDLE_WIDTH - 20),
        int(dock_y),
        AetherListColors.ROW_SEPARATOR
      )
    else:
      handle_bg = rl.Color(36, 26, 56, 245) if self._pressed_handle else rl.Color(24, 18, 38, 230)
      handle_border = AetherListColors.PRIMARY if self.pinned else AetherListColors.PANEL_BORDER
      _draw_perfect_card(self._handle_rect, roundness=0.20, segments=12, bg_color=handle_bg, border_color=handle_border, thickness=2.0)

    font_b = self.font_bold

    if not self.is_expanded and not self.pinned:
      # 1. COLLAPSED UNPINNED TAB: Centered "FAVORITES ▼" (No Pin button when collapsed)
      self._pin_rect = rl.Rectangle(0, 0, 0, 0)

      handle_title = "FAVORITES"
      h_text_size = _measure(font_b, handle_title, 14)
      total_c_w = 14.0 + 8.0 + h_text_size.x
      start_c_x = rect.x + (self.HANDLE_WIDTH - total_c_w) / 2.0

      handle_color = AetherListColors.HEADER

      # Down Chevron (▼)
      tri_size = 5.5
      tri_cx = start_c_x + 6.0
      tri_cy = self._handle_rect.y + self.HANDLE_HEIGHT / 2.0
      v1 = rl.Vector2(tri_cx, tri_cy + tri_size * 0.8)
      v2 = rl.Vector2(tri_cx + tri_size, tri_cy - tri_size * 0.6)
      v3 = rl.Vector2(tri_cx - tri_size, tri_cy - tri_size * 0.6)
      rl.draw_triangle(v1, v2, v3, handle_color)

      # Title "FAVORITES"
      h_text_pos = rl.Vector2(
        start_c_x + 18.0,
        self._handle_rect.y + (self.HANDLE_HEIGHT - h_text_size.y) / 2.0
      )
      _draw(font_b, handle_title, h_text_pos, 14, handle_color)

    elif self.is_expanded and not self.pinned:
      # 2. EXPANDED UNPINNED HEADER: Up Chevron (▲) + "FAVORITES" + Right Icon-Only Pin Pill
      self._pin_rect = rl.Rectangle(rect.x + self.HANDLE_WIDTH - 46.0, rect.y + 4.0, 40.0, self.HANDLE_HEIGHT - 8.0)

      handle_title = "FAVORITES"
      h_text_size = _measure(font_b, handle_title, 14)
      h_text_pos = rl.Vector2(
        rect.x + 25.0,
        self._handle_rect.y + (self.HANDLE_HEIGHT - h_text_size.y) / 2.0
      )
      handle_color = AetherListColors.HEADER
      _draw(font_b, handle_title, h_text_pos, 14, handle_color)

      # Up Chevron (▲)
      tri_size = 5.5
      tri_cx = rect.x + 14.0
      tri_cy = self._handle_rect.y + self.HANDLE_HEIGHT / 2.0
      v1 = rl.Vector2(tri_cx, tri_cy - tri_size * 0.8)
      v2 = rl.Vector2(tri_cx - tri_size, tri_cy + tri_size * 0.6)
      v3 = rl.Vector2(tri_cx + tri_size, tri_cy + tri_size * 0.6)
      rl.draw_triangle(v1, v2, v3, handle_color)

      # Right Icon-Only Pin Button Pill Badge (pixel-perfect inset stroke)
      pin_pill_bg = AetherListColors.PRIMARY if self._pressed_pin else rl.Color(50, 36, 75, 210)
      pin_pill_border = AetherListColors.PRIMARY if self._pressed_pin else rl.Color(255, 255, 255, 45)
      _draw_perfect_card(self._pin_rect, roundness=0.35, segments=12, bg_color=pin_pill_bg, border_color=pin_pill_border, thickness=1.5)

      # Centered Vector Push-Pin Icon (no text label)
      pin_icon_cx = self._pin_rect.x + self._pin_rect.width / 2.0
      pin_icon_cy = self._pin_rect.y + self._pin_rect.height / 2.0
      pin_icon_col = rl.WHITE if self._pressed_pin else AetherListColors.SUBTEXT

      rl.draw_circle(int(pin_icon_cx), int(pin_icon_cy - 3), 4, pin_icon_col)
      rl.draw_line_ex(
        rl.Vector2(pin_icon_cx, pin_icon_cy - 3),
        rl.Vector2(pin_icon_cx, pin_icon_cy + 6),
        2.5,
        pin_icon_col
      )

    else:
      # 3. PINNED HEADER: Centered Pin Icon + "UNPIN DOCK" button
      self._pin_rect = rl.Rectangle(rect.x, rect.y, self.HANDLE_WIDTH, self.HANDLE_HEIGHT)
      unpin_color = AetherListColors.PRIMARY
      unpin_text = "UNPIN DOCK"

      u_text_size = _measure(font_b, unpin_text, 14)
      total_u_w = 16.0 + 6.0 + u_text_size.x
      start_u_x = rect.x + (self.HANDLE_WIDTH - total_u_w) / 2.0

      # Push-Pin Icon
      pin_cx = start_u_x + 5.0
      pin_cy = self._handle_rect.y + self.HANDLE_HEIGHT / 2.0
      rl.draw_circle(int(pin_cx), int(pin_cy - 4), 5, unpin_color)
      rl.draw_line_ex(
        rl.Vector2(pin_cx, pin_cy - 4),
        rl.Vector2(pin_cx, pin_cy + 7),
        2.5,
        unpin_color
      )

      # "UNPIN DOCK" text
      u_text_pos = rl.Vector2(
        start_u_x + 18.0,
        self._handle_rect.y + (self.HANDLE_HEIGHT - u_text_size.y) / 2.0
      )
      _draw(font_b, unpin_text, u_text_pos, 14, unpin_color)

    # 2. Render Vertical Favorite Slot Cards (when expanded)
    if self.is_expanded:
      self._slot_rects.clear()
      cursor_y = dock_y + self.PADDING

      now = rl.get_time()
      for slot_index, slot in slots:
        slot_rect = rl.Rectangle(
          rect.x + self.PADDING,
          cursor_y,
          self.SLOT_WIDTH,
          self.SLOT_HEIGHT
        )
        self._slot_rects.append((slot_index, slot_rect))

        key = slot.get("key")
        spec = SlotVisualSpec(key, slot.get("label") or "", self._params)

        is_pressed = self._pressed_slot == slot_index
        is_feedback = self._feedback_slot == slot_index and (now - self._feedback_start_time < 0.6)

        # Tile card background color
        if is_feedback:
          card_bg = AetherListColors.PRIMARY
        elif is_pressed:
          card_bg = rl.Color(58, 42, 90, 245)
        else:
          card_bg = spec.bg_color

        is_active = spec.status_badge in ("ON", "CHILL", "EXP", "ACTION")

        # Inset stroke card rendering for zero camera bleed-through
        _draw_perfect_card(slot_rect, roundness=0.15, segments=12, bg_color=card_bg, border_color=spec.accent_color, thickness=2.0)

        # Render shared constellation star nodes pattern on active slot tiles
        if draw_constellation_nodes and _get_or_create_toggle_constellation and is_active:
          nodes, vecs = _get_or_create_toggle_constellation(f"fav_dock_slot_{slot_index}_{key}")
          draw_constellation_nodes(nodes, vecs, slot_rect, spec.accent_color, glow=1.0, scale=0.55)

        # Top Badge: Slot Index (#1, #2, #3)
        slot_num_str = f"#{slot_index + 1}"
        _draw(font_b, slot_num_str, rl.Vector2(slot_rect.x + 10, slot_rect.y + 8), 14, AetherListColors.SUBTEXT)

        # Top Right Status Badge Pill
        badge_size = _measure(font_b, spec.status_badge, 13)
        badge_w = badge_size.x + 12.0
        badge_h = 20.0
        badge_rect = rl.Rectangle(
          slot_rect.x + slot_rect.width - badge_w - 8.0,
          slot_rect.y + 6.0,
          badge_w,
          badge_h
        )
        rl.draw_rectangle_rounded(badge_rect, 0.35, 12, spec.accent_color)

        text_color = rl.Color(12, 16, 24, 255) if spec.status_badge in ("CHILL", "EXP", "ON") else rl.WHITE
        b_text_pos = rl.Vector2(
          badge_rect.x + (badge_rect.width - badge_size.x) / 2.0,
          badge_rect.y + (badge_rect.height - badge_size.y) / 2.0
        )
        _draw(font_b, spec.status_badge, b_text_pos, 13, text_color)

        # Center Title (BOLD font weight with auto-fitting 22pt down to 16pt)
        fitted_text, font_size = self._fit_label(spec.title, slot_rect.width - 16.0)
        lbl_size = _measure(font_b, fitted_text, font_size)
        lbl_pos = rl.Vector2(
          slot_rect.x + (slot_rect.width - lbl_size.x) / 2.0,
          slot_rect.y + 28.0 + (slot_rect.height - 34.0 - lbl_size.y) / 2.0
        )
        _draw(font_b, fitted_text, lbl_pos, font_size, AetherListColors.HEADER)

        cursor_y += self.SLOT_HEIGHT + self.GAP

  def _handle_mouse_press(self, mouse_pos: MousePos) -> None:
    self._last_interaction_time = rl.get_time()

    # Right-side Pin / Unpin button press
    if rl.check_collision_point_rec(mouse_pos, self._pin_rect):
      self._pressed_pin = True
      return

    # Main Header Bar Press
    if rl.check_collision_point_rec(mouse_pos, self._handle_rect):
      self._pressed_handle = True
      return

    if not self.is_expanded:
      return

    # Slot Cards Press
    for slot_index, slot_rect in self._slot_rects:
      if rl.check_collision_point_rec(mouse_pos, slot_rect):
        self._pressed_slot = slot_index
        return

  def _handle_mouse_release(self, mouse_pos: MousePos) -> None:
    self._last_interaction_time = rl.get_time()

    # Pin / Unpin Button Release
    if self._pressed_pin and rl.check_collision_point_rec(mouse_pos, self._pin_rect):
      self.pinned = not self.pinned
      if self.pinned:
        self.is_expanded = True
      self._pressed_pin = False
      return
    self._pressed_pin = False

    # Main Header Bar Release
    if self._pressed_handle and rl.check_collision_point_rec(mouse_pos, self._handle_rect):
      if self.pinned:
        self.pinned = False
      else:
        self.is_expanded = not self.is_expanded
      self._pressed_handle = False
      return
    self._pressed_handle = False

    if not self.is_expanded:
      return

    # Slot Cards Release
    if self._pressed_slot is not None:
      for slot_index, slot_rect in self._slot_rects:
        if slot_index == self._pressed_slot and rl.check_collision_point_rec(mouse_pos, slot_rect):
          if toggle_favorite_slot(slot_index, self._params, self._params_memory):
            self._feedback_slot = slot_index
            self._feedback_start_time = rl.get_time()
          break
      self._pressed_slot = None

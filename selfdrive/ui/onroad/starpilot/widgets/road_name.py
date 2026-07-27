import pyray as rl
from openpilot.common.params import Params
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import GridPlacement, GridAnchor
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached


class RoadNameWidget(LayoutWidget):
    def __init__(self, content_rect_getter):
        super().__init__(
            name="road_name",
            priority=10,
            placement=GridPlacement(
                zone="middle",
                anchor=GridAnchor.BOTTOM_CENTER,
                y_cell=50.2,
            ),
            render_layer=2,
        )
        self._params = Params()
        self._font = gui_app.font(FontWeight.BOLD)
        self._content_rect_getter = content_rect_getter

    @property
    def is_visible(self) -> bool:
        toggles = ui_state.starpilot_toggles
        if not bool(toggles.get("road_name_ui",
                                 self._params.get_bool("RoadNameUI"))):
            return False
        mapd = ui_state.sm["mapdOut"] if ui_state.sm.valid.get("mapdOut", False) else None
        if mapd is None:
            return False
        return bool(str(mapd.roadName or ""))

    def get_size(self) -> tuple[float, float]:
        mapd = ui_state.sm["mapdOut"] if ui_state.sm.valid.get("mapdOut", False) else None
        if mapd is None:
            return 100.0, 42.0
        road_name = str(mapd.roadName or "")
        if not road_name:
            return 100.0, 42.0
        sz = measure_text_cached(self._font, road_name, 32)
        return sz.x + 48, sz.y + 10

    def _render(self, rect: rl.Rectangle):
        mapd = ui_state.sm["mapdOut"] if ui_state.sm.valid.get("mapdOut", False) else None
        if mapd is None:
            return
        road_name = str(mapd.roadName or "")
        if not road_name:
            return

        content_rect = self._content_rect_getter()
        font_size = 32
        pad_x = 24
        pad_y = 5
        sz = measure_text_cached(self._font, road_name, font_size)

        pill_w = sz.x + pad_x * 2
        pill_h = font_size + pad_y * 2
        cx = content_rect.x + content_rect.width / 2
        by = content_rect.y + content_rect.height - pill_h - 16

        pill = rl.Rectangle(cx - pill_w / 2, by, pill_w, pill_h)
        rl.draw_rectangle_rounded(pill, 0.4, 8, rl.Color(0, 0, 0, 166))
        rl.draw_rectangle_rounded_lines_ex(pill, 0.4, 8, 1, rl.Color(255, 255, 255, 60))
        rl.draw_text_ex(self._font, road_name,
                        rl.Vector2(cx - sz.x / 2, by + pad_y), font_size, 0, rl.WHITE)

import time
import pyray as rl
from openpilot.common.params import Params
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import GridPlacement, GridAnchor
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.lib.starpilot_status import (
    ENGAGED_COLOR, EXPERIMENTAL_COLOR, TRAFFIC_COLOR,
)
from openpilot.system.ui.lib.application import gui_app, FontWeight


class StandstillTimerWidget(LayoutWidget):
    def __init__(self):
        super().__init__(
            name="standstill_timer",
            priority=5,
            placement=GridPlacement(
                zone="middle",
                anchor=GridAnchor.CENTER,
                y_cell=10.5,
            ),
            render_layer=1,
        )
        self._params = Params()
        self._font_bold = gui_app.font(FontWeight.BOLD)
        self._font_medium = gui_app.font(FontWeight.MEDIUM)
        self._started_at = 0.0

    @property
    def is_visible(self) -> bool:
        if not self._params.get_bool("stopped_timer"):
            self._started_at = 0.0
            return False
        return getattr(ui_state.sm["carState"], "standstill", False) \
            if ui_state.sm.valid.get("carState", False) else False

    def get_size(self) -> tuple[float, float]:
        return 400.0, 200.0

    def _render(self, rect: rl.Rectangle):
        if not ui_state.sm.valid.get("carState", False):
            return
        car_state = ui_state.sm["carState"]

        if getattr(car_state, "standstill", False):
            if self._started_at == 0.0:
                self._started_at = time.monotonic()
        else:
            self._started_at = 0.0
            return

        if self._started_at == 0.0:
            return

        duration = int(time.monotonic() - self._started_at)
        if duration < 60:
            return

        minutes = duration // 60
        seconds = duration % 60
        minute_text = f"{minutes} minute{'s' if minutes != 1 else ''}"
        second_text = f"{seconds} second{'s' if seconds != 1 else ''}"

        if duration < 150:
            t = (duration - 60) / 90.0
            duration_color = _blend(ENGAGED_COLOR, EXPERIMENTAL_COLOR, t)
        elif duration < 300:
            t = (duration - 150) / 150.0
            duration_color = _blend(EXPERIMENTAL_COLOR, TRAFFIC_COLOR, t)
        else:
            duration_color = TRAFFIC_COLOR

        x = gui_app.width / 2

        rl.draw_text_ex(
            self._font_bold, minute_text,
            rl.Vector2(x - 150, 210 - 88), 176, 0, duration_color,
        )
        rl.draw_text_ex(
            self._font_medium, second_text,
            rl.Vector2(x - 100, 290 - 33), 66, 0,
            rl.Color(255, 255, 255, 242),
        )


def _blend(s: rl.Color, e: rl.Color, t: float) -> rl.Color:
    t = max(0.0, min(1.0, t))
    return rl.Color(
        int(s.r + t * (e.r - s.r)),
        int(s.g + t * (e.g - s.g)),
        int(s.b + t * (e.b - s.b)),
        255,
    )

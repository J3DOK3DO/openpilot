import pyray as rl
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.onroad.starpilot.weather_icon import render_weather_icon
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.common.params import Params


class WeatherIconWidget(LayoutWidget):
    def __init__(self):
        super().__init__(
            name="weather_icon",
            priority=10,
            render_layer=2,
        )
        self._params = Params()

    @property
    def is_visible(self) -> bool:
        plan = ui_state.sm["starpilotPlan"] if ui_state.sm.valid.get(
            "starpilotPlan", False
        ) else None
        return plan is not None and plan.weatherId != 0

    def get_size(self) -> tuple[float, float]:
        return 120.0, 120.0

    def _render(self, rect: rl.Rectangle):
        render_weather_icon(rect)

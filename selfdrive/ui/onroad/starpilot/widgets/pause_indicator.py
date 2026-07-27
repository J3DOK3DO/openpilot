import pyray as rl
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.onroad.starpilot.pause_indicators import (
    render_lateral_paused, render_longitudinal_paused,
)
from openpilot.selfdrive.ui.ui_state import ui_state


class PauseIndicatorWidget(LayoutWidget):
    def __init__(self):
        super().__init__(
            name="pause_indicators",
            priority=10,
            render_layer=2,
        )
        self._badge_w = 120.0
        self._badge_h = 72.0
        self._spacing = 20.0

    @property
    def is_visible(self) -> bool:
        return bool(self._active_badges())

    def get_size(self) -> tuple[float, float]:
        count = len(self._active_badges())
        if count == 0:
            return 0.0, 0.0
        total_w = count * self._badge_w + (count - 1) * self._spacing
        return total_w, self._badge_h

    def _render(self, rect: rl.Rectangle):
        badges = self._active_badges()
        for i, badge in enumerate(badges):
            bx = rect.x + i * (self._badge_w + self._spacing)
            by = rect.y
            badge_rect = rl.Rectangle(bx, by, self._badge_w, self._badge_h)
            if badge == "lateral_paused":
                render_lateral_paused(badge_rect)
            elif badge == "longitudinal_paused":
                render_longitudinal_paused(badge_rect)

    def _active_badges(self) -> list[str]:
        scs = (
            ui_state.sm["starpilotCarState"]
            if ui_state.sm.valid.get("starpilotCarState", False) else None
        )
        if scs is None:
            return []
        badges = []
        if scs.pauseLateral:
            badges.append("lateral_paused")
        if scs.pauseLongitudinal or scs.forceCoast:
            badges.append("longitudinal_paused")
        return badges

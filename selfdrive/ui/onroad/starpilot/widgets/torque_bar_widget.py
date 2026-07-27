import pyray as rl
from openpilot.common.params import Params
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.onroad.starpilot.torque_bar import TorqueBar
from openpilot.selfdrive.ui.ui_state import ui_state


class TorqueBarWidget(LayoutWidget):
    def __init__(self):
        super().__init__(
            name="torque_bar",
            priority=20,
            render_layer=2,
        )
        self._params = Params()
        self._bar = TorqueBar()
        self._render_rect = None

    def set_render_rect(self, rect: rl.Rectangle):
        self._render_rect = rect
        self.set_rect(rect)

    @property
    def is_visible(self) -> bool:
        if not self._params.get_bool("EnableTorqueBarWidget", default=True):
            return False
        cs = ui_state.sm["controlsState"] if ui_state.sm.valid.get(
            "controlsState", False
        ) else None
        if cs is None:
            return False
        return cs.lateralControlState.which() != "angleState"

    def get_size(self) -> tuple[float, float]:
        return 0.0, 0.0

    def _render(self, rect: rl.Rectangle):
        render_rect = self._render_rect or rect
        rl.begin_scissor_mode(
            int(render_rect.x), int(render_rect.y),
            int(render_rect.width), int(render_rect.height),
        )
        self._bar.render(render_rect)
        rl.end_scissor_mode()

import pyray as rl
import time
from msgq.visionipc import VisionStreamType
from openpilot.common.params import Params
from openpilot.selfdrive.ui.onroad.augmented_road_view import AugmentedRoadView
from openpilot.selfdrive.ui.onroad.starpilot.starpilot_border import (
    render_behind, render_overlay, render_background_effects,
)
from openpilot.selfdrive.ui.onroad.starpilot.path import (
    render_adjacent_lanes, render_path_edges,
)
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.selfdrive.ui.onroad.starpilot.grid_layout_manager import GridLayoutManager
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import (
    GridAnchor, GridPlacement,
)
from openpilot.selfdrive.ui.onroad.starpilot.render_layer_manager import layer_should_render
from openpilot.selfdrive.ui.onroad.starpilot.widgets import (
    SetSpeedWidget, SpeedLimitWidget, PedalIconsWidget,
    AetherGaugeWidget, PersonalityButtonWidget, DriverMonitorWidget,
    SteeringWheelWidget, FavoritesDockWidget,
    StandstillTimerWidget, DeveloperMetricsWidget, RoadNameWidget,
    PauseIndicatorWidget, WeatherIconWidget, TorqueBarWidget,
)
from openpilot.selfdrive.ui.onroad.starpilot.stopping_point import render_stopping_point
from openpilot.selfdrive.ui.lib.starpilot_status import (
    get_screen_edge_color, ENGAGED_COLOR,
    EXPERIMENTAL_COLOR, TRAFFIC_COLOR,
)
from openpilot.system.ui.lib.application import MousePos, gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached
from cereal import log
AlertSize = log.SelfdriveState.AlertSize


class StarPilotOnroadView(AugmentedRoadView):
    def __init__(self, stream_type: VisionStreamType = VisionStreamType.VISION_STREAM_ROAD):
        super().__init__(stream_type)
        self._params = Params()
        self._font_bold = gui_app.font(FontWeight.BOLD)
        self._font_medium = gui_app.font(FontWeight.MEDIUM)

        self.layout_manager = GridLayoutManager(self._content_rect, parent_widget=self)

        self._draw_driver_state = False
        self._hud_renderer.draw_set_speed = False
        self._hud_renderer.draw_exp_button = False

        # Managed layout widgets — existing 8 (legacy zone API)
        self._set_speed_widget = SetSpeedWidget(self._hud_renderer)
        self._speed_limit_widget = SpeedLimitWidget()
        self._aethergauge_widget = AetherGaugeWidget(self._hud_renderer)
        self._steering_wheel_widget = SteeringWheelWidget(self._hud_renderer._exp_button)
        self._pedals_widget = PedalIconsWidget()
        self._personality_button_widget = PersonalityButtonWidget()
        self._driver_monitor_widget = DriverMonitorWidget(self.driver_state_renderer)
        self._favorites_dock_widget = FavoritesDockWidget()

        # FavoritesDock has special positioning — Y-anchor to speed_limit
        dock_placement = GridPlacement(
            zone="close",
            anchor=GridAnchor.TOP_LEFT,
            relative_to="speed_limit",
            relation="same_row",
            offset=(0.0, 0.0),
        )

        self.layout_manager.register_widget(self._set_speed_widget, zone="left", rendered=False)
        self.layout_manager.register_widget(self._speed_limit_widget, zone="left", rendered=False)
        self.layout_manager.register_widget(self._aethergauge_widget, zone="left")
        self.layout_manager.register_widget(self._steering_wheel_widget, zone="right")
        self.layout_manager.register_widget(self._pedals_widget, zone="right")
        self.layout_manager.register_widget(self._personality_button_widget, zone="bottom")
        self.layout_manager.register_widget(self._driver_monitor_widget, zone="bottom")
        self.layout_manager.register_widget(self._favorites_dock_widget, placement=dock_placement)

        # New grid-managed widgets
        self._standstill_timer_widget = StandstillTimerWidget()
        self._developer_metrics_widget = DeveloperMetricsWidget(self._get_border_width)
        self._road_name_widget = RoadNameWidget(lambda: self._content_rect)
        self._torque_bar_widget = TorqueBarWidget()

        self.layout_manager.register_widget(self._standstill_timer_widget,
                                             zone="middle")
        self.layout_manager.register_widget(self._developer_metrics_widget)
        self.layout_manager.register_widget(self._road_name_widget,
                                             zone="middle")
        self.layout_manager.register_widget(self._torque_bar_widget)

        # Anchored widgets
        self._pause_indicator_widget = PauseIndicatorWidget()
        self._weather_icon_widget = WeatherIconWidget()

        self.layout_manager.register_anchored(
            self._pause_indicator_widget,
            anchor_to="driver_monitor",
            relation="right_of",
            offset=(20.0, 0.0),
            render_layer=2,
        )
        self.layout_manager.register_anchored(
            self._weather_icon_widget,
            anchor_to="driver_monitor",
            relation="same_row",
            offset=(0.0, 0.0),
            render_layer=2,
        )

    def _render(self, rect: rl.Rectangle):
        border_width = self._get_border_width()
        border_color = get_screen_edge_color(ui_state)
        rl.draw_rectangle_rounded(rect, 0.12, 10, border_color)
        render_background_effects(rect, border_width)
        super()._render(rect)

        if not ui_state.started:
            return

        if self._draw_hud_controls:
            dm = self.driver_state_renderer
            is_rhd = dm.is_rhd if dm else False
            self.layout_manager.update_layout(self._content_rect, is_rhd=is_rhd)

            # Update weather icon snapped to far edge + DM row
            dm_rect = self.layout_manager.get_widget_rect("driver_monitor")
            if dm_rect is not None:
                weather_w = 120.0
                weather_h = 120.0
                if not is_rhd:
                    wx = self._content_rect.x + self._content_rect.width - 30 - weather_w
                else:
                    wx = self._content_rect.x + 30
                wy = dm_rect.y + dm_rect.height / 2 - weather_h / 2
                self._weather_icon_widget.set_rect(
                    rl.Rectangle(wx, wy, weather_w, weather_h)
                )

            alert_showing, alert_size = self.alert_renderer.will_render()

            # Layer 0: PRE_FULL_ALERT — SetSpeed and SpeedLimit
            if layer_should_render(0, alert_showing, alert_size):
                self._render_slc()

            # Inject full content rect into TorqueBar (self-positioning arc)
            self._torque_bar_widget.set_render_rect(self._content_rect)

            # Layer 1: OVERLAY
            self.layout_manager.render_layer(1, alert_showing, alert_size)

            # Layer 2: POST_LAYER
            self.layout_manager.render_layer(2, alert_showing, alert_size)

            # Layer 4: debug overlay
            if self._params.get_bool("GridDebugOverlay"):
                self.layout_manager.render_debug()

    def _on_after_model_render(self, rect: rl.Rectangle):
        self._render_path_features(rect)

    def _draw_border(self, rect: rl.Rectangle):
        border_width = self._get_border_width()
        rl.draw_rectangle_rounded_lines_ex(rect, 0.12, 10, border_width, rl.BLACK)
        border_rect = rl.Rectangle(
            rect.x + border_width, rect.y + border_width,
            rect.width - 2 * border_width, rect.height - 2 * border_width,
        )
        render_behind(border_rect, border_width)
        render_overlay(border_rect, border_width)

    def _render_slc(self):
        alert_showing, alert_size = self.alert_renderer.will_render()
        if alert_showing is not None and alert_size == AlertSize.full:
            return
        if self._speed_limit_widget.is_visible:
            self._speed_limit_widget.render(self._speed_limit_widget.rect)
        if self._set_speed_widget.is_visible:
            self._set_speed_widget.render(self._set_speed_widget.rect)

    def _render_path_features(self, rect: rl.Rectangle):
        mr = self.model_renderer
        if not mr._path.projected_points.size:
            return

        rl.begin_scissor_mode(
            int(rect.x), int(rect.y),
            int(rect.width), int(rect.height),
        )

        if mr._track_edge_vertices.size >= 4:
            render_path_edges(mr)

        render_adjacent_lanes(mr)
        render_stopping_point(mr, self._font_bold)

        rl.end_scissor_mode()

    def _handle_mouse_press(self, mouse_pos: MousePos):
        for name, rect in self.layout_manager.widget_rects.items():
            widget = self.layout_manager.get_widget(name)
            if widget and widget.is_visible and rl.check_collision_point_rec(mouse_pos, rect):
                return
        super()._handle_mouse_press(mouse_pos)

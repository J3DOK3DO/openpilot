import pyray as rl
from openpilot.common.params import Params
from openpilot.selfdrive.ui.onroad.starpilot.widgets.base import LayoutWidget
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app, FontWeight
from openpilot.system.ui.lib.text_measure import measure_text_cached


class DeveloperMetricsWidget(LayoutWidget):
    def __init__(self, border_width_fn):
        super().__init__(
            name="developer_metrics",
            priority=99,
            render_layer=1,
        )
        self._params = Params()
        self._font = gui_app.font(FontWeight.MEDIUM)
        self._border_width_fn = border_width_fn
        self._min_fps = 99.9
        self._max_fps = 0.0
        self._avg_fps = 0.0

    @property
    def is_visible(self) -> bool:
        toggles = ui_state.starpilot_toggles
        debug_mode = bool(toggles.get("debug_mode",
                                       self._params.get_bool("DebugMode")))
        developer_metrics = (
            bool(toggles.get("developer_ui",
                             self._params.get_bool("DeveloperUI")))
            and self._params.get_bool("DeveloperMetrics")
        ) or debug_mode or self._params.get_bool("DeveloperMetrics")

        if not developer_metrics:
            return False

        show_fps = _enabled(toggles, self._params, debug_mode,
                            "show_fps", "FPSCounter", True)
        show_cpu = _enabled(toggles, self._params, debug_mode,
                            "cpu_metrics", "ShowCPU", True)
        show_gpu = _enabled(toggles, self._params, debug_mode,
                            "gpu_metrics", "ShowGPU")
        show_temp = _enabled(toggles, self._params, debug_mode,
                             "numerical_temp", "NumericalTemp", True)
        show_memory = _enabled(toggles, self._params, debug_mode,
                               "memory_metrics", "ShowMemoryUsage", True)
        return any((show_fps, show_cpu, show_gpu, show_temp, show_memory))

    def get_size(self) -> tuple[float, float]:
        line = self._build_line()
        if not line:
            return 100.0, 24.0
        sz = measure_text_cached(self._font, line, 24)
        return sz.x, sz.y

    def _render(self, rect: rl.Rectangle):
        line = self._build_line()
        if not line:
            return

        font_size = 24
        sz = measure_text_cached(self._font, line, font_size)
        border_width = self._border_width_fn()

        target_rect = rect if rect and rect.width > 0 and rect.height > 0 else rl.Rectangle(0, 0, gui_app.width, gui_app.height)

        bx = target_rect.x + (target_rect.width - sz.x) / 2
        by = target_rect.y + target_rect.height - border_width + (border_width - sz.y) // 2

        for dx in (-1, 1):
            for dy in (-1, 1):
                rl.draw_text_ex(
                    self._font, line,
                    rl.Vector2(bx + dx, by + dy), font_size, 0, rl.BLACK,
                )
        rl.draw_text_ex(self._font, line, rl.Vector2(bx, by), font_size, 0, rl.WHITE)

    def _build_line(self) -> str:
        toggles = ui_state.starpilot_toggles
        debug_mode = bool(toggles.get("debug_mode",
                                       self._params.get_bool("DebugMode")))

        show_fps = _enabled(toggles, self._params, debug_mode,
                            "show_fps", "FPSCounter", True)
        show_cpu = _enabled(toggles, self._params, debug_mode,
                            "cpu_metrics", "ShowCPU", True)
        show_gpu = _enabled(toggles, self._params, debug_mode,
                            "gpu_metrics", "ShowGPU")
        show_temp = _enabled(toggles, self._params, debug_mode,
                             "numerical_temp", "NumericalTemp", True)
        show_memory = _enabled(toggles, self._params, debug_mode,
                               "memory_metrics", "ShowMemoryUsage", True)

        fps = rl.get_fps()
        if fps > 0:
            self._min_fps = min(self._min_fps, fps)
            self._max_fps = max(self._max_fps, fps)
            alpha = 1.0 / (60.0 * 5.0)
            if self._avg_fps == 0.0:
                self._avg_fps = fps
            else:
                self._avg_fps = alpha * fps + (1.0 - alpha) * self._avg_fps

        device_state = (
            ui_state.sm["deviceState"]
            if ui_state.sm.valid.get("deviceState", False) else None
        )
        cpu_val = 0
        gpu_val = 0
        temp_val = 0
        mem_val = 0
        mem_gb = 0.0
        if device_state:
            cpu_list = list(device_state.cpuUsagePercent)
            cpu_val = int(sum(cpu_list) / len(cpu_list)) if cpu_list else 0
            gpu_val = int(device_state.gpuUsagePercent)
            temp_val = int(device_state.maxTempC)
            mem_val = int(device_state.memoryUsagePercent)
            mem_gb = 8.0 * mem_val / 100.0

        parts = []
        if show_cpu:
            parts.append(f"CPU: {cpu_val}%")
        if show_gpu:
            parts.append(f"GPU: {gpu_val}%")
        if show_temp:
            parts.append(f"TEMP: {temp_val}\u00b0C")
        if show_memory:
            parts.append(f"RAM: {mem_gb:.1f} GB ({mem_val}%)")
        if show_fps:
            parts += [
                f"FPS: {round(fps)}",
                f"Min: {round(self._min_fps)}",
                f"Max: {round(self._max_fps)}",
                f"Avg: {round(self._avg_fps)}",
            ]
        return " | ".join(parts)


def _enabled(toggles, params, debug_mode, toggle_key, param_key,
             debug_override=False):
    if debug_mode and debug_override:
        return True
    return bool(toggles.get(toggle_key)) or params.get_bool(param_key)




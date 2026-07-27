from __future__ import annotations
import pyray as rl
from openpilot.selfdrive.ui.onroad.starpilot.grid import GridOccupancyMap
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import GridAnchor, GridPlacement
from openpilot.selfdrive.ui.onroad.starpilot.zones import get_zone, translate_legacy_zone
from openpilot.selfdrive.ui.onroad.starpilot.anchor_graph import AnchorGraph, AnchorCycleError
from openpilot.selfdrive.ui.onroad.starpilot.render_layer_manager import LAYERS, layer_should_render


_SPACING_PX = 15


class GridLayoutManager:
    def __init__(self, content_rect: rl.Rectangle, parent_widget=None):
        self._content_rect = content_rect
        self._parent_widget = parent_widget
        self._grid = GridOccupancyMap(content_rect)
        self._names: dict[str, object] = {}
        self._anchor_graph = AnchorGraph()

        self._zone_registry: dict[str, list[tuple]] = {}
        self._obstacles: dict[str, callable] = {}
        self._anchored_widgets: dict[str, tuple] = {}

        self._all_widgets: list = []
        self._managed_not_rendered: set[str] = set()
        self._widget_rects: dict[str, rl.Rectangle] = {}

    @property
    def content_rect(self) -> rl.Rectangle:
        return self._content_rect

    @property
    def all_widgets(self):
        return self._all_widgets

    @property
    def widget_rects(self) -> dict[str, rl.Rectangle]:
        return self._widget_rects

    def _register_name(self, name: str, owner: object) -> None:
        if name in self._names:
            old = type(self._names[name]).__name__
            raise ValueError(f"Name '{name}' already registered by {old}")
        self._names[name] = owner

    def register_widget(
        self,
        widget,
        zone: str | None = None,
        placement: GridPlacement | None = None,
        render_layer: int | None = None,
        managed: bool = True,
        rendered: bool = True,
    ) -> None:
        self._register_name(widget.name, widget)

        if self._parent_widget is not None:
            self._parent_widget._child(widget)

        if placement is None and zone is not None:
            placement = translate_legacy_zone(zone, widget.priority)

        if placement is not None:
            widget.placement = placement

        if render_layer is not None:
            widget.render_layer = render_layer

        if not rendered:
            self._managed_not_rendered.add(widget.name)

        self._all_widgets.append(widget)

        if placement is not None and placement.zone is not None:
            zone_name = placement.zone
            if zone_name not in self._zone_registry:
                self._zone_registry[zone_name] = []
            self._zone_registry[zone_name].append((widget, placement))
            self._zone_registry[zone_name].sort(key=lambda item: item[0].priority)

    def register_anchored(
        self,
        widget,
        anchor_to: str,
        relation: str,
        offset: tuple[float, float] = (0.0, 0.0),
        fallback: tuple[float, float] | None = None,
        render_layer: int | None = None,
    ) -> None:
        self._register_name(widget.name, widget)

        if self._parent_widget is not None:
            self._parent_widget._child(widget)

        if render_layer is not None:
            widget.render_layer = render_layer

        self._all_widgets.append(widget)

        self._anchor_graph.add(
            child_name=widget.name,
            parent_name=anchor_to,
            relation=relation,
            offset=offset,
            fallback=fallback,
            child_widget=widget,
        )
        self._anchored_widgets[widget.name] = (widget, anchor_to, relation, offset, fallback)

    def register_obstacle(self, name: str, bbox_fn: callable) -> None:
        self._register_name(name, bbox_fn)
        self._obstacles[name] = bbox_fn

    def update_layout(self, content_rect: rl.Rectangle,
                      is_rhd: bool = False) -> None:
        self._content_rect = content_rect
        self._grid.set_bounds(content_rect)
        self._widget_rects.clear()

        zone_groups: dict[str, dict[str, list[tuple]]] = {}

        for zone_name, items in self._zone_registry.items():
            template = get_zone(zone_name)
            for widget, placement in items:
                if not widget.is_visible:
                    continue
                if widget.name in self._anchored_widgets:
                    continue
                category = _vertical_category(placement.anchor)
                zone_groups.setdefault(zone_name, {})
                zone_groups[zone_name].setdefault(category, [])
                zone_groups[zone_name][category].append((widget, placement, template))

        for zone_name, categories in zone_groups.items():
            for category, items in categories.items():
                self._layout_zone_category(zone_name, category, items, is_rhd)

        try:
            anchored_rects = self._anchor_graph.resolve(self._widget_rects, is_rhd)
        except AnchorCycleError:
            anchored_rects = {}

        for name, rect in anchored_rects.items():
            if name in self._anchored_widgets:
                widget = self._anchored_widgets[name][0]
                widget.set_rect(rect)
                self._widget_rects[name] = rect
                self._grid.reserve(rect, name)

        for obs_name, bbox_fn in self._obstacles.items():
            try:
                self._grid.reserve(bbox_fn(), obs_name)
            except Exception:
                pass

    def _layout_zone_category(self, zone_name: str, category: str,
                               items: list[tuple], is_rhd: bool) -> None:
        template = get_zone(zone_name)
        col_start = template.col_start(is_rhd)
        col_end = template.col_end(is_rhd)

        if category == "top":
            self._layout_vertical_stack(items, col_start, col_end, is_rhd, zone_name)
        elif category == "bottom":
            self._layout_horizontal_strip(items, col_start, col_end, is_rhd, zone_name)
        elif category == "center":
            self._layout_center(items, col_start, col_end, is_rhd)

    def _layout_vertical_stack(self, items: list[tuple],
                                col_start: int, col_end: int,
                                is_rhd: bool, zone_name: str) -> None:
        if zone_name == "far":
            center_x = self._content_rect.x + self._content_rect.width - 146.0
        else:
            center_x = self._content_rect.x + 60.0 + 86.0

        current_y = self._content_rect.y + 45.0
        left_column_right_x = center_x + 86.0

        for widget, placement, _ in items:
            w, h = widget.get_size()

            if placement.relative_to is not None and placement.relation == "same_row":
                anchor_rect = self._widget_rects.get(placement.relative_to)
                dock_y = anchor_rect.y if anchor_rect is not None else self._content_rect.y + 264.0
                rect = rl.Rectangle(left_column_right_x + 15.0, dock_y, w, h)
            else:
                x = center_x - w / 2
                y = current_y
                rect = rl.Rectangle(x, y, w, h)
                current_y += h + _SPACING_PX

            widget.set_rect(rect)
            self._widget_rects[widget.name] = rect
            self._grid.reserve(rect, widget.name)

    def _layout_horizontal_strip(self, items: list[tuple],
                                  col_start: int, col_end: int,
                                  is_rhd: bool, zone_name: str) -> None:
        active = [(w, p) for w, p, _ in items if w.is_visible]
        if not active:
            return

        bottom_y = self._content_rect.y + self._content_rect.height - 146.0

        if not is_rhd:
            current_x = self._content_rect.x + 146.0
            for widget, _ in active:
                w, h = widget.get_size()
                rect = rl.Rectangle(current_x - w / 2, bottom_y - h / 2, w, h)
                widget.set_rect(rect)
                self._widget_rects[widget.name] = rect
                self._grid.reserve(rect, widget.name)
                current_x += w + _SPACING_PX
        else:
            total_w = sum(w.get_size()[0] for w, _ in active) + _SPACING_PX * (len(active) - 1)
            last_w = active[-1][0].get_size()[0]
            current_x = self._content_rect.x + self._content_rect.width - 146.0 - (total_w - last_w)
            for widget, _ in active:
                w, h = widget.get_size()
                rect = rl.Rectangle(current_x - w / 2, bottom_y - h / 2, w, h)
                widget.set_rect(rect)
                self._widget_rects[widget.name] = rect
                self._grid.reserve(rect, widget.name)
                current_x += w + _SPACING_PX

    def _layout_center(self, items: list[tuple],
                        col_start: int, col_end: int, is_rhd: bool) -> None:
        for widget, placement, _ in items:
            w, h = widget.get_size()
            cx = self._content_rect.x + self._content_rect.width / 2
            x = cx - w / 2
            y = self._grid.cell_to_pixel_float(0, placement.y_cell)[1]
            rect = rl.Rectangle(x, y, w, h)
            widget.set_rect(rect)
            self._widget_rects[widget.name] = rect
            self._grid.reserve(rect, widget.name)

    def render_layer(self, layer_index: int,
                     alert_showing=None, alert_size=None) -> None:
        if LAYERS.get(layer_index) is None:
            return
        if not layer_should_render(layer_index, alert_showing, alert_size):
            return
        for widget in self._all_widgets:
            if (widget.is_visible and widget.render_layer == layer_index
                    and widget.name not in self._managed_not_rendered):
                widget.render(widget.rect)

    def render_widgets(self, exclude: set[str] | None = None) -> None:
        skip = exclude or set()
        for widget in self._all_widgets:
            if (widget.is_visible and widget.name not in skip
                    and widget.name not in self._managed_not_rendered):
                widget.render(widget.rect)

    def render_debug(self) -> None:
        self._grid.render_debug(alpha=60)

    def get_widget(self, name: str):
        return self._names.get(name)

    def get_widget_rect(self, name: str) -> rl.Rectangle | None:
        return self._widget_rects.get(name)


def _vertical_category(anchor: GridAnchor) -> str:
    if anchor in (GridAnchor.TOP_LEFT, GridAnchor.TOP_CENTER, GridAnchor.TOP_RIGHT):
        return "top"
    if anchor in (GridAnchor.BOTTOM_LEFT, GridAnchor.BOTTOM_CENTER, GridAnchor.BOTTOM_RIGHT):
        return "bottom"
    if anchor in (GridAnchor.CENTER_LEFT, GridAnchor.CENTER, GridAnchor.CENTER_RIGHT):
        return "center"
    return "top"

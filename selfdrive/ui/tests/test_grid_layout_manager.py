import sys
import types
import unittest
from unittest.mock import MagicMock

rl = types.SimpleNamespace(
    Rectangle=lambda x=0, y=0, width=0, height=0: types.SimpleNamespace(
        x=x, y=y, width=width, height=height,
    ),
    check_collision_point_rec=lambda p, r: (
        r.x <= p.x <= r.x + r.width and r.y <= p.y <= r.y + r.height
    ),
    Color=lambda r, g, b, a: types.SimpleNamespace(r=r, g=g, b=b, a=a),
    ColorFromHSV=lambda h, s, v: types.SimpleNamespace(r=0, g=0, b=0, a=255),
    draw_rectangle_rounded=lambda *a, **k: None,
)
sys.modules["pyray"] = rl

ui_state = types.SimpleNamespace(
    is_metric=True,
    params=MagicMock(),
)
sys.modules["openpilot.selfdrive.ui.ui_state"] = types.SimpleNamespace(
    ui_state=ui_state,
)

widgets_mod = types.ModuleType("openpilot.system.ui.widgets")


class MockWidget:
    def __init__(self):
        self.rect = rl.Rectangle()
        self._children = []

    def _child(self, w):
        self._children.append(w)
        return w

    def set_rect(self, rect):
        self.rect = rect

    def render(self, rect):
        self.rect = rect


widgets_mod.Widget = MockWidget
sys.modules["openpilot.system.ui.widgets"] = widgets_mod

widgets_base = types.ModuleType(
    "openpilot.selfdrive.ui.onroad.starpilot.widgets.base",
)


class LayoutWidget(MockWidget):
    def __init__(self, name="", priority=0, placement=None, render_layer=1):
        super().__init__()
        self.name = name
        self.priority = priority
        self.placement = placement
        self.render_layer = render_layer
        self._visible = True

    @property
    def is_visible(self) -> bool:
        return getattr(self, "_visible", True)

    @is_visible.setter
    def is_visible(self, value):
        self._visible = value

    def get_size(self) -> tuple[float, float]:
        return getattr(self, "_size", (100.0, 100.0))


widgets_base.LayoutWidget = LayoutWidget
sys.modules["openpilot.selfdrive.ui.onroad.starpilot.widgets.base"] = (
    widgets_base
)

# Import our new modules
from openpilot.selfdrive.ui.onroad.starpilot.grid import GridOccupancyMap
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import (
    GRID_CELL_SIZE, GRID_COLS, GRID_ROWS, GridAnchor, GridPlacement,
)
from openpilot.selfdrive.ui.onroad.starpilot.zones import (
    ZONES, ZoneTemplate, get_zone, translate_legacy_zone,
)
from openpilot.selfdrive.ui.onroad.starpilot.anchor_graph import (
    AnchorGraph, AnchorCycleError,
)
from openpilot.selfdrive.ui.onroad.starpilot.render_layer_manager import (
    LAYERS, layer_should_render,
)
from openpilot.selfdrive.ui.onroad.starpilot.grid_layout_manager import (
    GridLayoutManager,
)


class DummyWidget(LayoutWidget):
    def __init__(self, name="", priority=0, width=100.0, height=100.0,
                 visible=True, placement=None, render_layer=1):
        super().__init__(name=name, priority=priority, placement=placement,
                         render_layer=render_layer)
        self._size = (width, height)
        self._visible = visible

    def get_size(self) -> tuple[float, float]:
        return self._size


class TestGridOccupancyMap(unittest.TestCase):
    def setUp(self):
        bounds = rl.Rectangle(30, 30, 2100, 1020)
        self.grid = GridOccupancyMap(bounds)

    def test_bounds_set_correctly(self):
        self.assertEqual(self.grid.cols, 105)
        self.assertEqual(self.grid.rows, 51)

    def test_pixel_to_cell_origin(self):
        c, r = self.grid.pixel_to_cell(30, 30)
        self.assertEqual(c, 0)
        self.assertEqual(r, 0)

    def test_pixel_to_cell_mid(self):
        c, r = self.grid.pixel_to_cell(1088, 540)
        self.assertEqual(c, 52)
        self.assertEqual(r, 25)

    def test_cell_to_pixel(self):
        x, y = self.grid.cell_to_pixel(5, 10)
        self.assertEqual(x, 130)
        self.assertEqual(y, 230)

    def test_reserve_single_cell(self):
        rect = rl.Rectangle(30, 30, 18, 18)
        result = self.grid.reserve(rect, "w1")
        self.assertTrue(result)
        self.assertTrue(self.grid.is_occupied(0, 0))

    def test_reserve_rejects_overlap(self):
        rect1 = rl.Rectangle(30, 30, 100, 100)
        self.assertTrue(self.grid.reserve(rect1, "w1"))
        rect2 = rl.Rectangle(40, 40, 100, 100)
        self.assertFalse(self.grid.reserve(rect2, "w2"))

    def test_reserve_adjacent_no_overlap(self):
        rect1 = rl.Rectangle(30, 30, 100, 100)
        self.assertTrue(self.grid.reserve(rect1, "w1"))
        rect2 = rl.Rectangle(130, 30, 100, 100)
        self.assertTrue(self.grid.reserve(rect2, "w2"))

    def test_release_frees_cells(self):
        rect = rl.Rectangle(30, 30, 100, 100)
        self.grid.reserve(rect, "w1")
        self.assertTrue(self.grid.is_occupied(1, 1))
        self.grid.release("w1")
        self.assertFalse(self.grid.is_occupied(1, 1))

    def test_clear(self):
        rect = rl.Rectangle(30, 30, 100, 100)
        self.grid.reserve(rect, "w1")
        self.grid.clear()
        self.assertFalse(self.grid.is_occupied(1, 1))

    def test_has_overlap(self):
        rect1 = rl.Rectangle(30, 30, 100, 100)
        self.grid.reserve(rect1, "w1")
        self.assertTrue(self.grid.has_overlap(rl.Rectangle(80, 80, 50, 50)))
        self.assertFalse(self.grid.has_overlap(rl.Rectangle(200, 200, 50, 50)))

    def test_has_overlap_with_exclude(self):
        rect1 = rl.Rectangle(30, 30, 100, 100)
        self.grid.reserve(rect1, "w1")
        self.assertTrue(self.grid.has_overlap(rl.Rectangle(80, 80, 50, 50)))
        self.assertFalse(
            self.grid.has_overlap(rl.Rectangle(80, 80, 50, 50), exclude={"w1"})
        )

    def test_set_bounds_resizes_grid(self):
        self.grid.set_bounds(rl.Rectangle(0, 0, 1920, 1080))
        self.assertEqual(self.grid.cols, 96)
        self.assertEqual(self.grid.rows, 54)

    def test_set_bounds_clears(self):
        rect = rl.Rectangle(30, 30, 100, 100)
        self.grid.reserve(rect, "w1")
        self.grid.set_bounds(rl.Rectangle(0, 0, 1920, 1080))
        self.assertFalse(self.grid.is_occupied(1, 1))


class TestZoneTemplate(unittest.TestCase):
    def test_zones_registered(self):
        self.assertIn("close", ZONES)
        self.assertIn("middle", ZONES)
        self.assertIn("far", ZONES)

    def test_get_zone_valid(self):
        z = get_zone("close")
        self.assertEqual(z.name, "close")

    def test_get_zone_invalid(self):
        with self.assertRaises(ValueError):
            get_zone("nonexistent")

    def test_close_zone_lhd(self):
        z = get_zone("close")
        self.assertEqual(z.col_start(False), 0)
        self.assertEqual(z.col_end(False), 34)

    def test_close_zone_rhd(self):
        z = get_zone("close")
        self.assertEqual(z.col_start(True), 70)
        self.assertEqual(z.col_end(True), 104)

    def test_middle_zone_unchanged(self):
        z = get_zone("middle")
        self.assertEqual(z.col_start(False), 35)
        self.assertEqual(z.col_start(True), 35)

    def test_far_zone_rhd_swaps(self):
        z = get_zone("far")
        self.assertEqual(z.col_start(False), 70)
        self.assertEqual(z.col_start(True), 0)


class TestLegacyZone(unittest.TestCase):
    def test_legacy_left_maps_to_close(self):
        p = translate_legacy_zone("left", 1)
        self.assertEqual(p.zone, "close")
        self.assertEqual(p.anchor, GridAnchor.TOP_LEFT)

    def test_legacy_right_maps_to_far(self):
        p = translate_legacy_zone("right", 1)
        self.assertEqual(p.zone, "far")
        self.assertEqual(p.anchor, GridAnchor.TOP_RIGHT)

    def test_legacy_bottom_maps_to_close_bottom(self):
        p = translate_legacy_zone("bottom", 1)
        self.assertEqual(p.zone, "close")
        self.assertEqual(p.anchor, GridAnchor.BOTTOM_LEFT)

    def test_modern_zone_passthrough(self):
        p = translate_legacy_zone("middle", 1)
        self.assertEqual(p.zone, "middle")

    def test_invalid_zone_raises(self):
        with self.assertRaises(ValueError):
            translate_legacy_zone("invalid", 1)


class TestAnchorGraph(unittest.TestCase):
    def setUp(self):
        self.graph = AnchorGraph()

    def test_single_anchor_right_of(self):
        w = DummyWidget("child", width=100, height=100)
        self.graph.add("child", "parent", "right_of", (20.0, 0.0), None, w)
        parent_rect = rl.Rectangle(100, 100, 200, 200)
        result = self.graph.resolve({"parent": parent_rect}, False)
        self.assertIn("child", result)
        self.assertEqual(result["child"].x, 320)
        self.assertEqual(result["child"].y, 150)

    def test_chain_two_levels(self):
        w1 = DummyWidget("child1", width=100, height=100)
        w2 = DummyWidget("child2", width=100, height=100)
        self.graph.add("child1", "parent", "right_of", (20.0, 0.0), None, w1)
        self.graph.add("child2", "child1", "right_of", (20.0, 0.0), None, w2)
        parent_rect = rl.Rectangle(100, 100, 100, 100)

        known = {"parent": parent_rect}
        result = self.graph.resolve(known, False)

        self.assertIn("child1", result)
        self.assertIn("child2", result)
        self.assertEqual(result["child1"].x, 220)
        self.assertEqual(result["child2"].x, 340)

    def test_rhd_flips_right_of_to_left_of(self):
        w = DummyWidget("child", width=100, height=100)
        self.graph.add("child", "parent", "right_of", (20.0, 0.0), None, w)
        parent_rect = rl.Rectangle(500, 100, 200, 200)
        result = self.graph.resolve({"parent": parent_rect}, True)
        self.assertEqual(result["child"].x, 380)

    def test_cycle_detection(self):
        w1 = DummyWidget("a", width=100, height=100)
        w2 = DummyWidget("b", width=100, height=100)
        self.graph.add("a", "b", "right_of", (0, 0), None, w1)
        self.graph.add("b", "a", "right_of", (0, 0), None, w2)
        with self.assertRaises(AnchorCycleError):
            self.graph.resolve({}, False)

    def test_fallback_when_parent_missing(self):
        w = DummyWidget("child", width=100, height=100)
        self.graph.add("child", "missing", "right_of", (0, 0), (500.0, 300.0), w)
        result = self.graph.resolve({}, False)
        self.assertIn("child", result)
        self.assertEqual(result["child"].x, 500)
        self.assertEqual(result["child"].y, 300)


class TestRenderLayerManager(unittest.TestCase):
    def test_layer_0_full_only_hidden_by_full(self):
        self.assertTrue(layer_should_render(0, None, None))
        self.assertTrue(layer_should_render(0, "alert", 0))
        self.assertFalse(layer_should_render(0, "alert", 2))

    def test_layer_1_any_alert(self):
        self.assertTrue(layer_should_render(1, None, None))
        self.assertFalse(layer_should_render(1, "alert", None))

    def test_layer_3_never_hidden(self):
        self.assertTrue(layer_should_render(3, "alert", None))
        self.assertTrue(layer_should_render(3, None, None))

    def test_invalid_layer(self):
        self.assertTrue(layer_should_render(99, None, None))


class TestGridLayoutManager(unittest.TestCase):
    def setUp(self):
        self.content_rect = rl.Rectangle(30, 30, 2100, 1020)
        self.mgr = GridLayoutManager(self.content_rect)

    def test_register_widget_zone_left(self):
        w = DummyWidget("set_speed", priority=1, width=172, height=204)
        self.mgr.register_widget(w, zone="left")
        self.assertIn(w, self.mgr.all_widgets)

    def test_register_widget_duplicate_name_raises(self):
        w1 = DummyWidget("dup", priority=1)
        self.mgr.register_widget(w1, zone="left")
        w2 = DummyWidget("dup", priority=2)
        with self.assertRaises(ValueError):
            self.mgr.register_widget(w2, zone="left")

    def test_left_zone_vertical_stacking_positions(self):
        w1 = DummyWidget("set_speed", priority=1, width=172, height=204)
        w2 = DummyWidget("speed_limit", priority=2, width=176, height=176)

        self.mgr.register_widget(w1, zone="left")
        self.mgr.register_widget(w2, zone="left")
        self.mgr.update_layout(self.content_rect)

        self.assertEqual(w1.rect.x, 90)
        self.assertEqual(w1.rect.y, 75)
        self.assertEqual(w1.rect.width, 172)
        self.assertEqual(w1.rect.height, 204)

        self.assertEqual(w2.rect.x, 88)
        self.assertEqual(w2.rect.y, 294)

    def test_right_zone_vertical_stacking(self):
        w1 = DummyWidget("steering", priority=1, width=192, height=192)
        w2 = DummyWidget("pedals", priority=2, width=180, height=96)

        self.mgr.register_widget(w1, zone="right")
        self.mgr.register_widget(w2, zone="right")
        self.mgr.update_layout(self.content_rect)

        self.assertEqual(w1.rect.x, 1888)
        self.assertEqual(w1.rect.y, 75)
        self.assertEqual(w2.rect.x, 1894)
        self.assertEqual(w2.rect.y, 282)

    def test_bottom_zone_lhd_stacking(self):
        w1 = DummyWidget("personality", priority=1, width=192, height=192)
        w2 = DummyWidget("dm", priority=2, width=192, height=192)

        self.mgr.register_widget(w1, zone="bottom")
        self.mgr.register_widget(w2, zone="bottom")
        self.mgr.update_layout(self.content_rect, is_rhd=False)

        self.assertEqual(w1.rect.x, 80)
        self.assertEqual(w1.rect.y, 808)
        self.assertEqual(w2.rect.x, 287)
        self.assertEqual(w2.rect.y, 808)

    def test_bottom_zone_rhd_stacking(self):
        w1 = DummyWidget("personality", priority=1, width=192, height=192)
        w2 = DummyWidget("dm", priority=2, width=192, height=192)

        self.mgr.register_widget(w1, zone="bottom")
        self.mgr.register_widget(w2, zone="bottom")
        self.mgr.update_layout(self.content_rect, is_rhd=True)

        self.assertEqual(w1.rect.x, 1681)
        self.assertEqual(w2.rect.x, 1888)

    def test_visibility_shifting_skips_hidden(self):
        w1 = DummyWidget("w1", priority=1, width=100, height=100, visible=True)
        w2 = DummyWidget("w2", priority=2, width=100, height=100, visible=False)
        w3 = DummyWidget("w3", priority=3, width=100, height=100, visible=True)

        self.mgr.register_widget(w1, zone="left")
        self.mgr.register_widget(w2, zone="left")
        self.mgr.register_widget(w3, zone="left")
        self.mgr.update_layout(self.content_rect)

        self.assertEqual(w1.rect.y, 75)
        self.assertEqual(w3.rect.y, 190)

    def test_content_rect_change_repositions(self):
        w1 = DummyWidget("w1", priority=1, width=100, height=100)

        self.mgr.register_widget(w1, zone="right")
        self.mgr.update_layout(self.content_rect, is_rhd=False)
        initial_x = w1.rect.x

        new_rect = rl.Rectangle(0, 0, 1920, 1080)
        self.mgr.update_layout(new_rect, is_rhd=False)

        self.assertNotEqual(initial_x, w1.rect.x)

    def test_middle_zone_widget_centered(self):
        w = DummyWidget("standstill", priority=5, width=200, height=180,
                        placement=GridPlacement(
                            zone="middle", anchor=GridAnchor.CENTER,
                            y_cell=10.5,
                        ))

        self.mgr.register_widget(w, zone="middle")
        self.mgr.update_layout(self.content_rect)

        cx = w.rect.x + w.rect.width / 2
        self.assertAlmostEqual(cx, 1080, delta=5)

    def test_anchored_registration(self):
        w = DummyWidget("pause", priority=10, width=120, height=72)
        self.mgr.register_anchored(w, anchor_to="dm", relation="right_of",
                                    offset=(20.0, 0.0))

        dm = DummyWidget("dm", priority=1, width=192, height=192)
        self.mgr.register_widget(dm, zone="bottom")
        self.mgr.update_layout(self.content_rect)

        rect = self.mgr.get_widget_rect("pause")
        self.assertIsNotNone(rect)
        self.assertAlmostEqual(rect.x, 292, delta=5)

    def test_obstacle_registration(self):
        called = [False]

        def bbox():
            called[0] = True
            return rl.Rectangle(100, 100, 50, 50)

        self.mgr.register_obstacle("test_obs", bbox)
        self.mgr.update_layout(self.content_rect)
        self.assertTrue(called[0])

    def test_favorites_dock_special_positioning(self):
        slc = DummyWidget("speed_limit", priority=2, width=176, height=176)
        dock = DummyWidget("favorites_dock", priority=3, width=176, height=38,
                           placement=GridPlacement(
                               zone="close",
                               anchor=GridAnchor.TOP_LEFT,
                               relative_to="speed_limit",
                               relation="same_row",
                               offset=(0.0, 0.0),
                           ))
        ss = DummyWidget("set_speed", priority=1, width=172, height=204)

        self.mgr.register_widget(ss, zone="left")
        self.mgr.register_widget(slc, zone="left")
        self.mgr.register_widget(dock, placement=dock.placement)
        self.mgr.update_layout(self.content_rect)

        self.assertEqual(dock.rect.x, 277)
        self.assertEqual(dock.rect.y, slc.rect.y)

    def test_render_layer_respects_alert(self):
        w = DummyWidget("test", priority=1, width=100, height=100,
                        render_layer=1)
        self.mgr.register_widget(w, zone="left")
        self.mgr.update_layout(self.content_rect)

        rendered = []

        def track_render(rect):
            rendered.append(True)

        w.render = track_render
        self.mgr.render_layer(1, alert_showing="alert", alert_size=0)
        self.assertEqual(len(rendered), 0)

    def test_get_widget_rect(self):
        w = DummyWidget("test", priority=1, width=100, height=100)
        self.mgr.register_widget(w, zone="left")
        self.mgr.update_layout(self.content_rect)

        rect = self.mgr.get_widget_rect("test")
        self.assertIsNotNone(rect)
        self.assertEqual(rect.x, 126)
        self.assertEqual(rect.y, 75)

    def test_no_overlap_between_all_zones(self):
        widgets = []
        for i in range(3):
            w = DummyWidget(f"left_{i}", priority=i, width=172, height=204,
                            visible=True)
            self.mgr.register_widget(w, zone="left")
            widgets.append(w)
        for i in range(2):
            w = DummyWidget(f"right_{i}", priority=i, width=192, height=192,
                            visible=True)
            self.mgr.register_widget(w, zone="right")
            widgets.append(w)
        for i in range(2):
            w = DummyWidget(f"bottom_{i}", priority=i, width=192, height=192,
                            visible=True)
            self.mgr.register_widget(w, zone="bottom")
            widgets.append(w)

        self.mgr.update_layout(self.content_rect)

        for i, a in enumerate(widgets):
            for j, b in enumerate(widgets):
                if i >= j:
                    continue
                ax1, ay1 = a.rect.x, a.rect.y
                ax2, ay2 = a.rect.x + a.rect.width, a.rect.y + a.rect.height
                bx1, by1 = b.rect.x, b.rect.y
                bx2, by2 = b.rect.x + b.rect.width, b.rect.y + b.rect.height
                overlap = not (
                    ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1
                )
                self.assertFalse(
                    overlap,
                    f"{a.name} ({ax1},{ay1})-({ax2},{ay2}) overlaps "
                    f"{b.name} ({bx1},{by1})-({bx2},{by2})",
                )

    def test_empty_zones_no_crash(self):
        self.mgr.update_layout(self.content_rect)

    def test_all_hidden_no_crash(self):
        w = DummyWidget("test", priority=1, width=100, height=100,
                        visible=False)
        self.mgr.register_widget(w, zone="left")
        self.mgr.update_layout(self.content_rect)
        self.assertIsNone(self.mgr.get_widget_rect("test"))

    def test_favorites_dock_fallback_when_slc_invisible(self):
        ss = DummyWidget("set_speed", priority=1, width=172, height=204)
        slc = DummyWidget("speed_limit", priority=2, width=176, height=176,
                          visible=False)
        dock = DummyWidget("favorites_dock", priority=3, width=176, height=38,
                           placement=GridPlacement(
                               zone="close",
                               anchor=GridAnchor.TOP_LEFT,
                               relative_to="speed_limit",
                               relation="same_row",
                               offset=(0.0, 0.0),
                           ))

        self.mgr.register_widget(ss, zone="left")
        self.mgr.register_widget(slc, zone="left")
        self.mgr.register_widget(dock, placement=dock.placement)
        self.mgr.update_layout(self.content_rect)

        self.assertEqual(dock.rect.y, 294)


if __name__ == "__main__":
    unittest.main()

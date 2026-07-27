from __future__ import annotations
import pyray as rl
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import GRID_CELL_SIZE, GRID_COLS, GRID_ROWS


class GridOccupancyMap:
    def __init__(self, bounds: rl.Rectangle):
        self._bounds = bounds
        self._cols = 0
        self._rows = 0
        self._cells: set[tuple[int, int]] = set()
        self._rects: list[tuple[int, int, int, int, str]] = []
        self._owners: dict[str, tuple[int, int, int, int]] = {}
        self.set_bounds(bounds)

    def set_bounds(self, bounds: rl.Rectangle) -> None:
        self._bounds = bounds
        self._cols = max(1, int(bounds.width / GRID_CELL_SIZE))
        self._rows = max(1, int(bounds.height / GRID_CELL_SIZE))
        self.clear()

    def clear(self) -> None:
        self._cells.clear()
        self._rects.clear()
        self._owners.clear()

    @property
    def bounds(self) -> rl.Rectangle:
        return self._bounds

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    def pixel_to_cell(self, px: float, py: float) -> tuple[int, int]:
        col = max(0, min(self._cols - 1, int((px - self._bounds.x) / GRID_CELL_SIZE)))
        row = max(0, min(self._rows - 1, int((py - self._bounds.y) / GRID_CELL_SIZE)))
        return col, row

    def cell_to_pixel(self, col: int, row: int) -> tuple[float, float]:
        return (
            self._bounds.x + col * GRID_CELL_SIZE,
            self._bounds.y + row * GRID_CELL_SIZE,
        )

    def cell_to_pixel_float(self, col: float, row: float) -> tuple[float, float]:
        return (
            self._bounds.x + col * GRID_CELL_SIZE,
            self._bounds.y + row * GRID_CELL_SIZE,
        )

    def rect_to_cells(self, rect: rl.Rectangle) -> tuple[int, int, int, int]:
        c1, r1 = self.pixel_to_cell(rect.x, rect.y)
        c2, r2 = self.pixel_to_cell(
            rect.x + rect.width - 1, rect.y + rect.height - 1
        )
        return c1, r1, c2, r2

    def has_overlap(self, rect: rl.Rectangle, exclude: set[str] | None = None) -> bool:
        c1, r1, c2, r2 = self.rect_to_cells(rect)
        skip = exclude or set()
        for rc1, rr1, rc2, rr2, owner in self._rects:
            if owner in skip:
                continue
            if not (c2 < rc1 or c1 > rc2 or r2 < rr1 or r1 > rr2):
                return True
        return False

    def get_overlapping(self, rect: rl.Rectangle) -> list[str]:
        c1, r1, c2, r2 = self.rect_to_cells(rect)
        owners = []
        for rc1, rr1, rc2, rr2, owner in self._rects:
            if not (c2 < rc1 or c1 > rc2 or r2 < rr1 or r1 > rr2):
                owners.append(owner)
        return owners

    def reserve(self, rect: rl.Rectangle, owner_id: str) -> bool:
        if self.has_overlap(rect):
            return False
        c1, r1, c2, r2 = self.rect_to_cells(rect)
        self._rects.append((c1, r1, c2, r2, owner_id))
        self._owners[owner_id] = (c1, r1, c2, r2)
        for c in range(c1, c2 + 1):
            for r in range(r1, r2 + 1):
                self._cells.add((c, r))
        return True

    def release(self, owner_id: str) -> None:
        if owner_id not in self._owners:
            return
        c1, r1, c2, r2 = self._owners.pop(owner_id)
        for c in range(c1, c2 + 1):
            for r in range(r1, r2 + 1):
                self._cells.discard((c, r))
        self._rects = [
            (rc1, rr1, rc2, rr2, o)
            for rc1, rr1, rc2, rr2, o in self._rects
            if o != owner_id
        ]

    def is_occupied(self, col: int, row: int) -> bool:
        return (col, row) in self._cells

    def find_space(
        self,
        width: float,
        height: float,
        prefer_col: int | None = None,
        prefer_row: int | None = None,
    ) -> tuple[float, float] | None:
        span_cols = max(1, int(width / GRID_CELL_SIZE) + 1)
        span_rows = max(1, int(height / GRID_CELL_SIZE) + 1)
        if prefer_col is not None and prefer_row is not None:
            for r in range(prefer_row, self._rows - span_rows + 1):
                for c in range(prefer_col, self._cols - span_cols + 1):
                    if self._test_fit(c, r, span_cols, span_rows):
                        return self.cell_to_pixel(c, r)
        for r in range(0, self._rows - span_rows + 1):
            for c in range(0, self._cols - span_cols + 1):
                if self._test_fit(c, r, span_cols, span_rows):
                    return self.cell_to_pixel(c, r)
        return None

    def _test_fit(self, c: int, r: int, span_c: int, span_r: int) -> bool:
        if c + span_c > self._cols or r + span_r > self._rows:
            return False
        for rc1, rr1, rc2, rr2, _ in self._rects:
            if not (
                c + span_c - 1 < rc1 or c > rc2 or r + span_r - 1 < rr1 or r > rr2
            ):
                return False
        return True

    def render_debug(self, alpha: int = 60) -> None:
        for c1, r1, c2, r2, owner in self._rects:
            x, y = self.cell_to_pixel(c1, r1)
            w = (c2 - c1 + 1) * GRID_CELL_SIZE
            h = (r2 - r1 + 1) * GRID_CELL_SIZE
            color = self._owner_color(owner)
            color.a = alpha
            rl.draw_rectangle_rounded(
                rl.Rectangle(x, y, w, h), 0.1, 4, color
            )

    @staticmethod
    def _owner_color(owner: str) -> rl.Color:
        h = hash(owner) % 360
        return rl.ColorFromHSV(float(h), 0.6, 0.9)

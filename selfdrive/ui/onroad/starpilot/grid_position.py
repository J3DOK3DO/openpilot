from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


GRID_CELL_SIZE = 20
GRID_COLS = 105
GRID_ROWS = 51


class GridAnchor(Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class GridPlacement:
    zone: str | None = None
    anchor: GridAnchor = GridAnchor.TOP_LEFT
    x_cell: float = 0.0
    y_cell: float = 0.0
    relative_to: str | None = None
    relation: str | None = None
    offset: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    fallback: tuple[float, float] | None = None

    def __post_init__(self):
        if self.relative_to is not None and self.relation is None:
            raise ValueError("relative_to set but relation is None")

from __future__ import annotations
from dataclasses import dataclass
from openpilot.selfdrive.ui.onroad.starpilot.grid_position import GridAnchor, GridPlacement


@dataclass
class ZoneTemplate:
    name: str
    col_start_lhd: int
    col_end_lhd: int
    col_start_rhd: int
    col_end_rhd: int
    default_anchor: GridAnchor
    default_flow: str | None = None

    def col_start(self, is_rhd: bool) -> int:
        return self.col_start_rhd if is_rhd else self.col_start_lhd

    def col_end(self, is_rhd: bool) -> int:
        return self.col_end_rhd if is_rhd else self.col_end_lhd

    def col_count(self, is_rhd: bool) -> int:
        return self.col_end(is_rhd) - self.col_start(is_rhd) + 1


ZONES: dict[str, ZoneTemplate] = {
    "close": ZoneTemplate(
        name="close",
        col_start_lhd=0, col_end_lhd=34,
        col_start_rhd=70, col_end_rhd=104,
        default_anchor=GridAnchor.TOP_LEFT,
        default_flow="vertical",
    ),
    "middle": ZoneTemplate(
        name="middle",
        col_start_lhd=35, col_end_lhd=69,
        col_start_rhd=35, col_end_rhd=69,
        default_anchor=GridAnchor.CENTER,
        default_flow=None,
    ),
    "far": ZoneTemplate(
        name="far",
        col_start_lhd=70, col_end_lhd=104,
        col_start_rhd=0, col_end_rhd=34,
        default_anchor=GridAnchor.TOP_RIGHT,
        default_flow="vertical",
    ),
}


def get_zone(name: str) -> ZoneTemplate:
    if name not in ZONES:
        raise ValueError(f"Unknown zone: '{name}'. Valid: {', '.join(ZONES.keys())}")
    return ZONES[name]


_LEGACY_ZONE_MAP = {
    "left": "close",
    "right": "far",
    "bottom": "close",
}

_LEGACY_ANCHOR_MAP = {
    "left": GridAnchor.TOP_LEFT,
    "right": GridAnchor.TOP_RIGHT,
    "bottom": GridAnchor.BOTTOM_LEFT,
}

_LEGACY_FLOW_MAP = {
    "left": "vertical",
    "right": "vertical",
    "bottom": "horizontal",
}


def translate_legacy_zone(zone: str, priority: int,
                          is_rhd: bool = False) -> GridPlacement:
    if zone in ZONES:
        template = get_zone(zone)
        return GridPlacement(zone=zone, anchor=template.default_anchor)

    if zone in _LEGACY_ZONE_MAP:
        new_zone = _LEGACY_ZONE_MAP[zone]
        anchor = _LEGACY_ANCHOR_MAP[zone]
        template = get_zone(new_zone)

        if zone == "left":
            x_cell, y_cell = 3.8, 3.75
        elif zone == "right":
            x_cell = float(template.col_count(is_rhd) - 9.6)
            y_cell = 3.75
        elif zone == "bottom":
            x_cell, y_cell = 4.0, 40.4
        else:
            x_cell, y_cell = 0.0, 0.0

        return GridPlacement(zone=new_zone, anchor=anchor,
                             x_cell=x_cell, y_cell=y_cell)

    raise ValueError(f"Unknown zone: '{zone}'. Valid: {list(ZONES.keys())}")

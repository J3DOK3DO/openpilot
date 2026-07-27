from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AlertSuppression(Enum):
    NONE = 0
    FULL_ONLY = 1
    ANY_ALERT = 2


@dataclass
class RenderLayer:
    index: int
    name: str
    alert_suppression: AlertSuppression


LAYERS: dict[int, RenderLayer] = {
    0: RenderLayer(0, "PRE_FULL_ALERT", AlertSuppression.FULL_ONLY),
    1: RenderLayer(1, "OVERLAY", AlertSuppression.ANY_ALERT),
    2: RenderLayer(2, "POST_LAYER", AlertSuppression.ANY_ALERT),
    3: RenderLayer(3, "ROAD_SURFACE", AlertSuppression.NONE),
    4: RenderLayer(4, "FULL_SCENE", AlertSuppression.NONE),
}


def layer_should_render(layer_index: int, alert_showing: object | None,
                        alert_size: object | None = None) -> bool:
    layer = LAYERS.get(layer_index)
    if layer is None:
        return True

    if layer.alert_suppression == AlertSuppression.NONE:
        return True
    if layer.alert_suppression == AlertSuppression.ANY_ALERT:
        return alert_showing is None
    if layer.alert_suppression == AlertSuppression.FULL_ONLY:
        if alert_showing is None:
            return True
        if alert_size is None:
            return False
        return not _is_full_alert(alert_size)

    return True


def _is_full_alert(alert_size: object) -> bool:
    try:
        return int(alert_size) == 2
    except (TypeError, ValueError):
        return False

from __future__ import annotations
from collections import deque
import pyray as rl
from typing import Any


class AnchorCycleError(ValueError):
    pass


class AnchorResolutionError(RuntimeError):
    pass


class AnchorGraph:
    def __init__(self):
        self._anchors: dict[str, _AnchorNode] = {}

    def add(
        self,
        child_name: str,
        parent_name: str,
        relation: str,
        offset: tuple[float, float],
        fallback: tuple[float, float] | None,
        child_widget: Any,
    ) -> None:
        self._anchors[child_name] = _AnchorNode(
            child_name=child_name,
            parent_name=parent_name,
            relation=relation,
            offset=offset,
            fallback=fallback,
            widget=child_widget,
        )

    def resolve(
        self,
        known_rects: dict[str, rl.Rectangle],
        is_rhd: bool,
    ) -> dict[str, rl.Rectangle]:
        if not self._anchors:
            return {}

        in_degree: dict[str, int] = {}
        dependents: dict[str, list[str]] = {}
        for name, node in self._anchors.items():
            parent_exists = (
                node.parent_name in known_rects
                or node.parent_name in self._anchors
            )
            if parent_exists:
                in_degree[name] = 1 if node.parent_name not in known_rects else 0
            else:
                in_degree[name] = 0
            dependents.setdefault(node.parent_name, []).append(name)

        for name in known_rects:
            if name not in in_degree:
                in_degree[name] = 0

        for name in list(in_degree.keys()):
            if in_degree[name] == 0:
                for dep in dependents.get(name, []):
                    if dep in in_degree:
                        in_degree[dep] = max(0, in_degree[dep] - 1)

        queue: deque[str] = deque(
            n for n, d in in_degree.items() if d == 0 and n in self._anchors
        )

        resolved_order: list[str] = []

        while queue:
            name = queue.popleft()
            if name not in self._anchors:
                continue
            resolved_order.append(name)
            for dep in dependents.get(name, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        anchored_count = len(self._anchors)
        if len(resolved_order) < anchored_count:
            unresolved = set(self._anchors) - set(resolved_order)
            still_unresolved = set()
            for name in unresolved:
                node = self._anchors[name]
                parent_exists = (
                    node.parent_name in known_rects
                    or node.parent_name in self._anchors
                )
                if not parent_exists and node.fallback is not None:
                    continue
                still_unresolved.add(name)
            if still_unresolved:
                raise AnchorCycleError(
                    f"Circular anchor dependency involving: {still_unresolved}"
                )

        resolved_rects: dict[str, rl.Rectangle] = dict(known_rects)

        for child_name in resolved_order:
            node = self._anchors[child_name]
            parent_rect = resolved_rects.get(node.parent_name)

            if parent_rect is None:
                if node.fallback is not None:
                    w, h = node.widget.get_size()
                    resolved_rects[child_name] = rl.Rectangle(
                        node.fallback[0], node.fallback[1], w, h
                    )
                continue

            resolved_rects[child_name] = _compute_relation_rect(
                parent_rect,
                node.relation,
                node.offset,
                node.widget.get_size(),
                is_rhd,
            )

        return {
            name: rect
            for name, rect in resolved_rects.items()
            if name in self._anchors
        }


class _AnchorNode:
    def __init__(
        self,
        child_name: str,
        parent_name: str,
        relation: str,
        offset: tuple[float, float],
        fallback: tuple[float, float] | None,
        widget: Any,
    ):
        self.child_name = child_name
        self.parent_name = parent_name
        self.relation = relation
        self.offset = offset
        self.fallback = fallback
        self.widget = widget


def _compute_relation_rect(
    parent: rl.Rectangle,
    relation: str,
    offset: tuple[float, float],
    size: tuple[float, float],
    is_rhd: bool,
) -> rl.Rectangle:
    ox, oy = offset
    w, h = size

    effective_relation = relation
    if is_rhd:
        if relation == "right_of":
            effective_relation = "left_of"
        elif relation == "left_of":
            effective_relation = "right_of"

    if effective_relation == "right_of":
        x = parent.x + parent.width + ox
        y = parent.y + parent.height / 2 - h / 2 + oy
    elif effective_relation == "left_of":
        x = parent.x - w - ox
        y = parent.y + parent.height / 2 - h / 2 + oy
    elif effective_relation == "above":
        x = parent.x + parent.width / 2 - w / 2 + ox
        y = parent.y - h + oy
    elif effective_relation == "below":
        x = parent.x + parent.width / 2 - w / 2 + ox
        y = parent.y + parent.height + oy
    elif effective_relation == "same_row":
        x = parent.x + ox
        y = parent.y + oy
    else:
        x = parent.x + ox
        y = parent.y + oy

    return rl.Rectangle(x, y, w, h)

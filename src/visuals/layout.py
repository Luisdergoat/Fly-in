from __future__ import annotations

from typing import Any

import pygame

from .style import MAP_MARGIN, MAX_CELL, MIN_CELL, OUTER_MARGIN, PIXEL_SCALE


def extract_zones(parser_instance: Any) -> list[Any]:
    if parser_instance is None or not hasattr(parser_instance, "vars"):
        return []
    data = getattr(parser_instance, "vars", {})
    if not isinstance(data, dict):
        return []
    zones: list[Any] = []
    for value in data.values():
        if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "name"):
            zones.append(value)
    return zones


def bbox(zones: list[Any]) -> tuple[int, int, int, int]:
    if not zones:
        return 0, 0, 1, 1
    xs = [zone.x for zone in zones]
    ys = [zone.y for zone in zones]
    return min(xs), min(ys), max(xs), max(ys)


def compute_initial_size(zones: list[Any], base_window: tuple[int, int]) -> tuple[int, int]:
    min_x, min_y, max_x, max_y = bbox(zones)
    span_x = max(max_x - min_x, 0) + 1
    span_y = max(max_y - min_y, 0) + 1
    n_zones = max(len(zones), 1)
    spread = max(span_x, span_y, int(n_zones**0.5) + 1)
    cell = max(MIN_CELL, min(MAX_CELL, int(520 / max(spread, 2))))
    cell += min(24, n_zones * 2)

    map_w = MAP_MARGIN * 2 + cell * span_x
    map_h = MAP_MARGIN * 2 + cell * span_y
    width = OUTER_MARGIN * 2 + map_w
    height = max(base_window[1], OUTER_MARGIN * 2 + map_h + 80)
    width = max(width, base_window[0] + 120)
    return int(width), int(height)


def layout_rects(width: int, height: int) -> pygame.Rect:
    return pygame.Rect(
        OUTER_MARGIN,
        OUTER_MARGIN,
        max(120, width - OUTER_MARGIN * 2),
        max(120, height - OUTER_MARGIN * 2),
    )


def map_buffer_size(map_rect: pygame.Rect) -> tuple[int, int]:
    return max(32, map_rect.width // PIXEL_SCALE), max(24, map_rect.height // PIXEL_SCALE)


def cell_positions_buffer(
    zones: list[Any], bw: int, bh: int, margin_buf: int
) -> tuple[int, dict[str, tuple[int, int]]]:
    if not zones:
        return MIN_CELL // PIXEL_SCALE, {}

    min_x, min_y, max_x, max_y = bbox(zones)
    span_x = max(max_x - min_x, 0) + 1
    span_y = max(max_y - min_y, 0) + 1
    inner_w = max(1, bw - 2 * margin_buf)
    inner_h = max(1, bh - 2 * margin_buf)
    cell = int(min(inner_w / span_x, inner_h / span_y))
    cell = max(5, min(18, cell))

    positions: dict[str, tuple[int, int]] = {}
    for zone in zones:
        nx = (zone.x - min_x) / max(span_x - 1, 1) if span_x > 1 else 0.5
        ny = (zone.y - min_y) / max(span_y - 1, 1) if span_y > 1 else 0.5
        cx = margin_buf + int(nx * (inner_w - cell)) + cell // 2
        cy = margin_buf + int(ny * (inner_h - cell)) + cell // 2
        positions[zone.name] = (cx, cy)
    return cell, positions


def buf_to_screen(map_rect: pygame.Rect, bx: int, by: int) -> tuple[int, int]:
    bw, bh = map_buffer_size(map_rect)
    sx = map_rect.left + int(bx * map_rect.width / bw)
    sy = map_rect.top + int(by * map_rect.height / bh)
    return sx, sy

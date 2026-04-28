from __future__ import annotations

from .style import MAP_COLORS

Color = tuple[int, int, int]


def color_from_map_value(value: object) -> Color:
    if not isinstance(value, str):
        return (95, 170, 100)
    key = value.strip().lower()
    if key in MAP_COLORS:
        return MAP_COLORS[key]
    if key.startswith("#") and len(key) in (4, 7):
        try:
            if len(key) == 4:
                r = int(key[1], 16) * 17
                g = int(key[2], 16) * 17
                b = int(key[3], 16) * 17
            else:
                r = int(key[1:3], 16)
                g = int(key[3:5], 16)
                b = int(key[5:7], 16)
            return (r, g, b)
        except ValueError:
            return (95, 170, 100)
    return (95, 170, 100)


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def lerp_rgb(c0: Color, c1: Color, t: float) -> Color:
    return (lerp(c0[0], c1[0], t), lerp(c0[1], c1[1], t), lerp(c0[2], c1[2], t))

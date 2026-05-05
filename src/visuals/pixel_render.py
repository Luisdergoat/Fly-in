from __future__ import annotations

import pygame

from .helpers import MapColorUtils
from .style import (
    BAYER_4,
    BRIDGE,
    BRIDGE_HI,
    CLOUD,
    FOREST_GRASS_DARK,
    FOREST_GRASS_LIGHT,
    FOREST_GRASS_MID,
    FOREST_SOIL_DARK,
    FOREST_SOIL_LIGHT,
    FOREST_SOIL_MID,
    GRASS_HI,
    GRASS_TOP,
    ROCK_DARK,
    ROCK_LIGHT,
    ROCK_MID,
    SKY_HORIZON,
    SKY_MID,
    SKY_TOP,
)

Color = tuple[int, int, int]


class PixelRenderer:
    """Low-resolution buffer drawing: sky, islands, links, zone hubs."""

    @staticmethod
    def nearest_scale(src: pygame.Surface, target_w: int, target_h: int) -> pygame.Surface:
        sw, sh = src.get_size()
        if sw <= 0 or sh <= 0:
            return pygame.Surface((max(1, target_w), max(1, target_h)))
        dst = pygame.Surface((target_w, target_h))
        scale_x = target_w / sw
        scale_y = target_h / sh
        for sy in range(sh):
            y0 = int(sy * scale_y)
            y1 = int((sy + 1) * scale_y)
            if y1 <= y0:
                y1 = y0 + 1
            for sx in range(sw):
                x0 = int(sx * scale_x)
                x1 = int((sx + 1) * scale_x)
                if x1 <= x0:
                    x1 = x0 + 1
                dst.fill(src.get_at((sx, sy)), (x0, y0, x1 - x0, y1 - y0))
        return dst

    @staticmethod
    def draw_sky_dither(surf: pygame.Surface, w: int, h: int) -> None:
        for y in range(h):
            t = y / max(h - 1, 1)
            if t < 0.55:
                t2 = t / 0.55
                c_lo = MapColorUtils.lerp_rgb(SKY_TOP, SKY_MID, t2)
                c_hi = MapColorUtils.lerp_rgb(
                    (min(255, c_lo[0] + 18), min(255, c_lo[1] + 10), min(255, c_lo[2] + 8)),
                    SKY_MID,
                    t2,
                )
            else:
                t2 = (t - 0.55) / 0.45
                c_lo = MapColorUtils.lerp_rgb(SKY_MID, SKY_HORIZON, t2)
                c_hi = MapColorUtils.lerp_rgb(
                    SKY_MID,
                    (min(255, SKY_HORIZON[0] + 10), SKY_HORIZON[1], SKY_HORIZON[2]),
                    t2,
                )
            for x in range(w):
                bayer = BAYER_4[x % 4][y % 4]
                surf.set_at((x, y), c_hi if bayer < 8 else c_lo)

    @staticmethod
    def draw_clouds(surf: pygame.Surface, w: int, h: int, tick: int) -> None:
        drift = (tick // 50) % (w + 40)
        base_y = int(h * 0.18)
        blobs = (
            (-20 + drift, base_y, 36, 10),
            (w // 3 + drift // 2, base_y + 8, 44, 12),
            (2 * w // 3 - drift // 3, base_y + 3, 32, 9),
        )
        for cx, cy, cw, ch in blobs:
            for by in range(ch):
                for bx in range(cw):
                    dx = bx - cw // 2
                    dy = by - ch // 2
                    if (dx * dx) / ((cw // 2) ** 2 + 1) + (dy * dy) / ((ch // 2) ** 2 + 1) <= 1.0:
                        px = cx + bx
                        py = cy + by
                        if 0 <= px < w and 0 <= py < h:
                            surf.set_at((px, py), CLOUD)

    @staticmethod
    def draw_ground_forest(surf: pygame.Surface, w: int, h: int) -> None:
        ground_h = max(6, int(h * 0.14))
        y0 = h - ground_h
        for y in range(y0, h):
            for x in range(w):
                band = y - y0
                if band < 2:
                    color = FOREST_GRASS_LIGHT if (x + y) % 2 == 0 else FOREST_GRASS_MID
                elif band < 5:
                    color = FOREST_GRASS_MID if (x // 2 + y) % 2 == 0 else FOREST_GRASS_DARK
                else:
                    noise = (x // 3 + y // 2) % 3
                    if noise == 0:
                        color = FOREST_SOIL_DARK
                    elif noise == 1:
                        color = FOREST_SOIL_MID
                    else:
                        color = FOREST_SOIL_LIGHT
                surf.set_at((x, y), color)

        for x in range(0, w, 6):
            pygame.draw.line(surf, (52, 42, 30), (x, y0 + 4), (x, h - 1), 1)

        for x in range(2, w - 2, 5):
            top = y0 - 1 - ((x // 7) % 2)
            if 0 <= top < h:
                surf.set_at((x, top), FOREST_GRASS_LIGHT)
                if top + 1 < h:
                    surf.set_at((x - 1, top + 1), FOREST_GRASS_MID)
                    surf.set_at((x + 1, top + 1), FOREST_GRASS_MID)

    @staticmethod
    def draw_distant_trees(surf: pygame.Surface, w: int, h: int) -> None:
        y_base = h - max(6, int(h * 0.14)) - 2
        for index, tx in enumerate(range(8, w - 8, max(14, w // 7))):
            crown_y = y_base - 10 - (index % 3) * 2
            cx = tx + (index * 3) % 5
            for ty in range(6):
                for tx2 in range(2):
                    if 0 <= cx + tx2 < w and 0 <= y_base - ty < h:
                        surf.set_at((cx + tx2, y_base - ty), (34, 28, 32))
            for dy in range(-8, 2):
                for dx in range(-7, 8):
                    if dx * dx + dy * dy < 38:
                        px = cx + dx
                        py = crown_y + dy
                        if 0 <= px < w and 0 <= py < h:
                            shade = (160 + (dx + dy) % 20, 60 + abs(dy) * 8, 35 + abs(dx) * 2)
                            surf.set_at((px, py), shade)

    @staticmethod
    def draw_side_cliffs(surf: pygame.Surface, w: int, h: int) -> None:
        ground_y = h - max(6, int(h * 0.14))
        for side in (-1, 1):
            edge = 0 if side < 0 else w - 1
            for y in range(ground_y - int(h * 0.55), ground_y):
                span = int((ground_y - y) * 0.12)
                x0 = edge + side * min(span, 18)
                for x in range(min(x0, edge), max(x0, edge) + 1):
                    if 0 <= x < w:
                        surf.set_at((x, y), ROCK_DARK if (x + y) % 3 else ROCK_MID)
            for y in range(ground_y - 5, ground_y):
                x_strip = range(0, min(14, w // 4)) if side < 0 else range(w - min(14, w // 4), w)
                for x in x_strip:
                    surf.set_at((x, y), GRASS_TOP if (x + y) % 2 == 0 else GRASS_HI)

    @staticmethod
    def draw_pixel_scene_base(buf: pygame.Surface, tick: int) -> None:
        bw, bh = buf.get_size()
        PixelRenderer.draw_sky_dither(buf, bw, bh)
        PixelRenderer.draw_clouds(buf, bw, bh, tick)
        PixelRenderer.draw_distant_trees(buf, bw, bh)
        PixelRenderer.draw_side_cliffs(buf, bw, bh)
        PixelRenderer.draw_ground_forest(buf, bw, bh)

    @staticmethod
    def draw_clouds_bottom_band(surf: pygame.Surface, w: int, h: int, tick: int) -> None:
        drift = (tick // 70 + 33) % (w + 50)
        base_y = int(h * 0.52)
        blobs = (
            (-30 + drift, base_y, 48, 11),
            (w // 4 + drift // 3, base_y + 10, 40, 10),
            (w * 3 // 4 - drift // 4, base_y + 4, 36, 9),
        )
        for cx, cy, cw, ch in blobs:
            for by in range(ch):
                for bx in range(cw):
                    dx = bx - cw // 2
                    dy = by - ch // 2
                    if (dx * dx) / ((cw // 2) ** 2 + 1) + (dy * dy) / ((ch // 2) ** 2 + 1) <= 1.0:
                        px = cx + bx
                        py = cy + by
                        if 0 <= px < w and 0 <= py < h:
                            surf.set_at((px, py), CLOUD)

    @staticmethod
    def draw_pixel_scene_sky_only(buf: pygame.Surface, tick: int) -> None:
        bw, bh = buf.get_size()
        PixelRenderer.draw_sky_dither(buf, bw, bh)
        PixelRenderer.draw_clouds(buf, bw, bh, tick)
        PixelRenderer.draw_clouds_bottom_band(buf, bw, bh, tick)

    @staticmethod
    def draw_connection_line(
        buf: pygame.Surface, a: tuple[int, int], b: tuple[int, int], color: Color, width: int = 1
    ) -> None:
        w = max(1, width)
        pygame.draw.line(buf, color, a, b, width=w)

    @staticmethod
    def draw_floating_island(
        buf: pygame.Surface, cx: int, cy: int, pw: int, ph: int, top_tint: Color
    ) -> None:
        x0 = cx - pw // 2
        y0 = cy - ph // 2
        for y in range(ph):
            for x in range(pw):
                px, py = x0 + x, y0 + y
                if not (0 <= px < buf.get_width() and 0 <= py < buf.get_height()):
                    continue
                if y < 2:
                    color = top_tint if (x + y) % 2 == 0 else MapColorUtils.lerp_rgb(top_tint, ROCK_MID, 0.35)
                elif y < 4:
                    color = MapColorUtils.lerp_rgb(top_tint, ROCK_MID, 0.55)
                else:
                    noise = (x // 2 + y // 3) % 3
                    color = (ROCK_DARK, ROCK_MID, ROCK_LIGHT)[noise]
                buf.set_at((px, py), color)
        for x in range(pw):
            px = x0 + x
            py = y0 + ph - 1
            if 0 <= px < buf.get_width() and 0 <= py < buf.get_height():
                buf.set_at((px, py), (38, 36, 52))

    @staticmethod
    def _name_hash_to_unit(s: str) -> float:
        h = 0
        for ch in s:
            h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        return (h % 10001) / 10001.0

    @staticmethod
    def draw_zone_node(
        buf: pygame.Surface,
        zone: object,
        cx: int,
        cy: int,
        pw: int,
        ph: int,
        accent: Color,
        tick: int,
    ) -> None:
        hub = getattr(zone, "hub_kind", None) or "waypoint"
        zt = getattr(zone, "zone_type", "normal") or "normal"
        color_raw = getattr(zone, "color", None)
        if isinstance(color_raw, str) and color_raw.strip().lower() == "rainbow":
            accent = MapColorUtils.rainbow_rgb(tick / 2200.0 + PixelRenderer._name_hash_to_unit(zone.name))

        if zt == "blocked":
            accent = (55, 52, 58)
        if zt == "no_fly":
            accent = (90, 30, 40)

        top = accent
        if hub == "start":
            top = MapColorUtils.lerp_rgb(accent, (80, 200, 120), 0.25)
            PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, top)
            for dx in range(-1, 2):
                px = cx + dx
                if 0 <= px < buf.get_width() and 0 <= cy - ph // 2 - 1 < buf.get_height():
                    buf.set_at((px, cy - ph // 2 - 1), (255, 255, 100))
            return
        if hub == "end":
            top = MapColorUtils.lerp_rgb(accent, (200, 100, 255), 0.2)
            PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, top)
            for t in range(6):
                px = cx - 3 + (tick // 8 + t * 2) % 7
                py = cy - ph // 2 - 2 - (t % 2)
                if 0 <= px < buf.get_width() and 0 <= py < buf.get_height():
                    buf.set_at((px, py), (255, 255, 220))
            return

        if zt == "priority":
            PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, MapColorUtils.lerp_rgb(accent, (255, 230, 120), 0.15))
            for ox in range(-pw // 2 + 1, pw // 2 - 1, 2):
                px = cx + ox
                py = cy - ph // 2 + 1
                if 0 <= px < buf.get_width() and 0 <= py < buf.get_height():
                    buf.set_at((px, py), (255, 255, 200))
            return
        if zt == "restricted":
            PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, MapColorUtils.lerp_rgb(accent, (255, 140, 60), 0.12))
            for ox in range(-pw // 2, pw // 2, 2):
                px = cx + ox
                for oy in range(-ph // 2, ph // 2):
                    if (ox + oy) % 4 == 0:
                        py = cy + oy
                        if 0 <= px < buf.get_width() and 0 <= py < buf.get_height():
                            buf.set_at((px, py), (40, 35, 30))
            return
        if zt == "blocked":
            PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, top)
            for ox in range(-pw // 2, pw // 2):
                for oy in range(-ph // 2, ph // 2):
                    if abs(ox) == abs(oy) or ox == -oy:
                        px, py = cx + ox, cy + oy
                        if 0 <= px < buf.get_width() and 0 <= py < buf.get_height():
                            buf.set_at((px, py), (20, 18, 24))
            return
        if zt == "no_fly":
            PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, top)
            return

        PixelRenderer.draw_floating_island(buf, cx, cy, pw, ph, MapColorUtils.lerp_rgb(accent, ROCK_MID, 0.2))

    @staticmethod
    def draw_floating_platform(
        buf: pygame.Surface, cx: int, cy: int, pw: int, ph: int, top_tint: Color
    ) -> None:
        x0 = cx - pw // 2
        y0 = cy - ph // 2
        for y in range(ph):
            for x in range(pw):
                px, py = x0 + x, y0 + y
                if not (0 <= px < buf.get_width() and 0 <= py < buf.get_height()):
                    continue
                if y < 3:
                    color = GRASS_HI if (x + y) % 2 == 0 else top_tint
                elif y == 3:
                    color = MapColorUtils.lerp_rgb(top_tint, ROCK_MID, 0.4)
                else:
                    noise = (x // 2 + y // 3) % 3
                    color = (ROCK_DARK, ROCK_MID, ROCK_LIGHT)[noise]
                buf.set_at((px, py), color)
        for x in range(pw):
            px = x0 + x
            py = y0 + ph - 1
            if 0 <= px < buf.get_width() and 0 <= py < buf.get_height():
                buf.set_at((px, py), (42, 38, 48))

    @staticmethod
    def draw_bridge_line(buf: pygame.Surface, a: tuple[int, int], b: tuple[int, int]) -> None:
        x0, y0 = a
        x1, y1 = b
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        w, h = buf.get_size()
        while True:
            for ox, oy in ((0, 0), (1, 0), (0, 1)):
                px, py = x + ox, y + oy
                if 0 <= px < w and 0 <= py < h:
                    buf.set_at((px, py), BRIDGE if (px + py) % 2 == 0 else BRIDGE_HI)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

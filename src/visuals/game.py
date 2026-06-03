from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any, Callable

import pygame

from .helpers import MapColorUtils
from .layout import MapLayout
from .pixel_render import PixelRenderer
from .style import CONNECTION_PALETTE, MAP_MARGIN, PIXEL_SCALE, ROCK_MID


class Game:
    def __init__(
        self,
        parser_instance: Any = None,
        *,
        fullscreen: bool = True,
        algo: Any = None,
    ) -> None:
        pygame.init()
        self.parser = parser_instance
        self.algo = algo
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = fullscreen
        self._init_drone_visuals()
        self._setup_display()
        self._refresh_fonts()

    def _init_drone_visuals(self) -> None:
        rnd = random.Random(2026)
        self.drone_flight: dict[str, dict[str, float | int]] = {}
        self.drone_base_off: dict[str, tuple[int, int]] = {}
        nb = getattr(self.parser, "nb_drones", 0) or 0
        for i in range(nb):
            did = f"drone{i}"
            self.drone_flight[did] = {
                "amp": 2.0 + rnd.random() * 5.0,
                "freq": 1 + rnd.randint(0, 4),
                "phase": rnd.random() * math.tau,
                "zig": rnd.choice((-1, 1)),
            }
            self.drone_base_off[did] = (rnd.randint(-3, 3), rnd.randint(-2, 2))

    def _setup_display(self) -> None:
        if self.fullscreen:
            info = pygame.display.Info()
            self.width = int(info.current_w)
            self.height = int(info.current_h)
            flags = pygame.FULLSCREEN
            if hasattr(pygame, "SCALED"):
                flags |= pygame.SCALED
            try:
                self.screen = pygame.display.set_mode((self.width, self.height), flags)
            except pygame.error:
                self.fullscreen = False
                self.width, self.height = 1280, 720
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        else:
            self.width, self.height = 1100, 760
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Fly-in")

    def _sys_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        size = max(8, size)
        for name in ("Segoe UI", "Helvetica Neue", "Arial Unicode MS", "Arial", "DejaVu Sans"):
            try:
                font = pygame.font.SysFont(name, size, bold=bold)
                if font:
                    return font
            except Exception:
                continue
        return pygame.font.Font(None, size)

    def _refresh_fonts(self) -> None:
        h = max(480, self.height)
        self.hud_sub = self._sys_font(max(16, int(h * 0.024)), bold=True)
        self.small_font = self._sys_font(max(11, int(h * 0.018)), bold=False)
        self.zone_tag_font = self._sys_font(max(10, int(h * 0.016)), bold=True)
        # Compact turn readout (left margin, no top bar)
        self.turn_hud_main = self._sys_font(max(13, int(h * 0.021)), bold=True)
        self.turn_hud_phase = self._sys_font(max(10, int(h * 0.015)), bold=False)
        self.legend_font = self._sys_font(max(10, int(h * 0.014)), bold=False)
        self.splash_font = self._sys_font(max(28, int(h * 0.046)), bold=True)
        self.splash_sub = self._sys_font(max(18, int(h * 0.028)), bold=False)
        self.start_tag = self._sys_font(max(15, int(h * 0.022)), bold=False)

    @staticmethod
    def _smootherstep(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    def pump_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False
                return False
            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.width = max(640, int(event.w))
                self.height = max(480, int(event.h))
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self._refresh_fonts()
        return self.running

    def _layout_pack(self) -> tuple[list[Any], pygame.Rect, int, int, int, dict[str, tuple[int, int]]]:
        zones = MapLayout.extract_zones(self.parser)
        map_rect = MapLayout.layout_rects(self.width, self.height)
        bw, bh = MapLayout.map_buffer_size(map_rect)
        margin_buf = max(4, MAP_MARGIN // PIXEL_SCALE)
        cell, pos_buf = MapLayout.cell_positions_buffer(zones, bw, bh, margin_buf)
        return zones, map_rect, bw, bh, cell, pos_buf

    def _accent(self, zone: Any, tick: int) -> tuple[int, int, int]:
        raw = getattr(zone, "color", None)
        if isinstance(raw, str) and raw.strip().lower() == "rainbow":
            h = hash(zone.name)
            u = ((h % 10001) + 10001) % 10001 / 10001.0
            return MapColorUtils.rainbow_rgb(tick / 2000.0 + u)
        return MapColorUtils.color_from_map_value(raw)

    def _drones_by_zone(self) -> dict[str, list[str]]:
        m: dict[str, list[str]] = defaultdict(list)
        for z in self.parser.vars.values():
            if hasattr(z, "drones") and hasattr(z, "name"):
                for d in sorted(z.drones):
                    m[z.name].append(d)
        return m

    def _drone_zone_map(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for zname, z in self.parser.vars.items():
            if hasattr(z, "drones"):
                for d in z.drones:
                    out[d] = z.name
        return out

    def _buf_xy_transit(self, did: str, pos_buf: dict[str, tuple[int, int]]) -> tuple[float, float] | None:
        if not self.algo:
            return None
        tr = self.algo.transit_visual_anchor(did)
        if not tr:
            return None
        src, dst = tr
        if src not in pos_buf or dst not in pos_buf:
            return None
        sx, sy = pos_buf[src]
        ex, ey = pos_buf[dst]
        return (sx + ex) * 0.5, (sy + ey) * 0.5

    def _legend_rows(self) -> list[tuple[str, tuple[int, int, int]]]:
        """Full-word labels + RGB swatches matching `draw_zone_node` tints (default parser accents)."""
        return [
            ("Start hub", MapColorUtils.lerp_rgb((72, 168, 92), (80, 200, 120), 0.25)),
            ("Goal", MapColorUtils.lerp_rgb((234, 67, 53), (200, 100, 255), 0.2)),
            ("Waypoint", MapColorUtils.lerp_rgb((66, 133, 244), ROCK_MID, 0.2)),
            ("Priority zone", MapColorUtils.lerp_rgb((255, 193, 7), (255, 230, 120), 0.15)),
            ("Restricted zone", MapColorUtils.lerp_rgb((121, 85, 72), (255, 140, 60), 0.12)),
            ("Blocked", (55, 52, 58)),
            ("No-fly", (90, 30, 40)),
            ("Drone", (255, 99, 99)),
            *[(f"Route color {i}", CONNECTION_PALETTE[i]) for i in range(min(8, len(CONNECTION_PALETTE)))],
        ]

    def _draw_legend_bottom_right(self) -> None:
        sq = max(10, min(14, int(self.height * 0.016)))
        gap = 8
        pad = 12
        title_s = self.legend_font.render("Legend", True, (255, 255, 255))
        rows = self._legend_rows()
        line_h = max(self.legend_font.get_linesize(), sq + 2)
        max_w = title_s.get_width()
        rendered: list[tuple[pygame.Surface, tuple[int, int, int]]] = []
        for label, rgb in rows:
            t = self.legend_font.render(label, True, (245, 247, 252))
            rendered.append((t, rgb))
            max_w = max(max_w, sq + gap + t.get_width())
        block_h = title_s.get_height() + 8 + len(rows) * line_h + pad * 2
        block_w = max_w + pad * 2
        x0 = self.width - block_w - 12
        y0 = self.height - block_h - 12
        panel = pygame.Surface((block_w, block_h), pygame.SRCALPHA)
        panel.fill((12, 14, 26, 220))
        panel.blit(title_s, (pad, pad))
        y_base = pad + title_s.get_height() + 8
        for i, (surf, rgb) in enumerate(rendered):
            y = y_base + i * line_h + (line_h - sq) // 2
            pygame.draw.rect(panel, rgb, (pad, y, sq, sq))
            pygame.draw.rect(panel, (255, 255, 255), (pad, y, sq, sq), 1)
            panel.blit(
                surf,
                (pad + sq + gap, y_base + i * line_h + (line_h - surf.get_height()) // 2),
            )
        self.screen.blit(panel, (x0, y0))

    def _blit_outlined(
        self,
        surf: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        font: pygame.font.Font,
        fg: tuple,
        bg: tuple,
    ) -> None:
        x, y = rect.x, rect.y
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            surf.blit(font.render(text, True, bg), (x + ox, y + oy))
        surf.blit(font.render(text, True, fg), (x, y))

    def show_completion_splash(self, sim_turns: int, weighted_units: int) -> None:
        """Full-screen overlay: rounds + weighted move units (1 per normal step, 2 per restricted crossing)."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((10, 12, 22, 245))
        self.screen.blit(overlay, (0, 0))

        tr = self.splash_font.render("Complete", True, (255, 255, 255)).get_rect(
            center=(self.width // 2, self.height // 2 - 78)
        )
        self._blit_outlined(self.screen, tr, "Complete", self.splash_font, (255, 255, 255), (0, 0, 0))

        t1 = f"Simulation rounds: {sim_turns}"
        t2 = f"Move units (1 normal / 2 restricted): {weighted_units}"
        r1 = self.splash_sub.render(t1, True, (220, 230, 255)).get_rect(center=(self.width // 2, self.height // 2 - 18))
        r2 = self.splash_sub.render(t2, True, (200, 220, 255)).get_rect(center=(self.width // 2, self.height // 2 + 20))
        self._blit_outlined(self.screen, r1, t1, self.splash_sub, (220, 230, 255), (0, 0, 0))
        self._blit_outlined(self.screen, r2, t2, self.splash_sub, (200, 220, 255), (0, 0, 0))

        ht = "Press Esc to close"
        hr = self.legend_font.render(ht, True, (180, 190, 220)).get_rect(
            center=(self.width // 2, self.height // 2 + 72)
        )
        self._blit_outlined(self.screen, hr, ht, self.legend_font, (180, 190, 220), (0, 0, 0))
        pygame.display.flip()

        t0 = pygame.time.get_ticks()
        while pygame.time.get_ticks() - t0 < 300_000 and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    return
            self.clock.tick(120)

    def wait_for_space_to_start(self) -> bool:
        """Wait at the initial map view; Space starts, Esc or Q quits."""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return True
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        self.running = False
                        return False
                if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.width = max(640, int(event.w))
                    self.height = max(480, int(event.h))
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self._refresh_fonts()
            self.show_state(0, "Press SPACE to start")
            self.clock.tick(120)
        return False

    def _draw_start_screen(self, tick: int) -> None:
        _, _, _, _, _, pos_buf = self._layout_pack()
        xy = self._build_drone_xy_static(pos_buf)
        self._compose_frame(0, "", xy, show_legend=False)

        pulse = 0.5 + 0.5 * math.sin(tick / 260.0)
        veil_a = int(120 + 55 * pulse)
        veil = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        veil.fill((14, 18, 36, veil_a))
        self.screen.blit(veil, (0, 0))

        title = "Fly-in"
        tr = self.splash_font.render(title, True, (255, 255, 255)).get_rect(
            center=(self.width // 2, self.height // 2 - 48)
        )
        self._blit_outlined(self.screen, tr, title, self.splash_font, (255, 255, 255), (8, 10, 28))

        sub_c = MapColorUtils.lerp_rgb((160, 175, 210), (255, 255, 255), 0.35 + 0.45 * pulse)
        sub = "Press SPACE to start"
        sr = self.splash_sub.render(sub, True, sub_c).get_rect(center=(self.width // 2, self.height // 2 + 12))
        self._blit_outlined(self.screen, sr, sub, self.splash_sub, sub_c, (0, 0, 0))

        hint = "Esc or Q to quit"
        hr = self.start_tag.render(hint, True, (150, 160, 190)).get_rect(
            center=(self.width // 2, self.height // 2 + 58)
        )
        self._blit_outlined(self.screen, hr, hint, self.start_tag, (150, 160, 190), (0, 0, 0))

    def _buf_pos_for_drone(
        self,
        did: str,
        pos_buf: dict[str, tuple[int, int]],
        by_zone: dict[str, list[str]],
        zone_name: str,
    ) -> tuple[float, float]:
        cx, cy = pos_buf[zone_name]
        lst = by_zone.get(zone_name, [did])
        idx = lst.index(did) if did in lst else 0
        n = max(len(lst), 1)
        ang = math.tau * idx / n
        r = 2.0 if n <= 1 else 3.2
        ox, oy = self.drone_base_off.get(did, (0, 0))
        return cx + r * math.cos(ang) + ox, cy + r * math.sin(ang) + oy

    def _flight_offset(
        self, did: str, u: float, sx: float, sy: float, ex: float, ey: float
    ) -> tuple[float, float]:
        dx, dy = ex - sx, ey - sy
        ln = max(1.0, math.hypot(dx, dy))
        px, py = -dy / ln, dx / ln
        p = self.drone_flight[did]
        amp = float(p["amp"])
        freq = int(p["freq"])
        phase = float(p["phase"])
        zig = int(p["zig"])
        wobble = amp * math.sin(u * math.pi * freq + phase) * zig
        return px * wobble, py * wobble

    def _drone_colors(self, n: int) -> list[tuple[int, int, int]]:
        palette = (
            (255, 99, 99),
            (99, 200, 255),
            (255, 220, 99),
            (180, 120, 255),
            (99, 255, 180),
            (255, 140, 220),
            (220, 220, 120),
            (120, 255, 255),
        )
        return [palette[i % len(palette)] for i in range(n)]

    def _draw_drones_buf(
        self,
        buf: pygame.Surface,
        pos_buf: dict[str, tuple[int, int]],
        drone_buf_xy: dict[str, tuple[float, float]],
        tick: int,
        cell: int,
    ) -> None:
        colors = self._drone_colors(self.parser.nb_drones)
        radius = max(2, min(5, (cell + 6) // 4))
        for i in range(self.parser.nb_drones):
            did = f"drone{i}"
            if did not in drone_buf_xy:
                continue
            x, y = drone_buf_xy[did]
            ix, iy = int(round(x)), int(round(y))
            c = colors[i]
            core = (
                min(255, c[0] + 35 + (tick // 4 + i * 7) % 25),
                min(255, c[1] + 35 + (tick // 5 + i * 5) % 25),
                min(255, c[2] + 30 + (tick // 6 + i * 3) % 25),
            )
            pygame.draw.circle(buf, core, (ix, iy), radius)
            pygame.draw.circle(buf, (255, 255, 255), (ix, iy), radius, width=1)
            pygame.draw.circle(buf, (12, 10, 20), (ix, iy), max(1, radius - 1), width=1)

    def _draw_drones_screen_overlay(
        self,
        map_rect: pygame.Rect,
        bw: int,
        bh: int,
        drone_buf_xy: dict[str, tuple[float, float]],
        cell: int,
    ) -> None:
        """Second pass on screen space so drones stay visible after pixel-scale."""
        colors = self._drone_colors(self.parser.nb_drones)
        r_screen = max(5, min(14, int(map_rect.width / max(bw, 1) * max(2, min(5, (cell + 6) // 4)) + 3)))
        for i in range(self.parser.nb_drones):
            did = f"drone{i}"
            if did not in drone_buf_xy:
                continue
            bx, by = drone_buf_xy[did]
            sx = map_rect.left + int(bx * map_rect.width / max(bw, 1))
            sy = map_rect.top + int(by * map_rect.height / max(bh, 1))
            c = colors[i]
            hi = (
                min(255, c[0] + 50),
                min(255, c[1] + 50),
                min(255, c[2] + 45),
            )
            pygame.draw.circle(self.screen, hi, (sx, sy), r_screen)
            pygame.draw.circle(self.screen, c, (sx, sy), max(2, r_screen - 2))
            pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), r_screen, width=2)
            pygame.draw.circle(self.screen, (18, 16, 28), (sx, sy), max(2, r_screen - 3), width=1)
            lab = self.small_font.render(str(i), True, (255, 255, 255))
            lr = lab.get_rect(center=(sx, sy))
            self.screen.blit(lab, (lr.x + 1, lr.y + 1))
            self.screen.blit(lab, lr)

    def _compose_frame(
        self,
        turn_index: int,
        phase_label: str,
        drone_buf_xy: dict[str, tuple[float, float]],
        *,
        show_legend: bool = True,
    ) -> None:
        tick = pygame.time.get_ticks()
        zones, map_rect, bw, bh, cell, pos_buf = self._layout_pack()

        self.screen.fill((18, 22, 38))
        buf = pygame.Surface((bw, bh))
        PixelRenderer.draw_pixel_scene_sky_only(buf, tick)

        if not zones:
            t = self.hud_sub.render("No zones loaded.", True, (255, 240, 230))
            self.screen.blit(t, (24, 24))
            pygame.display.flip()
            return

        zone_by_name = {z.name: z for z in zones}
        line_w = max(1, min(2, 1 + cell // 14))

        for zone in zones:
            start = pos_buf.get(zone.name)
            if start is None:
                continue
            for ei, target in enumerate(getattr(zone, "connections", []) or []):
                if target not in zone_by_name:
                    continue
                end = pos_buf.get(target)
                if end is None:
                    continue
                col = CONNECTION_PALETTE[ei % len(CONNECTION_PALETTE)]
                PixelRenderer.draw_connection_line(buf, start, end, col, width=line_w)

        pw = max(6, min(14, cell + 2))
        ph = max(5, min(11, cell))
        for zone in zones:
            bx, by = pos_buf[zone.name]
            accent = self._accent(zone, tick)
            PixelRenderer.draw_zone_node(buf, zone, bx, by, pw, ph, accent, tick)

        self._draw_drones_buf(buf, pos_buf, drone_buf_xy, tick, cell)

        scaled = PixelRenderer.nearest_scale(buf, map_rect.width, map_rect.height)
        self.screen.blit(scaled, map_rect.topleft)
        self._draw_drones_screen_overlay(map_rect, bw, bh, drone_buf_xy, cell)
        pygame.draw.rect(self.screen, (120, 140, 200), map_rect, 2)

        screen_cell = max(8, int(cell * map_rect.width / max(bw, 1)))
        label_size = max(10, min(20, screen_cell // 2 + 6))
        if label_size != getattr(self, "_last_label_size", None):
            self._last_label_size = label_size
            self.map_label_font = self._sys_font(label_size, bold=True)

        if zones and pos_buf:
            screen_pw = max(8, int(pw * map_rect.width / bw))
            screen_ph = max(6, int(ph * map_rect.height / bh))
            for zone in zones:
                bx, by = pos_buf[zone.name]
                sx, sy = MapLayout.buf_to_screen(map_rect, bx, by)

                hub = getattr(zone, "hub_kind", None)
                tag = ""
                if isinstance(hub, str):
                    tag = {"start": "S", "end": "Z", "waypoint": "W"}.get(hub, "")
                if tag:
                    tag_surface = self.zone_tag_font.render(tag, True, (255, 255, 255))
                    tag_rect = tag_surface.get_rect(
                        center=(sx - screen_pw // 2 + max(8, screen_pw // 4), sy - screen_ph // 2 + 8)
                    )
                    outline = self.zone_tag_font.render(tag, True, (12, 10, 18))
                    for ox, oy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                        self.screen.blit(outline, (tag_rect.x + ox, tag_rect.y + oy))
                    self.screen.blit(tag_surface, tag_rect)

                name_s = zone.name
                if len(name_s) > 18:
                    name_s = name_s[:16] + "…"
                label = self.map_label_font.render(name_s, True, (248, 250, 252))
                label_rect = label.get_rect(center=(sx, sy + screen_ph // 2 + max(10, label_size)))
                outline_label = self.map_label_font.render(name_s, True, (10, 12, 24))
                for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
                    self.screen.blit(outline_label, (label_rect.x + ox, label_rect.y + oy))
                self.screen.blit(label, label_rect)

                zt = getattr(zone, "zone_type", "normal") or "normal"
                if zt != "normal" or hub == "end":
                    sub = f"{zt}" if hub != "end" else "Goal"
                    sm = self.small_font.render(sub, True, (210, 220, 245))
                    sm_r = sm.get_rect(center=(sx, label_rect.bottom + max(6, label_size // 2)))
                    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        o = self.small_font.render(sub, True, (15, 15, 25))
                        self.screen.blit(o, (sm_r.x + ox, sm_r.y + oy))
                    self.screen.blit(sm, sm_r)

        lx, ly = 10, 10
        turn_text = f"Turn {turn_index}"
        title = self.turn_hud_main.render(turn_text, True, (248, 250, 255))
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
            o = self.turn_hud_main.render(turn_text, True, (8, 10, 22))
            self.screen.blit(o, (lx + ox, ly + oy))
        self.screen.blit(title, (lx, ly))
        sy = ly + title.get_height() + 2
        sub = self.turn_hud_phase.render(phase_label, True, (200, 210, 235))
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            o2 = self.turn_hud_phase.render(phase_label, True, (6, 8, 18))
            self.screen.blit(o2, (lx + ox, sy + oy))
        self.screen.blit(sub, (lx, sy))

        if show_legend:
            self._draw_legend_bottom_right()

        pygame.display.flip()

    def _build_drone_xy_static(self, pos_buf: dict[str, tuple[int, int]]) -> dict[str, tuple[float, float]]:
        by_zone = self._drones_by_zone()
        loc = self._drone_zone_map()
        out: dict[str, tuple[float, float]] = {}
        for i in range(self.parser.nb_drones):
            did = f"drone{i}"
            mid = self._buf_xy_transit(did, pos_buf)
            if mid is not None:
                out[did] = mid
                continue
            z = loc.get(did)
            if z and z in pos_buf:
                x, y = self._buf_pos_for_drone(did, pos_buf, by_zone, z)
                out[did] = (x, y)
        return out

    def _build_drone_xy_animating(
        self,
        pos_buf: dict[str, tuple[int, int]],
        proposals: dict[str, tuple[str | None, str | None]],
        u: float,
    ) -> dict[str, tuple[float, float]]:
        by_zone = self._drones_by_zone()
        loc = self._drone_zone_map()
        incoming: dict[str, list[str]] = defaultdict(list)
        for did, proposal in proposals.items():
            if proposal and proposal[0] and proposal[1] and proposal[0] != proposal[1]:
                incoming[str(proposal[1])].append(did)
        for k in incoming:
            incoming[k].sort()

        out: dict[str, tuple[float, float]] = {}
        uu = Game._smootherstep(u)
        for i in range(self.parser.nb_drones):
            did = f"drone{i}"
            mid = self._buf_xy_transit(did, pos_buf)
            if mid is not None:
                out[did] = mid
                continue
            pr = proposals.get(did)
            if pr and pr[0] and pr[1]:
                src, dst = pr[0], pr[1]
                if src in pos_buf and dst in pos_buf and src != dst:
                    sx, sy = pos_buf[src]
                    ex, ey = pos_buf[dst]
                    bx0, by0 = self._buf_pos_for_drone(did, pos_buf, by_zone, src)
                    lst = incoming.get(dst, [did])
                    idx = lst.index(did) if did in lst else 0
                    n = max(len(lst), 1)
                    ang = math.tau * idx / n
                    r = 3.5 if n > 1 else 2.0
                    ox, oy = self.drone_base_off.get(did, (0, 0))
                    bx1 = ex + r * math.cos(ang) + ox
                    by1 = ey + r * math.sin(ang) + oy
                    x = bx0 + (bx1 - bx0) * uu
                    y = by0 + (by1 - by0) * uu
                    fox, foy = self._flight_offset(did, uu, float(sx), float(sy), float(ex), float(ey))
                    out[did] = (x + fox, y + foy)
                    continue
            z = loc.get(did)
            if z and z in pos_buf:
                x, y = self._buf_pos_for_drone(did, pos_buf, by_zone, z)
                out[did] = (x, y)
        return out

    def show_state(self, turn_index: int, phase_label: str = "State") -> bool:
        if not self.running:
            return False
        _, _, _, _, _, pos_buf = self._layout_pack()
        xy = self._build_drone_xy_static(pos_buf)
        self._compose_frame(turn_index, phase_label, xy)
        return True

    def play_turn_animation(
        self,
        turn_index: int,
        proposals: dict[str, tuple[str | None, str | None]],
        apply_callback: Callable[[], None],
        duration_ms: int = 520,
    ) -> bool:
        """Visual glide, then apply_callback updates parser state."""
        if not self.running:
            return False
        t0 = pygame.time.get_ticks()
        while pygame.time.get_ticks() - t0 < duration_ms:
            if not self.pump_events():
                return False
            u = (pygame.time.get_ticks() - t0) / float(duration_ms)
            u = min(1.0, u)
            _, _, _, _, _, pos_buf = self._layout_pack()
            xy = self._build_drone_xy_animating(pos_buf, proposals, u)
            phase = "Moving…" if u < 0.98 else "Applying turn"
            self._compose_frame(turn_index, phase, xy)
            self.clock.tick(144)

        apply_callback()
        self.show_state(turn_index, "Turn applied")
        settle = pygame.time.get_ticks()
        while pygame.time.get_ticks() - settle < 90:
            if not self.pump_events():
                return False
            self.clock.tick(90)
        return True

    def run(self) -> None:
        while self.running:
            if not self.pump_events():
                break
            self.show_state(0, "Pygame view — use Main for simulation")
            self.clock.tick(60)
        pygame.quit()

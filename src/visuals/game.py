from __future__ import annotations

from typing import Any

import pygame

from .helpers import color_from_map_value
from .layout import (
    buf_to_screen,
    cell_positions_buffer,
    compute_initial_size,
    extract_zones,
    layout_rects,
    map_buffer_size,
)
from .pixel_render import (
    draw_bridge_line,
    draw_floating_platform,
    draw_pixel_scene_base,
    nearest_scale,
)
from .style import BASE_WINDOW, GRASS_TOP, MAP_MARGIN, PIXEL_SCALE


class Game:
    def __init__(
        self,
        parser_instance: Any = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        pygame.init()
        self.parser = parser_instance
        self.clock = pygame.time.Clock()
        self.running = True

        zones = extract_zones(self.parser)
        default_w, default_h = compute_initial_size(zones, BASE_WINDOW)
        w = max(BASE_WINDOW[0], width if width is not None else default_w)
        h = max(BASE_WINDOW[1], height if height is not None else default_h)

        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        pygame.display.set_caption("Fly-in - Map")
        self.width, self.height = self.screen.get_size()

        self.small_font = self._sys_font(13, bold=False)
        self.map_label_font = self._sys_font(14, bold=True)

    def _sys_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        for name in ("Segoe UI", "Helvetica Neue", "Arial Unicode MS", "Arial"):
            font = pygame.font.SysFont(name, size, bold=bold)
            if font:
                return font
        return pygame.font.Font(None, size)

    def draw(self) -> None:
        zones = extract_zones(self.parser)
        map_rect = layout_rects(self.width, self.height)
        tick = pygame.time.get_ticks()

        self.screen.fill((28, 24, 22))
        bw, bh = map_buffer_size(map_rect)
        margin_buf = max(4, MAP_MARGIN // PIXEL_SCALE)

        buf = pygame.Surface((bw, bh))
        draw_pixel_scene_base(buf, tick)

        pos_buf: dict[str, tuple[int, int]] = {}
        cell = 6
        pw = 10
        ph = 8
        if not zones:
            msg_buf = pygame.font.Font(None, 14).render("No zones loaded.", True, (255, 240, 220))
            buf.blit(msg_buf, (margin_buf, margin_buf))
        else:
            cell, pos_buf = cell_positions_buffer(zones, bw, bh, margin_buf)
            pw = max(8, min(16, cell + 2))
            ph = max(6, min(12, cell - 1))
            zone_by_name = {zone.name: zone for zone in zones}

            for zone in zones:
                if not hasattr(zone, "connections"):
                    continue
                start = pos_buf.get(zone.name)
                if start is None:
                    continue
                for target in zone.connections:
                    if target not in zone_by_name:
                        continue
                    end = pos_buf.get(target)
                    if end is None:
                        continue
                    draw_bridge_line(buf, start, end)

            for zone in zones:
                bx, by = pos_buf[zone.name]
                accent = color_from_map_value(getattr(zone, "color", None))
                top_tint = (
                    min(255, int(accent[0] * 0.55 + GRASS_TOP[0] * 0.45)),
                    min(255, int(accent[1] * 0.55 + GRASS_TOP[1] * 0.45)),
                    min(255, int(accent[2] * 0.55 + GRASS_TOP[2] * 0.45)),
                )
                draw_floating_platform(buf, bx, by, pw, ph, top_tint)

        scaled = nearest_scale(buf, map_rect.width, map_rect.height)
        self.screen.blit(scaled, map_rect.topleft)
        pygame.draw.rect(self.screen, (48, 42, 38), map_rect, 2)

        if zones and pos_buf:
            screen_pw = max(8, int(pw * map_rect.width / bw))
            screen_ph = max(6, int(ph * map_rect.height / bh))
            for zone in zones:
                bx, by = pos_buf[zone.name]
                sx, sy = buf_to_screen(map_rect, bx, by)

                hub = getattr(zone, "hub_kind", None)
                tag = ""
                if isinstance(hub, str):
                    tag = {"start": "S", "end": "Z", "waypoint": "W"}.get(hub, "")
                if tag:
                    tag_surface = self.small_font.render(tag, True, (255, 255, 255))
                    tag_rect = tag_surface.get_rect(
                        center=(sx - screen_pw // 2 + 10, sy - screen_ph // 2 + 10)
                    )
                    outline = self.small_font.render(tag, True, (20, 18, 16))
                    self.screen.blit(outline, (tag_rect.x + 1, tag_rect.y + 1))
                    self.screen.blit(tag_surface, tag_rect)

                label = self.map_label_font.render(zone.name, True, (248, 250, 252))
                label_rect = label.get_rect(center=(sx, sy + screen_ph // 2 + 12))
                outline_label = self.map_label_font.render(zone.name, True, (18, 16, 20))
                for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    self.screen.blit(outline_label, (label_rect.x + ox, label_rect.y + oy))
                self.screen.blit(label, label_rect)

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    size = event.size if hasattr(event, "size") else (event.w, event.h)
                    self.width = max(BASE_WINDOW[0], int(size[0]))
                    self.height = max(BASE_WINDOW[1], int(size[1]))
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

            self.draw()
            self.clock.tick(60)

        pygame.quit()

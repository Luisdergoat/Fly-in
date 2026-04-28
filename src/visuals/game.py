import math
import pygame


class Game:
    def __init__(self, parser_instance=None, width=1100, height=700):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fly-in Visual Map")
        self.clock = pygame.time.Clock()
        self.running = True

        self.width = width
        self.height = height
        self.parser = parser_instance
        self.margin = 70
        self.pixel_size = 4
        self.zone_radius = 18 // self.pixel_size
        self.render_width = max(1, self.width // self.pixel_size)
        self.render_height = max(1, self.height // self.pixel_size)
        self.render_surface = pygame.Surface((self.render_width, self.render_height))
        self.font = pygame.font.SysFont("arial", max(8, 16 // self.pixel_size), bold=True)
        self.small_font = pygame.font.SysFont("arial", max(8, 12 // self.pixel_size))

        # Begrenzte Palette fuer klaren 8-Bit-Look.
        self.palette = {
            "water_0": (26, 75, 140),
            "water_1": (34, 92, 168),
            "water_2": (20, 58, 112),
            "foam": (188, 222, 255),
            "line": (225, 236, 255),
            "sand": (225, 198, 123),
            "grass": (88, 162, 88),
            "outline": (32, 44, 32),
            "text_dark": (20, 20, 24),
            "text_light": (246, 246, 250),
        }
        self.connection_color = self.palette["line"]

    def _extract_zones(self):
        if self.parser is None or not hasattr(self.parser, "vars"):
            return []

        vars_data = getattr(self.parser, "vars", {})
        if not isinstance(vars_data, dict):
            return []

        zones = []
        for value in vars_data.values():
            if hasattr(value, "x") and hasattr(value, "y"):
                zones.append(value)
        return zones

    def _compute_screen_positions(self, zones):
        if not zones:
            return {}

        min_x = min(zone.x for zone in zones)
        max_x = max(zone.x for zone in zones)
        min_y = min(zone.y for zone in zones)
        max_y = max(zone.y for zone in zones)

        dx = max(max_x - min_x, 1)
        dy = max(max_y - min_y, 1)

        scaled_margin = max(6, self.margin // self.pixel_size)
        usable_w = self.render_width - (scaled_margin * 2)
        usable_h = self.render_height - (scaled_margin * 2)

        positions = {}
        for zone in zones:
            nx = (zone.x - min_x) / dx
            ny = (zone.y - min_y) / dy
            px = scaled_margin + int(nx * usable_w)
            py = scaled_margin + int(ny * usable_h)
            positions[zone.name] = (px, py)
        return positions

    def _draw_animated_water(self, t):
        # Pixelwasser mit Schachmuster + diskreten Wellen-Phasen.
        block = 2
        phase = int(t // 140) % 3
        for y in range(0, self.render_height, block):
            for x in range(0, self.render_width, block):
                noise = (x // block + y // block + phase) % 3
                if noise == 0:
                    color = self.palette["water_0"]
                elif noise == 1:
                    color = self.palette["water_1"]
                else:
                    color = self.palette["water_2"]
                self.render_surface.fill(color, (x, y, block, block))

        # Wenige helle Pixelreihen als "Schaum" fuer 8-Bit-Animation.
        for row in range(2, self.render_height, 9):
            for x in range(0, self.render_width, 3):
                wave = math.sin((x * 0.33) + (row * 0.2) + (phase * 1.3))
                if wave > 0.82:
                    self.render_surface.fill(self.palette["foam"], (x, row, 1, 1))

    def _draw_connections(self, zones, positions):
        zone_by_name = {zone.name: zone for zone in zones}
        for zone in zones:
            if not hasattr(zone, "connections"):
                continue
            start_pos = positions.get(zone.name)
            if start_pos is None:
                continue
            for target_name in zone.connections:
                if target_name not in zone_by_name:
                    continue
                end_pos = positions.get(target_name)
                if end_pos is None:
                    continue
                pygame.draw.line(self.render_surface, self.connection_color, start_pos, end_pos, 1)

    def _draw_islands(self, zones, positions):
        for zone in zones:
            px, py = positions[zone.name]
            r_outer = self.zone_radius + 3
            r_inner = self.zone_radius

            # Pixel-Insel als kantige 8-Bit-Fliese.
            pygame.draw.rect(
                self.render_surface,
                self.palette["sand"],
                (px - r_outer, py - r_outer, r_outer * 2, r_outer * 2),
            )
            pygame.draw.rect(
                self.render_surface,
                self.palette["grass"],
                (px - r_inner, py - r_inner, r_inner * 2, r_inner * 2),
            )
            pygame.draw.rect(
                self.render_surface,
                self.palette["outline"],
                (px - r_outer, py - r_outer, r_outer * 2, r_outer * 2),
                1,
            )

            name_surface = self.font.render(zone.name, True, self.palette["text_dark"])
            name_rect = name_surface.get_rect(center=(px, py - 1))
            self.render_surface.blit(name_surface, name_rect)

            zone_type = getattr(zone, "zone_type", "normal")
            info_surface = self.small_font.render(str(zone_type), True, self.palette["text_light"])
            info_rect = info_surface.get_rect(center=(px, py + self.zone_radius + 4))
            self.render_surface.blit(info_surface, info_rect)

    def draw(self):
        zones = self._extract_zones()
        t = pygame.time.get_ticks()
        self._draw_animated_water(t)

        if not zones:
            msg = "Keine Zonen in parser.vars gefunden."
            text = self.font.render(msg, True, self.palette["text_light"])
            self.render_surface.blit(text, (8, 8))
            scaled = pygame.transform.scale(self.render_surface, (self.width, self.height))
            self.screen.blit(scaled, (0, 0))
            pygame.display.flip()
            return

        positions = self._compute_screen_positions(zones)
        self._draw_connections(zones, positions)
        self._draw_islands(zones, positions)

        scaled = pygame.transform.scale(self.render_surface, (self.width, self.height))
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False

            self.draw()
            self.clock.tick(60)

        pygame.quit()

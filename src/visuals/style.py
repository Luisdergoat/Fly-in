from __future__ import annotations

Color = tuple[int, int, int]

OUTER_MARGIN = 16
MAP_MARGIN = 24
MIN_CELL = 30
MAX_CELL = 90
BASE_WINDOW = (1100, 760)
PIXEL_SCALE = 3

SKY_TOP: Color = (175, 72, 38)
SKY_MID: Color = (230, 120, 58)
SKY_HORIZON: Color = (255, 214, 150)
CLOUD: Color = (255, 198, 145)

ROCK_DARK: Color = (62, 58, 72)
ROCK_MID: Color = (88, 82, 98)
ROCK_LIGHT: Color = (118, 112, 128)

GRASS_TOP: Color = (255, 168, 72)
GRASS_HI: Color = (255, 224, 120)

BRIDGE: Color = (130, 78, 48)
BRIDGE_HI: Color = (200, 140, 88)

FOREST_SOIL_DARK: Color = (64, 52, 36)
FOREST_SOIL_MID: Color = (88, 70, 45)
FOREST_SOIL_LIGHT: Color = (112, 92, 60)
FOREST_GRASS_DARK: Color = (52, 98, 50)
FOREST_GRASS_MID: Color = (74, 132, 62)
FOREST_GRASS_LIGHT: Color = (102, 168, 78)

BAYER_4: tuple[tuple[int, ...], ...] = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)

MAP_COLORS: dict[str, Color] = {
    "green": (72, 168, 92),
    "blue": (66, 133, 244),
    "red": (234, 67, 53),
    "yellow": (251, 188, 5),
    "orange": (255, 152, 0),
    "purple": (142, 68, 173),
    "cyan": (0, 188, 212),
    "magenta": (233, 30, 99),
    "white": (236, 240, 241),
    "gray": (149, 165, 166),
    "grey": (149, 165, 166),
    "black": (40, 44, 52),
}

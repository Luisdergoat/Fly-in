from __future__ import annotations

import sys

from src.main import Main


def parse_args(argv: list[str]) -> tuple[str | None, bool]:
    """Split argv into (map_path, capacity_info).

    Any argument equal to "--capacity-info" (or "capacity-info", the
    dash-free form make's own arg parser lets through) enables capacity
    info. The first remaining argument is treated as the map path.
    """
    capacity_info = False
    map_path = None
    for arg in argv:
        if arg in ("--capacity-info", "capacity-info"):
            capacity_info = True
        elif map_path is None:
            map_path = arg
    return map_path, capacity_info


if __name__ == "__main__":
    map_path, capacity_info = parse_args(sys.argv[1:])
    start = Main(map_path, capacity_info=capacity_info)
    start.run()

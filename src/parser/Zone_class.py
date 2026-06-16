from __future__ import annotations

from typing import Optional


class zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: str,
        color: Optional[str],
        max_drones: int,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.drones: list[str] = []
        self.connections: list[str] = []
        self.pending_incoming: int = 0
        self.link_capacity: dict[str, int] = {}

    def add_drone(self, drone_id: str) -> bool:
        if len(self.drones) < self.max_drones:
            self.drones.append(drone_id)
            return True
        else:
            print(f"Cannot add drone {drone_id} to {self.name}: "
                  f"max capacity reached")
            return False

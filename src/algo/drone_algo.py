try:
    from .parser.parser import parser
    from .visuals.game import Game
    from .algo.drone_algo import drone_algo
    from .algo.swap_zones import swap_zones
except ImportError:
    from src.parser.parser import parser
    from src.visuals.game import Game
    from src.algo.drone_algo import drone_algo
    from src.algo.swap_zones import swap_zones

class drone_algo:
    def __init__(self, parse_instance):
        self.parse_instance = parse_instance

    def check_next_move(self, drone_id, current_zone, next_zone):
        if current_zone.zone_type == "no_fly":
            print(f"Drone {drone_id} cannot move from {current_zone.name} to {next_zone.name}: current zone is no-fly")
            return False
        if next_zone.zone_type == "no_fly":
            print(f"Drone {drone_id} cannot move from {current_zone.name} to {next_zone.name}: next zone is no-fly")
            return False
        if hasattr(next_zone, "drones") and len(next_zone.drones) >= next_zone.max_drones:
            print(f"Drone {drone_id} cannot move from {current_zone.name} to {next_zone.name}: next zone is at max capacity")
            return False
        return True

    def move_drone(self, drone_id, current_zone_name, next_zone_name):
        if current_zone_name not in self.parse_instance.vars or next_zone_name not in self.parse_instance.vars:
            print("One or both zones not found")
            return False

        current_zone = self.parse_instance.vars[current_zone_name]
        next_zone = self.parse_instance.vars[next_zone_name]
        if self.check_next_move(drone_id, current_zone, next_zone) is False:
            return False

        # move the drone
        if hasattr(current_zone, "drones") and drone_id in current_zone.drones:
            current_zone.drones.remove(drone_id)
            next_zone.drones = getattr(next_zone, "drones", []) + [drone_id]
            print(f"Drone {drone_id} moved from {current_zone.name} to {next_zone.name}")
            return True
        else:
            print(f"Drone {drone_id} not found in current zone {current_zone.name}")
            return False

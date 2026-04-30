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


class swap_zones:
    def __init__(self, parse_instance):
        self.parse_instance = parse_instance

    def swap(self, zone_name1, zone_name2):
        if zone_name1 not in self.parse_instance.vars or zone_name2 not in self.parse_instance.vars:
            print("One or both zones not found")
            return False

        zone1 = self.parse_instance.vars[zone_name1]
        zone2 = self.parse_instance.vars[zone_name2]

        # Swap the Drones to diffrent Zone
        if hasattr(zone1, "drones"):
            if zone2.max_drones == hasattr(zone2, "drones"):
                print("Zone 2 is at max capacity")
                return False
            else:
                zone2.drones = getattr(zone2, "drones", []) + getattr(zone1, "drones", [])
                delattr(zone1, "drones")
        elif hasattr(zone2, "drones"):
            print("cannot swap, from zone2 to zone 1, wrong direction")
            return False


    def check_zone_type(self, zone_name):

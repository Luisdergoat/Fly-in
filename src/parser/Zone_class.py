class zone:
    def __init__(self, name, x, y, zone_type, color, max_drones):
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones
        self.drones = []  # Drohnen auf der Zone, nicht groesser als max_drones
        self.connections: list[str] = []
        # Drones committed to arrive next turn (restricted 2-step move); counts toward capacity.
        self.pending_incoming: int = 0
        # target_zone_name -> max drones using this directed edge per turn (None = unlimited)
        self.link_capacity: dict[str, int] = {}

    def add_drone(self, drone_id):
        if len(self.drones) < self.max_drones:
            self.drones.append(drone_id)
            return True
        else:
            print(f"Cannot add drone {drone_id} to {self.name}: max capacity reached")
            return False

class zone:
    def __init__(self, name, x, y, zone_type="normal", color=None, max_drones=1):
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

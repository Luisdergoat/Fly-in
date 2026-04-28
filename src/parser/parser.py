from .Zone_class import zone


class parser:
    def __init__(self):
        self.seen_start_hub = False
        self.seen_end_hub = False
        self.vars = {}
        self.nb_drones = 0

    def _parse_zone_definition(self, line):
        if "[" in line:
            main, meta = line.split("[", 1)
            meta = meta.strip("] ")
        else:
            main = line
            meta = ""

        try:
            parts = main.split()
            name = parts[1]
            x = int(parts[2])
            y = int(parts[3])
        except Exception:
            print("The Values must be {int}")
            return None

        zone_type = "normal"
        color = None
        max_drones = 1

        if meta:
            for item in meta.split():
                if "=" not in item:
                    continue
                key, value = item.split("=", 1)
                if key == "zone":
                    zone_type = value
                elif key == "color":
                    color = value
                elif key == "max_drones":
                    try:
                        max_drones = int(value)
                    except ValueError:
                        print("max_drones must be an integer")
                        return None

        return zone(name, x, y, zone_type, color, max_drones)

    def parse(self, file_path):
        if file_path is None:
            print("No file path provided")
            return False
        with open(file_path, 'r') as f:
            data = f.readlines()
            for line in data:
                if line.startswith('#') or line.startswith('//'):
                    continue
                if line.strip() == '':
                    continue
                line = line.strip()
                if self.parse_line(line) is False:
                    return False
        return True

    def parse_line(self, line):
        if line.startswith("nb_drones:"):

            try:

                nb_drones = int(line.split(":")[1].strip())
                self.nb_drones = nb_drones

            except ValueError:
                print("nb_drones must be an integer")
                return False

        elif line.startswith("start_hub:"):
            if self.seen_start_hub is True:
                print("Only one start_hub is allowed")
                return False
            self.seen_start_hub = True
            parsed_zone = self._parse_zone_definition(line)
            if parsed_zone is None:
                return False
            parsed_zone.hub_kind = "start"
            self.vars["Zone_" + parsed_zone.name] = parsed_zone

        elif line.startswith("end_hub:"):
            if self.seen_end_hub is True:
                print("Only one end_hub is allowed")
                return False
            self.seen_end_hub = True
            parsed_zone = self._parse_zone_definition(line)
            if parsed_zone is None:
                return False
            parsed_zone.hub_kind = "end"
            self.vars["Zone_" + parsed_zone.name] = parsed_zone
            return True
        elif line.startswith("hub:"):
            parsed_zone = self._parse_zone_definition(line)
            if parsed_zone is None:
                return False
            parsed_zone.hub_kind = "waypoint"
            self.vars["Zone_" + parsed_zone.name] = parsed_zone
            return True
        elif line.startswith("connection:"):
            connection_part = line.split(":", 1)[1].strip()
            if "-" not in connection_part:
                print("connection format must be: connection: A-B")
                return False
            start, end = [item.strip() for item in connection_part.split("-", 1)]
            connections = {start: end}
            return self.parse_map(self.vars, connections)

        else:
            print("Error while parsing")
            return False
        return True

    def parse_map(self, vars, connections):
        # hier muss ich die connections in die zones packen
        name_to_key = {value.name: key for key, value in vars.items()}

        for start, end in connections.items():
            start_key = name_to_key.get(start)
            end_key = name_to_key.get(end)
            if start_key and end_key:
                if not hasattr(vars[start_key], "connections"):
                    vars[start_key].connections = []
                vars[start_key].connections.append(end)

            else:
                print(f"Error: {start} or {end} not found in variables")
                return False
        return True

    def print_vars(self):
        if not self.vars:
            print("No zones parsed yet.")
            return
        for key, value in self.vars.items():
            print(f"{key}: {value.__dict__}")

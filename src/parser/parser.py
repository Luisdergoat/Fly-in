
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
        max_drones = 200

        if meta:
            try:
                from .Zone_class import zone
            except ImportError:
                from src.parser.Zone_class import zone
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

            try:
                return zone(name, x, y, zone_type, color, max_drones)
            except Exception as e:
                print(f"An Error has occured while creating the zone object: {e}")

    def parse(self, file_path):
        if file_path is None:
            print("No file path provided")
            return False
        try:
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
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return False

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
            self.vars[parsed_zone.name] = parsed_zone

        elif line.startswith("end_hub:"):
            if self.seen_end_hub is True:
                print("Only one end_hub is allowed")
                return False
            self.seen_end_hub = True
            parsed_zone = self._parse_zone_definition(line)
            if parsed_zone is None:
                return False
            parsed_zone.hub_kind = "end"
            self.vars[parsed_zone.name] = parsed_zone
            return True
        elif line.startswith("hub:"):
            parsed_zone = self._parse_zone_definition(line)
            if parsed_zone is None:
                return False
            parsed_zone.hub_kind = "waypoint"
            self.vars[parsed_zone.name] = parsed_zone
            return True
        elif line.startswith("connection:"):
            rest = line.split(":", 1)[1].strip()
            meta_str = ""
            if "[" in rest:
                main, meta_str = rest.split("[", 1)
                rest = main.strip()
                meta_str = meta_str.strip("] ")
            if "-" not in rest:
                print("connection format must be: connection: A-B")
                return False
            start, end = [item.strip() for item in rest.split("-", 1)]
            edge_meta = self._parse_connection_meta(meta_str)
            connections = {start: end}
            return self.parse_map(self.vars, connections, edge_meta)

        else:
            print("Error while parsing")
            return False
        return True

    def _parse_connection_meta(self, meta_str: str) -> dict:
        out: dict[str, str] = {}
        if not meta_str:
            return out
        for item in meta_str.split():
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            out[key.strip()] = value.strip()
        return out

    def place_drones(self):
        for i in range(self.nb_drones):
            drone_id = f"drone{i}"
            self.vars["start"].add_drone(drone_id)

    def parse_map(self, vars, connections, edge_meta: dict | None = None):
        # hier muss ich die connections in die zones packen
        edge_meta = edge_meta or {}
        name_to_key = {value.name: key for key, value in vars.items()}

        for start, end in connections.items():
            start_key = name_to_key.get(start)
            end_key = name_to_key.get(end)
            if start_key and end_key:
                if not hasattr(vars[start_key], "connections"):
                    vars[start_key].connections = []
                vars[start_key].connections.append(end)
                if "max_link_capacity" in edge_meta:
                    try:
                        cap = int(edge_meta["max_link_capacity"])
                        vars[start_key].link_capacity[end] = cap
                    except ValueError:
                        print("max_link_capacity must be an integer")
                        return False

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

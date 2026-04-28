class parser:
    def __init__(self):
        pass

    def parse(self, file_path):
        with open(file_path, 'r') as f:
            data = f.readlines()
            for line in data:
                if line.startswith('#') or line.startswith('//'):
                    continue
                if line.strip() == '':
                    continue
                line = line.strip()

    def parse_line(self, line):
        if line.startswith("nb_drones:"):

            nb = int(line.split(":")[1].strip())

        elif line.startswith("start_hub"):

            if "[" in line:
                main, meta = line.split("[")
                meta = main.strip("]")
            else:
                main = line
                meta = ""

            parts = main.split()
            try:

                name = parts[1]
                x = int(parts[2])
                y = int(parts[3])

            except Exception:
                print("The Values must be {int}")
                return

            zone_type = "normal"
            color = None
            max_drones = 1

        if meta:
            for item in meta.split():
                key, value = item.split("=")

                if key == "zone":
                    zone_type = value
                elif key == "color":
                    color = value
                elif key == "max_drones":

                    try:
                        max_drones = int(value)
                    except ValueError:
                        print("Max_drones musst be an {int}")
                        return

        elif line.startswith("end_hub:"):
            # auch gleicher shit
            return
        elif line.startswith("hub:"):
            # schere gleicher shit
            return
        elif line.startswith("connection:"):
            # kein plan was da rein soll omg
            return
        else:
            print("Error while parsing")
            return

class File_generator:
    def __init__(self, file_path):
        self.file_path = file_path
        self.turns = []

    def record_turn(self, moves_dict):
        """Record a turn's movements.
        moves_dict: {drone_id: destination_zone_name}
        Example: {'drone0': 'zone1', 'drone1': 'zone2'}
        """
        self.turns.append(moves_dict)

    def finalize(self):
        """Write all recorded turns to file in the exact output format."""
        try:
            with open(self.file_path, 'w') as f:
                for turn_moves in self.turns:
                    if not turn_moves:
                        continue

                    moves_list = []
                    for drone_id, zone_name in sorted(turn_moves.items()):
                        drone_num = drone_id.replace("drone", "")
                        moves_list.append(f"D{drone_num}-{zone_name}")

                    if moves_list:
                        f.write(" ".join(moves_list) + "\n")

        except IOError as e:
            print(f"Error writing to file: {e}")

    def create_file(self, counter):
        """Deprecated: use record_turn and finalize instead."""
        from src.parser.parser import parser
        try:
            with open(self.file_path, 'a') as f:
                for turn in parser.instance.vars:
                    if hasattr(parser.instance.vars[turn], "drones"):
                        for drone in parser.instance.vars[turn].drones:
                            f.write(f"{counter} {drone.name} {turn}\n")
        except IOError as e:
            print(f"Error writing to file: {e}")

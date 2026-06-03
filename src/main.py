import os


def _pygame_wait_quit(g, turn_index: int, subtitle: str = "Press Esc to close") -> None:
    import pygame

    t0 = pygame.time.get_ticks()
    while pygame.time.get_ticks() - t0 < 120_000 and g.running:
        if not g.pump_events():
            break
        g.show_state(turn_index, subtitle)
        g.clock.tick(20)
    pygame.quit()


class Main:
    def __init__(self, map):
        self.map = map
        pass

    def run(self) -> None:
        try:
            from .parser.parser import parser
            from .visuals.game import Game
            from .algo.drone_algo import drone_algo
            from .output_file.create_file import File_generator
        except ImportError:
            from src.parser.parser import parser
            from src.visuals.game import Game
            from src.algo.drone_algo import drone_algo
            from src.output_file.create_file import File_generator

        map_path = os.environ.get(
            "FLYIN_MAP",
            self.map,
        )
        if self.map is None and map_path is None:
            print(
                "No map provided. Please set the FLYIN_MAP environment "
                "variable or provide a map as a command-line argument.")
            return

        windowed = os.environ.get("FLYIN_WINDOWED", "").lower() in ("1", "true", "yes")
        verbose_print = os.environ.get("FLYIN_VERBOSE", "").lower() in ("1", "true", "yes")

        p = parser()
        if not p.parse(map_path):
            print(f"Failed to parse map: {map_path}")
            return
        p.place_drones()
        a = drone_algo(parser_instance=p)

        output_gen = File_generator("fly_in.txt")

        max_turns = int(os.environ.get("FLYIN_MAX_TURNS", "10000"))
        turn = 0

        print(f"Map: {map_path}  zones={len(p.vars)}  drones={p.nb_drones}")
        if "start" in p.vars and hasattr(p.vars["start"], "drones"):
            print("Start hub drone count:", len(p.vars["start"].drones))
        if verbose_print:
            p.print_vars()

        g = Game(p, fullscreen=not windowed, algo=a)
        a.begin_turn()
        if not g.wait_for_space_to_start():
            output_gen.finalize()
            print("Output written to fly_in.txt")
            import pygame

            pygame.quit()
            return

        while not a.all_drones_at_goal():
            turn += 1
            if turn > max_turns:
                print(f"\nStopped after {max_turns} turns (not all drones reached goal).")
                output_gen.finalize()
                print("Output written to fly_in.txt")
                g.show_state(turn, "Stopped — max turns")
                _pygame_wait_quit(g, turn, "Press Esc to close")
                return

            a.begin_turn()

            proposals: dict = {}
            for i in range(p.nb_drones):
                did = f"drone{i}"
                loc = a.current_zone_for_drone(did)
                if loc is None:
                    print(f"Drone {did} has no zone; skipping.")
                    continue
                zone = p.vars[loc]
                if getattr(zone, "hub_kind", None) == "end":
                    proposals[did] = (loc, loc)
                    continue
                nxt = a.decide_next_move(did, loc, quiet=True)
                if nxt is None:
                    proposals[did] = (loc, loc)
                else:
                    proposals[did] = (loc, nxt)

            turn_movements = {}
            for did, (src, dst) in proposals.items():
                if src != dst:
                    turn_movements[did] = dst

            if turn_movements:
                output_gen.record_turn(turn_movements)

            if not g.play_turn_animation(
                turn,
                proposals,
                lambda: a.apply_resolved_moves(proposals),
            ):
                print("Quit from visualization.")
                output_gen.finalize()
                print("Output written to fly_in.txt")
                import pygame

                pygame.quit()
                return

            if verbose_print or turn <= 2 or turn % 50 == 0:
                print(f"\n--- Turn {turn} ---")
                p.print_vars()

        os.system("clear")
        print(f"\nAll drones reached the goal in {turn} simulation round(s). Move units: {a.turn_units}")
        output_gen.finalize()
        print("Output written to fly_in.txt")
        g.show_state(turn, "")
        g.show_completion_splash(turn, a.turn_units)
        import pygame

        pygame.quit()

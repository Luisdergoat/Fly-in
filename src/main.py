class Main:
    def __init__(self):
        pass

    def run(self):
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
        p = parser()
        p.parse("maps/easy/01_linear_path.txt")
        p.print_vars()
        g = Game(parser_instance=p)
        g.run()
        a = drone_algo(parser_instance=p)
        s = swap_zones(parser_instance=p)
        a.move_drone("drone1", "hub_start", "zone1")
        s.swap("zone1", "zone2")

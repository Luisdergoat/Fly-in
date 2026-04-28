class Main:
    def __init__(self):
        pass

    def run(self):
        try:
            from .parser.parser import parser
            from .visuals.game import Game
        except ImportError:
            from src.parser.parser import parser
            from src.visuals.game import Game
        p = parser()
        p.parse("maps/challenger/01_the_impossible_dream.txt")
        p.print_vars()
        # g = Game(parser_instance=p)
        # g.run()

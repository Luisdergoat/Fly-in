if __name__ == "__main__":
    try:
        from src.main import Main
        import sys
        import os
    except ImportError:
        from main import Main
        import sys
        import os
    map = sys.argv[1] if len(sys.argv) > 1 else None
    start = Main(map)
    start.run()

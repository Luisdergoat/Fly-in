import sys

from src.main import Main


if __name__ == "__main__":
    map_path = sys.argv[1] if len(sys.argv) > 1 else None
    start = Main(map_path)
    start.run()

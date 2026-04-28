if __name__ == "__main__":
    try:
        from src.main import Main
    except ImportError:
        from main import Main
    start = Main()
    start.run()

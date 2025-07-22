if __name__ == '__main__':
    try:
        from .menu import menu_loop
    except ImportError:  # fall back when run as script
        from menu import menu_loop  # type: ignore
    menu_loop()

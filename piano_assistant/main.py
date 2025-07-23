from rich.console import Console
from rich.prompt import Prompt

console = Console()


def interactive_main():
    from . import menu
    while True:
        console.print("\n[bold cyan]Piano Assistant[/bold cyan]")
        console.print("[1] Convert Song")
        console.print("[2] Test Mode")
        console.print("[3] Play Song")
        console.print("[4] Exit")
        choice = Prompt.ask("Select option", choices=['1','2','3','4'])
        if choice == '1':
            menu.convert_menu()
        elif choice == '2':
            menu.test_menu()
        elif choice == '3':
            menu.play_menu()
        else:
            break


if __name__ == '__main__':
    from .cli import main as cli_main
    cli_main()

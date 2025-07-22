import os

from rich.console import Console
from rich.prompt import Prompt

from . import converter, player, tester
from .utils import list_music_files, show_files_table, OUTPUT_DIR

console = Console()


def select_source_file():
    files = list_music_files()
    if not files:
        console.print("[red]No music files found in source_files directory[/red]")
        return None
    show_files_table(files)
    choice = Prompt.ask("Select file", choices=[str(i) for i in range(1, len(files)+1)])
    return os.path.join(os.path.dirname(__file__), 'source_files', files[int(choice)-1])


def select_output_file():
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.txt')]
    if not files:
        console.print("[red]No converted files found[/red]")
        return None
    files.sort()
    show_files_table(files)
    choice = Prompt.ask("Select file", choices=[str(i) for i in range(1, len(files)+1)])
    return os.path.join(OUTPUT_DIR, files[int(choice)-1])


def convert_menu():
    src = select_source_file()
    if not src:
        return
    try:
        out_path = converter.convert(src)
    except ValueError as e:
        console.print(f"[red]Failed to convert:[/red] {e}")
        return
    console.print(f"Saved to [green]{out_path}[/green]")


def test_menu():
    song = select_output_file()
    if not song:
        return
    tester.test(song)


def play_menu():
    song = select_output_file()
    if not song:
        return
    player.play(song)

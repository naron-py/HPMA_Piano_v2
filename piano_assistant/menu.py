from __future__ import annotations
import os
from . import converter, player
from .utils import list_music_files, list_text_files, print_table, console

PROJECT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(PROJECT_DIR, 'source_files')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')


def menu_loop():
    while True:
        console.print("[bold magenta]Piano Assistant[/bold magenta]")
        console.print("[cyan]1.[/] Convert Song")
        console.print("[cyan]2.[/] Test Mode")
        console.print("[cyan]3.[/] Exit")
        choice = input("Select option: ").strip()
        if choice == '1':
            run_convert()
        elif choice == '2':
            run_test()
        elif choice == '3':
            break
        else:
            console.print("Invalid choice\n")


def run_convert():
    files = list_music_files(SOURCE_DIR)
    if not files:
        console.print("No source files found.")
        return
    print_table("Available Files", files)
    sel = input("Enter number to convert: ").strip()
    try:
        idx = int(sel) - 1
    except ValueError:
        console.print("Invalid selection")
        return
    if idx < 0 or idx >= len(files):
        console.print("Invalid selection")
        return
    path = os.path.join(SOURCE_DIR, files[idx])
    converter.convert_file(path, OUTPUT_DIR)


def run_test():
    files = list_text_files(OUTPUT_DIR)
    if not files:
        console.print("No converted songs found.")
        return
    print_table("Select Song", files)
    sel = input("Enter number to test: ").strip()
    try:
        idx = int(sel) - 1
    except ValueError:
        console.print("Invalid selection")
        return
    if idx < 0 or idx >= len(files):
        console.print("Invalid selection")
        return
    path = os.path.join(OUTPUT_DIR, files[idx])
    player.play_song(path, test_mode=True)

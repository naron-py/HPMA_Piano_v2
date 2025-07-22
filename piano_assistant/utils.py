import os
from datetime import datetime
from typing import List

from rich.console import Console
from rich.table import Table

SOURCE_DIR = os.path.join(os.path.dirname(__file__), 'source_files')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
console = Console()


def list_music_files() -> List[str]:
    files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.mid', '.mxl'))]
    files.sort()
    return files


def show_files_table(files: List[str]):
    table = Table(title='Available Files')
    table.add_column('Index')
    table.add_column('File')
    for i, f in enumerate(files, 1):
        table.add_row(str(i), f)
    console.print(table)


def timestamp() -> str:
    return datetime.now().strftime('%Y%m%d_%H%M%S')

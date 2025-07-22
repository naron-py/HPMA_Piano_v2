from __future__ import annotations
import os
import time
from typing import List
from rich.table import Table
from rich.console import Console

NOTE_NAME_TO_VALUE = {"C": "1", "D": "2", "E": "3", "F": "4", "G": "5", "A": "6", "B": "7"}
STANDARD_OCTAVE_TO_CUSTOM = {3: 1, 4: 2, 5: 3}

console = Console()

def list_music_files(directory: str) -> List[str]:
    if not os.path.exists(directory):
        return []
    files = []
    for f in os.listdir(directory):
        if f.lower().endswith(('.mid', '.midi', '.mxl', '.musicxml')):
            files.append(f)
    return sorted(files)

def list_text_files(directory: str) -> List[str]:
    if not os.path.exists(directory):
        return []
    return sorted([f for f in os.listdir(directory) if f.lower().endswith('.txt')])

def timestamped_filename(name: str) -> str:
    stamp = time.strftime('%Y%m%d_%H%M%S')
    base = os.path.splitext(os.path.basename(name))[0]
    return f"{base}_{stamp}.txt"

def print_table(title: str, items: List[str]) -> None:
    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("File")
    for i, f in enumerate(items, 1):
        table.add_row(str(i), f)
    console.print(table)

def pitch_to_key(note_name: str):
    # Convert e.g. C#4 to ('#1', octave)
    letter = note_name[0].upper()
    accidental = ''
    octave = int(note_name[-1])
    if len(note_name) > 2:
        accidental = note_name[1]
    value = NOTE_NAME_TO_VALUE.get(letter)
    if value is None:
        return None
    if accidental in ('#', '♯'):
        value = f"#{value}"
    elif accidental in ('-', 'b', '♭'):
        # flats -> previous note value (# of previous letter)
        mapping = ['1','2','3','4','5','6','7']
        idx = mapping.index(value)
        idx = (idx - 1) % len(mapping)
        value = f"#{mapping[idx]}"
    custom_octave = STANDARD_OCTAVE_TO_CUSTOM.get(octave)
    if custom_octave is None:
        # clamp to nearest
        if octave < 3:
            custom_octave = 1
        elif octave > 5:
            custom_octave = 3
    return value, custom_octave

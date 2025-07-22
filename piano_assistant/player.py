import time
from typing import List

import pyautogui

from .key_mapper import KEY_MAPPING


def _parse_note(note_str: str) -> str:
    name, octave = note_str.split('-')
    return KEY_MAPPING[(name, int(octave))]


def play(song_path: str):
    events = []
    with open(song_path) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            start, dur, notes = line.strip().split('\t')
            note_keys = [_parse_note(n) for n in notes.split('+')]
            events.append((float(start), float(dur), note_keys))
    events.sort(key=lambda x: x[0])
    start_time = time.time()
    for start, dur, keys in events:
        wait = start - (time.time() - start_time)
        if wait > 0:
            time.sleep(wait)
        for k in keys:
            pyautogui.keyDown(k)
        time.sleep(dur)
        for k in keys:
            pyautogui.keyUp(k)

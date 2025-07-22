import time
from typing import List

import pyautogui

from .key_mapper import KEY_MAPPING


def _parse_note(note_str: str) -> str:
    name, octave = note_str.split('-')
    return KEY_MAPPING[(name, int(octave))]


def play(song_path: str):
    """Play back a converted song file with support for overlapping notes."""
    events = []
    with open(song_path) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            start, dur, notes = line.strip().split('\t')
            note_keys = [_parse_note(n) for n in notes.split('+')]
            events.append((float(start), float(dur), note_keys))

    # Build key press/release actions so that notes starting at the same time
    # will overlap correctly instead of playing sequentially.
    actions: List[tuple[float, str, List[str]]] = []
    for start, dur, keys in events:
        actions.append((start, 'down', keys))
        actions.append((start + dur, 'up', keys))
    actions.sort(key=lambda x: x[0])

    start_time = time.time()
    pressed: dict[str, int] = {}

    for action_time, action, keys in actions:
        wait = action_time - (time.time() - start_time)
        if wait > 0:
            time.sleep(wait)
        for k in keys:
            if action == 'down':
                # Only press the key if it isn't already pressed.
                if pressed.get(k, 0) == 0:
                    pyautogui.keyDown(k)
                pressed[k] = pressed.get(k, 0) + 1
            else:
                # Only release when the last overlapping note finishes.
                count = pressed.get(k, 0)
                if count > 0:
                    if count == 1:
                        pyautogui.keyUp(k)
                    pressed[k] = count - 1

    # Ensure all keys are released at the end in case of any mismatch.
    for k, count in pressed.items():
        if count > 0:
            pyautogui.keyUp(k)

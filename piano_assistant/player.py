import time
from typing import List, Tuple

import pyautogui
from rich.console import Console

from .key_mapper import KEY_MAPPING

console = Console()


def _parse_note(note_str: str) -> str:
    name, octave = note_str.split('-')
    return KEY_MAPPING[(name, int(octave))]


def _read_song(song_path: str) -> Tuple[dict, List[Tuple[float, float]], List[Tuple[float, str]], List[Tuple[float, float, str]]]:
    """Parse a converted song file.

    Returns metadata, tempo events, time signature events and note events.
    """
    metadata: dict[str, str] = {}
    tempo_events: List[Tuple[float, float]] = []
    ts_events: List[Tuple[float, str]] = []
    events: List[Tuple[float, float, str]] = []

    with open(song_path) as f:
        for line in f:
            if line.startswith('#'):
                if line.startswith('# Tempo '):
                    rest = line[len('# Tempo '):].strip()
                    off_str, val = rest.split(':', 1)
                    bpm = float(val.replace('BPM', '').strip())
                    tempo_events.append((float(off_str), bpm))
                elif line.startswith('# TimeSignature '):
                    rest = line[len('# TimeSignature '):].strip()
                    off_str, val = rest.split(':', 1)
                    ts_events.append((float(off_str), val.strip()))
                elif ':' in line:
                    key, value = line[1:].split(':', 1)
                    metadata[key.strip()] = value.strip()
                continue
            if not line.strip():
                continue
            start, dur, notes = line.strip().split('\t')
            events.append((float(start), float(dur), notes))
    tempo_events.sort(key=lambda x: x[0])
    ts_events.sort(key=lambda x: x[0])
    return metadata, tempo_events, ts_events, events


def _beat_to_sec(beat: float, tempo_events: List[Tuple[float, float]], default_bpm: float = 120.0) -> float:
    """Convert a beat position to seconds according to tempo events."""
    tempo_events = sorted(tempo_events, key=lambda x: x[0])
    if tempo_events and tempo_events[0][0] > 0:
        # Insert an initial tempo if none exists at offset 0
        tempo_events = [(0.0, default_bpm)] + tempo_events
    elif not tempo_events:
        tempo_events = [(0.0, default_bpm)]

    sec = 0.0
    last_off, last_bpm = tempo_events[0]
    if beat < last_off:
        return (beat - 0) * 60.0 / last_bpm
    sec += (last_off - 0) * 60.0 / last_bpm
    for off, bpm in tempo_events[1:]:
        if beat < off:
            sec += (beat - last_off) * 60.0 / last_bpm
            return sec
        sec += (off - last_off) * 60.0 / last_bpm
        last_off, last_bpm = off, bpm
    sec += (beat - last_off) * 60.0 / last_bpm
    return sec


def play(song_path: str):
    """Play back a converted song file with support for overlapping notes."""
    metadata, tempo_events, ts_events, raw_events = _read_song(song_path)
    events: List[Tuple[float, float, List[str]]] = []
    for start, dur, notes in raw_events:
        note_keys = [_parse_note(n) for n in notes.split('+')]
        events.append((start, dur, note_keys))

    if metadata or tempo_events or ts_events:
        console.print("[bold]Song Info[/bold]")
        for key, val in metadata.items():
            console.print(f"{key}: {val}")
        for off, ts_val in ts_events:
            console.print(f"TimeSignature @ {off}: {ts_val}")
        for off, bpm in tempo_events:
            console.print(f"Tempo @ {off}: {int(bpm)} BPM")

    # Build key press/release actions so that notes starting at the same time
    # will overlap correctly instead of playing sequentially. Convert beat
    # positions to real seconds using the tempo map.
    actions: List[tuple[float, str, List[str]]] = []
    for start, dur, keys in events:
        start_sec = _beat_to_sec(start, tempo_events)
        end_sec = _beat_to_sec(start + dur, tempo_events)
        actions.append((start_sec, 'down', keys))
        actions.append((end_sec, 'up', keys))
    # Sort by time and ensure that releases happen before presses when
    # they share the same timestamp. This keeps rapid note repetitions
    # in sync between hands and prevents keys from remaining held down
    # when a new note should retrigger the same key.
    actions.sort(key=lambda x: (x[0], 0 if x[1] == 'up' else 1))

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

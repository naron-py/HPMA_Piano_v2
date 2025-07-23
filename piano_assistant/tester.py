import time

from typing import List, Tuple

from .key_mapper import KEY_MAPPING
from .tempo_utils import beat_to_sec


def _parse_note(note_str: str) -> str:
    name, octave = note_str.split('-')
    return KEY_MAPPING[(name, int(octave))]


def _read_song(song_path: str) -> Tuple[dict, List[Tuple[float, float]], List[Tuple[float, str]], List[Tuple[float, float, str]]]:
    """Parse a converted song file and return metadata, tempo events,
    time signature events, and note events."""
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




def test(song_path: str):
    """Print simulated key presses for a song, respecting overlapping notes and
    tempo changes."""
    metadata, tempo_events, ts_events, raw_events = _read_song(song_path)

    if metadata or tempo_events or ts_events:
        print("Song Info")
        for key, val in metadata.items():
            print(f"{key}: {val}")
        for off, ts in ts_events:
            print(f"TimeSignature @ {off}: {ts}")
        for off, bpm in tempo_events:
            print(f"Tempo @ {off}: {int(bpm)} BPM")

    actions = []
    for start, dur, notes in raw_events:
        keys = [_parse_note(n) for n in notes.split('+')]
        start_sec = beat_to_sec(start, tempo_events)
        end_sec = beat_to_sec(start + dur, tempo_events)
        actions.append((start_sec, 'down', notes, keys))
        actions.append((end_sec, 'up', notes, keys))
    # Sort so that key releases occur before presses at the same time.
    # This mirrors the behaviour of ``player.play`` and keeps
    # overlapping notes from drifting out of sync during rapid passages.
    actions.sort(key=lambda x: (x[0], 0 if x[1] == 'up' else 1))

    start_time = time.time()
    pressed: dict[str, int] = {}

    for action_time, action, note_str, keys in actions:
        wait = action_time - (time.time() - start_time)
        if wait > 0:
            time.sleep(wait)
        for k in keys:
            if action == 'down':
                if pressed.get(k, 0) == 0:
                    print(f"Press {k}")
                pressed[k] = pressed.get(k, 0) + 1
            else:
                count = pressed.get(k, 0)
                if count > 0:
                    if count == 1:
                        print(f"Release {k}")
                    pressed[k] = count - 1


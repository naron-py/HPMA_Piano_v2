import time

from .key_mapper import KEY_MAPPING


def _parse_note(note_str: str) -> str:
    name, octave = note_str.split('-')
    return KEY_MAPPING[(name, int(octave))]


def test(song_path: str):
    """Print simulated key presses for a song, respecting overlapping notes."""
    metadata: dict[str, str] = {}
    events = []
    with open(song_path) as f:
        for line in f:
            if line.startswith('#'):
                if ':' in line:
                    key, value = line[1:].split(':', 1)
                    metadata[key.strip()] = value.strip()
                continue
            if not line.strip():
                continue
            start, dur, notes = line.strip().split('\t')
            events.append((float(start), float(dur), notes))

    if metadata:
        print("Song Info")
        for key, val in metadata.items():
            print(f"{key}: {val}")

    actions = []
    for start, dur, notes in events:
        keys = [_parse_note(n) for n in notes.split('+')]
        actions.append((start, 'down', notes, keys))
        actions.append((start + dur, 'up', notes, keys))
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


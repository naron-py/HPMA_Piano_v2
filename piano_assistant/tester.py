import time

from .key_mapper import KEY_MAPPING


def _parse_note(note_str: str) -> str:
    name, octave = note_str.split('-')
    return KEY_MAPPING[(name, int(octave))]


def test(song_path: str):
    with open(song_path) as f:
        events = []
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            start, dur, notes = line.strip().split('\t')
            events.append((float(start), float(dur), notes))
    events.sort(key=lambda x: x[0])
    start_time = time.time()
    for start, dur, notes in events:
        wait = start - (time.time() - start_time)
        if wait > 0:
            time.sleep(wait)
        keys = [_parse_note(n) for n in notes.split('+')]
        print(f"Play {notes} -> {keys} for {dur:.2f}s")
        time.sleep(dur)

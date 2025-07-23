from typing import List, Tuple


def _read_song(song_path: str) -> Tuple[dict, List[Tuple[float, float]], List[Tuple[float, str]], List[Tuple[float, float, str]]]:
    """Parse a converted song file and return metadata, tempo events, time
    signature events, and note events."""
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

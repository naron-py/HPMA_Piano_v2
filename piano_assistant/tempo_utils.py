"""Utility functions for tempo calculations."""

from typing import List, Tuple


def beat_to_sec(beat: float, tempo_events: List[Tuple[float, float]], default_bpm: float = 120.0) -> float:
    """Convert a beat position to seconds using the provided tempo map."""
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

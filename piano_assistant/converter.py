from __future__ import annotations
import os
from typing import List, Tuple
from music21 import converter as m21converter, note, chord, tempo, stream, pitch
from .utils import timestamped_filename


def _tempo_events(score) -> List[Tuple[float, float]]:
    events = []
    for mm in score.recurse().getElementsByClass(tempo.MetronomeMark):
        bpm = mm.getQuarterBPM()
        if bpm is None:
            continue
        events.append((float(mm.offset), float(bpm)))
    if not events:
        events.append((0.0, 120.0))
    events.sort(key=lambda x: x[0])
    return events


def _offset_to_seconds(offset, tempo_map):
    seconds = 0.0
    last_off, last_bpm = tempo_map[0]
    if offset < last_off:
        return offset * 60.0 / last_bpm
    for off, bpm in tempo_map:
        if off >= offset:
            break
        seconds += (off - last_off) * 60.0 / last_bpm
        last_off, last_bpm = off, bpm
    seconds += (offset - last_off) * 60.0 / last_bpm
    return seconds


def convert_file(path: str, output_dir: str = "output") -> str | None:
    if not os.path.exists(path):
        print("File not found:", path)
        return None
    try:
        score = m21converter.parse(path)
    except Exception as exc:
        print("Parse error:", exc)
        return None

    tempo_map = _tempo_events(score)
    parts = score.parts
    if len(parts) >= 2:
        hand_map = {parts[0]: "RH", parts[1]: "LH"}
    else:
        hand_map = {part: "RH" for part in parts}

    events = []
    for part in parts:
        hand = hand_map[part]
        for el in part.flat.notesAndRests:
            if isinstance(el, note.Rest):
                continue
            start = _offset_to_seconds(float(el.offset), tempo_map)
            dur = _offset_to_seconds(float(el.offset + el.quarterLength), tempo_map) - start
            if isinstance(el, note.Note):
                pitches = [el.pitch.nameWithOctave]
            else:
                pitches = [p.nameWithOctave for p in el.pitches]
                pitches.sort(key=lambda x: pitch.Pitch(x))
            events.append((start, dur, pitches, hand))
    events.sort(key=lambda e: e[0])

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, timestamped_filename(path))
    with open(out_path, "w") as fh:
        for start, dur, pitches, hand in events:
            note_str = "+".join(pitches)
            fh.write(f"{hand}:{note_str}:{start:.3f}:{dur:.3f}\n")

    print("Converted", os.path.basename(path), "->", out_path)
    return out_path

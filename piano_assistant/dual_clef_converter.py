import os
from typing import List, Tuple

from music21 import converter as m21converter, note, meter, tempo

from piano_assistant.key_mapper import BASE_MIDI, NOTE_NAMES

ROUND_PRECISION = 3


def _midi_to_note(m: int) -> str:
    name = NOTE_NAMES[(m - BASE_MIDI) % 12]
    octave = (m - BASE_MIDI) // 12 + 1
    return f"{name}-{octave}"


class SustainedNote:
    def __init__(self, note: str, start: float, end: float):
        self.note = note
        self.start = start
        self.end = end


def convert_mxl_with_dual_clef(mxl_file_path: str, output_path: str) -> str:
    score = m21converter.parse(mxl_file_path)

    initial_ts = None
    initial_bpm = None
    ts_events: List[Tuple[float, str]] = []
    tempo_events: List[Tuple[float, float]] = []
    flat_meta = score.flatten()
    for ts in flat_meta.recurse().getElementsByClass(meter.TimeSignature):
        off = float(ts.offset)
        ts_events.append((off, ts.ratioString))
        if initial_ts is None:
            initial_ts = ts.ratioString
    for tm in flat_meta.recurse().getElementsByClass(tempo.MetronomeMark):
        if tm.number is None:
            continue
        off = float(tm.offset)
        tempo_events.append((off, float(tm.number)))
        if initial_bpm is None:
            initial_bpm = int(tm.number)

    sustained: List[SustainedNote] = []
    for el in score.flatten().notesAndRests:
        start_beat = float(el.offset)
        dur = float(el.quarterLength)
        end_beat = start_beat + dur
        if el.isRest:
            continue
        if isinstance(el, note.Note):
            notes = [_midi_to_note(el.pitch.midi)]
        else:
            notes = [_midi_to_note(p.midi) for p in el.pitches]
        for n in notes:
            sustained.append(SustainedNote(n, start_beat, end_beat))
    if not sustained:
        raise ValueError("No notes found")

    time_points = set()
    for sn in sustained:
        time_points.add(sn.start)
        time_points.add(sn.end)
    if sustained:
        min_start = min(sn.start for sn in sustained)
        if min_start > 0.001:
            time_points.add(0.0)
    time_points = sorted(time_points)
    uniq = []
    for t in time_points:
        if not uniq or t > uniq[-1] + 0.0001:
            uniq.append(t)
    time_points = uniq

    events: List[Tuple[float, float, str]] = []
    for i in range(len(time_points) - 1):
        start = time_points[i]
        end = time_points[i + 1]
        dur = end - start
        if dur <= 0.001:
            continue
        active = {sn.note for sn in sustained if sn.start < end and sn.end > start}
        note_str = "+".join(sorted(active)) if active else "R"
        events.append((round(start, ROUND_PRECISION), round(dur, ROUND_PRECISION), note_str))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(f"# Source: {os.path.basename(mxl_file_path)}\n")
        if initial_ts:
            f.write(f"# Time Signature: {initial_ts}\n")
        if initial_bpm:
            f.write(f"# Tempo: {initial_bpm} BPM\n")
        for off, ts_val in sorted(ts_events, key=lambda x: x[0]):
            f.write(f"# TimeSignature {off:.3f}: {ts_val}\n")
        for off, bpm in sorted(tempo_events, key=lambda x: x[0]):
            f.write(f"# Tempo {off:.3f}: {int(bpm)} BPM\n")
        f.write("# start\tduration\tnotes\n")
        for start, dur, notes in events:
            f.write(f"{start:.3f}\t{dur:.3f}\t{notes}\n")
    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("output_file")
    args = parser.parse_args()
    convert_mxl_with_dual_clef(args.input_file, args.output_file)

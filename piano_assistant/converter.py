import os
from typing import List

# Number of decimal places to round timing information to when converting.
ROUND_PRECISION = 3

from music21 import converter as m21converter, note, chord, meter, tempo

from .key_mapper import BASE_MIDI, NOTE_NAMES
from .utils import OUTPUT_DIR, timestamp

PLAYABLE_MIN = BASE_MIDI
PLAYABLE_MAX = BASE_MIDI + 36 - 1


def _compute_shift(min_note: int, max_note: int) -> int:
    """Return a shift in semitones to roughly center notes in the playable range."""
    playable_span = PLAYABLE_MAX - PLAYABLE_MIN
    span = max_note - min_note
    if span <= playable_span:
        shift = 0
        while max_note + shift > PLAYABLE_MAX:
            shift -= 12
        while min_note + shift < PLAYABLE_MIN:
            shift += 12
        return shift

    # If the range is too wide, shift to center the music and handle
    # out-of-range notes later during conversion.
    desired_center = (PLAYABLE_MAX + PLAYABLE_MIN) // 2
    current_center = (max_note + min_note) // 2
    return desired_center - current_center


def _clamp_midi(m: int) -> int:
    """Clamp a MIDI value to the playable range using octave shifts."""
    while m > PLAYABLE_MAX:
        m -= 12
    while m < PLAYABLE_MIN:
        m += 12
    return m


def _midi_to_note(m: int):
    name = NOTE_NAMES[(m - BASE_MIDI) % 12]
    octave = (m - BASE_MIDI) // 12 + 1
    return f"{name}-{octave}"


def _round_time(value: float) -> float:
    """Round time values to ``ROUND_PRECISION`` decimal places."""
    return round(value, ROUND_PRECISION)


def convert(file_path: str) -> str:
    score = m21converter.parse(file_path)
    # Merge tied notes so sustained pitches become single longer notes.
    # This allows the player to hold notes for their full duration instead of
    # re-triggering ties as separate events.
    score = score.stripTies(inPlace=False)

    # Extract basic metadata for reference during playback and collect all
    # time signature and tempo changes along with their offsets.
    initial_ts = None
    initial_bpm = None
    ts_events: List[tuple[float, str]] = []
    tempo_events: List[tuple[float, float]] = []
    flat_score_meta = score.flatten()
    for ts_elem in flat_score_meta.recurse().getElementsByClass(meter.TimeSignature):
        off = float(ts_elem.offset)
        ts_events.append((off, ts_elem.ratioString))
        if initial_ts is None:
            initial_ts = ts_elem.ratioString
    for tempo_elem in flat_score_meta.recurse().getElementsByClass(tempo.MetronomeMark):
        if tempo_elem.number is None:
            continue
        off = float(tempo_elem.offset)
        tempo_events.append((off, float(tempo_elem.number)))
        if initial_bpm is None:
            initial_bpm = int(tempo_elem.number)
    midi_numbers: List[int] = []
    for elem in score.recurse().notes:
        if isinstance(elem, note.Note):
            midi_numbers.append(elem.pitch.midi)
        elif isinstance(elem, chord.Chord):
            midi_numbers.extend(p.midi for p in elem.pitches)
    if not midi_numbers:
        raise ValueError('No notes found in file')
    shift = _compute_shift(min(midi_numbers), max(midi_numbers))
    score = score.transpose(shift)
    flat_score = score.flatten()

    events_map: dict[tuple[float, float], list[str]] = {}
    for el in flat_score.recurse().getElementsByClass((note.Note, chord.Chord)):
        # Store timing information in beats so playback can adjust according to
        # tempo changes.
        start = _round_time(el.offset)
        dur = _round_time(el.quarterLength)
        if isinstance(el, note.Note):
            midi = _clamp_midi(el.pitch.midi)
            notes = [_midi_to_note(midi)]
        else:
            midi_vals = [_clamp_midi(p.midi) for p in el.pitches]
            notes = [_midi_to_note(m) for m in midi_vals]
        key = (start, dur)
        events_map.setdefault(key, []).extend(notes)

    events = [(s, d, '+'.join(n)) for (s, d), n in events_map.items()]
    # Sort by the rounded start time so notes starting together stay together
    events.sort(key=lambda x: x[0])
    basename = os.path.splitext(os.path.basename(file_path))[0]
    out_name = f"{basename}_{timestamp()}.txt"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    with open(out_path, 'w') as f:
        f.write(f"# Source: {os.path.basename(file_path)}\n")
        if initial_ts:
            f.write(f"# Time Signature: {initial_ts}\n")
        if initial_bpm:
            f.write(f"# Tempo: {initial_bpm} BPM\n")
        for off, ts_val in sorted(ts_events, key=lambda x: x[0]):
            f.write(f"# TimeSignature {off:.3f}: {ts_val}\n")
        for off, bpm_val in sorted(tempo_events, key=lambda x: x[0]):
            f.write(f"# Tempo {off:.3f}: {int(bpm_val)} BPM\n")
        f.write("# start\tduration\tnotes\n")
        for start, dur, notestr in events:
            f.write(f"{start:.3f}\t{dur:.3f}\t{notestr}\n")
    return out_path

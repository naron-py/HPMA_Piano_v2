import os
from typing import List

from music21 import converter as m21converter, note, chord

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


def convert(file_path: str) -> str:
    score = m21converter.parse(file_path)
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
    events = []
    for entry in flat_score.secondsMap:
        el = entry['element']
        if isinstance(el, (note.Note, chord.Chord)):
            start = entry['offsetSeconds']
            dur = entry['durationSeconds']
            if isinstance(el, note.Note):
                midi = _clamp_midi(el.pitch.midi)
                notes = [_midi_to_note(midi)]
            else:
                midi_vals = [_clamp_midi(p.midi) for p in el.pitches]
                notes = [_midi_to_note(m) for m in midi_vals]
            events.append((start, dur, '+'.join(notes)))
    events.sort(key=lambda x: x[0])
    basename = os.path.splitext(os.path.basename(file_path))[0]
    out_name = f"{basename}_{timestamp()}.txt"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    with open(out_path, 'w') as f:
        f.write(f"# Source: {os.path.basename(file_path)}\n")
        f.write("# start\tduration\tnotes\n")
        for start, dur, notestr in events:
            f.write(f"{start:.3f}\t{dur:.3f}\t{notestr}\n")
    return out_path

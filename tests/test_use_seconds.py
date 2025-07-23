import os
import sys

import pytest
from music21 import stream, note, meter, tempo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from piano_assistant.converter import convert
from piano_assistant.tempo_utils import beat_to_sec


def create_score(path):
    s = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature('4/4'))
    p.insert(0, tempo.MetronomeMark(number=120))
    for i in range(4):
        p.insert(i, note.Note('C4', quarterLength=1))
    p.insert(4, meter.TimeSignature('3/4'))
    p.insert(4, tempo.MetronomeMark(number=60))
    for i in range(3):
        p.insert(4 + i, note.Note('C4', quarterLength=1))
    s.insert(0, p)
    xml_path = os.path.join(path, 'seconds.mxl')
    s.write('musicxml', fp=xml_path)
    return xml_path


def test_use_seconds(tmp_path):
    xml = create_score(tmp_path)
    out_path = convert(str(xml), use_seconds=True)
    with open(out_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    data_lines = [l for l in lines if not l.startswith('#')]

    starts = []
    durs = []
    for line in data_lines:
        start, dur, _ = line.split('\t')
        starts.append(float(start))
        durs.append(float(dur))

    tempo_events = [(0.0, 120.0), (4.0, 60.0)]
    beat_positions = [0, 1, 2, 3, 4, 5, 6]
    expected_starts = [beat_to_sec(b, tempo_events) for b in beat_positions]
    expected_durs = [
        beat_to_sec(b + 1, tempo_events) - beat_to_sec(b, tempo_events)
        for b in beat_positions
    ]

    assert starts == pytest.approx(expected_starts, abs=1e-3)
    assert durs == pytest.approx(expected_durs, abs=1e-3)

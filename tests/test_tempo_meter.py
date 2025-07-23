import os
import sys
import pytest
from music21 import stream, note, meter, tempo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from piano_assistant.converter import convert
from piano_assistant import tester


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
    xml_path = os.path.join(path, 'test.mxl')
    s.write('musicxml', fp=xml_path)
    return xml_path


def test_conversion_and_playback(tmp_path):
    xml = create_score(tmp_path)
    out_path = convert(str(xml))
    with open(out_path) as f:
        lines = [l.strip() for l in f if l.strip()]

    assert any(line.startswith('# TimeSignature 0.000: 4/4') for line in lines)
    assert any(line.startswith('# Tempo 0.000: 120 BPM') for line in lines)
    assert any(line.startswith('# TimeSignature 4.000: 3/4') for line in lines)
    assert any(line.startswith('# Tempo 4.000: 60 BPM') for line in lines)

    metadata, tempos, tss, events = tester._read_song(out_path)
    starts = [tester.beat_to_sec(start, tempos) for start, _dur, _notes in events]
    expected = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    assert starts == pytest.approx(expected, abs=1e-3)

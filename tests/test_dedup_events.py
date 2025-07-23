import os
import sys
from music21 import stream, note, meter, tempo

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from piano_assistant.converter import convert


def create_score(path):
    s = stream.Score()
    p1 = stream.Part()
    p1.insert(0, meter.TimeSignature('4/4'))
    p1.insert(0, tempo.MetronomeMark(number=120))
    p1.append(note.Note('C4', quarterLength=1))

    p2 = stream.Part()
    p2.insert(0, meter.TimeSignature('4/4'))
    p2.insert(0, tempo.MetronomeMark(number=120))
    p2.append(note.Note('E4', quarterLength=1))

    s.insert(0, p1)
    s.insert(0, p2)
    xml_path = os.path.join(path, 'dedup.mxl')
    s.write('musicxml', fp=xml_path)
    return xml_path


def test_dedup_events(tmp_path):
    xml = create_score(tmp_path)
    out_path = convert(str(xml))
    with open(out_path) as f:
        lines = [l.strip() for l in f if l.strip()]
    ts_lines = [l for l in lines if l.startswith('# TimeSignature')]
    tempo_lines = [l for l in lines if l.startswith('# Tempo')]
    assert ts_lines.count('# TimeSignature 0.000: 4/4') == 1
    assert tempo_lines.count('# Tempo 0.000: 120 BPM') == 1

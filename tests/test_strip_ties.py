import os
import sys
import pytest
from music21 import stream, note, meter, tie

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from piano_assistant.converter import convert


def create_tied_score(path):
    s = stream.Score()
    p = stream.Part()
    p.insert(0, meter.TimeSignature('4/4'))
    n1 = note.Note('C4', quarterLength=2)
    n1.tie = tie.Tie('start')
    n2 = note.Note('C4', quarterLength=2)
    n2.tie = tie.Tie('stop')
    p.append(n1)
    p.append(n2)
    s.insert(0, p)
    xml_path = os.path.join(path, 'tied.mxl')
    s.write('musicxml', fp=xml_path)
    return xml_path


def test_tied_notes_merged(tmp_path):
    xml = create_tied_score(tmp_path)
    out_path = convert(str(xml))
    lines = [l.strip() for l in open(out_path) if l.strip()]
    data_lines = [l for l in lines if not l.startswith('#')]
    assert len(data_lines) == 1
    start, dur, _notes = data_lines[0].split('\t')
    assert pytest.approx(float(dur), abs=1e-3) == 4.0


import os
import sys
import types
import pytest
from music21 import stream, note, meter, tempo

# Ensure player can be imported without a display
os.environ['DISPLAY'] = ':0'
sys.modules['pyautogui'] = types.SimpleNamespace(keyDown=lambda *a, **k: None, keyUp=lambda *a, **k: None)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from piano_assistant.dual_clef_converter import convert_mxl_with_dual_clef
from piano_assistant.player import _read_song, _beat_to_sec


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


def test_dual_clef_conversion(tmp_path):
    xml = create_score(tmp_path)
    out_file = os.path.join(tmp_path, 'out.txt')
    convert_mxl_with_dual_clef(str(xml), out_file)

    with open(out_file) as f:
        lines = [l.strip() for l in f if l.strip()]

    assert '# start\tduration\tnotes' in lines
    assert any(l.startswith('# TimeSignature 0.000: 4/4') for l in lines)
    assert any(l.startswith('# Tempo 0.000: 120 BPM') for l in lines)
    assert any(l.startswith('# TimeSignature 4.000: 3/4') for l in lines)
    assert any(l.startswith('# Tempo 4.000: 60 BPM') for l in lines)

    _, tempos, _, events = _read_song(out_file)
    starts = [_beat_to_sec(s, tempos) for s, _d, _n in events]
    expected = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    assert starts == pytest.approx(expected, abs=1e-3)

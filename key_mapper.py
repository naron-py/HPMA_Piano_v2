# key_mapping.py

"""
Maps musical notes to keyboard keys across three octaves.

The mapping is designed for a QWERTY keyboard layout.
- Octave 3 (Low): Bottom row of letters
- Octave 4 (Middle): Top row of letters
- Octave 5 (High): Number row
"""

NOTE_TO_KEY = {
    # Octave 3 (Low)
    "C3": "a", "C#3": "s", "D3": "d", "D#3": "f", "E3": "g", "F3": "h",
    "F#3": "j", "G3": "k", "G#3": "l", "A3": ";", "A#3": "'", "B3": "\\",

    # Octave 4 (Middle - C4 is Middle C)
    "C4": "q", "C#4": "w", "D4": "e", "D#4": "r", "E4": "t", "F4": "y",
    "F#4": "u", "G4": "i", "G#4": "o", "A4": "p", "A#4": "[", "B4": "]",

    # Octave 5 (High)
    "C5": "1", "C#5": "2", "D5": "3", "D#5": "4", "E5": "5", "F5": "6",
    "F#5": "7", "G5": "8", "G#5": "9", "A5": "0", "A#5": "-", "B5": "=",
}

# Add alternative names for sharps (flats)
# music21 often uses flats, so we map them to the same sharp keys.
NOTE_TO_KEY["D-3"] = NOTE_TO_KEY["C#3"]
NOTE_TO_KEY["E-3"] = NOTE_TO_KEY["D#3"]
NOTE_TO_KEY["G-3"] = NOTE_TO_KEY["F#3"]
NOTE_TO_KEY["A-3"] = NOTE_TO_KEY["G#3"]
NOTE_TO_KEY["B-3"] = NOTE_TO_KEY["A#3"]

NOTE_TO_KEY["D-4"] = NOTE_TO_KEY["C#4"]
NOTE_TO_KEY["E-4"] = NOTE_TO_KEY["D#4"]
NOTE_TO_KEY["G-4"] = NOTE_TO_KEY["F#4"]
NOTE_TO_KEY["A-4"] = NOTE_TO_KEY["G#4"]
NOTE_TO_KEY["B-4"] = NOTE_TO_KEY["A#4"]

NOTE_TO_KEY["D-5"] = NOTE_TO_KEY["C#5"]
NOTE_TO_KEY["E-5"] = NOTE_TO_KEY["D#5"]
NOTE_TO_KEY["G-5"] = NOTE_TO_KEY["F#5"]
NOTE_TO_KEY["A-5"] = NOTE_TO_KEY["G#5"]
NOTE_TO_KEY["B-5"] = NOTE_TO_KEY["A#5"]
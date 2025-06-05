# key_mapper.py

KEY_MAPPING = {
    # Lowest Octave (Octave 1), typically C3, D3, E3, etc.
    ("1", 1): "a", ("#1", 1): "s", ("2", 1): "d", ("#2", 1): "f", ("3", 1): "g",
    ("4", 1): "h", ("#4", 1): "j", ("5", 1): "k", ("#5", 1): "l", ("6", 1): ";",
    ("#6", 1): "'", ("7", 1): "\\",

    # Middle Octave (Octave 2), typically C4, D4, E4, etc. (Middle C)
    ("1", 2): "q", ("#1", 2): "w", ("2", 2): "e", ("#2", 2): "r", ("3", 2): "t",
    ("4", 2): "y", ("#4", 2): "u", ("5", 2): "i", ("#5", 2): "o", ("6", 2): "p",
    ("#6", 2): "[", ("7", 2): "]",

    # Highest Octave (Octave 3), typically C5, D5, E5, etc.
    ("1", 3): "1", ("#1", 3): "2", ("2", 3): "3", ("#2", 3): "4", ("3", 3): "5",
    ("4", 3): "6", ("#4", 3): "7", ("5", 3): "8", ("#5", 3): "9", ("6", 3): "0",
    ("#6", 3): "-", ("7", 3): "+", # Assuming + for the last key as per image
}

def get_keyboard_key(note_value, octave):
    """Looks up the keyboard key for a given note value and octave."""
    key_tuple = (note_value, octave)
    if key_tuple in KEY_MAPPING:
        return KEY_MAPPING[key_tuple]
    else:
        print(f"Warning: Note {note_value} in octave {octave} not found in keyboard mapping.")
        return None

# --- New functions for standard notation (e.g., from music21) to custom mapping ---

# Maps standard pitch names (C, C#, Db) to your custom note values (1, #1, 2)
# Ensure both sharps and flats are mapped if music21 might output flats.
STANDARD_PITCH_TO_CUSTOM_VALUE = {
    "C": "1",
    "C#": "#1", "Db": "#1", "C-": "#1",  # C♭ = B natural (but rare)
    "D": "2", 
    "D#": "#2", "Eb": "#2", "E-": "#2",  # E♭
    "Db": "#1", "D-": "#1",  # D♭ = C# 
    "E": "3",
    "F": "4",
    "F#": "#4", "Gb": "#4", "G-": "#4",  # G♭
    "G": "5",
    "G#": "#5", "Ab": "#5", "A-": "#5",  # A♭
    "A": "6",
    "A#": "#6", "Bb": "#6", "B-": "#6",  # B♭
    "B": "7",
    # Double flats (rare but can appear in music)
    "C--": "7",  # C♭♭ = B natural
    "D--": "1",  # D♭♭ = C natural
    "E--": "2",  # E♭♭ = D natural
    "F--": "3",  # F♭♭ = E natural
    "G--": "4",  # G♭♭ = F natural
    "A--": "5",  # A♭♭ = G natural
    "B--": "6",  # B♭♭ = A natural
    # Enharmonic equivalents (double sharps and other spellings)
    "B#": "1",   # B♯ = C natural
    "C##": "2",  # C♯♯ = D natural
    "E#": "4",   # E♯ = F natural
    "F##": "5",  # F♯♯ = G natural
    "G##": "6",  # G♯♯ = A natural
    "A##": "7",  # A♯♯ = B natural
}

# IMPORTANT: Adjust this mapping based on YOUR GAME'S virtual piano's actual octave range.
# Extended to support wider range of octaves and automatically transpose if needed
STANDARD_OCTAVE_TO_CUSTOM_OCTAVE = {
    1: 1,  # e.g., C1 to B1 maps to your lowest octave (A-key row) - very low notes
    2: 1,  # e.g., C2 to B2 maps to your lowest octave (A-key row) 
    3: 1,  # e.g., C3 to B3 maps to your lowest octave (A-key row)
    4: 2,  # e.g., C4 to B4 maps to your middle octave (Q-key row)
    5: 3,  # e.g., C5 to B5 maps to your highest octave (Number row)
    6: 3,  # e.g., C6 to B6 maps to your highest octave (Number row) - transpose down
    7: 3,  # e.g., C7 to B7 maps to your highest octave (Number row) - transpose down
}
# Add more if your music goes beyond these 3 octaves or if your game's range is different.

def convert_standard_note_to_custom(music21_note_name, music21_octave):
    """
    Converts a music21 note's name (e.g., 'C#') and octave (e.g., 4)
    to your custom (note_value, octave) tuple.
    """
    custom_note_value = STANDARD_PITCH_TO_CUSTOM_VALUE.get(music21_note_name)
    custom_octave = STANDARD_OCTAVE_TO_CUSTOM_OCTAVE.get(music21_octave)

    if custom_note_value is None:
        print(f"Warning: Could not map standard pitch '{music21_note_name}' to custom note value. Skipping.")
        return None, None
    if custom_octave is None:
        print(f"Warning: Could not map standard octave '{music21_octave}' to custom octave. Skipping.")
        return None, None

    return custom_note_value, custom_octave
# converter.py

import os
from collections import defaultdict
from music21 import converter, note, chord, stream, instrument, pitch

# The pitch 'C4' is often considered the dividing line between hands in simple piano music.
# This is a heuristic and may not be accurate for all pieces.
RIGHT_HAND_THRESHOLD = 'C4'

def get_hand(element):
    """
    Determines if a note or chord should be played by the left or right hand.
    Uses a simple pitch-based heuristic.
    """
    # In music21, a Rest has no pitch, so we can't assign it a hand.
    if isinstance(element, note.Rest):
        return ""

    # For a single note, compare its pitch to the threshold
    if isinstance(element, note.Note):
        if element.pitch >= note.Pitch(RIGHT_HAND_THRESHOLD):
            return "RH"
        else:
            return "LH"

    # For a chord, check the pitch of the lowest note
    if isinstance(element, chord.Chord):
        if element.sortAscending().pitches[0] >= note.Pitch(RIGHT_HAND_THRESHOLD):
            return "RH"
        else:
            return "LH"
    return ""

def shift_pitch_to_range(p):
    """Shift a pitch into the supported C3-B5 range."""
    # ``p`` can be a pitch.Pitch instance or a string/MIDI number. ``music21``
    # does not allow constructing ``Pitch`` with another ``Pitch`` directly, so
    # we clone when necessary.
    if isinstance(p, pitch.Pitch):
        p = pitch.Pitch(p.nameWithOctave)
    else:
        p = pitch.Pitch(p)

    while p.octave < 3:
        p.octave += 1
    while p.octave > 5:
        p.octave -= 1
    return p

def parse_file(file_path):
    """
    Parses a MusicXML or MIDI file and converts it into a custom text format.
    
    Args:
        file_path (str): The path to the input music file.

    Returns:
        str: The path to the newly created .txt song file, or None if conversion failed.
    """
    print(f"Parsing '{os.path.basename(file_path)}'...")
    try:
        # Load the score from the file
        score = converter.parse(file_path)
    except Exception as e:
        print(f"Error: Could not parse file. Reason: {e}")
        return None

    # Filter to piano parts when possible for better accuracy
    piano_parts = []
    for part in score.parts:
        inst = part.getInstrument(returnDefault=False)
        names = [part.partName, part.partAbbreviation]
        if inst:
            names.append(inst.instrumentName)
            names.append(inst.instrumentAbbreviation)
        name_str = " ".join(n.lower() for n in names if n)
        if "piano" in name_str:
            piano_parts.append(part)
    if piano_parts:
        score = stream.Score(piano_parts)

    # Flatten the score and remove ties so we can work with a single
    # sequence of events. This helps keep note ordering consistent when
    # multiple voices are present.
    score = score.flatten().stripTies()

    # --- Metadata Extraction ---
    tempo = 120  # Default tempo
    if score.metronomeMarkBoundaries():
        tempo = score.metronomeMarkBoundaries()[0][-1].number

    time_signature = "4/4" # Default time signature
    if score.getTimeSignatures():
        ts = score.getTimeSignatures()[0]
        time_signature = f"{ts.numerator}/{ts.denominator}"

    key_signature = "C major" # Default key signature
    try:
        key = score.analyze('key')
        key_signature = f"{key.tonic.name} {key.mode}"
    except Exception:
        # Some MIDI files lack key info, so we fall back to a default
        print("Warning: Could not determine key signature. Defaulting to C major.")
        
    # --- Note and Chord Processing ---
    song_data = []

    # Group elements by their start offset so chords can be constructed
    notes_by_offset = defaultdict(list)
    for element in score.notesAndRests:
        notes_by_offset[round(element.offset, 3)].append(element)

    sorted_offsets = sorted(notes_by_offset.keys())

    for idx, offset in enumerate(sorted_offsets):
        group = notes_by_offset[offset]
        # Determine duration based on the next event offset
        if idx + 1 < len(sorted_offsets):
            next_offset = sorted_offsets[idx + 1]
        else:
            next_offset = offset + max(e.duration.quarterLength for e in group)
        duration = next_offset - offset

        # Collect note names, ignoring rests if notes are present
        note_names = [shift_pitch_to_range(e.pitch).nameWithOctave
                      for e in group if isinstance(e, note.Note)]

        if note_names:
            note_names.sort(key=lambda n: pitch.Pitch(n))
            h_element = chord.Chord(note_names) if len(note_names) > 1 else note.Note(note_names[0])
            hand = get_hand(h_element)
            pitch_str = "-".join(note_names)
            song_data.append(f"{hand}:{pitch_str}:{duration}")
        else:
            song_data.append(f"Rest:{duration}")
            
    # --- Write to Output File ---
    if not song_data:
        print("Error: No musical data could be extracted.")
        return None
        
    output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.txt"
    output_path = os.path.join("songs", output_filename)
    
    with open(output_path, "w") as f:
        # Write metadata at the top of the file
        f.write(f"# Tempo: {tempo}\n")
        f.write(f"# Time Signature: {time_signature}\n")
        f.write(f"# Key Signature: {key_signature}\n")
        f.write("# ---\n")
        
        # Write the note data
        for line in song_data:
            f.write(f"{line}\n")
            
    print(f"Successfully converted song to '{output_path}'")
    return output_path
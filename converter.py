# converter.py

import os
from music21 import converter, note, chord, stream

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
    
    # Use .flat.notesAndRests to get a single stream of all musical events
    for element in score.flat.notesAndRests:
        hand = get_hand(element)
        
        # Format the line based on the element type
        if isinstance(element, note.Note):
            pitch_name = element.pitch.nameWithOctave
            duration = element.duration.quarterLength
            song_data.append(f"{hand}:{pitch_name}:{duration}")
            
        elif isinstance(element, chord.Chord):
            # Join all note names in the chord with a hyphen
            pitch_names = "-".join(p.nameWithOctave for p in element.pitches)
            duration = element.duration.quarterLength
            song_data.append(f"{hand}:{pitch_names}:{duration}")

        elif isinstance(element, note.Rest):
            duration = element.duration.quarterLength
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
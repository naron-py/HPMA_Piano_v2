# converter.py

import os
from music21 import (
    converter,
    note,
    chord,
    stream,
    instrument,
    pitch,
    tempo as m21tempo,
    meter,
)

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
    tempos = list(score.recurse().getElementsByClass(m21tempo.MetronomeMark))
    if tempos:
        mark = tempos[0]
        if mark.number is not None:
            tempo = mark.number
        elif mark.getQuarterBPM() is not None:
            tempo = mark.getQuarterBPM()

    time_signature = "4/4"  # Default time signature
    signatures = list(score.recurse().getElementsByClass(meter.TimeSignature))
    if signatures:
        ts = signatures[0]
        time_signature = f"{ts.numerator}/{ts.denominator}"

    key_signature = "C major" # Default key signature
    try:
        key = score.analyze('key')
        key_signature = f"{key.tonic.name} {key.mode}"
    except Exception:
        # Some MIDI files lack key info, so we fall back to a default
        print("Warning: Could not determine key signature. Defaulting to C major.")
        
    # --- Note and Chord Processing ---
    events = []
    for element in score.notesAndRests:
        offset = round(element.offset, 3)
        duration = round(element.duration.quarterLength, 3)

        if isinstance(element, note.Rest):
            events.append((offset, "Rest", "", duration))
            continue

        if isinstance(element, note.Note):
            hand = "RH" if element.pitch >= note.Pitch(RIGHT_HAND_THRESHOLD) else "LH"
            name = shift_pitch_to_range(element.pitch).nameWithOctave
            events.append((offset, hand, name, duration))
            continue

        if isinstance(element, chord.Chord):
            left = []
            right = []
            for n in element.notes:
                n_name = shift_pitch_to_range(n.pitch).nameWithOctave
                if n.pitch >= note.Pitch(RIGHT_HAND_THRESHOLD):
                    right.append(n_name)
                else:
                    left.append(n_name)
            if left:
                left.sort(key=lambda n: pitch.Pitch(n))
                events.append((offset, "LH", "-".join(left), duration))
            if right:
                right.sort(key=lambda n: pitch.Pitch(n))
                events.append((offset, "RH", "-".join(right), duration))

    # Sort and merge events that share offset, hand and duration
    events.sort(key=lambda e: (e[0], e[1]))
    merged = []
    for evt in events:
        if merged and evt[0] == merged[-1][0] and evt[1] == merged[-1][1] and evt[3] == merged[-1][3]:
            merged[-1][2] = merged[-1][2] + "-" + evt[2] if merged[-1][2] else evt[2]
        else:
            merged.append(list(evt))

    song_data = []
    for offset, hand, pitches, duration in merged:
        if hand == "Rest":
            song_data.append(f"Rest:{duration}")
        else:
            song_data.append(f"{hand}:{pitches}:{duration}")
            
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
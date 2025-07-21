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
    # Use chordify to merge simultaneous notes from all parts so that
    # rests from individual voices do not create unwanted gaps. The
    # duration of each resulting chord represents the time until the
    # next musical event.
    chordified = score.chordify().flatten().stripTies()

    events = []
    for element in chordified:
        if not isinstance(element, (note.Note, chord.Chord, note.Rest)):
            continue
        offset = round(element.offset, 3)
        duration = round(element.duration.quarterLength, 3)

        if isinstance(element, note.Rest):
            events.append((offset, "Rest", duration))
        else:
            if isinstance(element, note.Note):
                pitches = [shift_pitch_to_range(element.pitch).nameWithOctave]
            else:
                pitches = [shift_pitch_to_range(p).nameWithOctave for p in element.pitches]
                pitches.sort(key=lambda n: pitch.Pitch(n))
            events.append((offset, "-".join(pitches), duration))

    # Sort by offset to ensure correct playback order
    events.sort(key=lambda e: e[0])

    song_data = []
    for _, pitches, duration in events:
        if pitches == "Rest":
            song_data.append(f"Rest:{duration}")
        else:
            song_data.append(f"{pitches}:{duration}")
            
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
import music21
from music21 import note, chord, tempo
from key_mapper import convert_standard_note_to_custom

# Default tempo if none is found in the score
TEMPO_BPM = 98


def parse_music_file(file_path, manual_tempo=None, min_duration=0.0):
    """Parse a MusicXML/MIDI file into a list of playable note strings.

    Notes sounding at the same time are combined into chords. Durations are
    calculated using the note lengths and the tempo found in the score. If no
    tempo marking exists, the user is prompted to provide one or the default is
    used. Intervals shorter than ``min_duration`` are skipped.
    """
    song_notes = []
    try:
        print(f"🎵 Loading music file: {file_path}")
        score = music21.converter.parse(file_path)
        print("✓ File loaded successfully")
        print(f"📊 Score contains {len(score.parts)} parts")

        if manual_tempo is not None:
            tempo_bpm = float(manual_tempo)
        else:
            tempo_bpm = TEMPO_BPM
            tempos = score.flat.getElementsByClass(tempo.MetronomeMark)
            if tempos and tempos[0].number:
                tempo_bpm = float(tempos[0].number)
            else:
                try:
                    user_input = input(
                        f"⚠️  Tempo not found in score. Enter tempo in BPM (default {TEMPO_BPM}): "
                    ).strip()
                    if user_input:
                        tempo_bpm = float(user_input)
                except Exception:
                    print("Invalid tempo input. Using default.")

        qdur = 60.0 / tempo_bpm

        events = []  # list of (note_str, start_time, end_time)
        time_points = set()

        for part_idx, part in enumerate(score.parts):
            print(f"   Part {part_idx + 1}: {part.getInstrument()}")
            for el in part.flat.notesAndRests:
                offset = float(el.offset)
                start = offset * qdur
                dur = el.duration.quarterLength * qdur
                end = start + dur

                if dur < min_duration:
                    continue

                time_points.add(start)
                time_points.add(end)

                if el.isRest:
                    continue

                if isinstance(el, note.Note):
                    nv, oc = convert_standard_note_to_custom(el.name, el.octave)
                    if nv and oc:
                        events.append((f"{nv}-{oc}", start, end))
                elif isinstance(el, chord.Chord):
                    for n in el.notes:
                        nv, oc = convert_standard_note_to_custom(n.name, n.octave)
                        if nv and oc:
                            events.append((f"{nv}-{oc}", start, end))

        if not events:
            print("⚠️  No valid notes found in the score.")
            return []

        time_points = sorted(time_points)
        for i in range(len(time_points) - 1):
            start = time_points[i]
            end = time_points[i + 1]
            dur = end - start
            if dur <= 0 or dur < min_duration:
                continue

            active = {e[0] for e in events if e[1] < end and e[2] > start}
            if active:
                chord_str = "+".join(sorted(active))
                song_notes.append(f"{chord_str}:{dur:.3f}")
            else:
                song_notes.append(f"R:{dur:.3f}")

        print("✅ Processing complete!")
        print(f"   Notes generated: {len(song_notes)}")
        return song_notes

    except Exception as e:
        print(f"❌ Error parsing music file: {e}")
        import traceback
        traceback.print_exc()
        return []

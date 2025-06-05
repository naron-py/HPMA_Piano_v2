# music_file_parser.py - Enhanced parser that properly handles multi-part scores

import music21
from music21 import stream, note, chord, duration
from key_mapper import convert_standard_note_to_custom

# Set the tempo from your sheet music (e.g., J = 98 BPM from your PDF)
TEMPO_BPM = 98

def parse_music_file(file_path):
    """
    Enhanced music file parser that properly handles multi-part scores.
    Combines all parts and analyzes true simultaneous notes across all parts.
    """
    song_notes_list = []
    try:
        print(f"🎵 Loading music file: {file_path}")
        score = music21.converter.parse(file_path)
        print(f"✓ File loaded successfully")
        print(f"📊 Score contains {len(score.parts)} parts")
        
        # Collect ALL elements from ALL parts with their timing
        all_elements = []
        
        for part_idx, part in enumerate(score.parts):
            print(f"   Part {part_idx + 1}: {part.getInstrument()}")
            part_elements = part.flat.notesAndRests
            print(f"      Elements in this part: {len(part_elements)}")
            
            for element in part_elements:
                offset = float(element.offset)
                all_elements.append((offset, element, part_idx))
        
        print(f"🎼 Total elements across all parts: {len(all_elements)}")
        
        # Sort by offset time to process chronologically
        all_elements.sort(key=lambda x: x[0])
        
        # Group elements by their start time (with small tolerance for floating point)
        time_groups = {}
        tolerance = 0.001
        
        for offset, element, part_idx in all_elements:
            # Find if there's already a time group close to this offset
            matched_time = None
            for existing_time in time_groups.keys():
                if abs(offset - existing_time) <= tolerance:
                    matched_time = existing_time
                    break
            
            if matched_time is None:
                matched_time = offset
                time_groups[matched_time] = []
            
            time_groups[matched_time].append((element, part_idx))
        
        print(f"⏱️  Found {len(time_groups)} unique time points")
        
        # Process each time group
        processed_notes = 0
        skipped_notes = 0
        chord_count = 0
        rest_count = 0
        
        for time_offset in sorted(time_groups.keys()):
            elements_at_time = time_groups[time_offset]
            
            result = process_multi_part_group(elements_at_time, time_offset)
            if result:
                song_notes_list.extend(result['notes'])
                processed_notes += result['processed']
                skipped_notes += result['skipped']
                chord_count += result['chords']
                rest_count += result['rests']
        
        print(f"✅ Processing complete!")
        print(f"   📝 Total elements processed: {len(song_notes_list)}")
        print(f"   🎵 Notes processed: {processed_notes}")
        print(f"   🎹 Chords detected: {chord_count}")
        print(f"   🎼 Rests detected: {rest_count}")
        if skipped_notes > 0:
            print(f"   ⚠️  Skipped: {skipped_notes} notes (outside supported range)")
        
        return song_notes_list
        
    except Exception as e:
        print(f"❌ Error parsing music file: {e}")
        import traceback
        traceback.print_exc()
        return []


def process_multi_part_group(elements_with_parts, time_offset):
    """
    Process a group of musical elements from potentially multiple parts
    that start at the same time.
    """
    if not elements_with_parts:
        return None
    
    # Separate rests from notes
    notes_and_chords = []
    rests = []
    
    for element, part_idx in elements_with_parts:
        if isinstance(element, music21.note.Rest):
            rests.append((element, part_idx))
        else:
            notes_and_chords.append((element, part_idx))
    
    # If we only have rests, process the first one (ignore simultaneous rests)
    if not notes_and_chords and rests:
        rest_element = rests[0][0]
        duration_seconds = (60 / TEMPO_BPM) * rest_element.duration.quarterLength
        return {
            'notes': [f"R:{duration_seconds:.3f}"],
            'processed': 0,
            'skipped': 0,
            'chords': 0,
            'rests': 1
        }
    
    # Process all notes and chords at this time point
    all_note_pitches = []
    duration_seconds = None
    processed_count = 0
    skipped_count = 0
    
    for element, part_idx in notes_and_chords:
        # Set duration from first element (should be same for simultaneous elements)
        if duration_seconds is None:
            duration_seconds = (60 / TEMPO_BPM) * element.duration.quarterLength
        
        if isinstance(element, music21.note.Note):
            note_name = element.name
            octave = element.octave
            
            custom_note_value, custom_octave = convert_standard_note_to_custom(note_name, octave)
            
            if custom_note_value and custom_octave:
                all_note_pitches.append(f"{custom_note_value}-{custom_octave}")
                processed_count += 1
            else:
                skipped_count += 1
                if skipped_count <= 3:
                    print(f"⚠️  Skipping unmapped note: {note_name}{octave} (part {part_idx + 1})")
        
        elif isinstance(element, music21.chord.Chord):
            for note in element.notes:
                note_name = note.name
                octave = note.octave
                
                custom_note_value, custom_octave = convert_standard_note_to_custom(note_name, octave)
                
                if custom_note_value and custom_octave:
                    all_note_pitches.append(f"{custom_note_value}-{custom_octave}")
                    processed_count += 1
                else:
                    skipped_count += 1
                    if skipped_count <= 3:
                        print(f"⚠️  Skipping unmapped chord note: {note_name}{octave} (part {part_idx + 1})")
    
    if not all_note_pitches:
        return {
            'notes': [],
            'processed': 0,
            'skipped': skipped_count,
            'chords': 0,
            'rests': 0
        }
    
    # Remove duplicates while preserving order
    unique_pitches = []
    seen = set()
    for pitch in all_note_pitches:
        if pitch not in seen:
            unique_pitches.append(pitch)
            seen.add(pitch)
    
    # Format the output
    if len(unique_pitches) == 1:
        # Single note
        result_notes = [f"{unique_pitches[0]}:{duration_seconds:.3f}"]
        chord_detected = 0
    else:
        # Chord - join notes with '+' to indicate simultaneous play
        chord_string = "+".join(unique_pitches)
        result_notes = [f"{chord_string}:{duration_seconds:.3f}"]
        chord_detected = 1
        if time_offset < 50:  # Only print first few chords to avoid spam
            print(f"🎹 Chord at {time_offset:.1f}: {chord_string} ({len(unique_pitches)} notes)")
    
    return {
        'notes': result_notes,
        'processed': processed_count,
        'skipped': skipped_count,
        'chords': chord_detected,
        'rests': 0
    }
#!/usr/bin/env python3
# convert_mxl_dual_clef.py - Convert MXL to text with improved handling of treble and bass clefs
#
# Key improvements:
# 1. Explicitly handles both treble and bass clefs (dual-staff piano music)
# 2. Properly combines notes from both clefs into a unified timeline
# 3. Preserves proper sustain of notes while other melody notes are played
# 4. Maintains overlapping notes and chords like a real piano performance
# 5. Preserves musical information including tempo, key signature, and time signature

import os
import sys
import argparse
import glob
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
from music21 import converter, note, chord, meter, tempo, key, dynamics, expressions, clef, stream
# Import key_mapper at the top to avoid circular dependency
from key_mapper import STANDARD_PITCH_TO_CUSTOM_VALUE, convert_standard_note_to_custom

class UpdatedKeyMapper:
    """
    Enhanced key mapper class that extends the functionality of key_mapper.py
    without modifying the original file.
    This provides more accurate mapping for complex enharmonic equivalents
    and better octave mapping for piano music.
    """
    
    # Additional enharmonic equivalents that might be encountered
    ADDITIONAL_ENHARMONICS = {
        # Triple sharps/flats (rare but possible)
        "C###": "D#",
        "D###": "E#",
        "E###": "F##",
        "F###": "G#",
        "G###": "A#",
        "A###": "B#",
        "B###": "C##",
        "Cbbb": "A",
        "Dbbb": "B",
        "Ebbb": "C",
        "Fbbb": "D",
        "Gbbb": "E",
        "Abbb": "F",
        "Bbbb": "G",
        
        # Other unusual spellings
        "E--": "#2",  # E double-flat
        "B--": "#6",  # B double-flat
    }
    
    @staticmethod
    def normalize_note_name(note_name):
        """Convert complex note names to their simpler enharmonic equivalents"""
        
        # If the note name has an unusual enharmonic spelling, normalize it
        if note_name in UpdatedKeyMapper.ADDITIONAL_ENHARMONICS:
            normalized = UpdatedKeyMapper.ADDITIONAL_ENHARMONICS[note_name]
            return normalized
            
        # If not in our additions, pass through to the original mapper
        return note_name
    
    @staticmethod
    def adjust_octave_for_range(octave):
        """
        Adjust octaves that are outside the piano's normal range
        to fit within the playable range.
        """
        # Map to key_mapper's supported octaves (typically 1-3)
        if octave <= 0:
            return 1  # Map very low notes to the lowest octave
        elif octave >= 8:
            return 3  # Map very high notes to the highest octave
        return octave
        
    @staticmethod
    def enhanced_convert_note(note_name, octave):
        """
        Enhanced converter that better handles rare note spellings and adjusts
        notes outside the normal piano range.
        """
        
        # Step 1: Normalize the note name for unusual enharmonics
        normalized_note = UpdatedKeyMapper.normalize_note_name(note_name)
        
        # Step 2: Adjust octave to fit within playable range
        adjusted_octave = UpdatedKeyMapper.adjust_octave_for_range(octave)
        
        # Step 3: Use the original mapper for actual conversion
        return convert_standard_note_to_custom(normalized_note, adjusted_octave)

def list_and_select_mxl_file(directory=None):
    """
    Scans the directory for MXL files, lists them, and prompts user to select one.
    Returns the full path to the selected MXL file or None.
    """
    if directory is None:
        directory = r"c:\Users\domef\OneDrive\Desktop\HPMA_Piano\mxl"
    
    print(f"\n--- Available MXL Files in '{directory}' ---")
    
    # Find all MXL files
    mxl_pattern = os.path.join(directory, "*.mxl")
    mxl_files = glob.glob(mxl_pattern)
    
    if not mxl_files:
        print(f"No .mxl files found in '{directory}'.")
        return None
    
    # Display the list of MXL files
    for i, mxl_file in enumerate(mxl_files):
        filename = os.path.basename(mxl_file)
        print(f"[{i+1}] {filename}")
    
    while True:
        choice = input("Enter the number of the MXL file to convert (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            return None
        try:
            file_index = int(choice) - 1
            if 0 <= file_index < len(mxl_files):
                selected_file = mxl_files[file_index]
                print(f"✓ Selected: {os.path.basename(selected_file)}")
                return selected_file
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'.")

def get_custom_tempo(original_tempo):
    """
    Prompts user to enter a custom tempo or use the original.
    Returns the tempo to use.
    """
    print(f"\n--- Tempo Selection ---")
    print(f"Original tempo from MXL file: {original_tempo} BPM")
    
    while True:
        tempo_input = input(f"Enter custom tempo (BPM) or press Enter to use original ({original_tempo}): ").strip()
        
        if not tempo_input:
            # Use original tempo
            print(f"✓ Using original tempo: {original_tempo} BPM")
            return original_tempo
        
        try:
            custom_tempo = float(tempo_input)
            if custom_tempo <= 0:
                print("Tempo must be greater than 0. Please try again.")
                continue
            if custom_tempo > 300:
                print("Warning: Very high tempo (>300 BPM). Are you sure? (y/n)")
                confirm = input().strip().lower()
                if confirm != 'y':
                    continue
            
            print(f"✓ Using custom tempo: {custom_tempo} BPM")
            return custom_tempo
        except ValueError:
            print("Invalid tempo. Please enter a number or press Enter for original.")

def get_custom_time_signature(original_time_signature):
    """
    Prompts user to enter a custom time signature or use the original.
    Returns the time signature to use.
    """
    print(f"\n--- Time Signature Selection ---")
    print(f"Original time signature from MXL file: {original_time_signature}")
    print("Common time signatures: 4/4, 3/4, 2/4, 6/8, 9/8, 12/8")
    
    while True:
        time_sig_input = input(f"Enter custom time signature (e.g., 4/4, 3/4) or press Enter to use original ({original_time_signature}): ").strip()
        
        if not time_sig_input:
            # Use original time signature
            print(f"✓ Using original time signature: {original_time_signature}")
            return original_time_signature
        
        try:
            # Validate time signature format
            if '/' not in time_sig_input:
                print("Invalid format. Please use format like '4/4' or '3/4'.")
                continue
            
            numerator_str, denominator_str = time_sig_input.split('/')
            numerator = int(numerator_str.strip())
            denominator = int(denominator_str.strip())
            
            if numerator <= 0 or denominator <= 0:
                print("Both numerator and denominator must be positive numbers.")
                continue
            
            # Check if denominator is a power of 2 (common in music)
            if denominator not in [1, 2, 4, 8, 16, 32]:
                print(f"Warning: Unusual denominator '{denominator}'. Common values are 1, 2, 4, 8, 16, 32.")
                confirm = input("Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            custom_time_sig = f"{numerator}/{denominator}"
            print(f"✓ Using custom time signature: {custom_time_sig}")
            return custom_time_sig
            
        except ValueError:
            print("Invalid format. Please use format like '4/4' or '3/4'.")

@dataclass
class SustainedNote:
    """Represents a note that can be sustained over time"""
    note_str: str        # Note format like "C-4" or "G#-5"
    start_time: float    # Start time in seconds
    end_time: float      # End time in seconds
    clef_type: str       # "treble" or "bass"
    part_id: int         # The part/staff number
    voice_id: Optional[int] = None  # Voice number within the part/staff (if applicable)
    staff_distance: Optional[float] = None  # Distance from middle of staff (positive=above, negative=below)
    midi_pitch: Optional[int] = None  # MIDI pitch value for more accurate sorting/comparison
    is_cross_staff: bool = False  # Flag for notes that cross between staves
    role: str = "accompaniment"  # Musical role: "melody", "accompaniment", or "bass"
    
    def is_active_at(self, time: float, tolerance: float = 0.001) -> bool:
        """Check if this note is active (being held) at the given time"""
        return (self.start_time <= time + tolerance) and (time <= self.end_time + tolerance)
    
    @property
    def duration(self) -> float:
        """Get the duration of this note in seconds"""
        return self.end_time - self.start_time
        
    def determine_role(self, is_top_note: bool = False, voice_priorities: Dict[int, str] = None) -> str:
        """
        Determine the musical role of this note based on clef, pitch, and position.
        
        Args:
            is_top_note: Whether this is the highest note in a group at this time point
            voice_priorities: Optional dictionary mapping voice_ids to roles
        
        Returns:
            String role: "melody", "accompaniment", or "bass"
        """
        # If voice priorities are provided and this note's voice is specified
        if voice_priorities and self.voice_id is not None and self.voice_id in voice_priorities:
            return voice_priorities[self.voice_id]
            
        # Bass clef notes typically are bass or accompaniment
        if self.clef_type == "bass":
            # Very low notes are likely bass
            if self.midi_pitch is not None and self.midi_pitch < 48:  # Below C3
                return "bass"
            return "accompaniment"
            
        # Treble clef processing
        if self.clef_type == "treble":
            # Top notes in treble clef are often melody
            if is_top_note:
                return "melody"
            
            # Higher notes in treble are more likely to be melody
            if self.midi_pitch is not None:
                if self.midi_pitch >= 72:  # C5 and above - more likely melody
                    return "melody"
                else:
                    # Lower treble notes might be inner voices or accompaniment 
                    return "accompaniment"
        
        # Default case
        return "accompaniment"

def extract_musical_metadata(score):
    """Extract all musical metadata that affects performance"""
    metadata = {}
    
    # Time Signature
    time_sigs = score.flatten().getElementsByClass(meter.TimeSignature)
    if time_sigs:
        ts = time_sigs[0]
        metadata['time_signature'] = f"{ts.numerator}/{ts.denominator}"
        metadata['beats_per_measure'] = ts.numerator
        metadata['beat_unit'] = ts.denominator
        metadata['feel'] = determine_musical_feel(ts.numerator, ts.denominator)
    else:
        metadata['time_signature'] = "4/4"
        metadata['beats_per_measure'] = 4
        metadata['beat_unit'] = 4
        metadata['feel'] = "common_time"
    
    # Key Signature
    keys = score.flatten().getElementsByClass(key.KeySignature)
    if keys:
        k = keys[0]
        metadata['key_signature'] = str(k)
        metadata['sharps'] = k.sharps
        metadata['mode'] = getattr(k, 'mode', 'major')
    else:
        metadata['key_signature'] = "C major"
        metadata['sharps'] = 0
        metadata['mode'] = "major"
    
    # Tempo
    tempos = score.flatten().getElementsByClass(tempo.TempoIndication)
    metronomes = score.flatten().getElementsByClass(tempo.MetronomeMark)
    
    if metronomes:
        # Handle MetronomeMark
        metronome = metronomes[0]
        if hasattr(metronome, 'number') and metronome.number is not None:
            metadata['tempo_bpm'] = int(metronome.number)
        else:
            metadata['tempo_bpm'] = 120  # Default
        metadata['tempo_marking'] = str(metronome)
    elif tempos:
        # Try to extract BPM from tempo indication
        tempo_obj = tempos[0]
        metadata['tempo_marking'] = str(tempo_obj)
        if hasattr(tempo_obj, 'number') and tempo_obj.number is not None:
            metadata['tempo_bpm'] = int(tempo_obj.number)
        else:
            metadata['tempo_bpm'] = 120  # Default if can't extract
    else:
        metadata['tempo_bpm'] = 120
        metadata['tempo_marking'] = "Moderate"
    
    # Expression markings
    expressions_marks = score.flatten().getElementsByClass(expressions.TextExpression)
    if expressions_marks:
        metadata['expression'] = expressions_marks[0].content
    
    # Dynamics
    dynamics_marks = score.flatten().getElementsByClass(dynamics.Dynamic)
    if dynamics_marks:
        metadata['initial_dynamic'] = dynamics_marks[0].value
    
    # Analyze clefs and parts
    clef_analysis = {}
    
    # Detect if this is likely a piano score by examining the parts and staves
    is_piano_score = False
    part_count = len(score.parts)
    
    # Check for piano staff grouping - typically 2 parts with treble and bass clef
    if part_count == 2:
        # Get clefs for both parts
        part0_clefs = score.parts[0].flatten().getElementsByClass(clef.Clef)
        part1_clefs = score.parts[1].flatten().getElementsByClass(clef.Clef)
        
        # Check if part 0 has treble clef and part 1 has bass clef - typical for piano music
        has_treble = any(isinstance(c, clef.TrebleClef) for c in part0_clefs) if part0_clefs else False
        has_bass = any(isinstance(c, clef.BassClef) for c in part1_clefs) if part1_clefs else False
        
        if has_treble and has_bass:
            is_piano_score = True
    
    # Store piano score detection
    metadata['is_piano_score'] = is_piano_score
    
    # Process each part's clef
    for part_idx, part in enumerate(score.parts):
        # Get all clefs in this part
        part_clefs = part.flatten().getElementsByClass(clef.Clef)
        
        # Process the first clef (most common case)
        if part_clefs:
            primary_clef = part_clefs[0]
            clef_type = type(primary_clef).__name__
            clef_name = primary_clef.name
            
            # Check for octave shifts
            if hasattr(primary_clef, 'octaveChange') and primary_clef.octaveChange:
                if primary_clef.octaveChange == 1:
                    clef_name += '8va'  # Add octave up indicator
                elif primary_clef.octaveChange == -1:
                    clef_name += '8vb'  # Add octave down indicator
            
            clef_analysis[part_idx] = {
                'type': clef_type,
                'name': clef_name
            }
            
            # Check for multiple clefs in one part (less common but possible)
            if len(part_clefs) > 1:
                clef_analysis[part_idx]['multiple_clefs'] = True
                clef_analysis[part_idx]['secondary_clefs'] = [
                    {'type': type(c).__name__, 'name': c.name}
                    for c in part_clefs[1:]
                ]
        else:
            # Default to treble if no clef specified
            clef_analysis[part_idx] = {'type': 'TrebleClef', 'name': 'treble'}
    
    metadata['clef_analysis'] = clef_analysis
    metadata['num_parts'] = part_count
    
    return metadata

def identify_melody_and_accompaniment(notes_in_interval):
    """
    Separate notes into melody, accompaniment, and bass categories.
    
    Args:
        notes_in_interval: List of SustainedNote objects active at a specific time interval
    
    Returns:
        Tuple of (melody_notes, accompaniment_notes, bass_notes) - each a set of note_str values
    """
    if not notes_in_interval:
        return set(), set(), set()
    
    # Step 1: Find the highest note by MIDI pitch (likely the melody)
    highest_note = None
    for note in notes_in_interval:
        if note.midi_pitch is not None:
            if highest_note is None or note.midi_pitch > highest_note.midi_pitch:
                highest_note = note
    
    # Step 2: Mark roles for all notes
    melody_notes = set()
    accompaniment_notes = set()
    bass_notes = set()
    
    for note in notes_in_interval:
        # Determine if this is the top note
        is_top_note = (highest_note is not None and note is highest_note)
        
        # Assign role based on note properties
        role = note.determine_role(is_top_note=is_top_note)
        note.role = role
        
        # Add to appropriate set
        if role == "melody":
            melody_notes.add(note.note_str)
        elif role == "bass":
            bass_notes.add(note.note_str)
        else:
            accompaniment_notes.add(note.note_str)
    
    # If no melody was identified but we have notes, use the highest as melody
    if not melody_notes and highest_note is not None:
        melody_notes.add(highest_note.note_str)
        # Remove it from wherever it was
        if highest_note.note_str in accompaniment_notes:
            accompaniment_notes.remove(highest_note.note_str)
        if highest_note.note_str in bass_notes:
            bass_notes.remove(highest_note.note_str)
    
    return melody_notes, accompaniment_notes, bass_notes

def determine_musical_feel(numerator, denominator):
    """
    Determine the musical feel based on time signature.
    This affects how notes are played and interpreted rhythmically.
    """
    # Simple time signatures
    if denominator in [2, 4, 8]:
        # Simple Duple
        if numerator == 2:
            return "simple_duple"
        # Simple Triple (like waltz)
        elif numerator == 3:
            return "waltz" if denominator == 4 else "simple_triple"
        # Simple Quadruple (common time)
        elif numerator == 4:
            return "common_time"
            
    # Compound time signatures
    if denominator in [8, 16]:
        # Compound Duple (6/8)
        if numerator == 6:
            return "compound_duple"
        # Compound Triple (9/8)
        elif numerator == 9:
            return "compound_triple"
        # Compound Quadruple (12/8)
        elif numerator == 12:
            return "compound_quadruple"
    
    # Irregular time signatures
    if numerator in [5, 7, 11, 13]:
        return "irregular"
        
    # Cut time
    if numerator == 2 and denominator == 2:
        return "cut_time"
    
    # Odd or complex time signatures
    return "complex"

def apply_time_signature_feel(duration_seconds, time_signature_feel, beat_position=None):
    """
    Apply subtle rhythmic timing adjustments based on time signature feel.
    This improves the musicality of the performance by adding slight
    variations in note timing based on the musical style.
    
    Parameters:
    - duration_seconds: The nominal duration in seconds
    - time_signature_feel: The musical feel (from determine_musical_feel)
    - beat_position: The position within the measure (0 = first beat)
    
    Returns:
    - Adjusted duration in seconds
    """
    # No position provided or no modification needed
    if beat_position is None:
        return duration_seconds
        
    # Default adjustment factor (no change)
    adjustment_factor = 1.0
    
    # Apply subtle timing variations based on the musical feel
    if time_signature_feel == "waltz":
        # In waltz (3/4), emphasize first beat slightly
        if beat_position < 0.1:  # First beat
            adjustment_factor = 1.02  # Very slightly longer
        elif 0.9 < beat_position < 1.1:  # Second beat
            adjustment_factor = 0.98  # Slightly shorter
        elif 1.9 < beat_position < 2.1:  # Third beat
            adjustment_factor = 0.99  # Very slightly shorter
    
    elif time_signature_feel == "common_time":
        # In 4/4, subtle emphasis on beats 1 and 3
        if beat_position < 0.1:  # Beat 1
            adjustment_factor = 1.015
        elif 1.9 < beat_position < 2.1:  # Beat 3
            adjustment_factor = 1.01
    
    elif time_signature_feel == "compound_duple":
        # For 6/8, emphasize beats 1 and 4
        if beat_position < 0.1:  # Beat 1
            adjustment_factor = 1.02
        elif 2.9 < beat_position < 3.1:  # Beat 4
            adjustment_factor = 1.01
    
    elif time_signature_feel == "cut_time":
        # For 2/2, strong emphasis on beat 1
        if beat_position < 0.1:
            adjustment_factor = 1.03
    
    # Apply the adjustment, ensuring we don't make very short notes too short
    min_duration = 0.05  # Don't let notes get shorter than 50ms
    adjusted_duration = duration_seconds * adjustment_factor
    
    if adjusted_duration < min_duration:
        return min_duration
        
    return adjusted_duration

def identify_clef_type(element, metadata, part_idx):
    """
    Identify the clef type for a given element more accurately.
    Uses multiple methods to determine the correct clef:
    1. First checks metadata from explicit clef analysis
    2. Looks for piano staff groupings
    3. Examines position on staff and actual pitch
    4. Falls back to octave threshold as last resort
    """
    try:
        # Method 1: Use clef information from metadata if available
        if 'clef_analysis' in metadata and part_idx in metadata['clef_analysis']:
            clef_info = metadata['clef_analysis'][part_idx]
            # Check for special clef types
            if 'Bass' in clef_info['type'] or 'bass' in clef_info['name']:
                return "bass"
            elif '8vb' in clef_info['name']:  # Treble clef 8vb (sounds octave lower)
                return "bass"  # Treat as bass since it's in the lower register
            elif '8va' in clef_info['name'] or 'treble8va' in clef_info['name']:  # Treble clef 8va
                return "treble"  # Definitely treble (high register)
            return "treble"  # Default for regular treble clef
        
        # Method 2: Piano grand staff detection
        if metadata.get('is_piano_score', False) and metadata.get('num_parts', 0) == 2:
            # In piano scores, typically part 0 = treble, part 1 = bass
            if part_idx == 0:
                return "treble"
            elif part_idx == 1:
                return "bass"
        
        # Method 3: Based on staff position and pitch
        if hasattr(element, 'pitch'):
            # Single note - check pitch and octave 
            if element.pitch.octave <= 3:
                return "bass"
            elif element.pitch.octave >= 5:
                return "treble"
            else:
                # For octave 4 (middle), use more detailed analysis
                # Middle C (C4) and below typically go to bass clef
                if element.pitch.octave == 4 and element.pitch.step in ['C', 'D']:
                    return "bass"
                return "treble"
                
        elif hasattr(element, 'pitches'):
            # Chord - more sophisticated analysis
            pitches = list(element.pitches)
            
            if not pitches:  # Empty chord (shouldn't happen but check anyway)
                return "treble"
                
            # Calculate the average octave
            avg_octave = sum(pitch.octave for pitch in pitches) / len(pitches)
            
            # Get the lowest and highest pitch
            lowest_pitch = min(pitches, key=lambda p: p.ps)
            highest_pitch = max(pitches, key=lambda p: p.ps)
            
            # Special case for wide-spanning chords that might cross staves
            if highest_pitch.octave - lowest_pitch.octave >= 2:
                # If chord spans multiple octaves, consider it "cross-staff"
                # Use the part_idx as deciding factor
                if part_idx == 0:
                    return "treble"
                else:
                    return "bass"
            
            # For more focused chords, use the average octave
            if avg_octave < 4:
                return "bass"
            return "treble"
    except Exception as e:
        # Log the error but don't crash
        print(f"⚠️  Warning: Error determining clef type: {e}")
    
    # Default to treble if we can't determine
    return "treble"

def extract_note_from_element(element, start_time, quarter_note_duration, metadata, beat_position, part_idx, voice_id=None, verbose=False):
    """
    Extract SustainedNote objects from a music21 element with improved accuracy and error handling.
    
    Parameters:
    - element: The music21 element (note, chord, etc.)
    - start_time: The start time of the element in seconds
    - quarter_note_duration: Duration of quarter note in seconds based on tempo
    - metadata: Musical metadata dictionary
    - beat_position: Position within the measure
    - part_idx: Index of the part/staff
    - voice_id: Optional voice identifier
    - verbose: Whether to print detailed debug info
    
    Returns:
    - List of SustainedNote objects
    """
    sustained_notes = []
    
    if verbose:
        print(f"DEBUG: Processing element: {element}, offset: {element.offset}, duration qL: {element.duration.quarterLength if hasattr(element, 'duration') else 'N/A'}")
    
    try:
        # Skip if element doesn't have duration
        if not hasattr(element, 'duration'):
            if verbose:
                print(f"DEBUG: Skipping element without duration: {element}")
            return []
            
        duration_quarters = element.duration.quarterLength
        
        if verbose:
            print(f"DEBUG: Element: {element.name if hasattr(element, 'name') else type(element)}, Raw Duration (qL): {duration_quarters}")

        # Skip zero or negative duration elements
        if duration_quarters <= 0:
            if verbose:
                print(f"DEBUG: Skipping zero/negative duration element: {element}")
            return []
            
        # Calculate duration in seconds
        duration_seconds = duration_quarters * quarter_note_duration
        
        # For conversion we keep the raw duration.  Any expressive timing is
        # applied later during playback so the text file faithfully reflects the
        # original note lengths.
            
        # Calculate end time
        end_time = start_time + duration_seconds
        
        # Identify which clef this note belongs to
        clef_type = identify_clef_type(element, metadata, part_idx)
          # Case 1: Single Note
        if isinstance(element, note.Note):
            # Calculate staff distance (for cross-staff detection) if available
            staff_distance = None
            if hasattr(element, 'staff') and element.staff is not None:
                staff_distance = element.staff.distanceFromCenter
            
            # Get MIDI pitch for more accurate sorting - essential for melody detection
            midi_pitch = None
            if hasattr(element.pitch, 'midi'):
                midi_pitch = element.pitch.midi
            # Fallback calculation if midi property isn't available
            elif hasattr(element.pitch, 'ps'):  # pitch space value
                midi_pitch = int(element.pitch.ps)
            
            # Use our enhanced note converter
            custom_note = UpdatedKeyMapper.enhanced_convert_note(
                str(element.pitch.name), element.pitch.octave)
            
            if verbose:
                print(f"DEBUG: Note {element.pitch.nameWithOctave} -> Custom: {custom_note}, Clef: {clef_type}, Part: {part_idx}, Voice: {voice_id}")
            
            # Create sustained note if mapping succeeded
            if custom_note and custom_note[0] is not None and custom_note[1] is not None:
                note_value, octave = custom_note
                note_str = f"{note_value}-{octave}"
                
                sustained_notes.append(SustainedNote(
                    note_str=note_str, 
                    start_time=start_time, 
                    end_time=end_time, 
                    clef_type=clef_type,
                    part_id=part_idx,
                    voice_id=voice_id,
                    staff_distance=staff_distance,
                    midi_pitch=midi_pitch,
                    is_cross_staff=False  # Simple notes rarely cross staves
                ))
            else:
                # Log warning for unmapped notes
                print(f"⚠️  Warning: Could not map note {element.pitch.nameWithOctave} to custom format")
        
        # Case 2: Chord
        elif isinstance(element, chord.Chord):
            # Check if this might be a cross-staff chord (large span or special notation)
            chord_span = 0
            if hasattr(element, 'pitches') and len(element.pitches) >= 2:
                lowest = min(element.pitches, key=lambda p: p.midi if hasattr(p, 'midi') else 0)
                highest = max(element.pitches, key=lambda p: p.midi if hasattr(p, 'midi') else 127)
                if hasattr(lowest, 'midi') and hasattr(highest, 'midi'):
                    chord_span = highest.midi - lowest.midi
            
            is_cross_staff_chord = chord_span >= 24  # Two octaves span might indicate cross-staff
                
            if verbose:
                print(f"DEBUG: Chord detected. Pitches: {[p.nameWithOctave for p in element.pitches]}, Span: {chord_span}, Cross-staff: {is_cross_staff_chord}, Clef: {clef_type}")
              # Process each pitch in the chord
            for pitch in element.pitches:
                # Get MIDI pitch with fallback options
                midi_pitch = None
                if hasattr(pitch, 'midi'):
                    midi_pitch = pitch.midi
                elif hasattr(pitch, 'ps'):  # pitch space value
                    midi_pitch = int(pitch.ps)
                
                # Use our enhanced note converter
                custom_note = UpdatedKeyMapper.enhanced_convert_note(
                    str(pitch.name), pitch.octave)
                
                if verbose:
                    print(f"DEBUG:   Chord note {pitch.nameWithOctave} -> Custom: {custom_note}")
                
                # Create sustained note if mapping succeeded
                if custom_note and custom_note[0] is not None and custom_note[1] is not None:
                    note_value, octave = custom_note
                    note_str = f"{note_value}-{octave}"
                    
                    sustained_notes.append(SustainedNote(
                        note_str=note_str, 
                        start_time=start_time, 
                        end_time=end_time, 
                        clef_type=clef_type,
                        part_id=part_idx,
                        voice_id=voice_id,
                        staff_distance=None,  # Staff distance not typically available for individual chord notes
                        midi_pitch=midi_pitch,
                        is_cross_staff=is_cross_staff_chord
                    ))
                else:
                    # Log warning for unmapped notes
                    print(f"⚠️  Warning: Could not map chord pitch {pitch.nameWithOctave} to custom format")
    
    except Exception as e:
        print(f"⚠️  Error extracting note from element: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    
    return sustained_notes

def convert_mxl_with_dual_clef(mxl_file_path, output_path=None, custom_tempo=None, custom_time_signature=None, verbose=False):
    """
    Convert MXL to text format preserving both treble and bass clef information with improved handling.
    
    Parameters:
    - mxl_file_path: Path to the MXL file
    - output_path: Path for output file (or auto-generated if None)
    - custom_tempo: Custom tempo to override file's original tempo
    - custom_time_signature: Custom time signature to override file's original
    - verbose: Whether to print detailed debug information
    
    Returns:
    - True if conversion succeeded, False otherwise
    """
    if not os.path.exists(mxl_file_path):
        print(f"❌ Error: File '{mxl_file_path}' not found.")
        return False
    
    print(f"Converting '{mxl_file_path}' with improved dual clef handling...")
    
    try:
        # Parse the score
        try:
            score = converter.parse(mxl_file_path)
        except Exception as e:
            print(f"❌ Error parsing MXL file: {e}")
            return False
        
        # Extract musical metadata
        try:
            metadata = extract_musical_metadata(score)
        except Exception as e:
            print(f"⚠️ Warning: Error extracting metadata: {e}. Using defaults.")
            # Create basic default metadata
            metadata = {
                'time_signature': "4/4",
                'beats_per_measure': 4,
                'beat_unit': 4,
                'feel': "common_time",
                'key_signature': "C major",
                'sharps': 0,
                'tempo_bpm': 120,
                'tempo_marking': "Moderate",
                'num_parts': len(score.parts) if hasattr(score, 'parts') else 1,
                'clef_analysis': {}
            }
        
        # Use custom tempo if provided, otherwise use original
        if custom_tempo is not None:
            metadata['tempo_bpm'] = custom_tempo
        
        # Use custom time signature if provided, otherwise use original
        if custom_time_signature is not None:
            metadata['time_signature'] = custom_time_signature
            # Parse the custom time signature to update beats_per_measure and feel
            try:
                numerator, denominator = custom_time_signature.split('/')
                metadata['beats_per_measure'] = int(numerator)
                metadata['beat_unit'] = int(denominator)
                metadata['feel'] = determine_musical_feel(int(numerator), int(denominator))
            except ValueError:
                print(f"⚠️ Warning: Invalid time signature format: {custom_time_signature}. Using original.")
        
        # Display analysis with custom values if any
        if custom_tempo is not None or custom_time_signature is not None:
            print(f"📊 Musical Analysis (Custom Values):")
        else:
            print(f"📊 Musical Analysis:")
        
        print(f"   Time Signature: {metadata['time_signature']} ({metadata['feel']})")
        print(f"   Key: {metadata['key_signature']}")
        print(f"   Tempo: {metadata['tempo_bpm']} BPM")
        
        num_parts = metadata['num_parts']
        print(f"   Parts/Staves: {num_parts}")
        
        if 'clef_analysis' in metadata:
            print(f"   Clef Analysis:")
            for part_idx, clef_info in metadata['clef_analysis'].items():
                print(f"      Part {part_idx+1}: {clef_info['name']}")
        
        if 'expression' in metadata:
            print(f"   Expression: {metadata['expression']}")
        
        # Calculate timing based on actual tempo
        quarter_note_duration = 60.0 / metadata['tempo_bpm']
        
        # Collect ALL notes as SustainedNote objects
        all_sustained_notes = []
        
        if verbose:
            print(f"DEBUG: Total parts in score: {len(score.parts)}")

        # Process each part/staff
        for part_idx, part in enumerate(score.parts):
            if verbose:
                print(f"DEBUG: Processing Part {part_idx} (ID: {part.id if hasattr(part, 'id') else 'N/A'}, Class: {part.__class__.__name__})")
            
            # Get all notes and rests from the part
            try:
                part_elements = part.flatten().notesAndRests
            except Exception as e:
                print(f"⚠️ Warning: Error flattening part {part_idx}: {e}. Skipping this part.")
                continue
            
            if verbose:
                print(f"DEBUG: Part {part_idx} - Found {len(part_elements)} notesAndRests.")
                if part_elements:
                    # Get the last element to check its offset and duration
                    last_el = part_elements[-1]
                    max_offset_in_part = float(last_el.offset)
                    if hasattr(last_el, 'duration') and last_el.duration:
                        max_offset_in_part += float(last_el.duration.quarterLength)
                    print(f"DEBUG: Part {part_idx} - Estimated max quarterLength offset: {max_offset_in_part}")

            # Process each note/rest in this part
            for element_idx, element in enumerate(part_elements):
                try:
                    offset = float(element.offset)
                    start_time = offset * quarter_note_duration
                    beat_position = (offset % metadata['beats_per_measure'])
                    
                    if element.isRest:
                        # Rests are handled differently - they don't add to sustained notes
                        # But we could mark them for debugging
                        if verbose:
                            print(f"DEBUG: Rest at offset {offset}, duration: {element.duration.quarterLength}")
                    else:
                        # Extract notes from this element
                        sustained_notes = extract_note_from_element(
                            element, 
                            start_time, 
                            quarter_note_duration, 
                            metadata, 
                            beat_position, 
                            part_idx, 
                            voice_id=None,
                            verbose=verbose
                        )
                        all_sustained_notes.extend(sustained_notes)
                except Exception as e:
                    print(f"⚠️ Warning: Error processing element {element_idx} in part {part_idx}: {e}")
                    if verbose:
                        print(f"Element: {element}")
                        import traceback
                        traceback.print_exc()
        
        # Check if we extracted any notes
        if not all_sustained_notes:
            print("❌ Error: No valid notes found in the score.")
            return False
        
        if verbose:
            print(f"DEBUG: Total SustainedNote objects collected: {len(all_sustained_notes)}")
            if all_sustained_notes:
                print("DEBUG: First 5 SustainedNote objects:")
                for i, sn in enumerate(all_sustained_notes[:5]):
                    print(f"  {i}: {sn}")
                if len(all_sustained_notes) > 5:
                    print("DEBUG: Last 5 SustainedNote objects:")
                    for i, sn in enumerate(all_sustained_notes[-5:]):
                        print(f"  {len(all_sustained_notes) - 5 + i}: {sn}")

        # Find all unique time points where notes start or end
        time_points = set()
        for note_event in all_sustained_notes:
            # Round to microseconds to avoid floating point artefacts that can
            # lead to spurious very short intervals.
            time_points.add(round(note_event.start_time, 6))
            time_points.add(round(note_event.end_time, 6))
        
        # Ensure 0.0 is a time point if there are notes and the earliest note doesn't start at 0.0
        if all_sustained_notes:
            min_start_time = min(n.start_time for n in all_sustained_notes)
            if min_start_time > 0.001:  # Using a small tolerance
                time_points.add(0.0)
        
        time_points = sorted(list(time_points))
        
        # Filter out very close time points to avoid micro-duration segments
        if time_points:
            unique_time_points = [time_points[0]]
            # Use a very small tolerance to collapse nearly-identical times
            # caused by rounding while keeping true rhythmic divisions.
            tolerance = 0.0005
            
            for i in range(1, len(time_points)):
                if time_points[i] > time_points[i-1] + tolerance:
                    unique_time_points.append(time_points[i])
            
            time_points = unique_time_points        # Generate the song note list with separate melody and accompaniment
        melody_lines = []
        accomp_lines = []
        
        # Configure the output format
        SEPARATE_MELODY_ACCOMPANIMENT = True  # Set to True to separate melody from accompaniment
        
        if len(time_points) >= 2:  # Need at least two time points to form an interval
            for i in range(len(time_points) - 1):
                interval_start_time = time_points[i]
                interval_end_time = time_points[i+1]
                interval_duration = round(interval_end_time - interval_start_time, 6)

                # Skip negligible duration intervals
                if interval_duration <= 0.001:
                    continue

                # Find notes active during this interval
                active_notes = []
                for note_event in all_sustained_notes:
                    # A note (s, e) is active in interval [ts, te) if s < te and e > ts
                    if note_event.start_time < interval_end_time and \
                       note_event.end_time > interval_start_time:
                        active_notes.append(note_event)
                
                # Format the line for output
                if active_notes:
                    if SEPARATE_MELODY_ACCOMPANIMENT:
                        # Categorize notes by musical role
                        melody_notes, accompaniment_notes, bass_notes = identify_melody_and_accompaniment(active_notes)
                        
                        # Process melody notes
                        melody_str = "+".join(sorted(list(melody_notes))) if melody_notes else "R"
                        melody_lines.append(f"{melody_str}:{interval_duration:.3f}")
                        
                        # Process accompaniment and bass notes together
                        accomp_bass_notes = accompaniment_notes.union(bass_notes)
                        accomp_str = "+".join(sorted(list(accomp_bass_notes))) if accomp_bass_notes else "R"
                        accomp_lines.append(f"{accomp_str}:{interval_duration:.3f}")
                    else:
                        # Original method - combine all notes without separation
                        note_strs = {n.note_str for n in active_notes}
                        chord_str = "+".join(sorted(list(note_strs)))
                        melody_lines.append(f"{chord_str}:{interval_duration:.3f}")
                        accomp_lines.append(f"R:{interval_duration:.3f}")  # Empty for accomp
                else:
                    # This interval is a rest for both melody and accompaniment
                    melody_lines.append(f"R:{interval_duration:.3f}")
                    accomp_lines.append(f"R:{interval_duration:.3f}")
            
            # Combine the melody and accompaniment lines
            song_notes_list = []
            song_notes_list.append("# MELODY PART")
            song_notes_list.extend(melody_lines)
            song_notes_list.append("# ACCOMPANIMENT PART")
            song_notes_list.extend(accomp_lines)
                    
        # Check for potential issues
        elif all_sustained_notes and not time_points:
            print("⚠️  Warning: Notes were extracted, but no time points were generated. Output might be empty.")
            return False
        elif all_sustained_notes and len(time_points) == 1:
            print("⚠️  Warning: Only one time point generated. There might be issues with note durations.")
            return False
            
        # Determine output path
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(mxl_file_path))[0]
            output_path = os.path.join("songs", f"{base_name}.txt")
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write output file
        try:
            with open(output_path, "w", encoding="utf-8") as f:                # Write comprehensive musical header
                f.write(f"Generated_from:{mxl_file_path}\n")
                f.write(f"Total_notes:{len(song_notes_list)}\n")
                f.write(f"Time_Signature:{metadata['time_signature']}\n")
                f.write(f"Musical_Feel:{metadata['feel']}\n")
                f.write(f"Key_Signature:{metadata['key_signature']}\n")
                f.write(f"Sharps:{metadata['sharps']}\n")
                f.write(f"Original_BPM:{metadata['tempo_bpm']}\n")
                f.write(f"Tempo_Marking:{metadata.get('tempo_marking', 'Moderate')}\n")
                
                # Add metadata about clefs/staves found
                f.write(f"Parts:{metadata['num_parts']}\n")
                for part_idx, clef_info in metadata.get('clef_analysis', {}).items():
                    f.write(f"Part{part_idx+1}_Clef:{clef_info['name']}\n")
                    
                if 'expression' in metadata:
                    f.write(f"Expression:{metadata['expression']}\n")
                if 'initial_dynamic' in metadata:
                    f.write(f"Initial_Dynamic:{metadata['initial_dynamic']}\n")
                
                # Indicate we're using melody separation
                f.write("Melody_Separation:True\n")
                f.write("Format:NoteValue-Octave:Duration\n")
                f.write("Format_Note:Melody_and_Accompaniment_are_separated\n")
                f.write("---\n")
                
                # Write all notes/chords
                for note_line in song_notes_list:
                    f.write(note_line + "\n")
        except Exception as e:
            print(f"❌ Error writing output file: {e}")
            return False
        
        # Success!
        print(f"✅ Enhanced conversion complete with dual clef support!")
        print(f"   Output: {output_path}")
        print(f"   Notes: {len(song_notes_list)}")
        print(f"   Preserved: Note sustain, both clefs, overlapping notes, time signature, key, tempo")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False

def batch_convert_all_mxl_files(directory=None, force_overwrite=False, verbose=False):
    """
    Convert all MXL files in the directory to enhanced text format with dual clef support
    
    Parameters:
    - directory: Directory containing MXL files
    - force_overwrite: Whether to overwrite existing output files
    - verbose: Whether to print detailed debug information
    
    Returns:
    - True if at least one file was successfully converted, False otherwise
    """
    if directory is None:
        directory = r"c:\Users\domef\OneDrive\Desktop\HPMA_Piano\mxl"
    
    # Find all MXL files
    mxl_pattern = os.path.join(directory, "*.mxl")
    mxl_files = glob.glob(mxl_pattern)
    
    if not mxl_files:
        print(f"❌ No MXL files found in: {directory}")
        return False
    
    print(f"🎵 Found {len(mxl_files)} MXL files for batch conversion:")
    for i, file in enumerate(mxl_files, 1):
        print(f"   {i}. {os.path.basename(file)}")
    
    # Ensure songs directory exists
    songs_dir = os.path.join(os.path.dirname(directory), "songs")
    os.makedirs(songs_dir, exist_ok=True)
    
    # Track conversion results
    successful_conversions = 0
    failed_conversions = 0
    skipped_conversions = 0
    error_files = []
    
    print(f"\n🚀 Starting batch conversion with dual clef handling...")
    print("=" * 60)
    
    # Process each file
    for i, mxl_file in enumerate(mxl_files, 1):
        file_name = os.path.basename(mxl_file)
        base_name = os.path.splitext(file_name)[0]
        output_file = os.path.join(songs_dir, f"{base_name}.txt")
        
        print(f"\n[{i}/{len(mxl_files)}] Processing: {file_name}")
        
        # Check if output already exists
        if os.path.exists(output_file) and not force_overwrite:
            print(f"⏭️  Skipping: {os.path.basename(output_file)} already exists")
            print(f"   Use --force to overwrite existing files")
            skipped_conversions += 1
            continue
        
        # Convert the file
        try:
            success = convert_mxl_with_dual_clef(
                mxl_file, 
                output_file, 
                custom_tempo=None, 
                custom_time_signature=None, 
                verbose=verbose
            )
            
            if success:
                successful_conversions += 1
                print(f"✅ Successfully converted: {os.path.basename(output_file)}")
            else:
                failed_conversions += 1
                error_files.append(file_name)
                print(f"❌ Failed to convert: {file_name}")
        except Exception as e:
            failed_conversions += 1
            error_files.append(file_name)
            print(f"❌ Error converting {file_name}: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    # Summary report
    print("\n" + "=" * 60)
    print(f"📊 BATCH CONVERSION SUMMARY:")
    print(f"   Total MXL files found: {len(mxl_files)}")
    print(f"   ✅ Successfully converted: {successful_conversions}")
    print(f"   ❌ Failed conversions: {failed_conversions}")
    print(f"   ⏭️  Skipped (already exist): {skipped_conversions}")
    
    # Show failed files if any
    if failed_conversions > 0:
        print("\n❌ Files that failed conversion:")
        for i, file in enumerate(error_files, 1):
            print(f"   {i}. {file}")
    
    if successful_conversions > 0:
        print(f"\n🎉 Enhanced text files saved in: {songs_dir}")
        print(f"   All files preserve musical information from both clefs")
        
    return successful_conversions > 0

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Convert MXL files to text format with dual clef support for piano music",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_mxl_dual_clef.py                               # Interactive mode
  python convert_mxl_dual_clef.py waltz.mxl                     # Convert single file
  python convert_mxl_dual_clef.py waltz.mxl songs/custom_waltz.txt  # Custom output path
  python convert_mxl_dual_clef.py --batch-convert               # Convert all files
  python convert_mxl_dual_clef.py --batch-convert --force       # Force overwrite
  python convert_mxl_dual_clef.py --directory /path/to/mxl/files    # Custom directory
  python convert_mxl_dual_clef.py --verbose                     # Enable debug output
        """)
    
    # Main action group
    action_group = parser.add_mutually_exclusive_group(required=False)
    
    # Single file conversion
    action_group.add_argument('input_file', nargs='?', 
                            help='MXL file to convert (leave empty for interactive mode)')
    
    # Batch conversion
    action_group.add_argument('--batch-convert', '-b', action='store_true',
                            help='Convert all MXL files in the directory')
    
    # Interactive mode
    action_group.add_argument('--interactive', '-i', action='store_true',
                            help='Interactive mode to select files and tempo')
    
    # Optional arguments
    parser.add_argument('output_file', nargs='?',
                       help='Output text file path (optional, auto-generated if not provided)')
    
    parser.add_argument('--directory', '-d', 
                       help='Directory to search for MXL files (default: mxl/ subdirectory)')
    
    parser.add_argument('--force', '-f', action='store_true',
                       help='Overwrite existing output files')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose debug output')
    
    parser.add_argument('--version', action='version', 
                       version='MXL Piano Converter 2.0.0',
                       help='Show version information and exit')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        # Set the verbosity flag based on command line arguments
        verbose = args.verbose
        
        if args.batch_convert:
            # Batch conversion mode
            print("🎵 Enhanced MXL Batch Converter with Dual Clef Support")
            print("=" * 50)
            success = batch_convert_all_mxl_files(
                directory=args.directory, 
                force_overwrite=args.force,
                verbose=verbose
            )
            sys.exit(0 if success else 1)
            
        elif args.interactive or (not args.input_file and not args.batch_convert):
            # Interactive mode - either explicitly requested or no input file provided
            print("🎵 Enhanced MXL Converter - Interactive Mode")
            print("=" * 40)
            
            # Step 1: Select MXL file
            mxl_file_to_convert = list_and_select_mxl_file(args.directory)
            
            if not mxl_file_to_convert:
                print("❌ No file selected for conversion.")
                sys.exit(1)
            
            # Step 2: Parse file to get original tempo and time signature
            try:
                score = converter.parse(mxl_file_to_convert)
                metadata = extract_musical_metadata(score)
                original_tempo = metadata['tempo_bpm']
                original_time_signature = metadata['time_signature']
            except Exception as e:
                print(f"⚠️  Warning: Could not read original metadata from file: {e}. Using defaults.")
                original_tempo = 120
                original_time_signature = "4/4"
            
            # Step 3: Get custom tempo
            custom_tempo = get_custom_tempo(original_tempo)
            
            # Step 4: Get custom time signature
            custom_time_signature = get_custom_time_signature(original_time_signature)
            
            # Step 5: Convert with selected values
            print(f"\n🔄 Converting with tempo: {custom_tempo} BPM and time signature: {custom_time_signature}")
            success = convert_mxl_with_dual_clef(
                mxl_file_to_convert, 
                args.output_file, 
                custom_tempo, 
                custom_time_signature,
                verbose=verbose
            )
            sys.exit(0 if success else 1)
        
        elif args.input_file:
            # Single file conversion mode
            if not os.path.exists(args.input_file):
                print(f"❌ Error: Input file '{args.input_file}' not found.")
                sys.exit(1)
            
            print("🎵 Enhanced MXL Converter with Dual Clef Support")
            print("=" * 30)
            success = convert_mxl_with_dual_clef(
                args.input_file, 
                args.output_file,
                verbose=verbose
            )
            sys.exit(0 if success else 1)
            
        else:
            # This should never happen due to argument structure, but just in case
            print("❌ Invalid combination of arguments. Use --help for usage information.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Conversion interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)



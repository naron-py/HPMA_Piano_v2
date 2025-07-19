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

from table_utils import SONGS_DIR, print_table

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
    mxl_files = sorted(glob.glob(mxl_pattern))

    if not mxl_files:
        print(f"No .mxl files found in '{directory}'.")
        return None

    rows = []
    songs_dir = SONGS_DIR

    for i, mxl_file in enumerate(mxl_files, 1):
        filename = os.path.basename(mxl_file)
        bpm = "?"
        ts = "?"
        try:
            score = converter.parse(mxl_file)
            meta = extract_musical_metadata(score)
            bpm = meta.get("tempo_bpm", "?")
            ts = meta.get("time_signature", "?")
        except Exception:
            pass

        txt_name = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(songs_dir, txt_name)
        exists = "Yes" if os.path.exists(txt_path) else "No"
        rows.append([i, filename, bpm, ts, exists])

    print_table(["No.", "Song Name", "BPM", "Time Sig", "Converted"], rows)
    
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
    
    def is_active_at(self, time: float, tolerance: float = 0.001) -> bool:
        """Check if this note is active (being held) at the given time"""
        return (self.start_time <= time + tolerance) and (time <= self.end_time + tolerance)
    
    @property
    def duration(self) -> float:
        """Get the duration of this note in seconds"""
        return self.end_time - self.start_time

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
    
    for part_idx, part in enumerate(score.parts):
        part_clefs = part.flatten().getElementsByClass(clef.Clef) # Changed from part.flat
        if part_clefs:
            primary_clef = part_clefs[0]
            clef_analysis[part_idx] = {
                'type': type(primary_clef).__name__,
                'name': primary_clef.name
            }
        else:
            # Default to treble if no clef specified
            clef_analysis[part_idx] = {'type': 'TrebleClef', 'name': 'treble'}
    
    metadata['clef_analysis'] = clef_analysis
    metadata['num_parts'] = len(score.parts)
    
    return metadata

def determine_musical_feel(numerator, denominator):
    """Determine the musical feel based on time signature"""
    if numerator == 3 and denominator == 4:
        return "waltz"
    elif numerator == 4 and denominator == 4:
        return "common_time"
    elif numerator == 6 and denominator == 8:
        return "compound_duple"
    elif numerator == 9 and denominator == 8:
        return "compound_triple"
    elif numerator == 12 and denominator == 8:
        return "compound_quadruple"
    elif numerator == 2:
        return "duple"
    else:
        return "complex"

def apply_time_signature_feel(duration_seconds, time_signature_feel, beat_position=None):
    """Apply rhythmic feel based on time signature"""
    if time_signature_feel == "waltz":
        # In waltz, beat 1 is strongest, beats 2&3 are weaker
        # Could add slight timing variations or emphasis
        return duration_seconds
    elif time_signature_feel == "common_time":
        # In 4/4, beats 1&3 are strong, 2&4 are weak
        return duration_seconds
    else:
        return duration_seconds

def identify_clef_type(element, metadata, part_idx):
    """Identify the clef type for a given element"""
    try:
        # First, see if the metadata has detected clefs from analysis
        if 'clef_analysis' in metadata and part_idx in metadata['clef_analysis']:
            clef_info = metadata['clef_analysis'][part_idx]
            if 'Bass' in clef_info['type'] or 'bass' in clef_info['name']:
                return "bass"
            return "treble"
        
        # If we can't determine from the metadata, try to infer from the element
        if hasattr(element, 'pitch'):
            # Single note - check the octave
            if element.pitch.octave < 4:
                return "bass"
            return "treble"
        elif hasattr(element, 'pitches'):
            # Chord - check the average octave
            avg_octave = sum(pitch.octave for pitch in element.pitches) / len(element.pitches)
            if avg_octave < 4:
                return "bass"
            return "treble"
    except:
        pass
    
    # Default to treble if we can't determine
    return "treble"

def extract_note_from_element(element, start_time, quarter_note_duration, metadata, beat_position, part_idx, voice_id=None, verbose=False):
    """Extract SustainedNote objects from a music21 element"""
    from key_mapper import convert_standard_note_to_custom
    
    sustained_notes = []
    # ---- START DEBUG ----
    if verbose:
        print(f"DEBUG: Processing element: {element}, offset: {element.offset}, duration qL: {element.duration.quarterLength if hasattr(element, 'duration') else 'N/A'}")
    # if hasattr(element, 'pitch'):
    #     print(f"DEBUG: Element is Note: {element.pitch}")
    # elif hasattr(element, 'pitches'):
    #     print(f"DEBUG: Element is Chord: {[p for p in element.pitches]}")
    # elif element.isRest:
    #     print(f"DEBUG: Element is Rest")
    # else:
    #     print(f"DEBUG: Element is Other: {type(element)}")
    # ---- END DEBUG ----
    
    try:
        duration_quarters = element.duration.quarterLength
        # ---- START DEBUG ----
        # print(f"DEBUG: Element: {element.name if hasattr(element, 'name') else type(element)}, Raw Duration (qL): {duration_quarters}")
        # ---- END DEBUG ----

        if duration_quarters <= 0:
            # ---- START DEBUG ----
            # print(f"DEBUG: Skipping zero/negative duration element: {element}")
            # ---- END DEBUG ----
            return []  # Skip zero-duration notes
            
        duration_seconds = duration_quarters * quarter_note_duration
        duration_seconds = apply_time_signature_feel(duration_seconds, metadata['feel'], beat_position)
        end_time = start_time + duration_seconds
        
        # Identify which clef this note belongs to
        clef_type = identify_clef_type(element, metadata, part_idx)
        
        if isinstance(element, note.Note):
            # Single note
            custom_note = convert_standard_note_to_custom(str(element.pitch.name), element.pitch.octave)
            # ---- START DEBUG ----
            # print(f"DEBUG: Note {element.pitch.nameWithOctave} -> Custom: {custom_note}, Clef: {clef_type}, Part: {part_idx}, Voice: {voice_id}")
            # ---- END DEBUG ----
            if custom_note and custom_note[0] is not None and custom_note[1] is not None:
                note_value, octave = custom_note
                note_str = f"{note_value}-{octave}"
                sustained_notes.append(SustainedNote(
                    note_str=note_str, 
                    start_time=start_time, 
                    end_time=end_time, 
                    clef_type=clef_type,
                    part_id=part_idx,
                    voice_id=voice_id
                ))
        
        elif isinstance(element, chord.Chord):
            # Chord - extract each note in the chord
            # ---- START DEBUG ----
            # print(f"DEBUG: Chord detected. Pitches: {[p.nameWithOctave for p in element.pitches]}, Clef: {clef_type}, Part: {part_idx}, Voice: {voice_id}")
            # ---- END DEBUG ----
            for pitch in element.pitches:
                custom_note = convert_standard_note_to_custom(str(pitch.name), pitch.octave)
                # ---- START DEBUG ----
                # print(f"DEBUG:   Chord note {pitch.nameWithOctave} -> Custom: {custom_note}")
                # ---- END DEBUG ----
                if custom_note and custom_note[0] is not None and custom_note[1] is not None:
                    note_value, octave = custom_note
                    note_str = f"{note_value}-{octave}"
                    sustained_notes.append(SustainedNote(
                        note_str=note_str, 
                        start_time=start_time, 
                        end_time=end_time, 
                        clef_type=clef_type,
                        part_id=part_idx,
                        voice_id=voice_id
                    ))
    
    except Exception as e:
        print(f"⚠️  Error extracting note from element: {e} (Element: {element})") # Added element to error print
    
    return sustained_notes

def convert_mxl_with_dual_clef(mxl_file_path, output_path=None, custom_tempo=None, custom_time_signature=None, start_only=False, verbose=False):
    """Convert MXL to text format preserving both treble and bass clef information.

    If ``start_only`` is True only notes starting at the same time are grouped
    together.  Sustained notes from previous groups are not repeated in later
    chords which can make the resulting text file easier to read.  This option
    provides a simplified representation at the cost of losing some sustain
    information.
    """
    
    if not os.path.exists(mxl_file_path):
        print(f"❌ Error: File '{mxl_file_path}' not found.")
        return False

    if verbose:
        print(f"Converting '{mxl_file_path}' with improved dual clef handling...")
    
    try:
        score = converter.parse(mxl_file_path)
        
        # Extract musical metadata
        metadata = extract_musical_metadata(score)
        
        # Use custom tempo if provided, otherwise use original
        if custom_tempo is not None:
            metadata['tempo_bpm'] = custom_tempo
        
        # Use custom time signature if provided, otherwise use original
        if custom_time_signature is not None:
            metadata['time_signature'] = custom_time_signature
            # Parse the custom time signature to update beats_per_measure and feel
            numerator, denominator = custom_time_signature.split('/')
            metadata['beats_per_measure'] = int(numerator)
            metadata['beat_unit'] = int(denominator)
            metadata['feel'] = determine_musical_feel(int(numerator), int(denominator))
        
        # Display analysis with custom values if any
        if verbose:
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
        
        # ---- START DEBUG VIVA ----
        # print(f"DEBUG_VIVA: Total parts in score: {len(score.parts)}")
        # ---- END DEBUG VIVA ----

        for part_idx, part in enumerate(score.parts):
            # ---- START DEBUG VIVA ----
            if verbose:
                print(f"DEBUG_VIVA: Processing Part {part_idx} (ID: {part.id if hasattr(part, 'id') else 'N/A'}, Class: {part.__class__.__name__})")
            # ---- END DEBUG VIVA ----
            
            part_elements = part.flatten().notesAndRests # Get all notes and rests from the part directly
            
            # ---- START DEBUG VIVA ----
            if verbose:
                print(f"DEBUG_VIVA: Part {part_idx} - Found {len(part_elements)} notesAndRests directly from part.flatten().")
            max_offset_in_part = 0.0
            if part_elements:
                # Get the last element to check its offset and duration to estimate part length
                last_el = part_elements[-1]
                max_offset_in_part = float(last_el.offset)
                if hasattr(last_el, 'duration') and last_el.duration:
                    max_offset_in_part += float(last_el.duration.quarterLength)
            if verbose:
                print(f"DEBUG_VIVA: Part {part_idx} - Estimated max quarterLength offset in part: {max_offset_in_part}")
            # ---- END DEBUG VIVA ----

            for element_idx, element in enumerate(part_elements):
                offset = float(element.offset)
                start_time = offset * quarter_note_duration
                beat_position = (offset % metadata['beats_per_measure'])
                
                if element.isRest:
                    # Rests are handled differently - they don't add to sustained notes
                    pass
                else:
                    # Extract notes from this element
                    sustained_notes = extract_note_from_element(
                        element,
                        start_time,
                        quarter_note_duration,
                        metadata,
                        beat_position,
                        part_idx,
                        voice_id=None,  # Passing None for voice_id as we are not iterating explicit voices here
                        verbose=verbose
                    )
                    all_sustained_notes.extend(sustained_notes)
        
        if not all_sustained_notes:
            print("⚠️  No valid notes found in the score.")
            return False

        # ---- START NEW DEBUG ----
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
        # ---- END NEW DEBUG ----

        song_notes_list = []

        if start_only:
            # Group notes by their start time.  Notes that continue sounding are
            # not repeated in later chords.  This produces a simpler output that
            # can be easier to follow at the expense of exact sustain
            # information.
            grouped = {}
            tolerance = 0.001
            for n in all_sustained_notes:
                st = n.start_time
                matched = None
                for t in grouped.keys():
                    if abs(t - st) <= tolerance:
                        matched = t
                        break
                if matched is None:
                    grouped[st] = []
                    matched = st
                grouped[matched].append(n)

            last_time = 0.0
            for st in sorted(grouped.keys()):
                if st - last_time > tolerance:
                    song_notes_list.append(f"R:{st - last_time:.3f}")

                notes_here = grouped[st]
                chord = "+".join(sorted({n.note_str for n in notes_here}))
                chord_duration = min(n.end_time for n in notes_here) - st
                song_notes_list.append(f"{chord}:{chord_duration:.3f}")
                last_time = st + chord_duration

        else:
            # Original behaviour - compute chords for every interval where the
            # set of sounding notes changes.  This preserves sustain information
            # but can result in large chords if many notes overlap.

            # Find all unique time points where notes start or end
            time_points = set()
            for note_event in all_sustained_notes:  # Changed 'note' to 'note_event' for clarity
                time_points.add(note_event.start_time)
                time_points.add(note_event.end_time)

            # Ensure 0.0 is a time point if there are notes and the earliest note doesn't start at 0.0
            # This captures any initial rest.
            if all_sustained_notes:
                min_start_time = min(n.start_time for n in all_sustained_notes)
                if min_start_time > 0.001:  # Using a small tolerance
                    time_points.add(0.0)

            time_points = sorted(list(time_points))

            # Filter out very close time points to avoid micro-duration segments if any float precision issues occurred
            if time_points:
                unique_time_points = [time_points[0]]
                for i in range(1, len(time_points)):
                    if time_points[i] > time_points[i-1] + 0.0001:  # Tolerance for distinct points
                        unique_time_points.append(time_points[i])
                time_points = unique_time_points

            if len(time_points) >= 2:  # Need at least two time points to form an interval
                for i in range(len(time_points) - 1):
                    interval_start_time = time_points[i]
                    interval_end_time = time_points[i + 1]
                    interval_duration = interval_end_time - interval_start_time

                    # Skip zero or negligible duration intervals
                    if interval_duration <= 0.001:
                        continue

                    notes_in_interval = set()
                    for note_event in all_sustained_notes:
                        # A note (s, e) is active in the interval [ts, te)
                        # if the note's own active period [s, e) overlaps with [ts, te).
                        # Overlap condition: s < te and e > ts.
                        # (Assuming note_event.end_time is exclusive end of sounding period)
                        if note_event.start_time < interval_end_time and \
                           note_event.end_time > interval_start_time:
                            notes_in_interval.add(note_event.note_str)

                    if notes_in_interval:
                        chord_str = "+".join(sorted(list(notes_in_interval)))
                        song_notes_list.append(f"{chord_str}:{interval_duration:.3f}")
                    else:
                        # This interval is a rest
                        song_notes_list.append(f"R:{interval_duration:.3f}")
            elif all_sustained_notes and not time_points:  # Should not happen if all_sustained_notes is populated
                print(
                    "⚠️  Warning: Notes were extracted, but no time points were generated. Output might be empty or incorrect.")
            elif all_sustained_notes and len(time_points) == 1:  # e.g. all notes are instantaneous (duration 0)
                print(
                    "⚠️  Warning: Only one time point generated for existing notes. Output might be empty or incorrect.")
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(mxl_file_path))[0]
            output_path = os.path.join("songs", f"{base_name}.txt")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write enhanced song file with complete musical information
        with open(output_path, "w", encoding="utf-8") as f:
            # Write comprehensive musical header
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
            f.write("Format:NoteValue-Octave:Duration\n")
            f.write("---\n")
            
            for note_line in song_notes_list:
                f.write(note_line + "\n")
        
        if verbose:
            print(f"✅ Enhanced conversion complete with dual clef support!")
            print(f"   Output: {output_path}")
            print(f"   Notes: {len(song_notes_list)}")
            print(f"   Preserved: Note sustain, both clefs, overlapping notes, time signature, key, tempo")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False

def batch_convert_all_mxl_files(directory=None, force_overwrite=False, start_only=False, verbose=False):
    """Convert all MXL files in the directory to enhanced text format with dual clef support"""
    if directory is None:
        directory = r"c:\Users\domef\OneDrive\Desktop\HPMA_Piano\mxl"
    
    # Find all MXL files
    mxl_pattern = os.path.join(directory, "*.mxl")
    mxl_files = glob.glob(mxl_pattern)
    
    if not mxl_files:
        print(f"❌ No MXL files found in: {directory}")
        return False

    if verbose:
        print(f"🎵 Found {len(mxl_files)} MXL files for batch conversion:")
        for i, file in enumerate(mxl_files, 1):
            print(f"   {i}. {os.path.basename(file)}")
    
    # Ensure songs directory exists
    songs_dir = os.path.join(directory, "songs")
    os.makedirs(songs_dir, exist_ok=True)
    
    successful_conversions = 0
    failed_conversions = 0
    skipped_conversions = 0
    
    if verbose:
        print(f"\n🚀 Starting batch conversion with dual clef handling...")
        print("=" * 60)
    
    start_only_global = start_only

    for i, mxl_file in enumerate(mxl_files, 1):
        base_name = os.path.splitext(os.path.basename(mxl_file))[0]
        output_file = os.path.join(songs_dir, f"{base_name}.txt")
        
        if verbose:
            print(f"\n[{i}/{len(mxl_files)}] Processing: {os.path.basename(mxl_file)}")
        
        # Check if output already exists
        if os.path.exists(output_file) and not force_overwrite:
            if verbose:
                print(f"⏭️  Skipping: {os.path.basename(output_file)} already exists")
                print(f"   Use --force to overwrite existing files")
            skipped_conversions += 1
            continue
        
        # Convert the file
        success = convert_mxl_with_dual_clef(mxl_file, output_file, start_only=start_only_global, verbose=verbose)
        
        if success:
            successful_conversions += 1
            if verbose:
                print(f"✅ Successfully converted: {os.path.basename(output_file)}")
        else:
            failed_conversions += 1
            if verbose:
                print(f"❌ Failed to convert: {os.path.basename(mxl_file)}")
    
    # Summary report
    if verbose:
        print("\n" + "=" * 60)
        print(f"📊 BATCH CONVERSION SUMMARY:")
        print(f"   Total MXL files found: {len(mxl_files)}")
        print(f"   ✅ Successfully converted: {successful_conversions}")
        print(f"   ❌ Failed conversions: {failed_conversions}")
        print(f"   ⏭️  Skipped (already exist): {skipped_conversions}")

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
  python convert_mxl_dual_clef.py waltz.mxl
  python convert_mxl_dual_clef.py waltz.mxl songs/custom_waltz.txt
  python convert_mxl_dual_clef.py --batch-convert
  python convert_mxl_dual_clef.py --batch-convert --force
  python convert_mxl_dual_clef.py --batch-convert --directory /path/to/mxl/files
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
                       help='Directory to search for MXL files (default: current directory)')
    
    parser.add_argument('--force', '-f', action='store_true',
                       help='Overwrite existing output files')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')

    parser.add_argument('--start-only', action='store_true',
                        help='Simpler output using only note start events')
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        if args.batch_convert:
            # Batch conversion mode
            if args.verbose:
                print("🎵 Enhanced MXL Batch Converter with Dual Clef Support")
                print("=" * 50)
            success = batch_convert_all_mxl_files(
                directory=args.directory,
                force_overwrite=args.force,
                start_only=args.start_only,
                verbose=args.verbose,
            )
            sys.exit(0 if success else 1)
        elif args.interactive or (not args.input_file and not args.batch_convert):
            # Interactive mode - either explicitly requested or no input file provided
            if args.verbose:
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
                print(f"⚠️  Warning: Could not read original metadata from file. Using defaults.")
                original_tempo = 120
                original_time_signature = "4/4"
            
            # Step 3: Get custom tempo
            custom_tempo = get_custom_tempo(original_tempo)
            
            # Step 4: Get custom time signature
            custom_time_signature = get_custom_time_signature(original_time_signature)
            
            # Step 5: Convert with selected values
            if args.verbose:
                print(f"\n🔄 Converting with tempo: {custom_tempo} BPM and time signature: {custom_time_signature}")
            success = convert_mxl_with_dual_clef(
                mxl_file_to_convert,
                args.output_file,
                custom_tempo,
                custom_time_signature,
                start_only=args.start_only,
                verbose=args.verbose,
            )
            sys.exit(0 if success else 1)
        
        elif args.input_file:
            # Single file conversion mode
            if not os.path.exists(args.input_file):
                print(f"❌ Error: Input file '{args.input_file}' not found.")
                sys.exit(1)
            
            if args.verbose:
                print("🎵 Enhanced MXL Converter with Dual Clef Support")
                print("=" * 30)
            success = convert_mxl_with_dual_clef(
                args.input_file,
                args.output_file,
                start_only=args.start_only,
                verbose=args.verbose,
            )
            sys.exit(0 if success else 1)
        else:
            # This shouldn't happen but fallback to interactive mode
            if args.verbose:
                print("🎵 Enhanced MXL Converter - Interactive Mode")
                print("=" * 40)
            
            mxl_file_to_convert = list_and_select_mxl_file(args.directory)
            
            if not mxl_file_to_convert:
                print("❌ No file selected for conversion.")
                sys.exit(1)
            
            # Get original tempo and time signature and custom values
            try:
                score = converter.parse(mxl_file_to_convert)
                metadata = extract_musical_metadata(score)
                original_tempo = metadata['tempo_bpm']
                original_time_signature = metadata['time_signature']
            except Exception as e:
                print(f"⚠️  Warning: Could not read original metadata from file. Using defaults.")
                original_tempo = 120
                original_time_signature = "4/4"
            
            custom_tempo = get_custom_tempo(original_tempo)
            custom_time_signature = get_custom_time_signature(original_time_signature)
            
            if args.verbose:
                print(f"\n🔄 Converting with tempo: {custom_tempo} BPM and time signature: {custom_time_signature}")
            success = convert_mxl_with_dual_clef(
                mxl_file_to_convert,
                args.output_file,
                custom_tempo,
                custom_time_signature,
                start_only=args.start_only,
                verbose=args.verbose,
            )
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Conversion interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)

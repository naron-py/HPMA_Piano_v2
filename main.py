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
from enhanced_music_player import EnhancedMusicPlayer
from music_file_parser import parse_music_file
from convert_to_lua import convert_file_to_lua
from convert_mxl_dual_clef import extract_musical_metadata


def has_musical_metadata(file_path: str) -> bool:
    """Simple check to see if a song file contains musical metadata headers."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(
                    (
                        "Time_Signature:",
                        "Musical_Feel:",
                        "Key_Signature:",
                        "Original_BPM:",
                        "Tempo_Marking:",
                        "Expression:",
                        "Initial_Dynamic:",
                    )
                ):
                    return True
    except Exception:
        pass
    return False


def list_and_select_song(directory: str = SONGS_DIR):
    """List available .txt songs in the songs directory and prompt user to choose.

    Returns the path to the selected song or ``None`` if the user quits or no
    songs exist.
    """
    if not os.path.isdir(directory):
        print(f"Songs directory not found: {directory}")
        return None

    song_files = [f for f in sorted(os.listdir(directory)) if f.lower().endswith('.txt')]
    if not song_files:
        print(f"No song files found in '{directory}'.")
        return None

    rows = [[i + 1, name] for i, name in enumerate(song_files)]
    print(f"\n--- Available Songs in '{directory}' ---")
    print_table(["No.", "Song Name"], rows)

    while True:
        choice = input("Enter the number of the song to play (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(song_files):
                return os.path.join(directory, song_files[index])
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'.")

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

def main():
    print("Welcome to the Auto Piano Player!")
    print("---------------------------------")

    song_to_play = []
    source_file_path = "" # To track where the song was loaded from
    
    # Option 1: Select a song from the 'songs' directory
    selected_txt_path = list_and_select_song()
    if selected_txt_path:
        try:
            with open(selected_txt_path, "r", encoding="utf-8") as f:                # Filter out header lines but keep all note lines (including sharp notes starting with #)
                song_to_play = []
                for line in f:
                    line = line.strip()
                    # Skip all metadata and header lines
                    if line and not line.startswith(('Generated_from:', 'Total_notes:', 'Format:', 'Time_Signature:', 
                                                'Musical_Feel:', 'Key_Signature:', 'Sharps:', 'Original_BPM:',
                                                'Tempo_Marking:', 'Expression:', 'Initial_Dynamic:', '---', '# ')):
                        # Make sure the line has the expected note format (contains a dash and colon)
                        if '-' in line and ':' in line or line.lower().startswith('r:'):
                            song_to_play.append(line)
            source_file_path = selected_txt_path
            if not song_to_play:
                print(f"⚠️  Warning: Selected file '{selected_txt_path}' contains no playable notes.")
                print("The file may only contain comments. Please add actual note data like '1-2:0.5' or '5-3:1.0'")
            else:
                print(f"✓ Loaded {len(song_to_play)} notes from '{selected_txt_path}'")
        except FileNotFoundError:
            print(f"❌ Error: Selected file '{selected_txt_path}' not found.")
        except Exception as e:
            print(f"❌ Error reading '{selected_txt_path}': {e}")

    # Option 2: If no .txt song was selected or found, prompt for MusicXML/MIDI to parse
    if not song_to_play:
        print("\n--- Parse a new music file (.mxl/.musicxml/.mid) ---")
        user_input_path = input("Enter path to a MusicXML (.musicxml/.mxl) or MIDI (.mid) file to parse (or press Enter to skip): ").strip()
        if user_input_path:
            # Handle quoted paths
            user_input_path = user_input_path.strip('"\'')
            if not os.path.exists(user_input_path):
                print(f"❌ Error: File '{user_input_path}' not found.")
            else:
                source_file_path = user_input_path
                print(f"🎵 Attempting to parse '{source_file_path}'...")
                extracted_notes = parse_music_file(source_file_path)
                if extracted_notes:
                    print(f"✓ Successfully extracted {len(extracted_notes)} notes from '{source_file_path}'.")
                    
                    # Offer to save the parsed song to the 'songs' directory for future use
                    base_name = os.path.basename(source_file_path)
                    suggested_name = os.path.splitext(base_name)[0] + ".txt"

                    save_choice = input(
                        f"💾 Save this parsed song to '{os.path.join(SONGS_DIR, suggested_name)}' for future use? (y/n): "
                    ).strip().lower()
                    if save_choice == 'y':
                        save_path = os.path.join(SONGS_DIR, suggested_name)
                        try:
                            with open(save_path, "w") as f:
                                f.write("Generated_from:" + source_file_path + "\n")
                                f.write(f"Total_notes:{len(extracted_notes)}\n")
                                f.write("Format:NoteValue-Octave:Duration\n")
                                f.write("---\n")
                                for note_line in extracted_notes:
                                    f.write(note_line + "\n")
                            print(f"✓ Song saved to '{save_path}'. You can select it next time.")

                            lua_path = os.path.join(SONGS_DIR, os.path.splitext(suggested_name)[0] + ".lua")
                            if convert_file_to_lua(source_file_path, lua_path, detect_bpm=True, hold_notes=True):
                                print(f"✓ Lua script saved to '{lua_path}'.")
                        except Exception as e:
                            print(f"❌ Error saving song to '{save_path}': {e}")
                    song_to_play = extracted_notes
                else:
                    print("❌ Could not extract any playable notes from the provided music file.")
                    print("This might be due to:")
                    print("  - Unsupported file format")
                    print("  - Corrupted file")
                    print("  - Notes outside the supported octave range (3-5)")
        else:
            print("No file provided. Exiting.")
    
    # Play the song if notes are available
    if song_to_play:
        print(f"\n🎹 --- Playing song from: {source_file_path} ---")
        print("📝 Note format explanation:")
        print("   - Numbers 1-7 represent note values (1=C, 2=D, 3=E, 4=F, 5=G, 6=A, 7=B)")
        print("   - # prefix means sharp (e.g., #1 = C#)")
        print("   - Numbers after dash are octaves (1=low, 2=middle, 3=high)")
        print("   - Numbers after colon are duration in seconds")
        print("   - R: means rest/pause")
        print("\n🎮 Make sure your piano game window is active!")
          # Show first few notes as preview (making sure we only show actual notes)
        playable_notes = [note for note in song_to_play if '-' in note and ':' in note or note.lower().startswith('r:')]
        preview_notes = playable_notes[:5] if playable_notes else ["No playable notes found"]
        print(f"\n📋 Preview of first few notes: {preview_notes}...")
        
          
        # Create the player instance first
        player = EnhancedMusicPlayer()
        
        # Check if this is a file with musical information
        if (
            source_file_path.endswith('_enhanced.txt') or
            source_file_path.endswith('_sustained.txt') or
            source_file_path.endswith('_dual_clef.txt') or
            has_musical_metadata(source_file_path)
        ):
            print("🎵 Detected musical file with enhanced information - using musical feel player!")
            print("🎹 Playing with proper rhythm and feel...")
            player.play_song_with_musical_feel(source_file_path)
        else:
            print("📋 Using enhanced player for basic song files")
            # Use the enhanced player for all song files as it's more capable
            player.play_song(song_to_play)
    else:
        print("\n❌ No song loaded or extracted. Exiting.")
        print("\n💡 Tips:")
        print("  1. Place .txt song files in the 'songs/' directory")
        print("  2. Or provide a .mxl/.musicxml/.mid file to parse")
        print("  3. Note format: NoteValue-Octave:Duration (e.g., 1-2:0.5)")
        print("  4. Use R:0.3 for rests/pauses")


if __name__ == "__main__":
    main()

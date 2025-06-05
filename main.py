# main.py

import os
import sys

# Check for required dependencies
try:
    import pyautogui
    import music21
    print("✓ Required dependencies found")
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please install with: pip install pyautogui music21")
    sys.exit(1)

from enhanced_music_player import EnhancedMusicPlayer
from music_file_parser import parse_music_file
from table_utils import SONGS_DIR, print_table




def _get_song_metadata(file_path):
    """Extract tempo and time signature from a song text file."""
    tempo = "?"
    time_sig = "?"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                if line.startswith("Original_BPM:"):
                    tempo = line.split(":", 1)[1].strip()
                elif line.startswith("Time_Signature:"):
                    time_sig = line.split(":", 1)[1].strip()
                if tempo != "?" and time_sig != "?":
                    break
    except Exception:
        pass
    return tempo, time_sig

# SONGS_DIR constant imported from table_utils
def has_musical_metadata(file_path):
    """Check if the given text file contains musical metadata headers."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                if line.startswith(("Time_Signature:", "Musical_Feel:", "Original_BPM:")):
                    return True
    except Exception:
        pass
    return False

def list_and_select_song():
    """
    Scans the SONGS_DIR, lists available .txt song files,
    and prompts the user to select one.
    Returns the full path to the selected song file or None.
    """
    print(f"\n--- Available Songs in '{SONGS_DIR}/' ---")
    available_files = []

    # Create the songs directory if it doesn't exist
    if not os.path.exists(SONGS_DIR):
        os.makedirs(SONGS_DIR)
        print(f"'{SONGS_DIR}/' directory created. Please place your song .txt files here.")
        return None

    # Collect all .txt files in the songs directory
    for filename in os.listdir(SONGS_DIR):
        if filename.lower().endswith(".txt"):
            available_files.append(filename)

    available_files = sorted(available_files)

    if not available_files:
        print(f"No .txt song files found in '{SONGS_DIR}/'.")
        return None

    rows = []
    for i, song_name in enumerate(available_files, 1):
        bpm, ts = _get_song_metadata(os.path.join(SONGS_DIR, song_name))
        rows.append([i, song_name, bpm, ts])

    print_table(["No.", "Song Name", "BPM", "Time Sig"], rows)

    while True:
        choice = input("Enter the number of the song to play (or 'q' to quit): ").strip().lower()
        if choice == 'q':
            return None
        try:
            song_index = int(choice) - 1
            if 0 <= song_index < len(available_files):
                selected_filename = available_files[song_index]
                return os.path.join(SONGS_DIR, selected_filename)
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

                    save_choice = input(f"💾 Save this parsed song to '{os.path.join(SONGS_DIR, suggested_name)}' for future use? (y/n): ").strip().lower()
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

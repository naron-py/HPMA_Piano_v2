import os
# Use the `consolemenu` package for interactive CLI menus
from consolemenu import ConsoleMenu, SelectionMenu
from consolemenu.items import FunctionItem
import converter
import player

# --- Configuration ---
# Directory where your final .txt song files are stored
SONGS_DIR = "songs"
# Directory where your source .mid and .mxl files are located
# Default to the local `source_files` folder so the project works cross-platform
SOURCE_FILES_DIR = "source_files"

def create_songs_directory():
    """Creates the 'songs' directory if it doesn't already exist."""
    if not os.path.exists(SONGS_DIR):
        print(f"Creating directory: '{SONGS_DIR}'")
        os.makedirs(SONGS_DIR)

def get_song_list():
    """Returns a list of .txt files in the songs directory."""
    if not os.path.exists(SONGS_DIR):
        return []
    return [f for f in os.listdir(SONGS_DIR) if f.endswith('.txt')]

def get_source_file_list():
    """Scans the source directory for supported music files."""
    if not os.path.exists(SOURCE_FILES_DIR):
        print(f"Error: Source directory not found at '{SOURCE_FILES_DIR}'")
        return []
    
    supported_extensions = ('.mid', '.midi', '.mxl', '.musicxml')
    return [f for f in os.listdir(SOURCE_FILES_DIR) if f.lower().endswith(supported_extensions)]

def run_player():
    """Menu action to select and play a song."""
    song_files = get_song_list()
    if not song_files:
        print("\nNo songs found in the 'songs' directory.")
        input("Press Enter to return to the menu.")
        return

    # Use SelectionMenu to get the user's choice
    selected_song_index = SelectionMenu.get_selection(
        song_files,
        title="Select a Song to Play",
        subtitle="Choose a song from the list below."
    )

    if selected_song_index is None or selected_song_index < 0:
        return

    selected_song = song_files[selected_song_index]
    song_path = os.path.join(SONGS_DIR, selected_song)

    print("\nAfter selecting a song, quickly switch to your game window.")
    player.play_song(song_path)
    input("\nPress Enter to return to the main menu.")

def run_converter():
    """Menu action to select and parse a new music file from the source directory."""
    source_files = get_source_file_list()
    if not source_files:
        print(f"\nNo MIDI or MusicXML files found in '{SOURCE_FILES_DIR}'.")
        input("Press Enter to return to the menu.")
        return

    # Use SelectionMenu to get the user's choice
    selected_file_index = SelectionMenu.get_selection(
        source_files,
        title="Select a File to Convert",
        subtitle="Choose a file from the list below."
    )

    if selected_file_index is None or selected_file_index < 0:
        return

    # Get the selected file and call the converter
    selected_file = source_files[selected_file_index]
    file_path = os.path.join(SOURCE_FILES_DIR, selected_file)

    metadata = converter.detect_metadata(file_path)
    if metadata is None:
        input("\nPress Enter to return to the menu.")
        return
    default_tempo, time_sig, sigs = metadata
    if len(sigs) > 1:
        print(
            f"Warning: Multiple time signatures found: {', '.join(sigs)}. Using {time_sig}."
        )

    bpm_input = input(
        f"Detected tempo is {default_tempo} BPM. Enter a BPM to override or press Enter to keep: "
    )
    tempo_override = default_tempo
    if bpm_input.strip():
        try:
            tempo_override = float(bpm_input)
        except ValueError:
            print("Invalid BPM entered. Using detected tempo.")

    converter.parse_file(file_path, tempo_override)
    
    input("\nPress Enter to return to the main menu.")

def main():
    """Main function to run the application menu."""
    create_songs_directory()

    menu = ConsoleMenu("HPMA Piano Assistant", "Welcome! What would you like to do?")
    
    player_item = FunctionItem("Play a song from the 'songs' folder", run_player)
    converter_item = FunctionItem("Convert a file from your 'source_files' folder", run_converter)
    
    menu.append_item(player_item)
    menu.append_item(converter_item)
    
    menu.show()

if __name__ == "__main__":
    main()
import os
# This line was likely missing from your file
from console_menu import ConsoleMenu, MenuItem
import converter
import player

# --- Configuration ---
# Directory where your final .txt song files are stored
SONGS_DIR = "songs"
# Directory where your source .mid and .mxl files are located
SOURCE_FILES_DIR = r"C:\Users\domef\OneDrive\Desktop\HPMA_Piano_v2\source_files"

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

    # Create a sub-menu to select a song
    song_menu_items = [MenuItem(text=song) for song in song_files]
    song_menu = ConsoleMenu("Select a Song to Play", "Choose a song from the list below.")
    for item in song_menu_items:
        song_menu.append_item(item)
    
    song_menu.show()
    
    if song_menu.is_exit():
        return

    selected_song_index = song_menu.get_selection()
    selected_song = song_files[selected_song_index]
    song_path = os.path.join(SONGS_DIR, selected_song)

    window_title = input("\nEnter the exact title of the game/piano window: ")
    if not window_title:
        print("Window title cannot be empty.")
        return
        
    player.play_song(song_path, window_title)
    input("\nPress Enter to return to the main menu.")

def run_converter():
    """Menu action to select and parse a new music file from the source directory."""
    source_files = get_source_file_list()
    if not source_files:
        print(f"\nNo MIDI or MusicXML files found in '{SOURCE_FILES_DIR}'.")
        input("Press Enter to return to the menu.")
        return

    # Create a sub-menu to select a file to convert
    file_menu_items = [MenuItem(text=file) for file in source_files]
    file_menu = ConsoleMenu("Select a File to Convert", "Choose a file from the list below.")
    for item in file_menu_items:
        file_menu.append_item(item)
    
    file_menu.show()
    
    if file_menu.is_exit():
        return

    # Get the selected file and call the converter
    selected_file_index = file_menu.get_selection()
    selected_file = source_files[selected_file_index]
    file_path = os.path.join(SOURCE_FILES_DIR, selected_file)
    
    converter.parse_file(file_path)
    
    input("\nPress Enter to return to the main menu.")

def main():
    """Main function to run the application menu."""
    create_songs_directory()

    menu = ConsoleMenu("HPMA Piano Assistant", "Welcome! What would you like to do?")
    
    player_item = MenuItem("Play a song from the 'songs' folder", run_player)
    converter_item = MenuItem("Convert a file from your 'source_files' folder", run_converter)
    
    menu.append_item(player_item)
    menu.append_item(converter_item)
    
    menu.show()

if __name__ == "__main__":
    main()
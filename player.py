# player.py

import pyautogui
import time
import pywinctl as gw
from key_mapper import NOTE_TO_KEY

# Fail-safe: moving mouse to a corner will stop the script
pyautogui.FAILSAFE = True

def play_song(song_path, window_title):
    """
    Plays a song from a .txt file by sending keystrokes to a target window.

    Args:
        song_path (str): The path to the .txt song file.
        window_title (str): The title of the window to send keystrokes to.
    """
    # --- 1. Find and Activate Target Window ---
    try:
        target_window = gw.getWindowsWithTitle(window_title)
        if not target_window:
            print(f"Error: Window '{window_title}' not found.")
            return
        
        # Activate the window to ensure it has focus
        target_window[0].activate()
        print(f"Successfully focused window: '{window_title}'")
        
    except Exception as e:
        print(f"Error interacting with window: {e}")
        print("Please ensure the window title is correct and the application is running.")
        return

    # --- 2. Load and Parse Song File ---
    try:
        with open(song_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Song file '{song_path}' not found.")
        return
        
    # Default tempo if not specified in the file
    tempo = 120
    for line in lines:
        if line.startswith("# Tempo:"):
            tempo = float(line.split(":")[1].strip())
            break
            
    # Calculate duration of a single beat in seconds
    beat_duration = 60.0 / tempo
    print(f"Playing '{song_path}' at {tempo} BPM (beat duration: {beat_duration:.2f}s)")

    # --- 3. Countdown and Play ---
    print("Starting in:")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    print("Playing now!")

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = line.split(':')
        
        # Rests are handled by just sleeping
        if parts[0] == "Rest":
            duration = float(parts[1])
            time.sleep(duration * beat_duration)
            continue
        
        # The structure is Hand:Note:Duration, so note is at index 1 or 2
        note_info = parts[1] if len(parts) == 3 else parts[0]
        duration = float(parts[-1])
        
        # A chord will have '-' in its name
        if '-' in note_info:
            chord_notes = note_info.split('-')
            keys_to_press = [NOTE_TO_KEY.get(n) for n in chord_notes if NOTE_TO_KEY.get(n)]
            if keys_to_press:
                # Use pyautogui.hotkey for chords
                pyautogui.hotkey(*keys_to_press)
        else:
            # Single note
            key_to_press = NOTE_TO_KEY.get(note_info)
            if key_to_press:
                pyautogui.press(key_to_press)
        
        # Wait for the note's duration before playing the next one
        time.sleep(duration * beat_duration)
        
    print("Song finished.")
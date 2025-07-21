# player.py

"""Handle playback by automating key presses with ``pyautogui``.

If ``pyautogui`` cannot be initialized (e.g. running in a headless
environment without a display), we fall back to a mock implementation so
the rest of the program can still run for testing purposes.
"""

try:
    import pyautogui
except Exception as exc:  # pragma: no cover - defensive import
    print(f"Warning: pyautogui could not be loaded ({exc}). Using mock mode.")

    class _MockPyAutoGUI:
        """Minimal mock of pyautogui used when no GUI is available."""

        FAILSAFE = False

        def press(self, key):
            print(f"[MOCK press] {key}")

        def hotkey(self, *keys):
            joined = ", ".join(keys)
            print(f"[MOCK hotkey] {joined}")

    pyautogui = _MockPyAutoGUI()
import time
import threading

try:
    import keyboard  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    print(f"Warning: keyboard could not be loaded ({exc}). Hotkey stop disabled.")
    keyboard = None
from key_mapper import NOTE_TO_KEY

# Fail-safe: moving mouse to a corner will stop the script
pyautogui.FAILSAFE = True

# Event used to signal that playback should stop
_stop_event = threading.Event()


def request_stop():
    """Signal the currently playing song to stop."""
    _stop_event.set()


def _listen_for_hotkey():
    """Background thread waiting for the ESC key to stop playback."""
    if keyboard is None:
        return
    try:
        keyboard.wait("esc")
        _stop_event.set()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Hotkey listener stopped ({exc}).")


def _sleep_check_stop(seconds: float) -> bool:
    """Sleep in small increments and return True if stop is requested."""
    end_time = time.time() + seconds
    while time.time() < end_time:
        if _stop_event.is_set():
            return True
        time.sleep(min(0.1, end_time - time.time()))
    return _stop_event.is_set()

def play_song(song_path):
    """Plays a song from a .txt file by sending keystrokes to the active window.

    The user should manually focus the target game window before the countdown
    ends.

    Args:
        song_path (str): The path to the .txt song file.
    """
    # Ensure previous stop requests are cleared and start hotkey listener
    _stop_event.clear()
    if keyboard is not None:
        threading.Thread(target=_listen_for_hotkey, daemon=True).start()

    # --- 1. Load and Parse Song File ---
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

    # --- 2. Countdown and Play ---
    try:
        print("Switch to your game window now! Starting in:")
        for i in range(3, 0, -1):
            if _stop_event.is_set():
                print("Playback stopped.")
                return
            print(f"{i}...")
            time.sleep(1)
        print("Playing now! (press ESC to stop)")

        for line in lines:
            if _stop_event.is_set():
                print("Playback stopped.")
                return

            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(':')

            # Rests are handled by just sleeping
            if parts[0] == "Rest":
                duration = float(parts[1])
                if _sleep_check_stop(duration * beat_duration):
                    print("Playback stopped.")
                    return
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

            if _sleep_check_stop(duration * beat_duration):
                print("Playback stopped.")
                return

    except KeyboardInterrupt:
        print("\nPlayback interrupted by user.")
        return

    if _stop_event.is_set():
        print("Playback stopped.")
    else:
        print("Song finished.")

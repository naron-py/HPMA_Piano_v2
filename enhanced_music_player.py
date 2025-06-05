# enhanced_music_player.py - Player that respects musical elements like time signatures

import pyautogui
import time
import threading
from key_mapper import get_keyboard_key

# Configure pyautogui failsafe
pyautogui.FAILSAFE = False # Disabled for this script as it can be disruptive during playback
pyautogui.PAUSE = 0.005

class EnhancedMusicPlayer:
    def __init__(self):
        self.time_signature = "4/4"
        self.musical_feel = "common_time"
        self.tempo_bpm = 120
        self.key_signature = "C major"
        self.beat_position = 0
        self.measure_position = 0
        
    def load_song_with_musical_info(self, song_file):
        """Load song file and extract musical metadata"""
        song_notes = []
        metadata_section = True  # Assume we start in the metadata section
        
        with open(song_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                # Process metadata
                if line.startswith("Time_Signature:"):
                    self.time_signature = line.split(":", 1)[1]
                    print(f"🎵 Time Signature: {self.time_signature}")
                elif line.startswith("Musical_Feel:"):
                    self.musical_feel = line.split(":", 1)[1]
                    print(f"💫 Musical Feel: {self.musical_feel}")
                elif line.startswith("Original_BPM:"):
                    self.tempo_bpm = int(line.split(":", 1)[1])
                    print(f"⏱️  Tempo: {self.tempo_bpm} BPM")
                elif line.startswith("Key_Signature:"):
                    self.key_signature = line.split(":", 1)[1]
                    print(f"🎹 Key: {self.key_signature}")
                elif line.startswith("Expression:"):
                    expression = line.split(":", 1)[1]
                    print(f"🎭 Expression: {expression}")
                elif line.startswith("Initial_Dynamic:"):
                    dynamic = line.split(":", 1)[1]
                    print(f"🔊 Dynamics: {dynamic}")
                # Check if we've reached the end of the metadata section
                elif line == "---":
                    metadata_section = False  # We've passed the metadata separator
                # Process note data (only after the metadata section)
                elif not metadata_section and ('-' in line and ':' in line or line.lower().startswith('r:')):
                    song_notes.append(line)
        
        return song_notes
    
    def apply_musical_feel(self, duration_seconds, beat_in_measure):
        """Apply musical feel based on time signature and beat position"""
        if self.musical_feel == "waltz":
            # In waltz (3/4), beat 1 is strongest, beats 2&3 are lighter
            if beat_in_measure == 1:
                # Strong beat - might be played with slight emphasis
                return duration_seconds * 1.0  # Could add emphasis later
            else:
                # Weak beats - slightly lighter feel
                return duration_seconds * 0.98  # Slightly shorter for lilting feel
                
        elif self.musical_feel == "common_time":
            # In 4/4, beats 1&3 are strong, 2&4 are weak
            if beat_in_measure in [1, 3]:
                return duration_seconds * 1.0  # Strong beats
            else:
                return duration_seconds * 0.99  # Slightly lighter weak beats
        
        return duration_seconds
    
    def get_beat_in_measure(self):
        """Get current beat position within the measure"""
        if self.time_signature == "3/4":
            return (self.beat_position % 3) + 1
        elif self.time_signature == "4/4":
            return (self.beat_position % 4) + 1
        else:
            # For other time signatures, use the numerator
            numerator = int(self.time_signature.split('/')[0])
            return (self.beat_position % numerator) + 1
    
    def advance_beat_position(self, duration_in_beats):
        """Advance the beat position based on note duration"""
        self.beat_position += duration_in_beats
        
        # Calculate measure position
        if self.time_signature == "3/4":
            self.measure_position = int(self.beat_position // 3)
        elif self.time_signature == "4/4":
            self.measure_position = int(self.beat_position // 4)
    
    def play_note_with_feel(self, keyboard_char, duration_seconds):
        """Play a note with musical feel applied"""
        if keyboard_char is None:
            return
        
        beat_in_measure = self.get_beat_in_measure()
        adjusted_duration = self.apply_musical_feel(duration_seconds, beat_in_measure)
        
        print(f"🎵 Beat {beat_in_measure}/{self.time_signature.split('/')[0]} - Playing: '{keyboard_char}' for {adjusted_duration:.3f}s ({self.musical_feel})")
        try:
            # Calculate beat advancement (assuming quarter note = 1 beat)
            quarter_note_duration = 60.0 / self.tempo_bpm
            beats_duration = duration_seconds / quarter_note_duration
            
            if keyboard_char == '+':
                pyautogui.keyDown('shift')
                pyautogui.press('=')
                time.sleep(adjusted_duration)
                pyautogui.keyUp('shift')
            else:
                pyautogui.keyDown(keyboard_char)
                time.sleep(adjusted_duration)
                pyautogui.keyUp(keyboard_char)
            
            # Advance beat position
            self.advance_beat_position(beats_duration)
            
            time.sleep(0.01)
        except Exception as e:
            print(f"Error playing note {keyboard_char}: {e}")
    
    def play_chord_with_feel(self, keyboard_chars, duration_seconds):
        """Play a chord with musical feel applied"""
        if not keyboard_chars:
            return
        
        valid_chars = [char for char in keyboard_chars if char is not None]
        if not valid_chars:
            return
        
        beat_in_measure = self.get_beat_in_measure()
        adjusted_duration = self.apply_musical_feel(duration_seconds, beat_in_measure)
        
        print(f"🎹 Beat {beat_in_measure}/{self.time_signature.split('/')[0]} - CHORD: {valid_chars} for {adjusted_duration:.3f}s ({self.musical_feel})")
        
        try:
            # Calculate beat advancement
            quarter_note_duration = 60.0 / self.tempo_bpm
            beats_duration = duration_seconds / quarter_note_duration
            
            # Prepare keys
            keys_to_press = []
            for char in valid_chars:
                if char == '+':
                    keys_to_press.extend(['shift', '='])
                else:
                    keys_to_press.append(char)
            
            # Simultaneous press using threading
            press_threads = []
            
            def press_key(key):
                pyautogui.keyDown(key)
            
            def release_key(key):
                pyautogui.keyUp(key)
            
            # Press all keys simultaneously
            for key in keys_to_press:
                thread = threading.Thread(target=press_key, args=(key,))
                press_threads.append(thread)
                thread.start()
            
            for thread in press_threads:
                thread.join()
            
            # Hold for duration
            time.sleep(adjusted_duration)
            
            # Release all keys simultaneously
            release_threads = []
            for key in reversed(keys_to_press):
                thread = threading.Thread(target=release_key, args=(key,))
                release_threads.append(thread)
                thread.start()
            
            for thread in release_threads:
                thread.join()
            
            # Advance beat position
            self.advance_beat_position(beats_duration)
            
            time.sleep(0.01)
        except Exception as e:
            print(f"Error playing chord {valid_chars}: {e}")
    
    def parse_note_string(self, note_str):
        """Parse note string into components"""
        parts = note_str.split(':')
        note_octave_str = parts[0]
        duration = float(parts[1]) if len(parts) > 1 else 0.5
        
        if '+' in note_octave_str:
            # Chord
            chord_notes = []
            for single_note in note_octave_str.split('+'):
                note_parts = single_note.split('-')
                if len(note_parts) == 2:
                    note_value = note_parts[0]
                    octave = int(note_parts[1])
                    chord_notes.append((note_value, octave))
            return chord_notes, duration, True
        else:
            # Single note
            note_parts = note_octave_str.split('-')
            if len(note_parts) == 2:
                note_value = note_parts[0]
                octave = int(note_parts[1])
                return (note_value, octave), duration, False
        
        return None, duration, False
    
    def play_song_with_musical_feel(self, song_file):
        """Play song with proper musical feel and timing"""
        print(f"🎼 Loading song with musical information: {song_file}")
        
        song_notes = self.load_song_with_musical_info(song_file)
        if not song_notes:
            print("❌ No notes to play!")
            return
        
        print(f"\n🎵 Musical Context:")
        print(f"   Time Signature: {self.time_signature}")
        print(f"   Feel: {self.musical_feel}")
        print(f"   Tempo: {self.tempo_bpm} BPM")
        print(f"   Notes to play: {len(song_notes)}")
        
        print(f"\n🎮 Starting playback in 3 seconds...")
        print("🛑 Move mouse to top-left corner to stop (failsafe)")
        
        for i in range(3, 0, -1):
            print(f"⏱️  {i}...")
            time.sleep(1)
        
        print("🎹 Starting playback with musical feel!")
        
        # Reset beat tracking
        self.beat_position = 0
        self.measure_position = 0
        
        success_count = 0
        error_count = 0
        
        for i, note_str in enumerate(song_notes):
            try:
                if note_str.lower().startswith("r:"):
                    # Rest
                    rest_duration = float(note_str.split(':')[1])
                    quarter_note_duration = 60.0 / self.tempo_bpm
                    beats_duration = rest_duration / quarter_note_duration
                    
                    beat_in_measure = self.get_beat_in_measure()
                    print(f"[{i+1}/{len(song_notes)}] 🔇 Beat {beat_in_measure} - Rest: {rest_duration:.3f}s")
                    time.sleep(rest_duration)
                    
                    self.advance_beat_position(beats_duration)
                    success_count += 1
                    continue
                
                notes_data, duration, is_chord = self.parse_note_string(note_str)
                
                if notes_data is None:
                    print(f"[{i+1}/{len(song_notes)}] ⚠️  Skipped malformed note: {note_str}")
                    error_count += 1
                    continue
                
                if is_chord:
                    # Handle chord
                    keyboard_chars = []
                    note_names = []
                    
                    for note_value, octave in notes_data:
                        keyboard_char = get_keyboard_key(note_value, octave)
                        if keyboard_char:
                            keyboard_chars.append(keyboard_char)
                            note_names.append(f"{note_value}-{octave}")
                    
                    if keyboard_chars:
                        chord_display = "+".join(note_names)
                        print(f"[{i+1}/{len(song_notes)}] 🎹 Chord: {chord_display} ({duration:.3f}s)")
                        self.play_chord_with_feel(keyboard_chars, duration)
                        success_count += 1
                    else:
                        print(f"[{i+1}/{len(song_notes)}] ⚠️  Skipped unmapped chord: {note_str}")
                        error_count += 1
                else:
                    # Handle single note
                    note_value, octave = notes_data
                    keyboard_char = get_keyboard_key(note_value, octave)
                    if keyboard_char:
                        print(f"[{i+1}/{len(song_notes)}] 🎵 Note: {note_value}-{octave} → '{keyboard_char}' ({duration:.3f}s)")
                        self.play_note_with_feel(keyboard_char, duration)
                        success_count += 1
                    else:
                        print(f"[{i+1}/{len(song_notes)}] ⚠️  Skipped unmapped note: {note_str}")
                        error_count += 1
                        
            except Exception as e:
                print(f"[{i+1}/{len(song_notes)}] ❌ Error: {e}")
                error_count += 1
        
        print(f"\n🏁 Playback finished!")
        print(f"✅ Successfully played: {success_count} notes/chords")
        print(f"🎼 Musical feel: {self.musical_feel} in {self.time_signature} time")
        print(f"⏱️  Tempo: {self.tempo_bpm} BPM")
        if error_count > 0:
            print(f"❌ Errors/Skipped: {error_count} notes")
    
    # New method to handle basic song notes
    def play_song(self, song_notes):
        """Play song from a list of note strings"""
        print(f"🎵 Playing song with {len(song_notes)} notes using enhanced player")
        
        # Use some reasonable defaults
        self.time_signature = "4/4"
        self.musical_feel = "common_time"
        self.tempo_bpm = 120
        self.key_signature = "C major"
        
        if not song_notes:
            print("❌ No notes to play!")
            return
        
        # Filter header information that might be in the song_notes list
        filtered_notes = []
        for line in song_notes:
            if line and not line.startswith(('Time_Signature:', 'Musical_Feel:', 'Key_Signature:', 
                                           'Sharps:', 'Original_BPM:', 'Tempo_Marking:', '---',
                                           'Generated_from:', 'Total_notes:', 'Format:', 
                                           'Expression:', 'Initial_Dynamic:')):
                # Make sure it looks like a valid note
                if '-' in line and ':' in line or line.lower().startswith('r:'):
                    filtered_notes.append(line)
        
        print(f"\n🎮 Starting playback in 3 seconds...")
        print("🛑 Move mouse to top-left corner to stop (failsafe)")
        
        for i in range(3, 0, -1):
            print(f"⏱️  {i}...")
            time.sleep(1)
        
        print("🎹 Starting playback!")
        
        # Reset beat tracking
        self.beat_position = 0
        self.measure_position = 0
        
        success_count = 0
        error_count = 0
        
        for i, note_str in enumerate(filtered_notes):
            try:
                if note_str.lower().startswith("r:"):
                    # Rest
                    rest_duration = float(note_str.split(':')[1])
                    quarter_note_duration = 60.0 / self.tempo_bpm
                    beats_duration = rest_duration / quarter_note_duration
                    
                    beat_in_measure = self.get_beat_in_measure()
                    print(f"[{i+1}/{len(filtered_notes)}] 🔇 Beat {beat_in_measure} - Rest: {rest_duration:.3f}s")
                    time.sleep(rest_duration)
                    
                    self.advance_beat_position(beats_duration)
                    success_count += 1
                    continue
                
                notes_data, duration, is_chord = self.parse_note_string(note_str)
                
                if notes_data is None:
                    print(f"[{i+1}/{len(filtered_notes)}] ⚠️  Skipped malformed note: {note_str}")
                    error_count += 1
                    continue
                
                if is_chord:
                    # Handle chord
                    keyboard_chars = []
                    note_names = []
                    
                    for note_value, octave in notes_data:
                        keyboard_char = get_keyboard_key(note_value, octave)
                        if keyboard_char:
                            keyboard_chars.append(keyboard_char)
                            note_names.append(f"{note_value}-{octave}")
                    
                    if keyboard_chars:
                        chord_display = "+".join(note_names)
                        print(f"[{i+1}/{len(filtered_notes)}] 🎹 Chord: {chord_display} ({duration:.3f}s)")
                        self.play_chord_with_feel(keyboard_chars, duration)
                        success_count += 1
                    else:
                        print(f"[{i+1}/{len(filtered_notes)}] ⚠️  Skipped unmapped chord: {note_str}")
                        error_count += 1
                else:
                    # Handle single note
                    note_value, octave = notes_data
                    keyboard_char = get_keyboard_key(note_value, octave)
                    if keyboard_char:
                        print(f"[{i+1}/{len(filtered_notes)}] 🎵 Note: {note_value}-{octave} → '{keyboard_char}' ({duration:.3f}s)")
                        self.play_note_with_feel(keyboard_char, duration)
                        success_count += 1
                    else:
                        print(f"[{i+1}/{len(filtered_notes)}] ⚠️  Skipped unmapped note: {note_str}")
                        error_count += 1
                        
            except Exception as e:
                print(f"[{i+1}/{len(filtered_notes)}] ❌ Error: {e}")
                error_count += 1
        
        print(f"\n🏁 Playback finished!")
        print(f"✅ Successfully played: {success_count} notes/chords")
        print(f"⏱️  Using default tempo: {self.tempo_bpm} BPM")
        if error_count > 0:
            print(f"❌ Errors/Skipped: {error_count} notes")

# Test function
def test_enhanced_player():
    player = EnhancedMusicPlayer()
    
    # Test with enhanced waltz file
    test_file = "songs/Waltz_enhanced.txt"
    if os.path.exists(test_file):
        player.play_song_with_musical_feel(test_file)
    else:
        print(f"❌ Test file not found: {test_file}")
        print("Run the enhanced converter first: python convert_mxl_enhanced_musical.py Waltz.mxl")

if __name__ == "__main__":
    import os
    test_enhanced_player()

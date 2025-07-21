# HPMA Piano - Automated Piano Player for Games

An automated script that can play piano in games by simulating keyboard inputs. Supports parsing MusicXML (.mxl) files and converting them to playable sequences.

## 🎹 Key Mapping

The script maps piano notes to keyboard keys as shown in your game interface:

```
Octave 3 (Low):    A S D F G H J K L ; ' \
Octave 4 (Middle): Q W E R T Y U I O P [ ]
Octave 5 (High):   1 2 3 4 5 6 7 8 9 0 - +
```

## 🚀 Setup

1. **Install Python** (3.7 or higher)
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or manually:
   ```bash
   pip install pyautogui music21
   ```

## 📁 File Structure

```
HPMA_Piano/
├── main.py              # Main script to run
├── enhanced_music_player.py # Handles keyboard automation
├── music_file_parser.py # Parses .mxl/.mid files
├── key_mapper.py        # Maps notes to keyboard keys
├── songs/               # Directory for song files
│   ├── loop.txt         # Example song file
│   └── *.txt           # Your song files
└── requirements.txt     # Dependencies
```

## 🎵 Usage

### Quick Start
1. **Run the demo/guide**: `python demo.py`
2. **Convert .mxl to song file**: `python convert_mxl_dual_clef.py your_file.mxl`
3. **Play songs**: `python main.py`

### Option 1: Convert MusicXML Files
```bash
# Convert a .mxl file to a playable .txt song file
python convert_mxl_dual_clef.py loop.mxl
python convert_mxl_dual_clef.py M2M_Pretty_Boy.mxl

# The converted files will be saved in the songs/ directory
```

### Export to Lua
After converting an `.mxl` file you can create a Lua table for macro scripts:

```bash
# Convert to text then create Lua table
python convert_mxl_dual_clef.py song.mxl --start-only
lua mxl_to_lua.lua song.txt song.lua
```

### Command-Line Flags
`convert_mxl_dual_clef.py` supports several options:

- `-b`, `--batch-convert` – convert all `.mxl` files in a folder
- `-i`, `--interactive` – walk through file selection and tempo prompts
- `-d`, `--directory` – directory containing `.mxl` files
- `-f`, `--force` – overwrite existing output files
- `-v`, `--verbose` – extra debug output
- `--start-only` – output only note-on events for simpler exports

### `convert_to_lua.py` Options
- `--min-duration` – ignore generated notes/rests shorter than this many seconds

### Option 2: Play Existing Songs
```bash
# Run the main player
python main.py

# Select a song from the menu
# After selecting a song, switch to your piano game before the countdown ends
```

### Option 3: Test the System
```bash
# Test basic playback with sample notes (uses notepad to show key presses)
python test_playback.py

# Test chord functionality with sample chords
python test_chords.py
```

## 📝 Song File Format

Song files in the `songs/` directory should contain notes in this format:

```
# Comments start with #
NoteValue-Octave:Duration

Examples:
1-2:0.5       # C4 (middle C) for 0.5 seconds
#1-2:0.3      # C#4 for 0.3 seconds  
5-3:1.0       # G5 for 1.0 seconds
1-2+3-2:1.0   # C4+E4 chord for 1.0 seconds
1-2+3-2+5-2:1.5  # C4+E4+G4 chord (C major triad) for 1.5 seconds
R:0.2         # Rest (pause) for 0.2 seconds
```

### Note Values:
- `1` = C, `2` = D, `3` = E, `4` = F, `5` = G, `6` = A, `7` = B
- `#1` = C#, `#2` = D#, etc. (sharps)

### Chords:
- Use `+` to join notes that should play simultaneously
- Example: `1-2+3-2+5-2:2.0` plays C4, E4, and G4 together for 2 seconds

### Octaves:
- `1` = Low octave (A-row keys)
- `2` = Middle octave (Q-row keys) 
- `3` = High octave (Number row keys)

## 🔧 Configuration

### Tempo
Edit `TEMPO_BPM` in `music_file_parser.py` to match your sheet music:
```python
TEMPO_BPM = 98  # Adjust based on your music
```

### Key Mapping
Modify `KEY_MAPPING` in `key_mapper.py` if your game uses different keys.

### Octave Range
Adjust `STANDARD_OCTAVE_TO_CUSTOM_OCTAVE` in `key_mapper.py` if needed:
```python
STANDARD_OCTAVE_TO_CUSTOM_OCTAVE = {
    3: 1,  # C3-B3 → Low octave
    4: 2,  # C4-B4 → Middle octave
    5: 3,  # C5-B5 → High octave
}
```
Notes that fall outside these three octaves are automatically shifted to the
nearest supported octave when converting files.

## 🎮 Gaming Tips

1. **Window Focus**: Ensure your piano game is active before the 3‑second countdown finishes
2. **Failsafe**: Move mouse to top-left corner to stop playback immediately
3. **ESC Key**: Press `ESC` during playback to stop the current song
4. **Timing**: Adjust `TEMPO_BPM` if the music plays too fast/slow
5. **Practice**: Test with short songs first to calibrate timing

## 🛠️ Troubleshooting

### "No playable notes found"
- Check that your song file contains actual note data (not just comments)
- Verify the note format: `NoteValue-Octave:Duration`

### "Unmapped note" warnings
- Your music contains notes outside the supported range (octaves 3-5)
- Consider transposing the music or extending the octave mapping

### Timing issues
- Adjust `TEMPO_BPM` in `music_file_parser.py`
- Check that your game responds to the keyboard timing

### Import errors
- Install dependencies: `pip install pyautogui music21`
- For Windows, you might need: `pip install pillow`

## 📋 Example Workflow

1. **Get your music file**: Export from MuseScore, Audiveris, or find .mxl files online
2. **Parse it**: Run `python main.py` and provide the file path
3. **Save it**: Choose to save the parsed song to `songs/` directory
4. **Play it**: Next time, just select it from the menu
5. **Refine**: Edit the generated .txt file to fix any timing issues

## 🎼 Creating Song Files from PDFs

1. Use **Audiveris** to convert PDF sheet music to .mxl files
2. Use this script to parse the .mxl file into a .txt song file
3. Manually edit the .txt file if needed for better timing/accuracy

## ⚠️ Important Notes

- This script sends keyboard inputs to whatever window is active
- Make sure your piano game is focused before the countdown ends
- Some games may have anti-automation protection
- Test with simple songs first
- Use responsibly and follow game terms of service

# Piano Assistant

Terminal-based piano automation tool that converts MIDI or MusicXML files into a
simple text representation and can replay the score using the PC keyboard.

## Features

- Lists all `*.mid` and `*.mxl` files found in `piano_assistant/source_files`.
- Converts a selected file to a timestamped text file in
  `piano_assistant/output`.
- Plays back converted songs using `pyautogui` and a fixed three octave key
  mapping.
- Test mode prints which keys would be played without sending any keystrokes.
- Automatically transposes the entire song up or down in octave steps so all
  notes fit within the mapped three-octave range.

## Usage

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Place MIDI or MXL files in `piano_assistant/source_files/`.

3. Run the program:

   ```bash
   python -m piano_assistant.main
   ```

Follow the on-screen menu to convert or play songs. Converted files are stored
in `piano_assistant/output/` with a timestamp in the filename.

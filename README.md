# Piano Assistant

Terminal-based piano automation tool that converts MIDI or MusicXML files into a
simple text representation and can replay the score using the PC keyboard.

## Features

- Lists all `*.mid` and `*.mxl` files found in `piano_assistant/source_files`.
- Converts a selected file to a timestamped text file in
  `piano_assistant/output`. Converted files include the original time signature
  and tempo in comment lines for reference during playback.
- Plays back converted songs using `pyautogui` and a fixed three octave key
  mapping. When playing back a converted song, the program prints metadata such
  as the source file name, time signature, and tempo so you can verify the
  conversion.
- Test mode prints which keys would be played without sending any keystrokes.
- Automatically transposes the entire song up or down in octave steps so all
  notes fit within the mapped three-octave range. If the song spans more than
  three octaves, notes outside the range are shifted by octaves individually to
  stay playable.
- Supports overlapping notes so chords and polyphonic passages are reproduced
  accurately during playback.

## Usage

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Place MIDI or MXL files in `piano_assistant/source_files/`.

3. Use the CLI to convert, play, or test songs. For example:

   ```bash
   python -m piano_assistant.cli convert path/to/file.mid
   python -m piano_assistant.cli play piano_assistant/output/converted.txt
   python -m piano_assistant.cli test piano_assistant/output/converted.txt
   ```

Converted files are stored in `piano_assistant/output/` with a timestamp in the
filename.

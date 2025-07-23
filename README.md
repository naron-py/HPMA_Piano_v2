# Piano Assistant

Terminal-based piano automation tool that converts MIDI or MusicXML files into a
simple text representation and can replay the score using the PC keyboard.

## Features

- Lists all `*.mid` and `*.mxl` files found in `piano_assistant/source_files`.
- Converts a selected file to a timestamped text file in
  `piano_assistant/output`. Converted files include the original time signature
  and tempo in comment lines for reference during playback. Start and duration
  values are measured in beats by default so playback can follow tempo changes.
  The ``piano_assistant.converter.convert`` function also accepts
  ``use_seconds=True`` to output times in seconds instead.
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
   # For headless environments, also install pyvirtualdisplay
   pip install pyvirtualdisplay
   ```

2. Place MIDI or MXL files in `piano_assistant/source_files/`.

3. Run the program:

   ```bash
   python -m piano_assistant.main
   ```

Follow the on-screen menu to convert or play songs. Converted files are stored
in `piano_assistant/output/` with a timestamp in the filename.

## Display Requirements

`pyautogui` needs access to a GUI display. On Linux the program will try to
start a virtual X display when the `DISPLAY` variable isn't set. This step is
skipped on Windows and macOS where a display is usually available. If you are
running on a headless Linux system, install `pyvirtualdisplay` or configure a
display manually.

## Testing

Running the test suite requires the project's dependencies. Install them first and then run `pytest`:

```bash
pip install -r requirements.txt
pytest
```

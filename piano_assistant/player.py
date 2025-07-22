from __future__ import annotations
import time
import threading
try:
    import pyautogui
except Exception as exc:  # fallback in headless mode
    print(f"pyautogui unavailable ({exc}); using mock mode")
    class Mock:
        FAILSAFE = False
        def press(self, key):
            print(f"[MOCK press] {key}")
        def hotkey(self, *keys):
            print(f"[MOCK hotkey] {' '.join(keys)}")
    pyautogui = Mock()

from .key_mapper import KEY_MAPPING
from .utils import pitch_to_key

_stop = threading.Event()


def stop():
    _stop.set()


def play_song(path: str, test_mode: bool = False) -> None:
    _stop.clear()
    events = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            hand, notes, start, dur = line.split(':')
            start_f = float(start)
            dur_f = float(dur)
            events.append((start_f, dur_f, notes.split('+')))
    events.sort(key=lambda e: e[0])

    start_time = time.time()
    for ev_start, dur, notes in events:
        wait = ev_start - (time.time() - start_time)
        if wait > 0:
            time.sleep(wait)
        keys = []
        for n in notes:
            code = pitch_to_key(n)
            if code is None:
                continue
            key = KEY_MAPPING.get(code)
            if key:
                keys.append(key)
        if not keys:
            continue
        if test_mode:
            print(f"PLAY {notes} for {dur:.2f}s -> {keys}")
        else:
            if len(keys) > 1:
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys[0])
        if dur > 0:
            time.sleep(dur)
        if _stop.is_set():
            break

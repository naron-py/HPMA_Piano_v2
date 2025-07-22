from __future__ import annotations
from . import player


def test_song(path: str) -> None:
    player.play_song(path, test_mode=True)

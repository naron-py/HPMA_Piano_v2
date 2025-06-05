import os
from typing import List

SONGS_DIR = os.path.join(os.path.dirname(__file__), "songs")

def print_table(headers: List[str], rows: List[List[str]]) -> None:
    """Render rows as a simple ASCII table."""
    if not rows:
        return

    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i >= len(widths):
                widths.append(len(str(cell)))
            else:
                widths[i] = max(widths[i], len(str(cell)))

    top_border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_line = "| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    header_border = "+" + "+".join("=" * (w + 2) for w in widths) + "+"

    print(top_border)
    print(header_line)
    print(header_border)
    for row in rows:
        print("| " + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)) + " |")
    print(top_border)

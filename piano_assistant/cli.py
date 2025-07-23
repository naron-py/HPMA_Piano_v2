import argparse
from rich.console import Console

console = Console()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Piano Assistant command line interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_convert = subparsers.add_parser("convert", help="Convert a MIDI/MXL file")
    p_convert.add_argument("path", help="Path to a MIDI or MusicXML file")

    p_play = subparsers.add_parser("play", help="Play a converted song file")
    p_play.add_argument("path", help="Path to a converted song text file")

    p_test = subparsers.add_parser("test", help="Test a converted song file")
    p_test.add_argument("path", help="Path to a converted song text file")

    args = parser.parse_args(argv)

    if args.command == "convert":
        from . import converter
        try:
            out = converter.convert(args.path)
        except Exception as exc:
            console.print(f"[red]Failed to convert:[/red] {exc}")
            return 1
        console.print(f"Saved to [green]{out}[/green]")
    elif args.command == "play":
        from . import player
        player.play(args.path)
    elif args.command == "test":
        from . import tester
        tester.test(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

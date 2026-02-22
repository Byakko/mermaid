"""
sanitize_common.py
==================
Shared I/O infrastructure for sanitize_*.py scripts.

Each sanitize script supplies its own description, epilog, and prompt_name,
then delegates all argument parsing, file handling, and output writing here.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def make_arg_parser(description: str, epilog: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input file to read",
    )
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output file to write (default: same as input)",
    )
    parser.add_argument(
        "--line-ending",
        "-l",
        choices=["lf", "crlf"],
        default="lf",
        help="Line ending style: 'lf' for Unix/Linux/macOS, 'crlf' for Windows (default: lf)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip overwrite confirmation prompts",
    )
    return parser


# =============================================================================
# File helpers
# =============================================================================

def check_file_exists(file_path: Path) -> bool:
    return file_path.exists() and file_path.is_file()


def prompt_overwrite(file_path: Path) -> bool:
    response = input(f"File '{file_path}' exists. Overwrite? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def read_input_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def write_output_file(file_path: Path, content: str) -> None:
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)


# =============================================================================
# Input routing
# =============================================================================

def read_interactive_input(prompt_name: str) -> str:
    print(f"Enter {prompt_name} (press Ctrl+Z then Enter on Windows,")
    print("or Ctrl+D on Unix/Linux, or enter an empty line to finish):")
    print("-" * 40)

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    print("-" * 40)
    return "\n".join(lines)


def get_input_text(args: argparse.Namespace, prompt_name: str) -> Optional[str]:
    # Mode 1: No file specified - read from piped stdin or interactive input
    if args.input_file is None:
        if not sys.stdin.isatty():
            return sys.stdin.read()
        return read_interactive_input(prompt_name)

    input_path = Path(args.input_file)

    if not check_file_exists(input_path):
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        return None

    # Mode 2: One file specified - will overwrite same file
    if args.output_file is None:
        if not args.yes:
            if not prompt_overwrite(input_path):
                print("Cancelled.")
                return None
        return read_input_file(input_path)

    # Mode 3: Two files specified - read from first, write to second
    output_path = Path(args.output_file)

    if check_file_exists(output_path):
        if not args.yes:
            if not prompt_overwrite(output_path):
                print("Cancelled.")
                return None

    return read_input_file(input_path)


# =============================================================================
# Output routing
# =============================================================================

def apply_line_ending(text: str, style: str) -> str:
    """Normalise to LF first, then convert if CRLF is requested."""
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    if style == "crlf":
        return normalised.replace("\n", "\r\n")
    return normalised


def write_output(text: str, args: argparse.Namespace) -> None:
    # Mode 1: No file specified - print to stdout
    if args.input_file is None:
        print("\n" + "=" * 40)
        print("Sanitized Output:")
        print("=" * 40)
        print(text)
        return

    # Mode 2: One file specified - overwrite the same file
    if args.output_file is None:
        output_path = Path(args.input_file)
        write_output_file(output_path, text)
        print(f"Updated file: {output_path}")
        return

    # Mode 3: Two files specified - write to second file
    output_path = Path(args.output_file)
    write_output_file(output_path, text)
    print(f"Wrote to file: {output_path}")

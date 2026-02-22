#!/usr/bin/env python3
"""
Sanitize Mermaid Diagram Script (v2)

This script takes Mermaid diagram text, converts it to a Python object using
mermaid_to_python, then converts it back to text using python_to_mermaid,
producing consistently formatted output.

Currently only gantt charts are supported; other diagram types will be added
as converter modules are created.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from mermaid.base import LineEnding

from mermaid_to_python import mermaid_to_python
from python_to_mermaid import python_to_mermaid


# =============================================================================
# Argument Parsing
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Sanitize Mermaid diagrams by converting to Python objects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (type/paste Mermaid text)
  python sanitize_mermaid.py

  # Pipe from stdin
  cat diagram.mmd | python sanitize_mermaid.py

  # Read from file, overwrite same file
  python sanitize_mermaid.py diagram.mmd

  # Read from input file, write to output file
  python sanitize_mermaid.py input.mmd output.mmd

  # Specify Windows-style line endings
  python sanitize_mermaid.py --line-ending crlf diagram.mmd
        """
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input Mermaid file to read"
    )

    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output file to write (default: same as input)"
    )

    parser.add_argument(
        "--line-ending",
        "-l",
        choices=["lf", "crlf"],
        default="lf",
        help="Line ending style: 'lf' for Unix/Linux/macOS, 'crlf' for Windows (default: lf)"
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip overwrite confirmation prompts"
    )

    return parser.parse_args()


def parse_line_ending(value: str) -> LineEnding:
    """
    Convert line ending string to LineEnding enum.

    Args:
        value: Line ending string ("lf" or "crlf")

    Returns:
        LineEnding enum value
    """
    return LineEnding.CRLF if value.lower() == "crlf" else LineEnding.LF


# =============================================================================
# File Operations
# =============================================================================

def check_file_exists(file_path: Path) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return file_path.exists() and file_path.is_file()


def prompt_overwrite(file_path: Path) -> bool:
    """
    Prompt user to confirm file overwrite.

    Args:
        file_path: File that would be overwritten

    Returns:
        True if user confirms overwrite, False otherwise
    """
    response = input(f"File '{file_path}' exists. Overwrite? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def read_input_file(file_path: Path) -> str:
    """
    Read content from a file.

    Args:
        file_path: Path to file to read

    Returns:
        File contents as string
    """
    return file_path.read_text(encoding="utf-8")


def write_output_file(file_path: Path, content: str) -> None:
    """
    Write content to a file.

    Args:
        file_path: Path to file to write
        content: Content to write
    """
    # Use newline='' to preserve exact line endings without platform translation
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def read_interactive_input() -> str:
    """
    Read Mermaid text from interactive user input.

    User enters text line by line. Press Enter on an empty line
    (Ctrl+D on Unix, Ctrl+Z on Windows) to finish input.

    Returns:
        The entered text as a string
    """
    print("Enter Mermaid diagram text (press Ctrl+Z then Enter on Windows,")
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


def get_input_text(args: argparse.Namespace) -> Optional[str]:
    """
    Retrieve input text based on command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Input text, or None if user cancelled
    """
    # Mode 1: No file specified - read from piped stdin or interactive input
    if args.input_file is None:
        if not sys.stdin.isatty():
            return sys.stdin.read()
        return read_interactive_input()

    input_path = Path(args.input_file)

    # Check input file exists for modes 2 and 3
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
# Output Writing
# =============================================================================

def write_output(text: str, args: argparse.Namespace) -> None:
    """
    Write output to file or stdout based on command line arguments.

    Args:
        text: Output text
        args: Parsed command line arguments
    """
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


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_arguments()
    line_ending = parse_line_ending(args.line_ending)

    # Get input text
    input_text = get_input_text(args)

    if input_text is None:
        return 1

    if not input_text.strip():
        print("Error: No input provided.", file=sys.stderr)
        return 1

    print(f"Parsing with {line_ending.name} line endings...")

    # Parse the Mermaid text
    diagram = mermaid_to_python(input_text, line_ending)

    if diagram is None:
        print("Error: Failed to parse diagram.", file=sys.stderr)
        return 1

    print(f"Successfully parsed: {type(diagram).__name__}")

    # Convert back to Mermaid text
    output_text = python_to_mermaid(diagram)

    # Write output
    write_output(output_text, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

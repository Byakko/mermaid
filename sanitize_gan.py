#!/usr/bin/env python3
"""
Sanitize GanttProject .gan Script

Runs a .gan file through a grand round trip —
gan -> Python objects -> JSON -> Python objects -> gan —
producing consistently formatted output.
"""

import sys

from gan_to_python import gan_to_python
from json_to_python import json_to_python
from python_to_gan import python_to_gan
from python_to_json import python_to_json
from sanitize_common import apply_line_ending, get_input_text, make_arg_parser, write_output

_DESCRIPTION = (
    "Sanitize GanttProject .gan files via a grand round trip "
    "through Python objects and JSON"
)

_EPILOG = """
Examples:
  # Interactive mode (paste .gan XML)
  python sanitize_gan.py

  # Pipe from stdin
  cat project.gan | python sanitize_gan.py

  # Read from file, overwrite same file
  python sanitize_gan.py project.gan

  # Read from input file, write to output file
  python sanitize_gan.py input.gan output.gan

  # Specify Windows-style line endings
  python sanitize_gan.py --line-ending crlf project.gan
"""


def main() -> int:
    args = make_arg_parser(_DESCRIPTION, _EPILOG).parse_args()

    input_text = get_input_text(args, ".gan XML text")

    if input_text is None:
        return 1

    if not input_text.strip():
        print("Error: No input provided.", file=sys.stderr)
        return 1

    # Grand round trip: gan -> python -> json -> python -> gan

    doc = gan_to_python(input_text)
    if doc is None:
        print("Error: Failed to parse .gan file.", file=sys.stderr)
        return 1

    json_text = python_to_json(doc)
    if json_text is None:
        print("Error: Failed to render JSON.", file=sys.stderr)
        return 1

    doc2 = json_to_python(json_text)
    if doc2 is None:
        print("Error: Failed to parse JSON.", file=sys.stderr)
        return 1

    output_text = python_to_gan(doc2)
    if output_text is None:
        print("Error: Failed to render .gan file.", file=sys.stderr)
        return 1

    print(f"Successfully sanitized: {type(doc2.diagram).__name__}")

    write_output(apply_line_ending(output_text, args.line_ending), args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

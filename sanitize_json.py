#!/usr/bin/env python3
"""
Sanitize AST JSON Script

Round-trips diagram AST JSON through Python objects to produce consistently
formatted output.

Currently only Gantt diagrams are supported; other diagram types will be
added as converter modules are created.
"""

import sys

from json_to_python import json_to_python
from python_to_json import python_to_json
from sanitize_common import apply_line_ending, get_input_text, make_arg_parser, write_output

_DESCRIPTION = "Sanitize diagram AST JSON by round-tripping through Python objects"

_EPILOG = """
Examples:
  # Interactive mode (type/paste JSON)
  python sanitize_json.py

  # Pipe from stdin
  cat diagram.json | python sanitize_json.py

  # Read from file, overwrite same file
  python sanitize_json.py diagram.json

  # Read from input file, write to output file
  python sanitize_json.py input.json output.json

  # Specify Windows-style line endings
  python sanitize_json.py --line-ending crlf diagram.json
"""


def main() -> int:
    args = make_arg_parser(_DESCRIPTION, _EPILOG).parse_args()

    input_text = get_input_text(args, "diagram AST JSON")

    if input_text is None:
        return 1

    if not input_text.strip():
        print("Error: No input provided.", file=sys.stderr)
        return 1

    doc = json_to_python(input_text)
    if doc is None:
        print("Error: Failed to parse JSON.", file=sys.stderr)
        return 1

    print(f"Successfully parsed: {type(doc.diagram).__name__}")

    output_text = python_to_json(doc)
    if output_text is None:
        print("Error: Failed to render JSON.", file=sys.stderr)
        return 1

    write_output(apply_line_ending(output_text, args.line_ending), args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

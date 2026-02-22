#!/usr/bin/env python3
"""
Sanitize Mermaid Diagram Script

Runs a Mermaid diagram through a grand round trip —
mermaid -> Python objects -> JSON -> Python objects -> mermaid —
producing consistently formatted output.

Currently only Gantt diagrams are supported; other diagram types will be
added as converter modules are created.
"""

import sys

from json_to_python import json_to_python
from mermaid_to_python import mermaid_to_python
from python_to_json import python_to_json
from python_to_mermaid import python_to_mermaid
from sanitize_common import apply_line_ending, get_input_text, make_arg_parser, write_output

_DESCRIPTION = (
    "Sanitize Mermaid diagrams via a grand round trip "
    "through Python objects and JSON"
)

_EPILOG = """
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


def main() -> int:
    args = make_arg_parser(_DESCRIPTION, _EPILOG).parse_args()

    input_text = get_input_text(args, "Mermaid diagram text")

    if input_text is None:
        return 1

    if not input_text.strip():
        print("Error: No input provided.", file=sys.stderr)
        return 1

    # Grand round trip: mermaid -> python -> json -> python -> mermaid

    doc = mermaid_to_python(input_text)
    if doc is None:
        print("Error: Failed to parse Mermaid diagram.", file=sys.stderr)
        return 1

    json_text = python_to_json(doc)
    if json_text is None:
        print("Error: Failed to render JSON.", file=sys.stderr)
        return 1

    doc2 = json_to_python(json_text)
    if doc2 is None:
        print("Error: Failed to parse JSON.", file=sys.stderr)
        return 1

    output_text = python_to_mermaid(doc2)
    if output_text is None:
        print("Error: Failed to render Mermaid diagram.", file=sys.stderr)
        return 1

    print(f"Successfully sanitized: {type(doc2.diagram).__name__}")

    write_output(apply_line_ending(output_text, args.line_ending), args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

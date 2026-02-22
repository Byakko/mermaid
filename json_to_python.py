"""
Convert AST JSON to diagram_models Python objects.
"""

import json
import sys
from typing import Optional

from diagram_models import Document
from diagram_models.gantt import GanttDiagram

from json_to_python_converters.jtp_gantt import parse_gantt


# Maps diagram kind strings to their parser functions.
# Each parser receives the diagram sub-dict and returns a diagram_models object.
_PARSERS = {
    "GANTT_DIAGRAM": parse_gantt,
}


def json_to_python(text: str) -> Optional[Document]:
    """
    Parse AST JSON text into a diagram_models Document.

    Args:
        text: JSON text conforming to schema/schema.graphql

    Returns:
        A Document object, or None if parsing fails.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Warning: JSON parse error: {e}", file=sys.stderr)
        return None

    diagram_data = data.get("diagram", {})
    kind = diagram_data.get("kind")

    parser = _PARSERS.get(kind)
    if parser is None:
        print(f"Warning: Unknown or unsupported diagram kind '{kind}'", file=sys.stderr)
        return None

    try:
        diagram = parser(diagram_data)
        return Document(
            diagram=diagram,
            version=data.get("version"),
            frontmatter=data.get("frontmatter"),
        )
    except Exception as e:
        print(f"Warning: Error parsing {kind} diagram: {e}", file=sys.stderr)
        return None

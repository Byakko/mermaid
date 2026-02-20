"""
Convert Mermaid diagram text to Python objects.
"""

import sys
from typing import Optional

from mermaid.base import Diagram, LineEnding

from mermaid_to_python_converters.mtp_common import extract_frontmatter, detect_diagram_type
from mermaid_to_python_converters.mtp_gantt import parse_gantt
from mermaid_to_python_converters.mtp_pie_chart import parse_pie_chart
from mermaid_to_python_converters.mtp_flowchart import parse_flowchart
from mermaid_to_python_converters.mtp_sequence import parse_sequence
from mermaid_to_python_converters.mtp_timeline import parse_timeline


def mermaid_to_python(text: str, line_ending: LineEnding = LineEnding.LF) -> Optional[Diagram]:
    """
    Parse Mermaid text into a Python object.

    Currently only gantt charts are supported. Other diagram types will be
    added as separate converter modules.

    Args:
        text: Mermaid diagram text
        line_ending: Line ending style for output

    Returns:
        Python Mermaid diagram object, or None if parsing fails
    """
    # Save the full original input
    original_text = text

    # Extract frontmatter before parsing
    frontmatter, text = extract_frontmatter(text)

    diagram_type = detect_diagram_type(text)

    parsers = {
        "gantt": parse_gantt,
        "pie": parse_pie_chart,
        "flowchart": parse_flowchart,
        "sequence": parse_sequence,
        "timeline": parse_timeline,
    }

    parser = parsers.get(diagram_type)
    if parser:
        try:
            diagram = parser(text, line_ending)
            if diagram is not None:
                diagram.raw_input = original_text
                if frontmatter is not None:
                    diagram.raw_frontmatter = frontmatter
            return diagram
        except Exception as e:
            print(f"Warning: Error parsing {diagram_type} diagram: {e}", file=sys.stderr)

    print(f"Warning: Unknown or unsupported diagram type '{diagram_type}'", file=sys.stderr)
    return None

"""
Pie chart parser for converting Mermaid pie text to Python objects.
"""

import re
from typing import Optional

from mermaid import PieChart, ShowData
from mermaid.base import LineEnding

from mermaid_to_python_converters.mtp_common import (
    is_declaration,
    try_parse_directive,
)


def _parse_pie_declaration(line: str, diagram: PieChart) -> None:
    """
    Parse the pie declaration line for showData and title.

    The declaration line can be:
        pie
        pie showData
        pie title My Title
        pie showData title My Title
        pie title "My Title"
        pie showData title "My Title"
    """
    # Strip the "pie" keyword
    rest = re.sub(r'^pie\s*', '', line, flags=re.IGNORECASE).strip()
    if not rest:
        return

    # Check for showData
    if rest.lower().startswith('showdata'):
        diagram.show_data = ShowData.NAME
        rest = rest[len('showdata'):].strip()

    # Check for title
    title_match = re.match(r'title\s+(.+)', rest, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
        # Strip surrounding quotes if present
        if len(title) >= 2 and title[0] == '"' and title[-1] == '"':
            title = title[1:-1]
        diagram.title = title


def _parse_pie_slice(line: str) -> Optional[tuple]:
    """
    Parse a pie slice line like: "Label" : 42.5

    Returns:
        Tuple of (label, value) or None if not a slice line.
    """
    match = re.match(r'"([^"]+)"\s*:\s*([0-9]*\.?[0-9]+)', line)
    if match:
        label = match.group(1)
        value = float(match.group(2))
        return label, value
    return None


def parse_pie_chart(text: str, line_ending: LineEnding) -> PieChart:
    """
    Parse a Mermaid pie chart from text.

    Args:
        text: Mermaid pie chart text
        line_ending: Line ending style

    Returns:
        A PieChart object
    """
    diagram = PieChart(title=None, line_ending=line_ending)

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Skip comments (preserved from raw input by python_to_mermaid.py)
        if line.startswith("%%"):
            continue

        # Parse the declaration line
        if is_declaration(line, "pie"):
            _parse_pie_declaration(line, diagram)
            continue

        # Title on its own line
        title = try_parse_directive(line, "title")
        if title is not None:
            # Strip surrounding quotes if present
            if len(title) >= 2 and title[0] == '"' and title[-1] == '"':
                title = title[1:-1]
            diagram.title = title
            diagram.title_inline = False
            continue

        # showData on its own line
        if line.lower() == "showdata":
            diagram.show_data = ShowData.NAME
            diagram.title_inline = False
            continue

        # Parse slice line
        slice_data = _parse_pie_slice(line)
        if slice_data:
            label, value = slice_data
            diagram.add_slice(value, label)

    return diagram

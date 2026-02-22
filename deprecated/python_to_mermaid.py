"""
Convert Python diagram objects back to Mermaid text.
"""

from typing import List, Optional

from mermaid import GanttChart, PieChart, Flowchart, SequenceDiagram, Timeline
from mermaid.base import Diagram, DiagramType

from python_to_mermaid_converters.ptm_gantt import render_gantt
from python_to_mermaid_converters.ptm_pie_chart import render_pie_chart
from python_to_mermaid_converters.ptm_flowchart import render_flowchart
from python_to_mermaid_converters.ptm_sequence import render_sequence
from python_to_mermaid_converters.ptm_timeline import render_timeline

# Maps diagram types to their renderer functions.
_RENDERERS = {
    GanttChart: render_gantt,
    PieChart: render_pie_chart,
    Flowchart: render_flowchart,
    SequenceDiagram: render_sequence,
    Timeline: render_timeline,
}


def _build_output_with_comments(diagram: Diagram, content_lines: List[str]) -> str:
    """
    Build the final output by preserving comment and frontmatter lines from the
    raw input, and filling remaining slots with rendered content lines.

    Args:
        diagram: The diagram object (must have raw_input set)
        content_lines: Rendered content lines from the ptm_ renderer

    Returns:
        Final mermaid text with comments and frontmatter preserved
    """
    raw_lines = diagram.raw_input.split("\n")
    output: List[Optional[str]] = [None] * len(raw_lines)

    # Pre-fill: frontmatter lines, comment lines, blank lines
    in_frontmatter = False
    for i, line in enumerate(raw_lines):
        stripped = line.strip()

        # Track frontmatter block (between --- delimiters)
        if stripped == "---":
            output[i] = line
            in_frontmatter = not in_frontmatter
            continue

        if in_frontmatter:
            output[i] = line
            continue

        if stripped.startswith("%%"):
            output[i] = line
            continue

        if not stripped:
            output[i] = line
            continue

    # Fill remaining empty slots with rendered content lines
    content_idx = 0
    for i in range(len(output)):
        if output[i] is None and content_idx < len(content_lines):
            output[i] = content_lines[content_idx]
            content_idx += 1

    return diagram.line_ending.value.join(
        line for line in output if line is not None
    )


def python_to_mermaid(diagram: Diagram) -> str:
    """
    Convert a Python Mermaid diagram object to Mermaid text.

    If the diagram has raw_input stored, comments and frontmatter are
    preserved from the original text. Otherwise falls back to direct
    rendering.

    Args:
        diagram: A Mermaid diagram object

    Returns:
        Mermaid diagram text
    """
    renderer = _RENDERERS.get(type(diagram))

    if renderer is None:
        # Fallback for diagram types without a dedicated converter yet
        return diagram.to_mermaid()

    content_lines = renderer(diagram)

    # If we have raw input, preserve comments and frontmatter
    if diagram.raw_input is not None:
        return _build_output_with_comments(diagram, content_lines)

    # No raw input — just join the content lines
    return diagram.line_ending.value.join(content_lines)

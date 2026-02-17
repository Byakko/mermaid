"""
Common rendering utilities for converting Python diagram objects to Mermaid text.
"""

from typing import Any, Dict, List

from mermaid.base import Diagram, LineEnding


def join_lines(lines: List[str], line_ending: LineEnding) -> str:
    """
    Join lines using the specified line ending.

    Args:
        lines: List of strings to join
        line_ending: Line ending style to use

    Returns:
        String with lines joined by the specified line ending
    """
    return line_ending.value.join(lines)


def render_config(diagram: Diagram) -> str:
    """
    Render the frontmatter block.

    If raw_frontmatter is set (preserved from parsing), it is returned
    as-is.  This ensures nested YAML structures round-trip faithfully
    without needing a full YAML parser.

    Args:
        diagram: Diagram whose frontmatter to render

    Returns:
        Frontmatter block string, or empty string if none
    """
    if diagram.raw_frontmatter is not None:
        return diagram.raw_frontmatter
    return ""

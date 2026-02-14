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
    Render the configuration and frontmatter as YAML frontmatter.

    Args:
        diagram: Diagram whose config/frontmatter to render

    Returns:
        Frontmatter block string, or empty string if no config/frontmatter
    """
    config_dict = diagram.config.to_dict()
    if not config_dict and not diagram.frontmatter:
        return ""

    lines = ["---"]

    # Render top-level frontmatter keys (e.g. displayMode)
    for key, value in diagram.frontmatter.items():
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")

    # Render config section
    if config_dict:
        lines.append("config:")
        for key, value in config_dict.items():
            if key == "elk":
                lines.append("  elk:")
                for elk_key, elk_value in value.items():
                    lines.append(f"    {elk_key}: {elk_value}")
            else:
                lines.append(f"  {key}: {value}")

    lines.append("---")
    return join_lines(lines, diagram.line_ending)

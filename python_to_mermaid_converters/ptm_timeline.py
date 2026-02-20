"""
Timeline renderer for converting Python Timeline objects to Mermaid text.

Returns a list of content lines (no frontmatter, no comments -- those are
handled by python_to_mermaid.py using the raw input).
"""

from typing import List

from mermaid.timeline import Timeline, TimePeriod, TimelineSection


def _render_period(period: TimePeriod, indent: int) -> str:
    """Render a time period with its events as a single line."""
    prefix = "    " * indent
    parts = [period.period] + period.events
    return f"{prefix}{' : '.join(parts)}"


def render_timeline(diagram: Timeline) -> List[str]:
    """
    Render a Timeline object as a list of content lines.

    Frontmatter and comments are NOT included -- those are preserved
    from the raw input by python_to_mermaid.py.

    Args:
        diagram: The Timeline to render

    Returns:
        List of content lines
    """
    lines: List[str] = []

    # Directive
    if diagram.directive:
        lines.append(str(diagram.directive))

    # Declaration
    lines.append("timeline")

    # Render from ordered items if available
    if diagram.items:
        in_section = False
        for item in diagram.items:
            if isinstance(item, tuple):
                tag = item[0]
                if tag == 'title':
                    lines.append(f"    title {item[1]}")
                elif tag == 'raw':
                    indent = 2 if in_section else 1
                    lines.append(f"{'    ' * indent}{item[1]}")
            elif isinstance(item, TimelineSection):
                in_section = True
                lines.append(f"    section {item.name}")
            elif isinstance(item, TimePeriod):
                indent = 2 if in_section else 1
                lines.append(_render_period(item, indent))
    else:
        # Fallback for programmatically created diagrams without items
        if diagram.title:
            lines.append(f"    title {diagram.title}")

        for period in diagram.periods:
            lines.append(_render_period(period, 1))

        for section in diagram.sections:
            lines.append(f"    section {section.name}")
            for period in section.periods:
                lines.append(_render_period(period, 2))

    return lines

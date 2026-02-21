"""
Timeline parser for converting Mermaid timeline text to Python objects.
"""

from typing import Optional, List

from mermaid.timeline import Timeline, TimePeriod, TimelineSection
from mermaid.base import LineEnding

from mermaid_to_python_converters.mtp_common import (
    is_declaration,
    try_parse_directive,
    try_parse_section,
    is_skip_line,
    split_colon_parts,
)


def _parse_period_line(line: str) -> Optional[TimePeriod]:
    """
    Parse a time period line with one or more events.

    Handles:
        2024 : Event One
        2002 : LinkedIn : Myspace : Facebook
        Industrial Revolution : Steam Engine

    Returns:
        A TimePeriod, or None if no colon separator found.
    """
    if ':' not in line:
        return None

    parts = split_colon_parts(line)
    if len(parts) < 2:
        return None

    period = parts[0]
    events = [p for p in parts[1:] if p]

    return TimePeriod(period=period, events=events)


def _parse_continuation(line: str) -> Optional[List[str]]:
    """
    Check if a line is a continuation (additional events for the previous period).

    Continuation lines start with ':' (after stripping whitespace):
        : New styles of pottery appear.

    Returns:
        List of event strings, or None if not a continuation.
    """
    stripped = line.strip()
    if not stripped.startswith(':'):
        return None

    events = [p.strip() for p in stripped.split(':') if p.strip()]
    return events if events else None


def parse_timeline(text: str, line_ending: LineEnding) -> Timeline:
    """
    Parse a Mermaid timeline diagram from text.

    Args:
        text: Mermaid timeline text (frontmatter already stripped)
        line_ending: Line ending style

    Returns:
        A Timeline object
    """
    diagram = Timeline(line_ending=line_ending)
    current_section: Optional[TimelineSection] = None
    last_period: Optional[TimePeriod] = None

    for raw_line in text.split("\n"):
        line = raw_line.strip()

        if is_skip_line(line):
            continue

        if is_declaration(line, "timeline"):
            continue

        # Title
        title = try_parse_directive(line, "title")
        if title is not None:
            diagram.title = title
            diagram.items.append(('title', title))
            continue

        # Section
        section_name = try_parse_section(line)
        if section_name is not None:
            current_section = TimelineSection(name=section_name)
            diagram.add_section(current_section)
            diagram.items.append(current_section)
            last_period = None
            continue

        # Continuation line (: event text) — appends to previous period
        cont_events = _parse_continuation(line)
        if cont_events is not None and last_period is not None:
            for ev in cont_events:
                last_period.add_event(ev)
            # No separate item — events are already on the period object
            continue

        # Time period with events
        period = _parse_period_line(line)
        if period is not None:
            if current_section:
                current_section.add_period(period)
            else:
                diagram.add_period(period)
            diagram.items.append(period)
            last_period = period
            continue

        # Unknown line — store as raw for round-tripping
        diagram.items.append(('raw', line))

    return diagram

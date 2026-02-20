"""
Timeline diagram classes for Mermaid.

This module contains classes for representing Mermaid timeline diagrams,
including time periods with multiple events and section grouping.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Union
from datetime import datetime

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


@dataclass
class TimePeriod:
    """
    Represents a time period with one or more events.

    Examples:
        2024-01-01 : Project Start
        2002 : LinkedIn : Myspace : Facebook
        Industrial Revolution : Invention of the Steam Engine
    """
    period: str
    events: List[str] = field(default_factory=list)

    def add_event(self, event: str) -> None:
        """Add an event to this time period."""
        self.events.append(event)


@dataclass
class TimelineSection:
    """
    Represents a section grouping in a timeline.

    Example:
        section Section Name
            2024-01-01 : Event 1
            2024-06-15 : Event 2
    """
    name: str
    periods: List[TimePeriod] = field(default_factory=list)

    def add_period(self, period: TimePeriod) -> None:
        """Add a time period to this section."""
        self.periods.append(period)


@dataclass
class Event:
    """
    Represents a legacy event in a timeline (kept for backward compatibility).

    Example:
        2024-01-01 : Project Start
        2024-06-15 : Milestone 1
    """
    date: Union[str, datetime]
    title: str
    description: Optional[str] = None

    def render(self) -> str:
        """Render the event in Mermaid syntax."""
        if isinstance(self.date, datetime):
            date_str = self.date.strftime("%Y-%m-%d")
        else:
            date_str = self.date

        if self.description:
            return f'{date_str} : "{self.title}" : {self.description}'
        return f'{date_str} : "{self.title}"'


class Timeline(Diagram):
    """
    Represents a Mermaid timeline diagram.

    Example:
        timeline
            title Project Timeline
            section Early
                2024-01-01 : Project Start
            section Late
                2024-12-31 : Project End
    """

    def __init__(
        self,
        title: Optional[str] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.events: List[Event] = []  # Legacy flat list
        self.sections: List[TimelineSection] = []
        self.periods: List[TimePeriod] = []  # Top-level (sectionless) periods
        self.items: List[Any] = []  # Ordered items for round-trip rendering

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.TIMELINE

    def add_event(self, event: Event) -> 'Timeline':
        """Add a legacy event to the timeline."""
        self.events.append(event)
        return self

    def add_section(self, section: TimelineSection) -> 'Timeline':
        """Add a section to the timeline."""
        self.sections.append(section)
        return self

    def add_period(self, period: TimePeriod) -> 'Timeline':
        """Add a top-level time period."""
        self.periods.append(period)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the timeline.

        Returns:
            String containing valid Mermaid syntax
        """
        lines = []

        # Add config frontmatter if present
        if self.config.to_dict() or self.frontmatter:
            lines.append(self._render_config())

        # Add directive if present
        if self.directive:
            lines.append(str(self.directive))

        # Add diagram type declaration
        lines.append(self.diagram_type.value)

        # Add title
        if self.title:
            lines.append(f'    title {self.title}')

        # Add events (legacy)
        for event in self.events:
            lines.append(f"    {event.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the timeline."""
        n_periods = len(self.periods) + sum(len(s.periods) for s in self.sections)
        return f"Timeline(title={self.title!r}, periods={n_periods})"

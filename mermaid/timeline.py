"""
Timeline diagram classes for Mermaid.

This module contains classes for representing Mermaid timeline diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


@dataclass
class Event:
    """
    Represents an event in a timeline.

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
            2024-01-01 : Project Start
            2024-06-15 : Milestone 1
            2024-12-31 : Project End
    """

    def __init__(
        self,
        title: str = "Timeline",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a timeline.

        Args:
            title: Title of the timeline
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.events: List[Event] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.TIMELINE

    def add_event(self, event: Event) -> 'Timeline':
        """Add an event to the timeline."""
        self.events.append(event)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the timeline.

        Returns:
            String containing valid Mermaid syntax
        """
        lines = []

        # Add config frontmatter if present
        if self.config.to_dict():
            lines.append(self._render_config())

        # Add directive if present
        if self.directive:
            lines.append(str(self.directive))

        # Add diagram type declaration
        lines.append(self.diagram_type.value)

        # Add title
        lines.append(f'    title "{self.title}"')

        # Add events
        for event in self.events:
            lines.append(f"    {event.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the timeline."""
        return f"Timeline(title='{self.title}', events={len(self.events)})"

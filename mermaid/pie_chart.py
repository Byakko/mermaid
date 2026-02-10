"""
Pie chart diagram classes for Mermaid.

This module contains classes for representing Mermaid pie charts.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


class ShowData(Enum):
    """Options for showing data in pie charts."""
    NONE = ""  # Don't show data
    NAME = "showData"  # Show data labels
    PERCENTAGE = "showData"  # Show percentage
    VALUE = "showData"  # Show values


@dataclass
class PieSlice:
    """
    Represents a slice in a pie chart.

    Example:
        - 60: Chrome
        - 30: Safari
        - 10: Others
    """
    value: float
    label: str

    def render(self) -> str:
        """Render the pie slice in Mermaid syntax."""
        return f"{self.value}: {self.label}"


class PieChart(Diagram):
    """
    Represents a Mermaid pie chart.

    Example:
        pie title Pets adopted by volunteers
            "Dogs" : 386
            "Cats" : 85
            "Rats" : 15
    """

    def __init__(
        self,
        title: str = "Pie Chart",
        show_data: ShowData = ShowData.NONE,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a pie chart.

        Args:
            title: Title of the pie chart
            show_data: Whether to show data labels
            config: Diagram configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.show_data = show_data
        self.slices: List[PieSlice] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.PIE

    def add_slice(self, value: float, label: str) -> 'PieChart':
        """Add a slice to the pie chart."""
        self.slices.append(PieSlice(value=value, label=label))
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the pie chart.

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
        lines.append(f"    title {self.title}")

        # Add show data if present
        if self.show_data != ShowData.NONE:
            lines.append(f"    {self.show_data.value}")

        # Add slices
        for slice in self.slices:
            lines.append(f"    {slice.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the pie chart."""
        return f"PieChart(title='{self.title}', slices={len(self.slices)})"

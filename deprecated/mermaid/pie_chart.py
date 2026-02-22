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
        # When True, showData/title appear on the 'pie' declaration line.
        # When False, they appear on separate indented lines.
        self.title_inline: bool = True

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.PIE

    def add_slice(self, value: float, label: str) -> 'PieChart':
        """Add a slice to the pie chart."""
        self.slices.append(PieSlice(value=value, label=label))
        return self

    def __repr__(self) -> str:
        """String representation of the pie chart."""
        return f"PieChart(title='{self.title}', slices={len(self.slices)})"

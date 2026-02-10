"""
Radar chart diagram classes for Mermaid.

This module contains classes for representing Mermaid radar charts.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


@dataclass
class Axis:
    """
    Represents an axis in a radar chart.

    Example:
        "Speed" : [80, 90, 70]
    """
    name: str
    values: List[float]

    def render(self) -> str:
        """Render the axis in Mermaid syntax."""
        values_str = ", ".join(str(v) for v in self.values)
        return f'"{self.name}" : [{values_str}]'


class RadarChart(Diagram):
    """
    Represents a Mermaid radar chart.

    Example:
        radar-beta
            title Skill Comparison
            axis "Speed", "Power", "Defense"
            "Player 1" : [80, 90, 70]
            "Player 2" : [70, 85, 90]
    """

    def __init__(
        self,
        title: str = "Radar Chart",
        axes: Optional[List[str]] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a radar chart.

        Args:
            title: Title of the radar chart
            axes: Names of the axes
            config: Diagram configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.axes = axes or []
        self.series: Dict[str, List[float]] = {}

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.RADAR

    def add_axis(self, name: str) -> 'RadarChart':
        """Add an axis to the chart."""
        self.axes.append(name)
        return self

    def add_series(self, name: str, values: List[float]) -> 'RadarChart':
        """Add a data series to the chart."""
        self.series[name] = values
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the radar chart.

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

        # Add axes
        if self.axes:
            axes_str = ", ".join(f'"{axis}"' for axis in self.axes)
            lines.append(f"    axis {axes_str}")

        # Add series
        for name, values in self.series.items():
            values_str = ", ".join(str(v) for v in values)
            lines.append(f'    "{name}" : [{values_str}]')

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the radar chart."""
        return f"RadarChart(title='{self.title}', series={len(self.series)})"

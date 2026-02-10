"""
Quadrant chart diagram classes for Mermaid.

This module contains classes for representing Mermaid quadrant charts.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


@dataclass
class Quadrant:
    """
    Represents a quadrant in a quadrant chart.

    Example:
        Quadrant 1
    """
    label: str
    x_range: Optional[Tuple[float, float]] = None  # (min, max)
    y_range: Optional[Tuple[float, float]] = None  # (min, max)


@dataclass
class Point:
    """
    Represents a point in a quadrant chart.

    Example:
        - Apple: [0.85, 0.9]
    """
    label: str
    x: float
    y: float

    def render(self) -> str:
        """Render the point in Mermaid syntax."""
        return f"{self.label}: [{self.x}, {self.y}]"


class QuadrantChart(Diagram):
    """
    Represents a Mermaid quadrant chart.

    Example:
        quadrantChart
            title Reach and engagement of campaigns
            x-axis Low reach --> High reach
            y-axis Low engagement --> High engagement
            quadrant-1 We should expand
            quadrant-2 Need to promote
            quadrant-3 Re-evaluate
            quadrant-4 Great opportunity
            Campaign A: [0.3, 0.8]
            Campaign B: [0.6, 0.5]
    """

    def __init__(
        self,
        title: str = "Quadrant Chart",
        x_axis_label: str = "X-axis",
        y_axis_label: str = "Y-axis",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a quadrant chart.

        Args:
            title: Title of the chart
            x_axis_label: Label for the x-axis
            y_axis_label: Label for the y-axis
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.x_axis_label = x_axis_label
        self.y_axis_label = y_axis_label
        self.quadrants: Dict[str, str] = {}  # quadrant_id -> label
        self.points: List[Point] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.QUADRANT

    def set_quadrant(self, number: int, label: str) -> 'QuadrantChart':
        """Set the label for a quadrant (1-4)."""
        self.quadrants[f"quadrant-{number}"] = label
        return self

    def add_point(self, label: str, x: float, y: float) -> 'QuadrantChart':
        """Add a point to the chart."""
        self.points.append(Point(label=label, x=x, y=y))
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the quadrant chart.

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

        # Add axis labels
        lines.append(f"    x-axis {self.x_axis_label}")
        lines.append(f"    y-axis {self.y_axis_label}")

        # Add quadrants
        for quad_id, label in self.quadrants.items():
            lines.append(f"    {quad_id} {label}")

        # Add points
        for point in self.points:
            lines.append(f"    {point.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the quadrant chart."""
        return f"QuadrantChart(title='{self.title}', points={len(self.points)})"

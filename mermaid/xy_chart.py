"""
XY Chart diagram classes for Mermaid.

This module contains classes for representing Mermaid XY charts.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from enum import Enum
from datetime import datetime

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


class XYChartType(Enum):
    """Types of XY charts."""
    LINE = "line"
    BAR = "bar"
    AREA = "area"


@dataclass
class Axis:
    """
    Represents an axis in an XY chart.

    Example:
        x-axis "Time" [January, February, March]
    """
    title: str
    labels: Optional[List[str]] = None
    # For time series
    is_time_series: bool = False
    time_format: Optional[str] = None  # e.g., "%Y-%m-%d"

    def render_x(self) -> str:
        """Render as x-axis."""
        if self.labels:
            labels_str = ", ".join(f'"{label}"' for label in self.labels)
            return f'x-axis "{self.title}" [{labels_str}]'
        return f'x-axis "{self.title}"'

    def render_y(self) -> str:
        """Render as y-axis."""
        return f'y-axis "{self.title}"'


@dataclass
class DataPoint:
    """
    Represents a data point in a series.

    Example:
        - 10
        - 15.5
        - "2024-01-01"
    """
    x: Union[float, str, datetime]
    y: Union[float, str]

    def render(self) -> str:
        """Render the data point."""
        if isinstance(self.x, datetime):
            x_str = self.x.strftime("%Y-%m-%d")
        elif isinstance(self.x, str):
            x_str = f'"{self.x}"'
        else:
            x_str = str(self.x)

        if isinstance(self.y, str):
            y_str = f'"{self.y}"'
        else:
            y_str = str(self.y)

        return f"[{x_str}, {y_str}]"


@dataclass
class DataSeries:
    """
    Represents a data series in an XY chart.

    Example:
        "Series 1" : [10, 15, 20]
    """
    title: str
    data_points: List[DataPoint] = field(default_factory=list)
    # For simple data (just y values)
    simple_values: Optional[List[float]] = None
    chart_type: XYChartType = XYChartType.LINE
    fill: Optional[str] = None  # Fill color for area charts

    def render(self) -> str:
        """Render the data series in Mermaid syntax."""
        if self.simple_values:
            values_str = ", ".join(str(v) for v in self.simple_values)
            return f'"{self.title}" : [{values_str}]'

        points_str = ", ".join(point.render() for point in self.data_points)
        return f'"{self.title}" : [{points_str}]'


class XYChart(Diagram):
    """
    Represents a Mermaid XY chart.

    Example:
        xychart-beta
            title "Sales Revenue"
            x-axis "Year" [2021, 2022, 2023, 2024]
            y-axis "Revenue" 0 to 10000
            "Product A" : [2000, 3500, 5000, 7000]
            "Product B" : [1500, 2500, 4000, 6000]
    """

    def __init__(
        self,
        title: str = "XY Chart",
        chart_type: XYChartType = XYChartType.LINE,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize an XY chart.

        Args:
            title: Title of the chart
            chart_type: Type of chart
            config: Diagram configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.chart_type = chart_type
        self.x_axis: Optional[Axis] = None
        self.y_axis: Optional[Axis] = None
        self.series: List[DataSeries] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.XY_CHART

    def set_x_axis(self, axis: Axis) -> 'XYChart':
        """Set the x-axis."""
        self.x_axis = axis
        return self

    def set_y_axis(self, axis: Axis) -> 'XYChart':
        """Set the y-axis."""
        self.y_axis = axis
        return self

    def add_series(self, series: DataSeries) -> 'XYChart':
        """Add a data series to the chart."""
        self.series.append(series)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the XY chart.

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

        # Add x-axis
        if self.x_axis:
            lines.append(f"    {self.x_axis.render_x()}")

        # Add y-axis
        if self.y_axis:
            lines.append(f"    {self.y_axis.render_y()}")

        # Add series
        for series in self.series:
            lines.append(f"    {series.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the XY chart."""
        return f"XYChart(title='{self.title}', series={len(self.series)})"

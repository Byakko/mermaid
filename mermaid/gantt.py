"""
Gantt chart diagram classes for Mermaid.

This module contains classes for representing Mermaid Gantt charts.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


class TaskStatus(Enum):
    """Status for Gantt tasks."""
    DONE = "done"
    ACTIVE = "active"
    CRIT = "crit"
    MILESTONE = "milestone"
    VERT = "vert"


@dataclass
class DateRange:
    """Represents a date range for a task."""
    start: Union[str, datetime]
    end: Union[str, datetime]

    def __str__(self) -> str:
        """Render the date range."""
        return f"{self.start}, {self.end}"


@dataclass
class GanttTask:
    """
    Represents a task in a Gantt chart.

    Examples:
        - task1 : 2024-01-01, 10d
        - task2 :id1, 2024-01-01, 10d
        - task3 :after task1, 5d
        - task4 :active, id4, 2024-01-01, 10d
        - task5 :crit, active, 3d  # multiple statuses
    """
    name: str
    start: Union[str, datetime, DateRange]
    duration: Optional[str] = None
    status: Optional[TaskStatus] = None  # Primary status (for backward compat)
    statuses: List[str] = field(default_factory=list)  # Multiple status keywords
    task_id: Optional[str] = None
    assignee: Optional[str] = None
    # For exclusive tasks
    excludes: Optional[str] = None

    def render(self) -> str:
        """Rendering has been moved to python_to_mermaid_converters/ptm_gantt.py"""
        raise NotImplementedError(
            "GanttTask.render() has been moved to "
            "python_to_mermaid_converters.ptm_gantt.render_gantt_task()"
        )


@dataclass
class GanttMilestone:
    """
    Represents a milestone in a Gantt chart.

    Example:
        milestone : 2024-01-10, 0d
    """
    name: str
    date: Union[str, datetime]

    def render(self) -> str:
        """Render the milestone in Mermaid syntax."""
        return f"milestone : {self.name}, {self.date}, 0d"


@dataclass
class GanttSection:
    """
    Represents a section in a Gantt chart.

    Example:
        section Design
            task1: 2024-01-01, 10d
            task2: 2024-01-01, 10d
    """
    name: str
    tasks: List[GanttTask] = field(default_factory=list)
    milestones: List[GanttMilestone] = field(default_factory=list)
    # Ordered list of items (tasks, milestones, and comment strings) preserving
    # original ordering so that ``%%`` comments survive round-tripping.
    items: List[Union[GanttTask, GanttMilestone, str]] = field(default_factory=list)

    def add_task(self, task: GanttTask) -> 'GanttSection':
        """Add a task to the section."""
        self.tasks.append(task)
        self.items.append(task)
        return self

    def add_milestone(self, milestone: GanttMilestone) -> 'GanttSection':
        """Add a milestone to the section."""
        self.milestones.append(milestone)
        self.items.append(milestone)
        return self

    def add_comment(self, text: str) -> 'GanttSection':
        """Add a comment line (including the ``%%`` prefix) to the section."""
        self.items.append(text)
        return self


class GanttChart(Diagram):
    """
    Represents a Mermaid Gantt chart.

    Example:
        gantt
            title A Gantt Diagram
            dateFormat  YYYY-MM-DD
            section Section
            A task           :a1, 2014-01-01, 30d
            Another task     :after a1  , 20d
            section Another
            Task in sec      :2014-01-12  , 12d
            another task      : 24d
    """

    def __init__(
        self,
        title: Optional[str] = None,
        date_format: Optional[str] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a Gantt chart.

        Args:
            title: Title of the chart
            date_format: Date format string
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.date_format = date_format
        self.sections: List[GanttSection] = []
        # Tasks not belonging to any section
        self.tasks: List[GanttTask] = []
        # Comments in the directive/pre-section area
        self.header_comments: List[str] = []
        # Axis formatting
        self.axis_format: Optional[str] = None  # e.g., "%Y-%m-%d"
        # Exclusions
        self.excludes: Optional[str] = None  # e.g., "weekends"
        # Weekend override
        self.weekend: Optional[str] = None  # e.g., "friday"

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.GANTT

    def add_task(self, task: GanttTask) -> 'GanttChart':
        """Add a sectionless task to the chart."""
        self.tasks.append(task)
        return self

    def add_section(self, section: GanttSection) -> 'GanttChart':
        """Add a section to the chart."""
        self.sections.append(section)
        return self

    def set_axis_format(self, format_str: str) -> 'GanttChart':
        """Set the axis format."""
        self.axis_format = format_str
        return self

    def set_excludes(self, excludes: str) -> 'GanttChart':
        """Set the exclusions (e.g., 'weekends')."""
        self.excludes = excludes
        return self

    def to_mermaid(self) -> str:
        """Rendering has been moved to python_to_mermaid_converters/ptm_gantt.py"""
        raise NotImplementedError(
            "GanttChart.to_mermaid() has been moved to "
            "python_to_mermaid_converters.ptm_gantt.render_gantt()"
        )

    def __repr__(self) -> str:
        """String representation of the Gantt chart."""
        return f"GanttChart(title='{self.title}', sections={len(self.sections)})"

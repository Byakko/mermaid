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
        """Render the task in Mermaid syntax."""
        # Build the task line: TaskName :status1, status2, taskID, start, duration
        # Example: "Task :crit, active, id1, 2014-01-01, 3d" or "Task :crit, active, 3d"
        parts = []

        # Status(es) first (after colon)
        # Use statuses list if available, otherwise fall back to single status
        if self.statuses:
            # Multiple statuses: join with ", "
            status_str = ", ".join(self.statuses)
            parts.append(f":{status_str}")
        elif self.status:
            parts.append(f":{self.status.value}")
        else:
            parts.append(":")

        # Task ID (optional)
        if self.task_id:
            parts.append(self.task_id)

        # Start date/duration
        # If start is DateRange, add it
        if isinstance(self.start, DateRange):
            parts.append(str(self.start))
        # If we have a duration, add start (if non-empty) and duration
        elif self.duration:
            if self.start:  # Add start only if non-empty
                parts.append(str(self.start))
            parts.append(self.duration)
        # Otherwise just add start if it's non-empty
        elif self.start:
            parts.append(str(self.start))

        # Join parts, filtering out empty parts (like lone ":")
        filtered_parts = [p for p in parts if p != ":"]

        # If we have no status, the first part should start with ":"
        if not self.statuses and not self.status and filtered_parts:
            return f"{self.name} : {', '.join(filtered_parts)}"
        elif filtered_parts:
            return f"{self.name} {', '.join(filtered_parts)}"
        else:
            return f"{self.name} :"


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

    def add_task(self, task: GanttTask) -> 'GanttSection':
        """Add a task to the section."""
        self.tasks.append(task)
        return self

    def add_milestone(self, milestone: GanttMilestone) -> 'GanttSection':
        """Add a milestone to the section."""
        self.milestones.append(milestone)
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
        title: str = "Gantt Chart",
        date_format: str = "YYYY-MM-DD",
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
        # Axis formatting
        self.axis_format: Optional[str] = None  # e.g., "%Y-%m-%d"
        # Exclusions
        self.excludes: Optional[str] = None  # e.g., "weekends"

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.GANTT

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
        """
        Generate Mermaid syntax for the Gantt chart.

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

        # Add date format
        lines.append(f"    dateFormat {self.date_format}")

        # Add axis format if present
        if self.axis_format:
            lines.append(f"    axisFormat {self.axis_format}")

        # Add exclusions if present
        if self.excludes:
            lines.append(f"    excludes {self.excludes}")

        # Add sections
        for section in self.sections:
            lines.append(f"    section {section.name}")
            for task in section.tasks:
                lines.append(f"        {task.render()}")
            for milestone in section.milestones:
                lines.append(f"        {milestone.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the Gantt chart."""
        return f"GanttChart(title='{self.title}', sections={len(self.sections)})"

"""
Kanban diagram classes for Mermaid.

This module contains classes for representing Mermaid Kanban diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


class TaskStatus(Enum):
    """Status of tasks in Kanban boards."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class KanbanTask:
    """
    Represents a task in a Kanban board.

    Example:
        Task 1
    """
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    tags: Optional[List[str]] = None

    def render(self) -> str:
        """Render the task in Mermaid syntax."""
        if self.description:
            return f'{self.title} : {self.description}'
        if self.assignee:
            return f'{self.title} : Assigned to {self.assignee}'
        if self.tags:
            tags_str = ", ".join(self.tags)
            return f'{self.title} : {tags_str}'
        return self.title


@dataclass
class KanbanBoard:
    """
    Represents a Kanban board with columns.

    Example:
        Todo
            Task 1
            Task 2
        In Progress
            Task 3
        Done
            Task 4
    """
    title: str
    columns: Dict[str, List[KanbanTask]] = field(default_factory=dict)

    def add_column(self, name: str, tasks: Optional[List[KanbanTask]] = None) -> 'KanbanBoard':
        """Add a column to the board."""
        self.columns[name] = tasks or []
        return self

    def add_task(self, column: str, task: KanbanTask) -> 'KanbanBoard':
        """Add a task to a specific column."""
        if column not in self.columns:
            self.columns[column] = []
        self.columns[column].append(task)
        return self


class KanbanDiagram(Diagram):
    """
    Represents a Mermaid Kanban diagram.

    Example:
        kanban
            title Project Kanban Board
            Todo
                Task 1
                Task 2
            In Progress
                Task 3
            Done
                Task 4
    """

    def __init__(
        self,
        title: str = "Kanban Board",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a Kanban diagram.

        Args:
            title: Title of the Kanban board
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.board = KanbanBoard(title=title)

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.KANBAN

    def add_column(self, name: str, tasks: Optional[List[KanbanTask]] = None) -> 'KanbanDiagram':
        """Add a column to the board."""
        self.board.add_column(name, tasks)
        return self

    def add_task(self, column: str, task: KanbanTask) -> 'KanbanDiagram':
        """Add a task to a specific column."""
        self.board.add_task(column, task)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the Kanban diagram.

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
        lines.append(f"    title {self.title}")

        # Add columns and tasks
        for column_name, tasks in self.board.columns.items():
            lines.append(f"    {column_name}")
            for task in tasks:
                lines.append(f"        {task.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the Kanban diagram."""
        return f"KanbanDiagram(title='{self.title}', columns={len(self.board.columns)})"

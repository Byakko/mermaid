"""
User Journey diagram classes for Mermaid.

This module contains classes for representing Mermaid user journey diagrams.
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


class TaskSection(Enum):
    """Section types for user journey tasks."""
    PLANNED = "planned"
    DONE = "done"


@dataclass
class Task:
    """
    Represents a task in a user journey.

    Example:
        Buy fruits: 5: Me
    """
    description: str
    score: int  # 0-10, represented as 0-5 in Mermaid (displayed as column width)
    actor: str
    section: Optional[TaskSection] = None

    def render(self) -> str:
        """Render the task in Mermaid syntax."""
        section_prefix = ""
        if self.section:
            section_prefix = f"{self.section.value}: "
        score_display = self.score // 2  # Convert 0-10 to 0-5 for Mermaid
        return f"{section_prefix}{self.description}: {score_display}: {self.actor}"


@dataclass
class Actor:
    """
    Represents an actor in a user journey.

    Example:
        Accountant: 5, 4
    """
    name: str
    scores: List[int] = field(default_factory=list)  # Scores for each task column

    def render(self) -> str:
        """Render the actor in Mermaid syntax."""
        scores_str = ", ".join(str(s // 2) for s in self.scores)  # Convert to 0-5 range
        return f"{self.name}: {scores_str}"


class UserJourney(Diagram):
    """
    Represents a Mermaid user journey diagram.

    Example:
        journey
            title My working day
            section Go to work
              Make tea: 5: Me
              Go upstairs: 3: Me
              Do work: 1: Me, Cat
            section Go home
              Go downstairs: 5: Me
              Sit down: 5: Me
    """

    def __init__(
        self,
        title: str = "User Journey",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a user journey diagram.

        Args:
            title: Title of the journey
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.sections: Dict[str, List[Task]] = {}
        self.actors: Dict[str, Actor] = {}

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.USER_JOURNEY

    def add_task(self, section: str, task: Task) -> 'UserJourney':
        """Add a task to a section."""
        if section not in self.sections:
            self.sections[section] = []
        self.sections[section].append(task)
        return self

    def add_actor(self, actor: Actor) -> 'UserJourney':
        """Add an actor to the journey."""
        self.actors[actor.name] = actor
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the user journey.

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

        # Add sections and tasks
        for section_name, tasks in self.sections.items():
            lines.append(f"    section {section_name}")
            for task in tasks:
                lines.append(f"      {task.render()}")

        # Add actors (optional, usually auto-generated from tasks)
        for actor in self.actors.values():
            lines.append(f"    {actor.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the user journey."""
        return f"UserJourney(title='{self.title}', sections={len(self.sections)})"

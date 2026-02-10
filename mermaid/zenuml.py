"""
ZenUML diagram classes for Mermaid.

This module contains classes for representing Mermaid ZenUML sequence diagrams.
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


class ZenParticipant:
    """
    Represents a participant in a ZenUML diagram.

    Example:
        @Actor User
        @Service API
    """
    id: str
    type: str = "Actor"  # Actor, Service, Database, etc.
    label: Optional[str] = None

    def render(self) -> str:
        """Render the participant in ZenUML syntax."""
        if self.label:
            return f"@{self.type} {self.id} : {self.label}"
        return f"@{self.type} {self.id}"


@dataclass
class ZenMessage:
    """
    Represents a message in a ZenUML diagram.

    Example:
        User -> API : LoginRequest
        API -> Database : ValidateUser
    """
    from_participant: str
    to_participant: str
    message: str
    is_return: bool = False
    is_async: bool = False

    def render(self) -> str:
        """Render the message in ZenUML syntax."""
        if self.is_return:
            arrow = "<--"
        elif self.is_async:
            arrow = "->"
        else:
            arrow = "->"
        return f"{self.from_participant} {arrow} {self.to_participant} : {self.message}"


@dataclass
class ZenInteraction:
    """
    Represents an interaction block in ZenUML.

    Example:
        @Loop {
            User -> API : Retry
        }
    """
    type: str  # Loop, Alt, Opt, Par, etc.
    condition: Optional[str] = None
    messages: List[ZenMessage] = field(default_factory=list)
    nested_interactions: List['ZenInteraction'] = field(default_factory=list)

    def add_message(self, message: ZenMessage) -> 'ZenInteraction':
        """Add a message to the interaction."""
        self.messages.append(message)
        return self

    def add_nested(self, interaction: 'ZenInteraction') -> 'ZenInteraction':
        """Add a nested interaction."""
        self.nested_interactions.append(interaction)
        return self

    def render(self, indent: int = 0) -> str:
        """Render the interaction in ZenUML syntax."""
        indent_str = "    " * indent
        lines = []

        if self.condition:
            lines.append(f"{indent_str}@{self.type}({self.condition}) {{")
        else:
            lines.append(f"{indent_str}@{self.type} {{")

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        for nested in self.nested_interactions:
            lines.append(nested.render(indent + 1))

        lines.append(f"{indent_str}}}")
        return self._join_lines(lines)


class ZenUMLDiagram(Diagram):
    """
    Represents a Mermaid ZenUML sequence diagram.

    Example:
        zenuml
            @Actor User
            @Service API
            User -> API : LoginRequest
            API -> Database : ValidateUser
    """

    def __init__(
        self,
        title: Optional[str] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a ZenUML diagram.

        Args:
            title: Optional title for the diagram
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.participants: List[ZenParticipant] = []
        self.messages: List[ZenMessage] = []
        self.interactions: List[ZenInteraction] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.ZENUML

    def add_participant(self, participant: ZenParticipant) -> 'ZenUMLDiagram':
        """Add a participant to the diagram."""
        self.participants.append(participant)
        return self

    def add_message(self, message: ZenMessage) -> 'ZenUMLDiagram':
        """Add a message to the diagram."""
        self.messages.append(message)
        return self

    def add_interaction(self, interaction: ZenInteraction) -> 'ZenUMLDiagram':
        """Add an interaction block to the diagram."""
        self.interactions.append(interaction)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the ZenUML diagram.

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

        # Add title if present
        if self.title:
            lines.append(f'    title "{self.title}"')

        # Add participants
        for participant in self.participants:
            lines.append(f"    {participant.render()}")

        # Add messages
        for message in self.messages:
            lines.append(f"    {message.render()}")

        # Add interactions
        for interaction in self.interactions:
            lines.append(interaction.render())

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the ZenUML diagram."""
        return f"ZenUMLDiagram(participants={len(self.participants)}, messages={len(self.messages)})"

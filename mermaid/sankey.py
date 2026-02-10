"""
Sankey diagram classes for Mermaid.

This module contains classes for representing Mermaid Sankey diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    Color,
    LineEnding
)


@dataclass
class SankeyNode:
    """
    Represents a node in a Sankey diagram.

    Example:
        Egypt : 46.8
    """
    id: str
    value: Optional[float] = None
    label: Optional[str] = None
    color: Optional[Color] = None

    def render(self) -> str:
        """Render the node in Mermaid syntax."""
        if self.value:
            return f"{self.id} : {self.value}"
        return self.id


@dataclass
class SankeyLink:
    """
    Represents a link between nodes in a Sankey diagram.

    Example:
        Egypt|Hydropower|0.0|Renewable
    """
    from_node: str
    to_node: str
    value: float
    from_label: Optional[str] = None
    to_label: Optional[str] = None

    def render(self) -> str:
        """Render the link in Mermaid syntax."""
        parts = [self.from_node]
        if self.from_label:
            parts.append(self.from_label)
        parts.append(str(self.value))
        parts.append(self.to_node)
        if self.to_label:
            parts.append(self.to_label)
        return "|".join(parts)


class SankeyDiagram(Diagram):
    """
    Represents a Mermaid Sankey diagram.

    Example:
        sankey-beta
            Egypt,Coal,46.8,Electricity generation
            Egypt,Oil,23.3,Electricity generation
            Egypt,Natural gas,22.2,Electricity generation
    """

    def __init__(
        self,
        title: Optional[str] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a Sankey diagram.

        Args:
            title: Optional title for the diagram
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.nodes: List[SankeyNode] = []
        self.links: List[SankeyLink] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.SANKEY

    def add_node(self, node: SankeyNode) -> 'SankeyDiagram':
        """Add a node to the diagram."""
        self.nodes.append(node)
        return self

    def add_link(self, link: SankeyLink) -> 'SankeyDiagram':
        """Add a link to the diagram."""
        self.links.append(link)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the Sankey diagram.

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
            lines.append(f"    title {self.title}")

        # Add nodes
        for node in self.nodes:
            lines.append(f"    {node.render()}")

        # Add links
        for link in self.links:
            lines.append(f"    {link.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the Sankey diagram."""
        return f"SankeyDiagram(nodes={len(self.nodes)}, links={len(self.links)})"

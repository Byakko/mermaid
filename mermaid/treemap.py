"""
Treemap diagram classes for Mermaid.

This module contains classes for representing Mermaid treemap diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
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
class TreemapNode:
    """
    Represents a node in a treemap.

    Example:
        Root : 100
        A : 50
        B : 30
        C : 20
    """
    id: str
    value: Optional[float] = None
    label: Optional[str] = None
    color: Optional[Color] = None
    children: List['TreemapNode'] = field(default_factory=list)

    def add_child(self, child: 'TreemapNode') -> 'TreemapNode':
        """Add a child node."""
        self.children.append(child)
        return self

    def render(self, indent: int = 0) -> str:
        """Render the node in Mermaid syntax."""
        indent_str = "    " * indent

        if self.value:
            line = f'{indent_str}{self.id} : {self.value}'
        elif self.label:
            line = f'{indent_str}{self.id} : "{self.label}"'
        else:
            line = f'{indent_str}{self.id}'

        if self.children:
            for child in self.children:
                line += "\n" + child.render(indent + 1)

        return line


class Treemap(Diagram):
    """
    Represents a Mermaid treemap diagram.

    Example:
        treemap-beta
            title Project Budget Distribution
            "Development" : 50000
            "Design" : 25000
            "Marketing" : 20000
    """

    def __init__(
        self,
        title: str = "Treemap",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a treemap.

        Args:
            title: Title of the treemap
            config: Diagram configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.root_node: Optional[TreemapNode] = None
        self.nodes: List[TreemapNode] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.TREEMAP

    def set_root(self, node: TreemapNode) -> 'Treemap':
        """Set the root node of the treemap."""
        self.root_node = node
        return self

    def add_node(self, node: TreemapNode) -> 'Treemap':
        """Add a node to the treemap (flat structure)."""
        self.nodes.append(node)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the treemap.

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

        # Add root node if present
        if self.root_node:
            lines.append(self.root_node.render())

        # Add flat nodes
        for node in self.nodes:
            lines.append(f"    {node.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the treemap."""
        return f"Treemap(title='{self.title}', nodes={len(self.nodes)})"

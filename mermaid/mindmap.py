"""
Mindmap diagram classes for Mermaid.

This module contains classes for representing Mermaid mindmap diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    Style,
    Color,
    LineEnding
)


class Icon(Enum):
    """Icons available for mindmap nodes."""
    # Font Awesome icons
    FA_CIRCLE = "fa fa-circle"
    FA_SQUARE = "fa fa-square"
    FA_STAR = "fa fa-star"
    FA_CHECK = "fa fa-check"
    FA_CLOCK = "fa fa-clock"
    FA_COG = "fa fa-cog"
    FA_DATABASE = "fa fa-database"
    FA_CODE = "fa fa-code"
    FA_BUG = "fa fa-bug"
    FA_CLOUD = "fa fa-cloud"
    FA_BOLT = "fa fa-bolt"
    FA_CREDIT_CARD = "fa fa-credit-card"
    FA_GRADUATION_CAP = "fa fa-graduation-cap"


@dataclass
class MindmapNode:
    """
    Represents a node in a mindmap.

    Example:
        root((Mindmap))
          Origins
            Long history
              ::icon(fa fa-book)
              Popularisation
                British popular psychology author Tony Buzan
            Research
              On effectiveness
    """
    id: str
    label: Optional[str] = None
    # For root nodes with special shape
    is_root: bool = False
    shape: Optional[str] = None  # (( )) for circle, [ ] for rounded
    icon: Optional[Icon] = None
    # For styling
    style: Optional[str] = None  # CSS class name
    color: Optional[Color] = None
    children: List['MindmapNode'] = field(default_factory=list)

    def add_child(self, child: 'MindmapNode') -> 'MindmapNode':
        """Add a child node."""
        self.children.append(child)
        return self

    def render(self, indent: int = 0) -> str:
        """Render the node in Mermaid syntax."""
        indent_str = "    " * indent

        if self.is_root and self.shape:
            return f"{indent_str}{self.id}{self.shape}{self.label or ''}{self.shape}"

        parts = []
        if self.label:
            parts.append(self.label)
        if self.icon:
            parts.append(f"::icon({self.icon.value})")

        line = f"{indent_str}{self.id}{''.join(parts)}"

        if self.children:
            for child in self.children:
                line += "\n" + child.render(indent + 1)

        return line


class Mindmap(Diagram):
    """
    Represents a Mermaid mindmap.

    Example:
        mindmap
          root((Mindmap))
            Origins
              Long history
              ::icon(fa fa-book)
              Popularisation
                British popular psychology author Tony Buzan
            Research
              On effectiveness
    """

    def __init__(
        self,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a mindmap.

        Args:
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.root_node: Optional[MindmapNode] = None
        self.styles: Dict[str, str] = {}

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.MINDMAP

    def set_root(self, node: MindmapNode) -> 'Mindmap':
        """Set the root node of the mindmap."""
        node.is_root = True
        self.root_node = node
        return self

    def add_style(self, class_name: str, css: str) -> 'Mindmap':
        """Add a style class for the mindmap."""
        self.styles[class_name] = css
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the mindmap.

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

        # Add root node and all children
        if self.root_node:
            lines.append(self.root_node.render())

        # Add styles
        for class_name, css in self.styles.items():
            lines.append(f"    {class_name}{{{css}}}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the mindmap."""
        return f"Mindmap(root={self.root_node.label if self.root_node else None})"

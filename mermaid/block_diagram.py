"""
Block diagram classes for Mermaid.

This module contains classes for representing Mermaid block diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Tuple
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


class BlockShape(Enum):
    """Shapes for blocks in block diagrams."""
    SQUARE = "square"
    ROUNDED = "rounded"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    STADIUM = "stadium"


@dataclass
class Block:
    """
    Represents a block in a block diagram.

    Example:
        space:40
        a(space:40)
        b
    """
    id: str
    label: Optional[str] = None
    shape: BlockShape = BlockShape.SQUARE
    width: Optional[int] = None
    height: Optional[int] = None
    # For space blocks
    is_space: bool = False
    space_width: Optional[int] = None

    def render(self) -> str:
        """Render the block in Mermaid syntax."""
        if self.is_space and self.space_width:
            return f"{self.id}({self.space_width})"

        parts = []
        if self.width:
            parts.append(f"width:{self.width}")
        if self.height:
            parts.append(f"height:{self.height}")

        props = f"[{', '.join(parts)}]" if parts else ""

        if self.label:
            return f'{self.id}["{self.label}"]{props}'
        return f"{self.id}{props}"


@dataclass
class BlockRelation:
    """
    Represents a relation between blocks.

    Example:
        a --> b
        a -.-> b
    """
    from_block: str
    to_block: str
    line_type: str = "--"  # "--" or "-."
    arrow: bool = True
    label: Optional[str] = None

    def render(self) -> str:
        """Render the relation in Mermaid syntax."""
        line = f"{self.line_type}>{'' if self.arrow else ''}"
        result = f"{self.from_block} {line} {self.to_block}"
        if self.label:
            result = f'{result} : "{self.label}"'
        return result


@dataclass
class BlockRow:
    """
    Represents a row in a block diagram.

    Example:
        a b c
    """
    blocks: List[Union[Block, str]]  # Can be Block objects or block IDs

    def render(self) -> str:
        """Render the row in Mermaid syntax."""
        parts = []
        for block in self.blocks:
            if isinstance(block, Block):
                parts.append(block.render())
            else:
                parts.append(str(block))
        return " ".join(parts)


class BlockDiagram(Diagram):
    """
    Represents a Mermaid block diagram.

    Example:
        block-beta
            columns 1
            space:40
            a
            b
            a --> b
    """

    def __init__(
        self,
        columns: int = 1,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a block diagram.

        Args:
            columns: Number of columns in the diagram
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.columns = columns
        self.blocks: Dict[str, Block] = {}
        self.rows: List[BlockRow] = []
        self.relations: List[BlockRelation] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.BLOCK

    def add_block(self, block: Block) -> 'BlockDiagram':
        """Add a block to the diagram."""
        self.blocks[block.id] = block
        return self

    def add_row(self, row: BlockRow) -> 'BlockDiagram':
        """Add a row to the diagram."""
        self.rows.append(row)
        return self

    def add_relation(self, relation: BlockRelation) -> 'BlockDiagram':
        """Add a relation to the diagram."""
        self.relations.append(relation)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the block diagram.

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

        # Add columns
        lines.append(f"    columns {self.columns}")

        # Add blocks
        for block in self.blocks.values():
            lines.append(f"    {block.render()}")

        # Add rows
        for row in self.rows:
            lines.append(f"    {row.render()}")

        # Add relations
        for rel in self.relations:
            lines.append(f"    {rel.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the block diagram."""
        return f"BlockDiagram(columns={self.columns}, blocks={len(self.blocks)})"

"""
Packet diagram classes for Mermaid.

This module contains classes for representing Mermaid packet diagrams.
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


class PacketSize(Enum):
    """Standard sizes for packet fields."""
    BIT = 1
    NIBBLE = 4
    BYTE = 8
    WORD = 16
    DWORD = 32
    QWORD = 64


@dataclass
class PacketField:
    """
    Represents a field in a packet diagram.

    Example:
        0 : 7 : Version
        8 : 15 : Header Length
    """
    start_bit: int
    end_bit: int
    name: str
    size: Optional[int] = None  # Display size (not actual bits)
    color: Optional[Color] = None
    repeat: Optional[int] = None  # Number of repetitions

    def render(self) -> str:
        """Render the field in Mermaid syntax."""
        repeat_str = f" repeat {self.repeat}" if self.repeat else ""
        return f"{self.start_bit} : {self.end_bit} : {self.name}{repeat_str}"


@dataclass
class PacketRow:
    """
    Represents a row of packet fields (displayed as blocks).

    Example:
        0 : 31 : Header
        32 : 63 : Data
    """
    fields: List[PacketField]

    def render(self, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the row in Mermaid syntax."""
        lines = []
        for field in self.fields:
            lines.append(f"    {field.render()}")
        return line_ending.value.join(lines)


class PacketDiagram(Diagram):
    """
    Represents a Mermaid packet diagram.

    Example:
        packet-beta
            0 : 7 : Version
            8 : 15 : Header Length
            16 : 31 : Total Length
    """

    def __init__(
        self,
        title: Optional[str] = None,
        bit_width: int = 32,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a packet diagram.

        Args:
            title: Optional title for the diagram
            bit_width: Total width of the packet in bits
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.bit_width = bit_width
        self.fields: List[PacketField] = []
        self.rows: List[PacketRow] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.PACKET

    def add_field(self, field: PacketField) -> 'PacketDiagram':
        """Add a field to the diagram."""
        self.fields.append(field)
        return self

    def add_row(self, row: PacketRow) -> 'PacketDiagram':
        """Add a row to the diagram."""
        self.rows.append(row)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the packet diagram.

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

        # Add bit width
        lines.append(f"    {self.bit_width}")

        # Add fields
        for field in self.fields:
            lines.append(f"    {field.render()}")

        # Add rows
        for row in self.rows:
            lines.append(row.render(self.line_ending))

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the packet diagram."""
        return f"PacketDiagram(bit_width={self.bit_width}, fields={len(self.fields)})"

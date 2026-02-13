"""
Base classes for Mermaid diagrams.

This module contains the fundamental classes that are used across
all Mermaid diagram types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
from enum import Enum


class DiagramType(Enum):
    """All supported Mermaid diagram types."""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequenceDiagram"
    CLASS = "classDiagram"
    STATE = "stateDiagram"
    ER = "erDiagram"
    USER_JOURNEY = "journey"
    GANTT = "gantt"
    PIE = "pie"
    QUADRANT = "quadrantChart"
    REQUIREMENT = "requirementDiagram"
    GITGRAPH = "gitGraph"
    C4 = "C4"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"
    ZENUML = "zenuml"
    SANKEY = "sankey-beta"
    XY_CHART = "xychart-beta"
    BLOCK = "block-beta"
    PACKET = "packet-beta"
    KANBAN = "kanban"
    ARCHITECTURE = "architecture"
    RADAR = "radar"
    TREEMAP = "treemap"


class Theme(Enum):
    """Mermaid theme options."""
    DEFAULT = "default"
    FOREST = "forest"
    DARK = "dark"
    NEUTRAL = "neutral"
    BASE = "base"


class Look(Enum):
    """Visual appearance options for diagrams."""
    HAND_DRAWN = "handdrawn"
    CLASSIC = "classic"


class Layout(Enum):
    """Layout algorithm options."""
    DAGRE = "dagre"
    ELK = "elk"


class FontStyle(Enum):
    """Font style options."""
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold italic"


class StrokeStyle(Enum):
    """Stroke style options."""
    SOLID = "solid"
    DOTTED = "dotted"
    DASHED = "dashed"


class LineEnding(Enum):
    """Line ending options for diagram output."""
    LF = "\n"      # Unix/Linux/macOS standard
    CRLF = "\r\n"  # Windows standard


@dataclass
class Color:
    """Represents a color in various formats."""
    name: Optional[str] = None
    hex: Optional[str] = None
    rgb: Optional[tuple[int, int, int]] = None
    rgba: Optional[tuple[int, int, int, float]] = None

    def __str__(self) -> str:
        if self.hex:
            return self.hex
        if self.rgb:
            return f"rgb({self.rgb[0]}, {self.rgb[1]}, {self.rgb[2]})"
        if self.rgba:
            return f"rgba({self.rgba[0]}, {self.rgba[1]}, {self.rgba[2]}, {self.rgba[3]})"
        if self.name:
            return self.name
        return ""


@dataclass
class DiagramConfig:
    """Configuration options for a diagram."""
    theme: Theme = Theme.DEFAULT
    look: Optional[Look] = None
    layout: Optional[Layout] = None
    title: Optional[str] = None
    # ELK specific options
    elk_merge_edges: Optional[bool] = None
    elk_node_placement_strategy: Optional[str] = None  # SIMPLE, NETWORK_SIMPLEX, LINEAR_SEGMENTS, BRANDES_KOEPF
    # Additional config as key-value pairs
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        config: Dict[str, Any] = {}
        if self.theme != Theme.DEFAULT:
            config["theme"] = self.theme.value
        if self.look:
            config["look"] = self.look.value
        if self.layout:
            config["layout"] = self.layout.value
        if self.title:
            config["title"] = self.title
        if self.elk_merge_edges is not None:
            config["elk"] = config.get("elk", {})
            config["elk"]["mergeEdges"] = self.elk_merge_edges
        if self.elk_node_placement_strategy:
            config["elk"] = config.get("elk", {})
            config["elk"]["nodePlacementStrategy"] = self.elk_node_placement_strategy
        config.update(self.additional_config)
        return config


@dataclass
class Directive:
    """
    Represents a Mermaid directive that can reconfigure a diagram before rendering.
    Format: %%{ <key>: <value> }%%
    """
    directives: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        if not self.directives:
            return ""
        items = ", ".join(f"{k}: {v}" for k, v in self.directives.items())
        return f"%%{{ {items} }}%%"


@dataclass
class Style:
    """Represents styling information for diagram elements."""
    fill: Optional[Color] = None
    stroke: Optional[Color] = None
    stroke_width: Optional[int] = None
    stroke_style: Optional[StrokeStyle] = None
    font_style: Optional[FontStyle] = None
    font_color: Optional[Color] = None
    font_size: Optional[int] = None
    font_family: Optional[str] = None
    # Additional CSS properties
    css_properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class Link:
    """Represents a hyperlink for diagram elements."""
    url: str
    tooltip: Optional[str] = None
    target: Optional[str] = None  # e.g., "_blank", "_self"


class Diagram(ABC):
    """
    Abstract base class for all Mermaid diagrams.

    All diagram types should inherit from this class and implement
    the to_mermaid() method to generate Mermaid syntax.
    """

    def __init__(
        self,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        metadata: Optional[Dict[str, Any]] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a diagram.

        Args:
            config: Diagram configuration options
            directive: Directive for pre-render configuration
            metadata: Additional metadata associated with the diagram
            line_ending: Line ending style to use in output (default: LF for Unix)
        """
        self.config = config or DiagramConfig()
        self.directive = directive
        self.metadata = metadata or {}
        self.frontmatter: Dict[str, Any] = {}
        self._comments: List[str] = []
        self.line_ending = line_ending

    @property
    @abstractmethod
    def diagram_type(self) -> DiagramType:
        """Return the type of this diagram."""
        pass

    @abstractmethod
    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for this diagram.

        Returns:
            String containing valid Mermaid syntax
        """
        pass

    def add_comment(self, comment: str) -> None:
        """
        Add a comment to the diagram.

        Args:
            comment: The comment text (without %% prefix)
        """
        self._comments.append(comment)

    def _join_lines(self, lines: List[str]) -> str:
        """
        Join lines using the configured line ending.

        Args:
            lines: List of strings to join

        Returns:
            String with lines joined by the configured line ending
        """
        return self.line_ending.value.join(lines)

    def _render_comments(self) -> str:
        """Render all comments as Mermaid syntax."""
        return self._join_lines(f"%% {comment}" for comment in self._comments)

    def _render_config(self) -> str:
        """Render the configuration and frontmatter as YAML frontmatter."""
        config_dict = self.config.to_dict()
        if not config_dict and not self.frontmatter:
            return ""

        lines = ["---"]

        # Render top-level frontmatter keys (e.g. displayMode)
        for key, value in self.frontmatter.items():
            if isinstance(value, bool):
                lines.append(f"{key}: {'true' if value else 'false'}")
            else:
                lines.append(f"{key}: {value}")

        # Render config section
        if config_dict:
            lines.append("config:")
            for key, value in config_dict.items():
                if key == "elk":
                    lines.append("  elk:")
                    for elk_key, elk_value in value.items():
                        lines.append(f"    {elk_key}: {elk_value}")
                else:
                    lines.append(f"  {key}: {value}")

        lines.append("---")
        return self._join_lines(lines)

    def __str__(self) -> str:
        """String representation of the diagram."""
        return self.to_mermaid()


@dataclass
class Label:
    """Represents a label/text element in a diagram."""
    text: str
    icon: Optional[str] = None
    emoji: Optional[str] = None
    class_name: Optional[str] = None  # For styling

    def __str__(self) -> str:
        if self.emoji:
            return f"{self.emoji} {self.text}"
        if self.icon:
            return f"<{self.icon}> {self.text}"
        return self.text


@dataclass
class StyledElement:
    """Base class for elements that can have styles and classes."""
    id: str
    label: Optional[Union[str, Label]] = None
    style: Optional[Style] = None
    class_name: Optional[str] = None
    link: Optional[Link] = None
    tooltip: Optional[str] = None

    def get_label_text(self) -> str:
        """Get the text representation of the label."""
        if self.label is None:
            return self.id
        if isinstance(self.label, Label):
            return str(self.label)
        return self.label


@dataclass
class ClassDef:
    """
    Represents a class definition for styling.
    Format: classDef className fill:#f9f,stroke:#333,stroke-width:4px
    """
    name: str
    style: Style

    def to_mermaid(self) -> str:
        """Generate Mermaid syntax for class definition."""
        parts = [f"classDef {self.name}"]
        if self.style.fill:
            parts.append(f"fill:{self.style.fill}")
        if self.style.stroke:
            parts.append(f"stroke:{self.style.stroke}")
        if self.style.stroke_width:
            parts.append(f"stroke-width:{self.style.stroke_width}px")
        if self.style.stroke_style:
            parts.append(f"stroke-dasharray: 5 5" if self.style.stroke_style != StrokeStyle.SOLID else "")
        if self.style.font_color:
            parts.append(f"color:{self.style.font_color}")
        if self.style.font_family:
            parts.append(f"font-family:{self.style.font_family}")
        if self.style.font_size:
            parts.append(f"font-size:{self.style.font_size}px")
        for prop, value in self.style.css_properties.items():
            parts.append(f"{prop}:{value}")
        return " ".join(p for p in parts if p)

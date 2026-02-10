"""
Flowchart diagram classes for Mermaid.

This module contains classes for representing Mermaid flowchart diagrams,
including nodes, edges, subgraphs, and various node shapes.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
from enum import Enum
from abc import abstractmethod

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    Style,
    Color,
    Link,
    Label,
    StyledElement,
    ClassDef,
    StrokeStyle,
    LineEnding,
)


class FlowchartDirection(Enum):
    """Direction of flowchart layout."""
    TOP_TO_BOTTOM = "TB"
    BOTTOM_TO_TOP = "BT"
    LEFT_TO_RIGHT = "LR"
    RIGHT_TO_LEFT = "RL"


class FlowchartNodeShape(Enum):
    """Node shapes in flowcharts."""
    # Basic shapes
    RECTANGLE = "rect"  # [text]
    ROUNDED = "rounded"  # (text)
    STADIUM = "stadium"  # ([text])
    SUBROUTINE = "subroutine"  # [[text]]
    CYLINDER = "cylinder"  # [(text)]
    CIRCLE = "circle"  # ((text))
    # Asymmetric shapes
    HEXAGON = "hexagon"  # {{text}}
    PARALLELOGRAM = "parallelogram"  # [/text/]
    PARALLELOGRAM_ALT = "parallelogram_alt"  # [\text/]
    TRAPEZOID = "trapezoid"  # [/text\]
    TRAPEZOID_ALT = "trapezoid_alt"  # [\text/]
    # Double shapes
    DOUBLE_CIRCLE = "double_circle"  # (((text)))
    # Rhombus
    RHOMBUS = "rhombus"  # {text}
    # Lean shapes
    LEAN_RIGHT = "lean_right"  # [text/]
    LEAN_LEFT = "lean_left"  # [\text]
    # Flagged shapes
    FLAG_RIGHT = "flag_right"  # ~text~
    FLAG_LEFT = "flag_left"  # text~

    @staticmethod
    def get_prefix(shape: 'FlowchartNodeShape') -> str:
        """Get the prefix for the shape."""
        prefixes = {
            FlowchartNodeShape.RECTANGLE: "[",
            FlowchartNodeShape.ROUNDED: "(",
            FlowchartNodeShape.STADIUM: "([",
            FlowchartNodeShape.SUBROUTINE: "[[",
            FlowchartNodeShape.CYLINDER: "[(",
            FlowchartNodeShape.CIRCLE: "((",
            FlowchartNodeShape.HEXAGON: "{{",
            FlowchartNodeShape.PARALLELOGRAM: "/",
            FlowchartNodeShape.PARALLELOGRAM_ALT: "[",
            FlowchartNodeShape.TRAPEZOID: "/",
            FlowchartNodeShape.TRAPEZOID_ALT: "[",
            FlowchartNodeShape.DOUBLE_CIRCLE: "(((",
            FlowchartNodeShape.RHOMBUS: "{",
            FlowchartNodeShape.LEAN_RIGHT: "[",
            FlowchartNodeShape.LEAN_LEFT: "[",
            FlowchartNodeShape.FLAG_RIGHT: "~",
            FlowchartNodeShape.FLAG_LEFT: "",
        }
        return prefixes.get(shape, "[")

    @staticmethod
    def get_suffix(shape: 'FlowchartNodeShape') -> str:
        """Get the suffix for the shape."""
        suffixes = {
            FlowchartNodeShape.RECTANGLE: "]",
            FlowchartNodeShape.ROUNDED: ")",
            FlowchartNodeShape.STADIUM: "])",
            FlowchartNodeShape.SUBROUTINE: "]]",
            FlowchartNodeShape.CYLINDER: ")]",
            FlowchartNodeShape.CIRCLE: "))",
            FlowchartNodeShape.HEXAGON: "}}",
            FlowchartNodeShape.PARALLELOGRAM: "/",
            FlowchartNodeShape.PARALLELOGRAM_ALT: "/]",
            FlowchartNodeShape.TRAPEZOID: "\\",
            FlowchartNodeShape.TRAPEZOID_ALT: "\\]",
            FlowchartNodeShape.DOUBLE_CIRCLE: ")))",
            FlowchartNodeShape.RHOMBUS: "}",
            FlowchartNodeShape.LEAN_RIGHT: "/]",
            FlowchartNodeShape.LEAN_LEFT: "\\]",
            FlowchartNodeShape.FLAG_RIGHT: "~",
            FlowchartNodeShape.FLAG_LEFT: "~",
        }
        return suffixes.get(shape, "]")


class FlowchartEdgeType(Enum):
    """Edge types (arrow styles)."""
    ARROW = "->"
    OPEN_ARROW = "-)"
    DOTTED_ARROW = "-->"
    DOTTED = "--"
    DOTTED_OPEN_ARROW = "--)"
    THICK_ARROW = "==>"
    DOUBLE_ARROW = "<->"
    DOTTED_DOUBLE_ARROW = "<-->"
    CROSS = "-x"
    DOTTED_CROSS = "--x"
    CIRCLE = "-o"
    DOTTED_CIRCLE = "--o"


class LinkStyle(Enum):
    """Link style for connections."""
    DEFAULT = 0
    NONE = 1
    CROSS = 2
    CIRCLE = 3


class LineType(Enum):
    """Line type for edges."""
    SOLID = 0
    DOTTED = 1
    THICK = 2


@dataclass
class FlowchartNode(StyledElement):
    """
    Represents a node in a flowchart.

    Examples:
        - Node with id: id1
        - Node with id and text: id1[This is the text]
        - Node with markdown: id1[**Bold** and *italic*]
    """
    shape: FlowchartNodeShape = FlowchartNodeShape.RECTANGLE
    icon: Optional[str] = None  # Font Awesome icon name
    fa_icon: Optional[str] = None  # Alternative Font Awesome icon format

    def render(self) -> str:
        """Render the node in Mermaid syntax."""
        text = self.get_label_text()
        prefix = FlowchartNodeShape.get_prefix(self.shape)
        suffix = FlowchartNodeShape.get_suffix(self.shape)

        # Handle icons
        if self.icon:
            text = f"<i class='fa fa-{self.icon}'></i> {text}"
        elif self.fa_icon:
            text = f"<i class='fa {self.fa_icon}'></i> {text}"

        return f"{self.id}{prefix}{text}{suffix}"


@dataclass
class EdgeLabel:
    """Represents a label on an edge."""
    text: str
    position: Optional[str] = None  # 'start', 'middle', 'end'

    def __str__(self) -> str:
        if self.position:
            return f"{self.position} : {self.text}"
        return self.text


@dataclass
class FlowchartEdge:
    """
    Represents an edge (connection) between nodes in a flowchart.

    Examples:
        - A-->B
        - A-->|text|B
        - A-->B-->C
    """
    start: str  # Start node ID
    end: str  # End node ID
    edge_type: FlowchartEdgeType = FlowchartEdgeType.ARROW
    label: Optional[str] = None
    label_text: Optional[str] = None  # Alternative label format
    length: Optional[int] = None  # Edge length for rendering

    def render(self) -> str:
        """Render the edge in Mermaid syntax."""
        arrow = self.edge_type.value

        if self.label is not None:
            return f"{self.start}{arrow}|{self.label}|{self.end}"
        elif self.label_text is not None:
            return f"{self.start}{arrow} : {self.label_text} {self.end}"
        else:
            return f"{self.start}{arrow}{self.end}"


@dataclass
class FlowchartSubgraph:
    """
    Represents a subgraph in a flowchart.

    Examples:
        subgraph title
          graph direction
          id1[Node 1]
          id2[Node 2]
          id1 --> id2
        end
    """
    id: str
    title: Optional[str] = None
    direction: Optional[FlowchartDirection] = None
    nodes: List[FlowchartNode] = field(default_factory=list)
    edges: List[FlowchartEdge] = field(default_factory=list)
    # Subgraphs can contain nested subgraphs
    subgraphs: List['FlowchartSubgraph'] = field(default_factory=list)
    style: Optional[Style] = None
    class_name: Optional[str] = None

    def add_node(self, node: FlowchartNode) -> None:
        """Add a node to this subgraph."""
        self.nodes.append(node)

    def add_edge(self, edge: FlowchartEdge) -> None:
        """Add an edge to this subgraph."""
        self.edges.append(edge)

    def add_subgraph(self, subgraph: 'FlowchartSubgraph') -> None:
        """Add a nested subgraph."""
        self.subgraphs.append(subgraph)

    def render(self, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the subgraph in Mermaid syntax."""
        lines = []
        lines.append(f"subgraph {self.id}")
        if self.title:
            lines.append(f"    direction {self.direction.value if self.direction else ''}")

        for node in self.nodes:
            lines.append(f"    {node.render()}")

        for edge in self.edges:
            lines.append(f"    {edge.render()}")

        for subgraph in self.subgraphs:
            subgraph_lines = subgraph.render(line_ending).split(line_ending.value)
            lines.extend(f"    {line}" for line in subgraph_lines)

        lines.append("end")
        return line_ending.value.join(lines)


@dataclass
class Interaction:
    """
    Represents a clickable interaction on a node.
    Format: click nodeId "tooltip" callback "url"
    """
    node_id: str
    callback: Optional[str] = None  # JavaScript callback function
    tooltip: Optional[str] = None
    url: Optional[str] = None
    target: Optional[str] = None  # For URLs: _blank, _self, etc.

    def render(self) -> str:
        """Render the interaction in Mermaid syntax."""
        parts = [f"click {self.node_id}"]
        if self.callback:
            parts.append(f'"{self.callback}"')
        if self.tooltip:
            parts.append(f'"{self.tooltip}"')
        if self.url:
            parts.append(f'"{self.url}"')
            if self.target:
                parts.append(f'"{self.target}"')
        return " ".join(parts)


@dataclass
class StyleClass:
    """
    Represents a style class assignment.
    Format: class nodeId1,nodeId2 className
    """
    node_ids: List[str]
    class_name: str

    def render(self) -> str:
        """Render the class assignment in Mermaid syntax."""
        nodes = ",".join(self.node_ids)
        return f"class {nodes} {self.class_name}"


@dataclass
class Comment:
    """Represents a comment in the diagram."""
    text: str

    def render(self) -> str:
        """Render the comment in Mermaid syntax."""
        return f"%% {self.text}"


class Flowchart(Diagram):
    """
    Represents a Mermaid flowchart diagram.

    Example:
        flowchart LR
            A[Start] --> B{Is it working?}
            B -->|Yes| C[Great!]
            B -->|No| D[Fix it]
            C --> E[End]
            D --> E
    """

    def __init__(
        self,
        direction: FlowchartDirection = FlowchartDirection.TOP_TO_BOTTOM,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a flowchart.

        Args:
            direction: The direction of the flowchart
            config: Diagram configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.direction = direction
        self.nodes: Dict[str, FlowchartNode] = {}
        self.edges: List[FlowchartEdge] = []
        self.subgraphs: List[FlowchartSubgraph] = []
        self.class_defs: List[ClassDef] = []
        self.style_classes: List[StyleClass] = []
        self.interactions: List[Interaction] = []
        self.comments: List[Comment] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.FLOWCHART

    def add_node(self, node: FlowchartNode) -> 'Flowchart':
        """
        Add a node to the flowchart.

        Args:
            node: The node to add

        Returns:
            Self for method chaining
        """
        self.nodes[node.id] = node
        return self

    def add_edge(self, edge: FlowchartEdge) -> 'Flowchart':
        """
        Add an edge to the flowchart.

        Args:
            edge: The edge to add

        Returns:
            Self for method chaining
        """
        self.edges.append(edge)
        return self

    def add_subgraph(self, subgraph: FlowchartSubgraph) -> 'Flowchart':
        """
        Add a subgraph to the flowchart.

        Args:
            subgraph: The subgraph to add

        Returns:
            Self for method chaining
        """
        self.subgraphs.append(subgraph)
        return self

    def add_class_def(self, class_def: ClassDef) -> 'Flowchart':
        """Add a class definition."""
        self.class_defs.append(class_def)
        return self

    def add_style_class(self, style_class: StyleClass) -> 'Flowchart':
        """Add a style class assignment."""
        self.style_classes.append(style_class)
        return self

    def add_interaction(self, interaction: Interaction) -> 'Flowchart':
        """Add a clickable interaction."""
        self.interactions.append(interaction)
        return self

    def add_comment(self, comment: Union[str, Comment]) -> 'Flowchart':
        """Add a comment to the flowchart."""
        if isinstance(comment, str):
            comment = Comment(text=comment)
        self.comments.append(comment)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the flowchart.

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
        lines.append(f"{self.diagram_type.value} {self.direction.value}")

        # Add comments
        for comment in self.comments:
            lines.append(f"    {comment.render()}")

        # Add nodes
        for node in self.nodes.values():
            lines.append(f"    {node.render()}")

        # Add edges
        for edge in self.edges:
            lines.append(f"    {edge.render()}")

        # Add subgraphs
        for subgraph in self.subgraphs:
            subgraph_lines = subgraph.render(self.line_ending).split(self.line_ending.value)
            lines.extend(f"    {line}" for line in subgraph_lines)

        # Add class definitions
        for class_def in self.class_defs:
            lines.append(f"    {class_def.to_mermaid()}")

        # Add style class assignments
        for style_class in self.style_classes:
            lines.append(f"    {style_class.render()}")

        # Add interactions
        for interaction in self.interactions:
            lines.append(f"    {interaction.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the flowchart."""
        return f"Flowchart(direction={self.direction}, nodes={len(self.nodes)}, edges={len(self.edges)})"

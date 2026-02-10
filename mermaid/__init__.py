"""
Mermaid Diagram Library

A Python library for representing diverse Mermaid diagram syntax objects.
These objects encapsulate the possible variations of Mermaid diagrams for
import by other Python scripts.
"""

from mermaid.base import (
    Diagram,
    DiagramConfig,
    Directive,
    Theme,
    Look,
    Layout,
    FontStyle,
    StrokeStyle,
    Color,
    LineEnding,
)

# Flowchart
from mermaid.flowchart import (
    Flowchart,
    FlowchartDirection,
    FlowchartNode,
    FlowchartNodeShape,
    FlowchartEdge,
    FlowchartEdgeType,
    FlowchartSubgraph,
)

# Sequence Diagram
from mermaid.sequence import (
    SequenceDiagram,
    Participant,
    ParticipantType,
    Message,
    MessageArrow,
    Activation,
    Note,
    LoopBlock,
    AltBlock,
    OptBlock,
    ParallelBlock,
    CriticalBlock,
    BreakBlock,
    RectBlock,
    BoxGroup,
)

# Class Diagram
from mermaid.class_diagram import (
    ClassDiagram,
    Class,
    Relationship,
    RelationshipType,
    Visibility,
    Method,
    Property,
    GenericParameter,
    Annotation,
    Namespace,
)

# State Diagram
from mermaid.state_diagram import (
    StateDiagram,
    State,
    StateType,
    Transition,
    ChoiceState,
    ForkJoinState,
    CompositeState,
    ConcurrentState,
)

# Entity Relationship Diagram
from mermaid.er_diagram import (
    ERDiagram,
    Entity,
    Attribute,
    AttributeType,
    ERRelationship,
    RelationshipCardinality,
    Identifiability,
)

# User Journey
from mermaid.user_journey import (
    UserJourney,
    Actor,
    Task,
    TaskSection,
)

# Gantt Chart
from mermaid.gantt import (
    GanttChart,
    GanttSection,
    GanttTask,
    GanttMilestone,
    DateRange,
    TaskStatus,
)

# Pie Chart
from mermaid.pie_chart import (
    PieChart,
    PieSlice,
    ShowData,
)

# Quadrant Chart
from mermaid.quadrant_chart import (
    QuadrantChart,
    Quadrant,
    Point,
)

# Requirement Diagram
from mermaid.requirement_diagram import (
    RequirementDiagram,
    Requirement,
    RequirementType,
    Element,
    ElementKind,
    RelationshipType as RequirementRelationshipType,
    RequirementRelationship,
)

# Git Graph
from mermaid.git_graph import (
    GitGraph,
    Commit,
    Branch,
    Checkout,
    Merge,
    CherryPick,
)

# C4 Context Diagram
from mermaid.c4_diagram import (
    C4Diagram,
    C4DiagramType,
    BoundaryType,
    Person,
    System,
    Container,
    ContainerBoundary,
    SystemBoundary,
    C4Relationship,
    DeploymentNode,
    C4Deployment,
)

# Mindmap
from mermaid.mindmap import (
    Mindmap,
    MindmapNode,
    Icon,
)

# Timeline
from mermaid.timeline import (
    Timeline,
    Event,
)

# ZenUML
from mermaid.zenuml import (
    ZenUMLDiagram,
    ZenParticipant,
    ZenMessage,
    ZenInteraction,
)

# Sankey Diagram
from mermaid.sankey import (
    SankeyDiagram,
    SankeyNode,
    SankeyLink,
)

# XY Chart
from mermaid.xy_chart import (
    XYChart,
    XYChartType,
    Axis,
    DataSeries,
)

# Block Diagram
from mermaid.block_diagram import (
    BlockDiagram,
    Block,
    BlockRelation,
)

# Packet Diagram
from mermaid.packet import (
    PacketDiagram,
    PacketField,
    PacketSize,
)

# Kanban
from mermaid.kanban import (
    KanbanDiagram,
    KanbanBoard,
    KanbanTask,
)

# Architecture Diagram
from mermaid.architecture import (
    ArchitectureDiagram,
    ServiceGroup,
    Service,
    Relation,
    DB,
    EdgeKind,
)

# Radar Chart
from mermaid.radar_chart import (
    RadarChart,
    Axis as RadarAxis,
)

# Treemap
from mermaid.treemap import (
    Treemap,
    TreemapNode,
)

__version__ = "0.1.0"
__all__ = [
    # Base
    "Diagram",
    "DiagramConfig",
    "Directive",
    "Theme",
    "Look",
    "Layout",
    "FontStyle",
    "StrokeStyle",
    "Color",
    "LineEnding",
    # Flowchart
    "Flowchart",
    "FlowchartDirection",
    "FlowchartNode",
    "FlowchartNodeShape",
    "FlowchartEdge",
    "FlowchartEdgeType",
    "FlowchartSubgraph",
    # Sequence Diagram
    "SequenceDiagram",
    "Participant",
    "ParticipantType",
    "Message",
    "MessageArrow",
    "Activation",
    "Note",
    "LoopBlock",
    "AltBlock",
    "OptBlock",
    "ParallelBlock",
    "CriticalBlock",
    "BreakBlock",
    "RectBlock",
    "BoxGroup",
    # Class Diagram
    "ClassDiagram",
    "Class",
    "Relationship",
    "RelationshipType",
    "Visibility",
    "Method",
    "Property",
    "GenericParameter",
    "Annotation",
    "Namespace",
    # State Diagram
    "StateDiagram",
    "State",
    "StateType",
    "Transition",
    "ChoiceState",
    "ForkJoinState",
    "CompositeState",
    "ConcurrentState",
    # Entity Relationship Diagram
    "ERDiagram",
    "Entity",
    "Attribute",
    "AttributeType",
    "ERRelationship",
    "RelationshipCardinality",
    "Identifiability",
    # User Journey
    "UserJourney",
    "Actor",
    "Task",
    "TaskSection",
    # Gantt Chart
    "GanttChart",
    "GanttSection",
    "GanttTask",
    "GanttMilestone",
    "DateRange",
    "TaskStatus",
    # Pie Chart
    "PieChart",
    "PieSlice",
    "ShowData",
    # Quadrant Chart
    "QuadrantChart",
    "Quadrant",
    "Point",
    # Requirement Diagram
    "RequirementDiagram",
    "Requirement",
    "RequirementType",
    "Element",
    "RequirementRelationship",
    "RequirementRelationshipType",
    # Git Graph
    "GitGraph",
    "Commit",
    "Branch",
    "Checkout",
    "Merge",
    "CherryPick",
    # C4 Diagram
    "C4Diagram",
    "C4DiagramType",
    "BoundaryType",
    "Person",
    "System",
    "Container",
    "ContainerBoundary",
    "SystemBoundary",
    "C4Relationship",
    "C4Deployment",
    "DeploymentNode",
    # Mindmap
    "Mindmap",
    "MindmapNode",
    "Icon",
    # Timeline
    "Timeline",
    "Event",
    # ZenUML
    "ZenUMLDiagram",
    "ZenParticipant",
    "ZenMessage",
    "ZenInteraction",
    # Sankey
    "SankeyDiagram",
    "SankeyNode",
    "SankeyLink",
    # XY Chart
    "XYChart",
    "XYChartType",
    "Axis",
    "DataSeries",
    # Block Diagram
    "BlockDiagram",
    "Block",
    "BlockRelation",
    # Packet
    "PacketDiagram",
    "PacketField",
    "PacketSize",
    # Kanban
    "KanbanDiagram",
    "KanbanBoard",
    "KanbanTask",
    # Architecture
    "ArchitectureDiagram",
    "ServiceGroup",
    "Service",
    "Relation",
    "DB",
    "EdgeKind",
    # Radar Chart
    "RadarChart",
    "RadarAxis",
    # Treemap
    "Treemap",
    "TreemapNode",
]

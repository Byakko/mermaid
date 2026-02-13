"""
C4 Context diagram classes for Mermaid.

This module contains classes for representing Mermaid C4 architecture diagrams.
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


class C4DiagramType(Enum):
    """Types of C4 diagrams."""
    CONTEXT = "C4_Context"
    CONTAINER = "C4_Container"
    COMPONENT = "C4_Component"
    DEPLOYMENT = "C4_Deployment"
    DYNAMIC = "C4_Dynamic"


class BoundaryType(Enum):
    """Types of boundaries in C4 diagrams."""
    SYSTEM_BOUNDARY = "System_Boundary"
    CONTAINER_BOUNDARY = "Container_Boundary"


@dataclass
class Person:
    """
    Represents a person (user/actor) in a C4 diagram.

    Example:
        Person(user, "User", "A user of the system")
    """
    id: str
    label: str
    description: Optional[str] = None

    def render(self) -> str:
        """Render the person in Mermaid syntax."""
        if self.description:
            return f'Person({self.id}, "{self.label}", "{self.description}")'
        return f'Person({self.id}, "{self.label}")'


@dataclass
class System:
    """
    Represents a system in a C4 diagram.

    Example:
        System(sys1, "System 1", "Description of system 1")
    """
    id: str
    label: str
    description: Optional[str] = None
    type: str = "System"  # System, System_Ext

    def render(self) -> str:
        """Render the system in Mermaid syntax."""
        if self.description:
            return f'{self.type}({self.id}, "{self.label}", "{self.description}")'
        return f'{self.type}({self.id}, "{self.label}")'


@dataclass
class Container:
    """
    Represents a container in a C4 diagram.

    Example:
        Container(cnt1, "Container 1", "Technology", "Description")
    """
    id: str
    label: str
    technology: Optional[str] = None
    description: Optional[str] = None

    def render(self) -> str:
        """Render the container in Mermaid syntax."""
        if self.technology and self.description:
            return f'Container({self.id}, "{self.label}", "{self.technology}", "{self.description}")'
        elif self.description:
            return f'Container({self.id}, "{self.label}", "{self.description}")'
        return f'Container({self.id}, "{self.label}")'


@dataclass
class ContainerBoundary:
    """
    Represents a container boundary in a C4 diagram.

    Example:
        Container_Boundary(b1, "Boundary 1") {
            Container(cnt1, "Container 1")
        }
    """
    id: str
    label: str
    containers: List[Container] = field(default_factory=list)

    def add_container(self, container: Container) -> 'ContainerBoundary':
        """Add a container to the boundary."""
        self.containers.append(container)
        return self

    def render(self, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the container boundary in Mermaid syntax."""
        lines = [f'Container_Boundary({self.id}, "{self.label}") {{']
        for container in self.containers:
            lines.append(f"    {container.render()}")
        lines.append("}")
        return line_ending.value.join(lines)


@dataclass
class SystemBoundary:
    """
    Represents a system boundary in a C4 diagram.

    Example:
        System_Boundary(b1, "Boundary 1") {
            System(sys1, "System 1")
        }
    """
    id: str
    label: str
    systems: List[System] = field(default_factory=list)
    containers: List[Container] = field(default_factory=list)
    container_boundaries: List[ContainerBoundary] = field(default_factory=list)

    def add_system(self, system: System) -> 'SystemBoundary':
        """Add a system to the boundary."""
        self.systems.append(system)
        return self

    def add_container(self, container: Container) -> 'SystemBoundary':
        """Add a container to the boundary."""
        self.containers.append(container)
        return self

    def add_container_boundary(self, boundary: ContainerBoundary) -> 'SystemBoundary':
        """Add a container boundary to the boundary."""
        self.container_boundaries.append(boundary)
        return self

    def render(self, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the system boundary in Mermaid syntax."""
        lines = [f'System_Boundary({self.id}, "{self.label}") {{']
        for system in self.systems:
            lines.append(f"    {system.render()}")
        for container in self.containers:
            lines.append(f"    {container.render()}")
        for boundary in self.container_boundaries:
            boundary_lines = boundary.render(line_ending).split(line_ending.value)
            lines.extend(f"    {line}" for line in boundary_lines)
        lines.append("}")
        return line_ending.value.join(lines)


@dataclass
class C4Relationship:
    """
    Represents a relationship between C4 elements.

    Example:
        Rel(user, sys, "Uses", "HTTPS")
    """
    from_id: str
    to_id: str
    label: str
    technology: Optional[str] = None
    description: Optional[str] = None

    def render(self) -> str:
        """Render the relationship in Mermaid syntax."""
        if self.technology:
            return f'Rel({self.from_id}, {self.to_id}, "{self.label}", "{self.technology}")'
        return f'Rel({self.from_id}, {self.to_id}, "{self.label}")'


@dataclass
class DeploymentNode:
    """
    Represents a deployment node in a C4 deployment diagram.

    Example:
        Deployment_Node(dep1, "Deployment Node", "Technology", "Description")
    """
    id: str
    label: str
    technology: Optional[str] = None
    description: Optional[str] = None
    instances: Optional[int] = None
    nodes: List['DeploymentNode'] = field(default_factory=list)
    containers: List[Container] = field(default_factory=list)

    def add_node(self, node: 'DeploymentNode') -> 'DeploymentNode':
        """Add a nested deployment node."""
        self.nodes.append(node)
        return self

    def add_container(self, container: Container) -> 'DeploymentNode':
        """Add a container to the deployment node."""
        self.containers.append(container)
        return self

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the deployment node in Mermaid syntax."""
        indent_str = "    " * indent
        parts = [self.id, f'"{self.label}"']
        if self.technology:
            parts.append(f'"{self.technology}"')
        if self.description:
            parts.append(f'"{self.description}"')
        if self.instances:
            parts.append(f"Instances:{self.instances}")

        lines = [f'{indent_str}Deployment_Node({", ".join(parts)}) {{']
        for container in self.containers:
            lines.append(f"    {indent_str}{container.render()}")
        for node in self.nodes:
            node_lines = node.render(indent + 1, line_ending).split(line_ending.value)
            lines.extend(node_lines)
        lines.append(f"{indent_str}}}")
        return line_ending.value.join(lines)


class C4Diagram(Diagram):
    """
    Represents a Mermaid C4 architecture diagram.

    Example:
        C4_Context
            title System Context Diagram
            Person(user, "User", "A user of the system")
            System(system, "System", "The system being described")
            Rel(user, system, "Uses", "HTTP")
    """

    def __init__(
        self,
        diagram_type: C4DiagramType = C4DiagramType.CONTEXT,
        title: str = "C4 Diagram",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a C4 diagram.

        Args:
            diagram_type: Type of C4 diagram
            title: Title of the diagram
            config: Diagram configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.diagram_type_enum = diagram_type
        self.title = title
        self.persons: List[Person] = []
        self.systems: List[System] = []
        self.containers: List[Container] = []
        self.system_boundaries: List[SystemBoundary] = []
        self.container_boundaries: List[ContainerBoundary] = []
        self.relationships: List[C4Relationship] = []
        self.deployment_nodes: List[DeploymentNode] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.C4

    def add_person(self, person: Person) -> 'C4Diagram':
        """Add a person to the diagram."""
        self.persons.append(person)
        return self

    def add_system(self, system: System) -> 'C4Diagram':
        """Add a system to the diagram."""
        self.systems.append(system)
        return self

    def add_container(self, container: Container) -> 'C4Diagram':
        """Add a container to the diagram."""
        self.containers.append(container)
        return self

    def add_system_boundary(self, boundary: SystemBoundary) -> 'C4Diagram':
        """Add a system boundary to the diagram."""
        self.system_boundaries.append(boundary)
        return self

    def add_container_boundary(self, boundary: ContainerBoundary) -> 'C4Diagram':
        """Add a container boundary to the diagram."""
        self.container_boundaries.append(boundary)
        return self

    def add_relationship(self, relationship: C4Relationship) -> 'C4Diagram':
        """Add a relationship to the diagram."""
        self.relationships.append(relationship)
        return self

    def add_deployment_node(self, node: DeploymentNode) -> 'C4Diagram':
        """Add a deployment node to the diagram."""
        self.deployment_nodes.append(node)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the C4 diagram.

        Returns:
            String containing valid Mermaid syntax
        """
        lines = []

        # Add config frontmatter if present
        if self.config.to_dict() or self.frontmatter:
            lines.append(self._render_config())

        # Add directive if present
        if self.directive:
            lines.append(str(self.directive))

        # Add diagram type declaration
        lines.append(self.diagram_type_enum.value)

        # Add title
        lines.append(f"    title {self.title}")

        # Add persons
        for person in self.persons:
            lines.append(f"    {person.render()}")

        # Add systems
        for system in self.systems:
            lines.append(f"    {system.render()}")

        # Add containers
        for container in self.containers:
            lines.append(f"    {container.render()}")

        # Add system boundaries
        for boundary in self.system_boundaries:
            boundary_lines = boundary.render(self.line_ending).split(self.line_ending.value)
            lines.extend(f"    {line}" for line in boundary_lines)

        # Add container boundaries
        for boundary in self.container_boundaries:
            boundary_lines = boundary.render(self.line_ending).split(self.line_ending.value)
            lines.extend(f"    {line}" for line in boundary_lines)

        # Add deployment nodes
        for node in self.deployment_nodes:
            node_lines = node.render(line_ending=self.line_ending).split(self.line_ending.value)
            lines.extend(f"    {line}" for line in node_lines)

        # Add relationships
        for rel in self.relationships:
            lines.append(f"    {rel.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the C4 diagram."""
        return f"C4Diagram(type={self.diagram_type_enum}, title='{self.title}')"


class C4Deployment(Diagram):
    """
    Represents a Mermaid C4 deployment diagram.
    """

    def __init__(
        self,
        title: str = "Deployment Diagram",
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """Initialize a C4 deployment diagram."""
        super().__init__(config, directive, line_ending=line_ending)
        self.title = title
        self.deployment_nodes: List[DeploymentNode] = []
        self.relationships: List[C4Relationship] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.C4

    def add_deployment_node(self, node: DeploymentNode) -> 'C4Deployment':
        """Add a deployment node to the diagram."""
        self.deployment_nodes.append(node)
        return self

    def add_relationship(self, relationship: C4Relationship) -> 'C4Deployment':
        """Add a relationship to the diagram."""
        self.relationships.append(relationship)
        return self

    def to_mermaid(self) -> str:
        """Generate Mermaid syntax for the C4 deployment diagram."""
        lines = []

        if self.config.to_dict() or self.frontmatter:
            lines.append(self._render_config())

        if self.directive:
            lines.append(str(self.directive))

        lines.append(C4DiagramType.DEPLOYMENT.value)
        lines.append(f"    title {self.title}")

        for node in self.deployment_nodes:
            node_lines = node.render(line_ending=self.line_ending).split(self.line_ending.value)
            lines.extend(f"    {line}" for line in node_lines)

        for rel in self.relationships:
            lines.append(f"    {rel.render()}")

        return self._join_lines(lines)

"""
Architecture diagram classes for Mermaid.

This module contains classes for representing Mermaid architecture diagrams.
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


class EdgeKind(Enum):
    """Types of edges in architecture diagrams."""
    SOLID = "->"
    DOTTED = "-."
    DASHED = "--"
    DOUBLE = "=>"


@dataclass
class DB:
    """
    Represents a database in an architecture diagram.

    Example:
        DB[(PostgreSQL)]
    """
    name: str
    alias: Optional[str] = None
    store: Optional[str] = None  # e.g., "Redis", "PostgreSQL"

    def render(self) -> str:
        """Render the database in Mermaid syntax."""
        if self.alias:
            return f'{self.alias}[({self.store or self.name})]'
        return f'DB[({self.name})]'


@dataclass
class Service:
    """
    Represents a service in an architecture diagram.

    Example:
        Service["API Gateway"]
    """
    name: str
    icon: Optional[str] = None  # e.g., "fa:fa-database"
    input_def: Optional[str] = None  # Input definition
    output_def: Optional[str] = None  # Output definition

    def render(self) -> str:
        """Render the service in Mermaid syntax."""
        if self.icon:
            return f'Service["{self.name}"<{self.icon}>]'
        return f'Service["{self.name}"]'


@dataclass
class ServiceGroup:
    """
    Represents a group of services in an architecture diagram.

    Example:
        Group["Backend Services"] {
            Service["API"]
            Service["Auth"]
        }
    """
    name: str
    services: List[Service] = field(default_factory=list)
    nested_groups: List['ServiceGroup'] = field(default_factory=list)
    databases: List[DB] = field(default_factory=list)

    def add_service(self, service: Service) -> 'ServiceGroup':
        """Add a service to the group."""
        self.services.append(service)
        return self

    def add_group(self, group: 'ServiceGroup') -> 'ServiceGroup':
        """Add a nested group."""
        self.nested_groups.append(group)
        return self

    def add_database(self, database: DB) -> 'ServiceGroup':
        """Add a database to the group."""
        self.databases.append(database)
        return self

    def render(self, indent: int = 0) -> str:
        """Render the service group in Mermaid syntax."""
        indent_str = "    " * indent
        lines = [f'{indent_str}Group["{self.name}" {{']

        for service in self.services:
            lines.append(f"{indent_str}    {service.render()}")

        for db in self.databases:
            lines.append(f"{indent_str}    {db.render()}")

        for group in self.nested_groups:
            lines.append(group.render(indent + 1))

        lines.append(f"{indent_str}}}")
        return self._join_lines(lines)


@dataclass
class Relation:
    """
    Represents a relation between services in an architecture diagram.

    Example:
        Service1 -> Service2
        Service1 -.-> Service3
    """
    from_service: str
    to_service: str
    edge_kind: EdgeKind = EdgeKind.SOLID
    label: Optional[str] = None

    def render(self) -> str:
        """Render the relation in Mermaid syntax."""
        edge = self.edge_kind.value
        result = f"{self.from_service} {edge} {self.to_service}"
        if self.label:
            result = f'{result} : "{self.label}"'
        return result


class ArchitectureDiagram(Diagram):
    """
    Represents a Mermaid architecture diagram.

    Example:
        architecture-beta
            service api["API Gateway"] {
                port: 8080
            }
            service db["Database"] {
                port: 5432
                technology: PostgreSQL
            }
            api -> db
    """

    def __init__(
        self,
        title: Optional[str] = None,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
    ):
        """
        Initialize an architecture diagram.

        Args:
            title: Optional title for the diagram
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive)
        self.title = title
        self.services: Dict[str, Service] = {}
        self.service_groups: List[ServiceGroup] = []
        self.databases: List[DB] = []
        self.relations: List[Relation] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.ARCHITECTURE

    def add_service(self, id: str, service: Service) -> 'ArchitectureDiagram':
        """Add a service to the diagram."""
        self.services[id] = service
        return self

    def add_service_group(self, group: ServiceGroup) -> 'ArchitectureDiagram':
        """Add a service group to the diagram."""
        self.service_groups.append(group)
        return self

    def add_database(self, database: DB) -> 'ArchitectureDiagram':
        """Add a database to the diagram."""
        self.databases.append(database)
        return self

    def add_relation(self, relation: Relation) -> 'ArchitectureDiagram':
        """Add a relation to the diagram."""
        self.relations.append(relation)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the architecture diagram.

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

        # Add services
        for id, service in self.services.items():
            lines.append(f"    {id} : {service.render()}")

        # Add service groups
        for group in self.service_groups:
            group_lines = group.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in group_lines)

        # Add databases
        for db in self.databases:
            lines.append(f"    {db.render()}")

        # Add relations
        for rel in self.relations:
            lines.append(f"    {rel.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the architecture diagram."""
        return f"ArchitectureDiagram(title='{self.title}', services={len(self.services)})"

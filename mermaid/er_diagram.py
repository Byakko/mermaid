"""
Entity Relationship diagram classes for Mermaid.

This module contains classes for representing Mermaid ER diagrams,
including entities, attributes, and relationships.
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
    Label,
    LineEnding
)


class AttributeType(Enum):
    """Types of attributes in ER diagrams."""
    PRIMARY_KEY = "PK"
    FOREIGN_KEY = "FK"
    NORMAL = ""


class Identifiability(Enum):
    """Identifiability for entities."""
    NORMAL = "normal"
    IDENTIFIABILITY = "identifiability"


class RelationshipCardinality(Enum):
    """Cardinality for relationships."""
    ONE_OR_MORE = "||"
    ZERO_OR_MORE = "|o"
    ONE_OR_NONE = "|}"
    EXACTLY_ONE = "||"
    ZERO_OR_ONE = "o|"
    MANY = "}{"


@dataclass
class Attribute:
    """
    Represents an attribute of an entity.

    Examples:
        - name: string
        - age: int PK
        - department_id: int FK
    """
    name: str
    type_hint: Optional[str] = None
    attribute_type: AttributeType = AttributeType.NORMAL
    comment: Optional[str] = None

    def render(self) -> str:
        """Render the attribute in Mermaid syntax."""
        parts = [self.name]
        if self.type_hint:
            parts.append(self.type_hint)
        if self.attribute_type != AttributeType.NORMAL:
            parts.append(self.attribute_type.value)
        if self.comment:
            parts.append(f'"{self.comment}"')
        return " ".join(parts)


@dataclass
class Entity:
    """
    Represents an entity in an ER diagram.

    Examples:
        Employee {
            string name
            int id PK
            string department_id FK
        }
    """
    name: str
    attributes: List[Attribute] = field(default_factory=list)
    alias: Optional[str] = None

    def add_attribute(self, attribute: Attribute) -> 'Entity':
        """Add an attribute to the entity."""
        self.attributes.append(attribute)
        return self

    def render(self) -> str:
        """Render the entity in Mermaid syntax."""
        lines = []
        if self.alias:
            lines.append(f"{self.alias}{{{self.name}")
        else:
            lines.append(f"{self.name}{{")

        for attr in self.attributes:
            lines.append(f"    {attr.render()}")

        lines.append("}")
        return self._join_lines(lines)


@dataclass
class ERRelationship:
    """
    Represents a relationship between entities.

    Examples:
        Employee ||--o{ Department : "works in"
        Customer }|--|{ Order : places
    """
    from_entity: str
    to_entity: str
    from_cardinality: str = "||"
    to_cardinality: str = "o|"
    label: Optional[str] = None
    relationship_label: Optional[str] = None

    def render(self) -> str:
        """Render the relationship in Mermaid syntax."""
        result = f"{self.from_entity} {self.from_cardinality}--{self.to_cardinality} {self.to_entity}"
        if self.label:
            result = f'{result} : "{self.label}"'
        elif self.relationship_label:
            result = f'{result} : "{self.relationship_label}"'
        return result


class ERDiagram(Diagram):
    """
    Represents a Mermaid Entity Relationship diagram.

    Example:
        erDiagram
            CUSTOMER ||--o{ ORDER : places
            CUSTOMER {
                string name
                string id PK
                string email
            }
            ORDER {
                int id PK
                string date
                customer_id FK
            }
    """

    def __init__(
        self,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize an ER diagram.

        Args:
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[ERRelationship] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.ER

    def add_entity(self, entity: Entity) -> 'ERDiagram':
        """Add an entity to the diagram."""
        self.entities[entity.name] = entity
        return self

    def add_relationship(self, relationship: ERRelationship) -> 'ERDiagram':
        """Add a relationship to the diagram."""
        self.relationships.append(relationship)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the ER diagram.

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

        # Add relationships first (Mermaid convention)
        for rel in self.relationships:
            lines.append(f"    {rel.render()}")

        # Add entities
        for entity in self.entities.values():
            entity_lines = entity.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in entity_lines)

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the ER diagram."""
        return f"ERDiagram(entities={len(self.entities)}, relationships={len(self.relationships)})"

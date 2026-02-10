"""
Requirement diagram classes for Mermaid.

This module contains classes for representing Mermaid requirement diagrams.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    LineEnding
)


class RequirementType(Enum):
    """Types of requirements."""
    FUNCTIONAL = "Functional Requirement"
    INTERFACE = "Interface Requirement"
    PERFORMANCE = "Performance Requirement"
    DESIGN = "Design Constraint"
    QUALITY = "Quality Constraint"
    PHYSICAL = "Physical Constraint"


class ElementKind(Enum):
    """Kinds of elements."""
    REQUIREMENT = "Requirement"
    ELEMENT = "Element"
    INTERFACE = "Interface"
    COMPONENT = "Component"


class RelationshipType(Enum):
    """Types of relationships in requirement diagrams."""
    CONTAINS = "contains"
    COPIES = "copies"
    DERIVES = "derives"
    SATISFIES = "satisfies"
    VERIFIES = "verifies"
    REFINES = "refines"
    TRACES = "traces"


@dataclass
class Requirement:
    """
    Represents a requirement in a requirement diagram.

    Example:
        requirement req1 {
            id: 1
            text: This is a requirement
            risk: high
            verifyMethod: test
        }
    """
    id: str
    text: Optional[str] = None
    risk: Optional[str] = None  # high, medium, low
    verifyMethod: Optional[str] = None  # analysis, demonstration, inspection, test
    requirement_type: RequirementType = RequirementType.FUNCTIONAL
    # For element type
    element_type: Optional[ElementKind] = None

    def render(self) -> str:
        """Render the requirement in Mermaid syntax."""
        if self.element_type:
            lines = [f"{self.element_type.value} {self.id} {{"]
        else:
            lines = [f"requirement {self.id} {{"]

        lines.append(f"    id: {self.id}")
        if self.text:
            lines.append(f"    text: {self.text}")
        if self.risk:
            lines.append(f"    risk: {self.risk}")
        if self.verifyMethod:
            lines.append(f"    verifyMethod: {self.verifyMethod}")
        if self.requirement_type != RequirementType.FUNCTIONAL:
            lines.append(f"    type: {self.requirement_type.value}")

        lines.append("}")
        return self._join_lines(lines)


@dataclass
class Element:
    """
    Represents an element in a requirement diagram.

    Example:
        element el1 {
            id: 1
            text: This is an element
        }
    """
    id: str
    text: Optional[str] = None
    type: Optional[str] = None

    def render(self) -> str:
        """Render the element in Mermaid syntax."""
        lines = [f"element {self.id} {{"]
        lines.append(f"    id: {self.id}")
        if self.text:
            lines.append(f"    text: {self.text}")
        if self.type:
            lines.append(f"    type: {self.type}")
        lines.append("}")
        return self._join_lines(lines)


@dataclass
class RequirementRelationship:
    """
    Represents a relationship between requirements or elements.

    Example:
        req1 - satisfies -> req2
        el1 - verifies -> req1
    """
    from_id: str
    to_id: str
    relationship_type: RelationshipType

    def render(self) -> str:
        """Render the relationship in Mermaid syntax."""
        return f"{self.from_id} - {self.relationship_type.value} -> {self.to_id}"


@dataclass
class RequirementRelationship:
    """Alias for RequirementRelationship for compatibility."""
    from_id: str
    to_id: str
    relationship_type: RelationshipType

    def render(self) -> str:
        """Render the relationship in Mermaid syntax."""
        return f"{self.from_id} - {self.relationship_type.value} -> {self.to_id}"


class RequirementDiagram(Diagram):
    """
    Represents a Mermaid requirement diagram.

    Example:
        requirementDiagram
            requirement req1 {
                id: 1
                text: This is a requirement
                risk: high
                verifyMethod: test
            }
            element el1 {
                id: 1
                text: This is an element
            }
            el1 - satisfies -> req1
    """

    def __init__(
        self,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a requirement diagram.

        Args:
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.requirements: Dict[str, Requirement] = {}
        self.elements: Dict[str, Element] = {}
        self.relationships: List[RequirementRelationship] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.REQUIREMENT

    def add_requirement(self, requirement: Requirement) -> 'RequirementDiagram':
        """Add a requirement to the diagram."""
        self.requirements[requirement.id] = requirement
        return self

    def add_element(self, element: Element) -> 'RequirementDiagram':
        """Add an element to the diagram."""
        self.elements[element.id] = element
        return self

    def add_relationship(self, relationship: RequirementRelationship) -> 'RequirementDiagram':
        """Add a relationship to the diagram."""
        self.relationships.append(relationship)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the requirement diagram.

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

        # Add requirements
        for req in self.requirements.values():
            req_lines = req.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in req_lines)

        # Add elements
        for el in self.elements.values():
            el_lines = el.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in el_lines)

        # Add relationships
        for rel in self.relationships:
            lines.append(f"    {rel.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the requirement diagram."""
        return f"RequirementDiagram(requirements={len(self.requirements)}, elements={len(self.elements)})"

"""
Class diagram classes for Mermaid.

This module contains classes for representing Mermaid class diagrams,
including classes, relationships, members, and annotations.
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


class Visibility(Enum):
    """Visibility modifiers for class members."""
    PUBLIC = "+"
    PRIVATE = "-"
    PROTECTED = "#"
    PACKAGE = "~"
    INTERNAL = ""  # No symbol


class RelationshipType(Enum):
    """Types of relationships between classes."""
    INHERITANCE = "inheritance"  # <|-- or --|>
    COMPOSITION = "composition"  # *-- or --*
    AGGREGATION = "aggregation"  # o-- or --o
    ASSOCIATION = "association"  # --> or -->
    DEPENDENCY = "dependency"  # ..> or <..
    REALIZATION = "realization"  # ..|> or <|..
    LINK = "link"  # :::
    LOLLIPPOP = "lollipop"  # ()-- or --()


class RelationshipCardinality(Enum):
    """Cardinality for relationships."""
    ZERO_OR_ONE = "0..1"
    EXACTLY_ONE = "1"
    ZERO_OR_MANY = "0..*"
    ONE_OR_MANY = "1..*"
    MANY = "*"
    N = "n"
    OPTIONAL = "?"


class MemberType(Enum):
    """Types of class members."""
    METHOD = "method"
    PROPERTY = "property"


@dataclass
class TypedElement:
    """Base class for typed elements (methods, properties)."""
    name: str
    type_hint: Optional[str] = None
    visibility: Visibility = Visibility.PUBLIC
    is_static: bool = False
    is_abstract: bool = False


@dataclass
class Property(TypedElement):
    """
    Represents a property/attribute of a class.

    Examples:
        - name: string
        - +age: int
        - -private: bool
    """

    def render(self) -> str:
        """Render the property in Mermaid syntax."""
        parts = []
        if self.visibility != Visibility.INTERNAL:
            parts.append(self.visibility.value)
        if self.is_static:
            parts.append("{static}")
        if self.is_abstract:
            parts.append("{abstract}")
        parts.append(self.name)
        if self.type_hint:
            parts.append(f"{self.type_hint}")
        return " ".join(parts)


@dataclass
class Method(TypedElement):
    """
    Represents a method of a class.

    Examples:
        - getName()
        - +setName(name: string)
        - +calculate(x: int, y: int): float
    """
    parameters: List[tuple[str, Optional[str]]] = field(default_factory=list)  # (name, type)
    return_type: Optional[str] = None

    def render(self) -> str:
        """Render the method in Mermaid syntax."""
        parts = []
        if self.visibility != Visibility.INTERNAL:
            parts.append(self.visibility.value)
        if self.is_static:
            parts.append("{static}")
        if self.is_abstract:
            parts.append("{abstract}")

        # Build parameter string
        params = ", ".join(
            f"{name}" + (f": {type_hint}" if type_hint else "")
            for name, type_hint in self.parameters
        )

        method_signature = f"{self.name}({params})"

        if self.return_type:
            method_signature += f" {self.return_type}"

        parts.append(method_signature)
        return " ".join(parts)


@dataclass
class GenericParameter:
    """Represents a generic type parameter."""
    name: str
    constraints: Optional[List[str]] = None  # e.g., ["T", "U"] for T extends U


@dataclass
class Annotation:
    """
    Represents a class annotation.

    Examples:
        <<interface>>
        <<abstract>>
        <<service>>
        <<enumeration>>
    """
    name: str

    def render(self) -> str:
        """Render the annotation."""
        return f"<<{self.name}>>"


@dataclass
class Class:
    """
    Represents a class in a class diagram.

    Examples:
        class Animal{
            +age: int
            +name: string
            +speak()
        }
    """
    name: str
    properties: List[Property] = field(default_factory=list)
    methods: List[Method] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    generic_parameters: List[GenericParameter] = field(default_factory=list)
    style: Optional[Style] = None
    note: Optional[str] = None

    def add_property(self, property: Property) -> 'Class':
        """Add a property to the class."""
        self.properties.append(property)
        return self

    def add_method(self, method: Method) -> 'Class':
        """Add a method to the class."""
        self.methods.append(method)
        return self

    def add_annotation(self, annotation: Annotation) -> 'Class':
        """Add an annotation to the class."""
        self.annotations.append(annotation)
        return self

    def render(self) -> str:
        """Render the class in Mermaid syntax."""
        lines = []
        annotations_str = " ".join(a.render() for a in self.annotations)
        if annotations_str:
            lines.append(f"class {self.name}{annotations_str}{{")
        else:
            lines.append(f"class {name}{{")

        for prop in self.properties:
            lines.append(f"    {prop.render()}")

        for method in self.methods:
            lines.append(f"    {method.render()}")

        lines.append("}")
        return self._join_lines(lines)


@dataclass
class Relationship:
    """
    Represents a relationship between two classes.

    Examples:
        Animal <|-- Duck
        Student *-- Course
        Car o-- Engine
    """
    from_class: str
    to_class: str
    relationship_type: RelationshipType = RelationshipType.ASSOCIATION
    label: Optional[str] = None
    from_cardinality: Optional[RelationshipCardinality] = None
    to_cardinality: Optional[RelationshipCardinality] = None
    namespace_from: Optional[str] = None  # e.g., "namespace.Class"
    namespace_to: Optional[str] = None

    def render(self) -> str:
        """Render the relationship in Mermaid syntax."""
        # Build the arrow notation
        rel_map = {
            RelationshipType.INHERITANCE: "<|--",
            RelationshipType.COMPOSITION: "*--",
            RelationshipType.AGGREGATION: "o--",
            RelationshipType.ASSOCIATION: "-->",
            RelationshipType.DEPENDENCY: "..>",
            RelationshipType.REALIZATION: "..|>",
            RelationshipType.LINK: ":::",
            RelationshipType.LOLLIPPOP: "()--",
        }

        arrow = rel_map.get(self.relationship_type, "-->")

        # Add cardinality if present
        from_card = self.from_cardinality.value if self.from_cardinality else ""
        to_card = self.to_cardinality.value if self.to_cardinality else ""

        # Build the relationship string
        if from_card:
            result = f'"{from_card}" {self.from_class} {arrow}'
        else:
            result = f"{self.from_class} {arrow}"

        if to_card:
            result = f'{result} "{to_card}"'
        else:
            result = f"{result} "

        result = f"{result} {self.to_class}"

        # Add label if present
        if self.label:
            result = f"{result} : {self.label}"

        return result


@dataclass
class Namespace:
    """
    Represents a namespace for organizing classes.

    Example:
        namespace "My Namespace" {
            class Class1
            class Class2
        }
    """
    name: str
    classes: List[Class] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    nested_namespaces: List['Namespace'] = field(default_factory=list)

    def add_class(self, cls: Class) -> 'Namespace':
        """Add a class to the namespace."""
        self.classes.append(cls)
        return self

    def add_relationship(self, relationship: Relationship) -> 'Namespace':
        """Add a relationship to the namespace."""
        self.relationships.append(relationship)
        return self

    def render(self) -> str:
        """Render the namespace in Mermaid syntax."""
        lines = []
        lines.append(f"namespace \"{self.name}\" {{")

        for cls in self.classes:
            lines.append(f"    {cls.render()}")

        for rel in self.relationships:
            lines.append(f"    {rel.render()}")

        for ns in self.nested_namespaces:
            ns_lines = ns.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in ns_lines)

        lines.append("}")
        return self._join_lines(lines)


class ClassDiagram(Diagram):
    """
    Represents a Mermaid class diagram.

    Example:
        classDiagram
            Animal <|-- Duck
            Animal <|-- Fish
            Animal <|-- Zebra
    """

    def __init__(
        self,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a class diagram.

        Args:
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.classes: Dict[str, Class] = {}
        self.relationships: List[Relationship] = []
        self.namespaces: List[Namespace] = []
        self.notes: List[str] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.CLASS

    def add_class(self, cls: Class) -> 'ClassDiagram':
        """Add a class to the diagram."""
        self.classes[cls.name] = cls
        return self

    def add_relationship(self, relationship: Relationship) -> 'ClassDiagram':
        """Add a relationship to the diagram."""
        self.relationships.append(relationship)
        return self

    def add_namespace(self, namespace: Namespace) -> 'ClassDiagram':
        """Add a namespace to the diagram."""
        self.namespaces.append(namespace)
        return self

    def add_note(self, note: str, for_class: Optional[str] = None) -> 'ClassDiagram':
        """Add a note to the diagram."""
        if for_class:
            self.notes.append(f"note for {for_class} \"{note}\"")
        else:
            self.notes.append(f"note \"{note}\"")
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the class diagram.

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
        lines.append(self.diagram_type.value)

        # Add notes
        for note in self.notes:
            lines.append(f"    {note}")

        # Add namespaces
        for ns in self.namespaces:
            ns_lines = ns.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in ns_lines)

        # Add classes
        for cls in self.classes.values():
            cls_lines = cls.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in cls_lines)

        # Add relationships
        for rel in self.relationships:
            lines.append(f"    {rel.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the class diagram."""
        return f"ClassDiagram(classes={len(self.classes)}, relationships={len(self.relationships)})"

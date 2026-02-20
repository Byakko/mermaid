"""
Sequence diagram classes for Mermaid.

This module contains classes for representing Mermaid sequence diagrams,
including participants, messages, activations, notes, and control structures.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod

from mermaid.base import (
    Diagram,
    DiagramType,
    DiagramConfig,
    Directive,
    Style,
    Color,
    Link,
    LineEnding,
)


class ParticipantType(Enum):
    """Types of participants in sequence diagrams."""
    PARTICIPANT = "participant"
    ACTOR = "actor"
    BOUNDARY = "boundary"
    CONTROL = "control"
    ENTITY = "entity"
    DATABASE = "database"
    COLLECTIONS = "collections"
    QUEUE = "queue"


class MessageArrow(Enum):
    """Arrow types for messages."""
    SOLID_NO_ARROW = "->"
    DOTTED_NO_ARROW = "-->"
    SOLID_ARROW = "->>"
    DOTTED_ARROW = "-->>"
    SOLID_BI_ARROW = "<<->>"
    DOTTED_BI_ARROW = "<<-->>"
    SOLID_CROSS = "-x"
    DOTTED_CROSS = "--x"
    SOLID_OPEN_ARROW = "-)"
    DOTTED_OPEN_ARROW = "--)"


class NotePosition(Enum):
    """Position of notes relative to participants."""
    RIGHT_OF = "right of"
    LEFT_OF = "left of"
    OVER = "over"


@dataclass
class Participant:
    """
    Represents a participant/actor in a sequence diagram.

    Examples:
        participant Alice
        actor Bob as "Bob the Builder"
        participant P as "Person"
    """
    id: str
    label: Optional[str] = None
    type: ParticipantType = ParticipantType.PARTICIPANT
    order: Optional[int] = None  # Explicit order of appearance
    raw_alias: Optional[str] = None  # Preserves original alias text for round-tripping
    raw_line: Optional[str] = None  # Preserves full original line (e.g. @{} syntax)

    def render(self) -> str:
        """Render the participant in Mermaid syntax."""
        if self.raw_line is not None:
            return self.raw_line
        type_str = self.type.value
        if self.raw_alias is not None:
            return f"{type_str} {self.id} as {self.raw_alias}"
        if self.label:
            return f"{type_str} {self.id} as {self.label}"
        return f"{type_str} {self.id}"

    def __repr__(self) -> str:
        return f"Participant(id={self.id}, type={self.type})"


@dataclass
class ActorLink:
    """Represents a link menu for an actor."""
    actor_id: str
    label: str
    url: str

    def render(self) -> str:
        """Render the actor link in Mermaid syntax."""
        return f'link {self.actor_id}: "{self.label}" @{self.url}'


@dataclass
class ActorLinks:
    """Advanced JSON-formatted links for an actor."""
    actor_id: str
    links: List[Dict[str, str]]

    def render(self) -> str:
        """Render the actor links in Mermaid syntax."""
        import json
        return f"links {self.actor_id}: {json.dumps(self.links)}"


@dataclass
class Message:
    """
    Represents a message between participants.

    Examples:
        Alice->>Bob: Hello
        Alice-->Bob: Hello
        Alice->>Bob: Hello\nBob-->>Alice: Hi
    """
    from_participant: str
    to_participant: str
    text: str
    arrow: MessageArrow = MessageArrow.SOLID_ARROW
    activate_sender: bool = False
    deactivate_sender: bool = False
    activate_receiver: bool = False
    deactivate_receiver: bool = False

    def render(self) -> str:
        """Render the message in Mermaid syntax."""
        arrow = self.arrow.value

        # Handle activation/deactivation shortcuts
        # +/- goes between arrow and receiver: Alice->>+Bob: Hello
        receiver_prefix = ""
        if self.activate_receiver:
            receiver_prefix = "+"
        elif self.deactivate_receiver:
            receiver_prefix = "-"
        if self.activate_sender:
            arrow = "+" + arrow
        elif self.deactivate_sender:
            arrow = "-" + arrow

        # Handle line breaks in message text
        text = self.text.replace("\n", "\\n")

        return f"{self.from_participant}{arrow}{receiver_prefix}{self.to_participant}: {text}"


@dataclass
class Activation:
    """
    Represents an activation/deactivation of a participant.

    Examples:
        activate Alice
        deactivate Bob
    """
    participant: str
    is_activate: bool = True

    def render(self) -> str:
        """Render the activation in Mermaid syntax."""
        keyword = "activate" if self.is_activate else "deactivate"
        return f"{keyword} {self.participant}"


@dataclass
class Note:
    """
    Represents a note in the sequence diagram.

    Examples:
        Note right of Alice: Hello
        Note over Alice, Bob: Conversation
    """
    position: NotePosition
    participants: Union[str, List[str]]
    text: str
    color: Optional[Color] = None
    raw_participants: Optional[str] = None  # Preserves original participant text

    def render(self) -> str:
        """Render the note in Mermaid syntax."""
        if self.raw_participants is not None:
            participants_str = self.raw_participants
        else:
            participants_str = (
                ", ".join(self.participants)
                if isinstance(self.participants, list)
                else self.participants
            )
        text = self.text.replace("\n", "\\n")

        color_prefix = ""
        color_suffix = ""
        if self.color:
            color_prefix = f"{self.color} "
            color_suffix = " "

        return f"Note {color_prefix}{self.position.value} {participants_str}{color_suffix}: {text}"


@dataclass
class BoxGroup:
    """
    Represents a box group for grouping participants.

    Examples:
        box Aqua Group Description
            participant A
            participant B
        end
    """
    color: Optional[Color] = None
    description: Optional[str] = None
    participants: List[Participant] = field(default_factory=list)
    raw_header: Optional[str] = None  # Preserves original header for round-tripping

    def add_participant(self, participant: Participant) -> None:
        """Add a participant to the box."""
        self.participants.append(participant)

    def render(self, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the box group in Mermaid syntax."""
        lines = []
        if self.raw_header is not None:
            lines.append(self.raw_header)
        elif self.description and self.color:
            lines.append(f"box {self.color} {self.description}")
        elif self.description:
            lines.append(f"box {self.description}")
        elif self.color:
            lines.append(f"box {self.color}")
        else:
            lines.append("box")

        for participant in self.participants:
            lines.append(f"    {participant.render()}")

        lines.append("end")
        return line_ending.value.join(lines)


@dataclass
class LoopBlock:
    """
    Represents a loop block in the sequence diagram.

    Example:
        loop Loop text
            Alice->>Bob: Hello
        end
    """
    loop_text: str
    messages: List[Message] = field(default_factory=list)
    nested_blocks: List['SequenceBlock'] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to the loop."""
        self.messages.append(message)

    def add_nested_block(self, block: 'SequenceBlock') -> None:
        """Add a nested block."""
        self.nested_blocks.append(block)

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the loop block in Mermaid syntax."""
        indent_str = "    " * indent
        lines = [f"{indent_str}loop {self.loop_text}"]

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        for block in self.nested_blocks:
            lines.append(block.render(indent + 1, line_ending))

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


@dataclass
class AltOption:
    """Represents an option in an alt block."""
    description: str
    messages: List[Message] = field(default_factory=list)
    nested_blocks: List['SequenceBlock'] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to this option."""
        self.messages.append(message)

    def add_nested_block(self, block: 'SequenceBlock') -> None:
        """Add a nested block."""
        self.nested_blocks.append(block)

    def render(self, indent: int = 0, is_else: bool = False, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the option in Mermaid syntax."""
        indent_str = "    " * indent
        keyword = "else" if is_else else "alt"
        lines = [f"{indent_str}{keyword} {self.description}"]

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        for block in self.nested_blocks:
            lines.append(block.render(indent + 1, line_ending))

        return line_ending.value.join(lines)


@dataclass
class AltBlock:
    """
    Represents an alt/else block in the sequence diagram.

    Example:
        alt Describing text
            Alice->>Bob: Hello
        else
            Alice->>Charlie: Hi
        end
    """
    options: List[AltOption] = field(default_factory=list)

    def add_option(self, option: AltOption, is_else: bool = False) -> None:
        """Add an option to the alt block."""
        self.options.append((option, is_else))

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the alt block in Mermaid syntax."""
        indent_str = "    " * indent
        lines = []

        for i, (option, is_else) in enumerate(self.options):
            option_lines = option.render(indent, is_else, line_ending).split(line_ending.value)
            lines.extend(option_lines)

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


@dataclass
class OptBlock:
    """
    Represents an optional block (opt) in the sequence diagram.

    Example:
        opt Describing text
            Alice->>Bob: Hello
        end
    """
    description: str
    messages: List[Message] = field(default_factory=list)
    nested_blocks: List['SequenceBlock'] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to the opt block."""
        self.messages.append(message)

    def add_nested_block(self, block: 'SequenceBlock') -> None:
        """Add a nested block."""
        self.nested_blocks.append(block)

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the opt block in Mermaid syntax."""
        indent_str = "    " * indent
        lines = [f"{indent_str}opt {self.description}"]

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        for block in self.nested_blocks:
            lines.append(block.render(indent + 1, line_ending))

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


@dataclass
class ParallelBlock:
    """
    Represents a parallel block in the sequence diagram.

    Example:
        par [Action 1]
            Alice->>Bob: Hello
        and [Action 2]
            Alice->>Charlie: Hi
        end
    """
    actions: List[AltOption] = field(default_factory=list)  # Reusing AltOption structure

    def add_action(self, description: str, messages: List[Message]) -> None:
        """Add a parallel action."""
        option = AltOption(description=description, messages=messages)
        self.actions.append(option)

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the parallel block in Mermaid syntax."""
        indent_str = "    " * indent
        lines = []

        for i, action in enumerate(self.actions):
            keyword = "and" if i > 0 else "par"
            lines.append(f"{indent_str}{keyword} {action.description}")

            for message in action.messages:
                lines.append(f"{indent_str}    {message.render()}")

            for block in action.nested_blocks:
                lines.append(block.render(indent + 1, line_ending))

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


@dataclass
class CriticalOption:
    """Represents an option in a critical block."""
    description: str
    messages: List[Message] = field(default_factory=list)


@dataclass
class CriticalBlock:
    """
    Represents a critical block in the sequence diagram.

    Example:
        critical [Action that must be performed]
            Alice->>Bob: Hello
        option [Circumstance A]
            Alice->>Charlie: Hi
        end
    """
    action: str
    messages: List[Message] = field(default_factory=list)
    options: List[CriticalOption] = field(default_factory=list)

    def add_option(self, description: str, messages: List[Message]) -> None:
        """Add an option to the critical block."""
        self.options.append(CriticalOption(description=description, messages=messages))

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the critical block in Mermaid syntax."""
        indent_str = "    " * indent
        lines = [f"{indent_str}critical {self.action}"]

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        for option in self.options:
            lines.append(f"{indent_str}option {option.description}")
            for message in option.messages:
                lines.append(f"{indent_str}    {message.render()}")

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


@dataclass
class BreakBlock:
    """
    Represents a break block in the sequence diagram.

    Example:
        break [something happened]
            Alice->>Bob: Sorry
        end
    """
    description: str
    messages: List[Message] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to the break block."""
        self.messages.append(message)

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the break block in Mermaid syntax."""
        indent_str = "    " * indent
        lines = [f"{indent_str}break {self.description}"]

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


@dataclass
class RectBlock:
    """
    Represents a background highlighting rect block.

    Example:
        rect rgb(0, 255, 0)
            Alice->>Bob: Hello
        end
    """
    color: Color
    messages: List[Message] = field(default_factory=list)
    raw_header: Optional[str] = None  # Preserves original header for round-tripping

    def add_message(self, message: Message) -> None:
        """Add a message to the rect block."""
        self.messages.append(message)

    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the rect block in Mermaid syntax."""
        indent_str = "    " * indent
        header = self.raw_header if self.raw_header is not None else f"rect {self.color}"
        lines = [f"{indent_str}{header}"]

        for message in self.messages:
            lines.append(f"{indent_str}    {message.render()}")

        lines.append(f"{indent_str}end")
        return line_ending.value.join(lines)


# Base class for sequence blocks
class SequenceBlock(ABC):
    """Abstract base class for all sequence blocks."""

    @abstractmethod
    def render(self, indent: int = 0, line_ending: LineEnding = LineEnding.LF) -> str:
        """Render the block in Mermaid syntax."""
        pass


@dataclass
class CreateDirective:
    """
    Represents a participant creation directive.

    Example:
        create participant B
        A --> B: Hello
    """
    participant_id: str
    participant_type: ParticipantType = ParticipantType.PARTICIPANT
    label: Optional[str] = None

    def render(self) -> str:
        """Render the create directive."""
        type_str = self.participant_type.value
        if self.label:
            return f"create {type_str} {self.participant_id} as \"{self.label}\""
        return f"create {type_str} {self.participant_id}"


@dataclass
class DestroyDirective:
    """
    Represents a participant destruction directive.

    Example:
        A --> B: Goodbye
        destroy B
    """
    participant_id: str

    def render(self) -> str:
        """Render the destroy directive."""
        return f"destroy {self.participant_id}"


@dataclass
class SequenceConfig:
    """
    Configuration options for sequence diagrams.

    Based on mermaid.sequenceConfig options.
    """
    mirror_actors: bool = False
    bottom_margin_adj: float = 1.0
    actor_font_size: int = 14
    actor_font_family: str = '"Open Sans", sans-serif'
    actor_font_weight: str = '"Open Sans", sans-serif'
    note_font_size: int = 14
    note_font_family: str = '"trebuchet ms", verdana, arial'
    note_font_weight: str = '"trebuchet ms", verdana, arial'
    note_align: str = "center"
    message_font_size: int = 16
    message_font_family: str = '"trebuchet ms", verdana, arial'
    message_font_weight: str = '"trebuchet ms", verdana, arial'
    show_sequence_numbers: bool = False
    diagram_margin_x: int = 50
    diagram_margin_y: int = 10
    box_text_margin: int = 5
    note_margin: int = 10
    message_margin: int = 35

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary format."""
        return {
            "mirrorActors": self.mirror_actors,
            "bottomMarginAdj": self.bottom_margin_adj,
            "actorFontSize": self.actor_font_size,
            "actorFontFamily": self.actor_font_family,
            "actorFontWeight": self.actor_font_weight,
            "noteFontSize": self.note_font_size,
            "noteFontFamily": self.note_font_family,
            "noteFontWeight": self.note_font_weight,
            "noteAlign": self.note_align,
            "messageFontSize": self.message_font_size,
            "messageFontFamily": self.message_font_family,
            "messageFontWeight": self.message_font_weight,
            "sequence": {"showSequenceNumbers": self.show_sequence_numbers},
            "diagramMarginX": self.diagram_margin_x,
            "diagramMarginY": self.diagram_margin_y,
            "boxTextMargin": self.box_text_margin,
            "noteMargin": self.note_margin,
            "messageMargin": self.message_margin,
        }


class SequenceDiagram(Diagram):
    """
    Represents a Mermaid sequence diagram.

    Example:
        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>Bob: Hello Bob, how are you?
            Bob-->>Alice: I am good thanks!
    """

    def __init__(
        self,
        config: Optional[DiagramConfig] = None,
        sequence_config: Optional[SequenceConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF,
    ):
        """
        Initialize a sequence diagram.

        Args:
            config: General diagram configuration
            sequence_config: Sequence-specific configuration
            directive: Directive for pre-render configuration
            line_ending: Line ending style to use in output
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.sequence_config = sequence_config or SequenceConfig()
        self.participants: Dict[str, Participant] = {}
        self.messages: List[Message] = []
        self.activations: List[Activation] = []
        self.notes: List[Note] = []
        self.blocks: List[SequenceBlock] = []
        self.box_groups: List[BoxGroup] = []
        self.actor_links: List[Union[ActorLink, ActorLinks]] = []
        self.autonumber: bool = False
        self.items: List[Any] = []  # Ordered items for round-trip rendering

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.SEQUENCE

    def add_participant(self, participant: Participant) -> 'SequenceDiagram':
        """Add a participant to the diagram."""
        self.participants[participant.id] = participant
        return self

    def add_message(self, message: Message) -> 'SequenceDiagram':
        """Add a message to the diagram."""
        self.messages.append(message)
        return self

    def add_activation(self, activation: Activation) -> 'SequenceDiagram':
        """Add an activation/deactivation."""
        self.activations.append(activation)
        return self

    def add_note(self, note: Note) -> 'SequenceDiagram':
        """Add a note to the diagram."""
        self.notes.append(note)
        return self

    def add_block(self, block: SequenceBlock) -> 'SequenceDiagram':
        """Add a control block (loop, alt, etc.)."""
        self.blocks.append(block)
        return self

    def add_box_group(self, box: BoxGroup) -> 'SequenceDiagram':
        """Add a box group."""
        self.box_groups.append(box)
        return self

    def add_actor_link(self, link: Union[ActorLink, ActorLinks]) -> 'SequenceDiagram':
        """Add an actor link/menu."""
        self.actor_links.append(link)
        return self

    def set_autonumber(self, enabled: bool = True) -> 'SequenceDiagram':
        """Enable or disable automatic message numbering."""
        self.autonumber = enabled
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the sequence diagram.

        Returns:
            String containing valid Mermaid syntax
        """
        lines = []

        # Add config frontmatter if present
        all_config = self.config.to_dict()
        seq_config = self.sequence_config.to_dict()
        if seq_config:
            all_config.update(seq_config)
        if all_config:
            lines.append("---")
            lines.append("config:")
            for key, value in all_config.items():
                if isinstance(value, dict):
                    lines.append(f"  {key}:")
                    for k, v in value.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {key}: {value}")
            lines.append("---")

        # Add directive if present
        if self.directive:
            lines.append(str(self.directive))

        # Add autonumber directive
        if self.autonumber:
            lines.append("autonumber")

        # Add diagram type declaration
        lines.append(self.diagram_type.value)

        # Add participants
        for participant in self.participants.values():
            if participant.order is not None:
                # Order is implicit by position in Mermaid syntax
                lines.append(f"    {participant.render()}")
            else:
                lines.append(f"    {participant.render()}")

        # Add box groups
        for box in self.box_groups:
            box_lines = box.render(self.line_ending).split(self.line_ending.value)
            lines.extend(f"    {line}" for line in box_lines)

        # Add activations/deactivations
        for activation in self.activations:
            lines.append(f"    {activation.render()}")

        # Add messages
        for message in self.messages:
            lines.append(f"    {message.render()}")

        # Add notes
        for note in self.notes:
            lines.append(f"    {note.render()}")

        # Add blocks
        for block in self.blocks:
            lines.append(block.render(line_ending=self.line_ending))

        # Add actor links
        for link in self.actor_links:
            lines.append(f"    {link.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the sequence diagram."""
        return f"SequenceDiagram(participants={len(self.participants)}, messages={len(self.messages)})"

"""
State diagram classes for Mermaid.

This module contains classes for representing Mermaid state diagrams,
including states, transitions, and composite states.
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


class StateType(Enum):
    """Types of states in a state diagram."""
    SIMPLE = "simple"
    START = "start"
    END = "end"
    FORK = "fork"
    JOIN = "join"
    CHOICE = "choice"
    COMPOSITE = "composite"
    CONCURRENT = "concurrent"


class TransitionType(Enum):
    """Types of transitions."""
    DIRECT = "->"
    DOTTED = "-->"
    NOTE = ":"


@dataclass
class State:
    """
    Represents a state in a state diagram.

    Examples:
        [*] --> Still
        Still --> [*]
        Still --> Moving
    """
    id: str
    label: Optional[str] = None
    description: Optional[str] = None
    type: StateType = StateType.SIMPLE
    note: Optional[str] = None
    # For choice states
    is_choice: bool = False
    # For fork/join
    is_fork: bool = False
    is_join: bool = False

    def render(self) -> str:
        """Render the state in Mermaid syntax."""
        if self.type == StateType.START:
            return "[*]"
        elif self.type == StateType.END:
            return "[*]"
        elif self.is_choice:
            return f"<<choice>> {self.id}"
        elif self.is_fork:
            return f"<<fork>> {self.id}"
        elif self.is_join:
            return f"<<join>> {self.id}"
        elif self.label:
            return f"{self.id} : {self.label}"
        else:
            return self.id


@dataclass
class Transition:
    """
    Represents a transition between states.

    Examples:
        [*] --> Still
        Still --> Moving : start moving
        Moving --> Still : stop moving
    """
    from_state: str
    to_state: str
    label: Optional[str] = None
    transition_type: TransitionType = TransitionType.DIRECT

    def render(self) -> str:
        """Render the transition in Mermaid syntax."""
        arrow = self.transition_type.value
        if self.label:
            return f"{self.from_state} {arrow} {self.to_state} : {self.label}"
        return f"{self.from_state} {arrow} {self.to_state}"


@dataclass
class ChoiceState(State):
    """
    Represents a choice state (decision point).

    Example:
        state if_state <<choice>>
        [*] --> if_state
        if_state --> else_state : [condition is false]
    """
    def __init__(self, id: str, label: Optional[str] = None):
        super().__init__(id=id, label=label, is_choice=True, line_ending=line_ending)


@dataclass
class ForkJoinState(State):
    """
    Represents a fork or join state for concurrent execution.

    Example:
        state fork_state <<fork>>
        state join_state <<join>>
        [*] --> fork_state
        fork_state --> State1
        fork_state --> State2
        State1 --> join_state
        State2 --> join_state
        join_state --> [*]
    """
    is_fork: bool = True
    is_join: bool = False


@dataclass
class StateAction:
    """
    Represents an action within a state.

    Example:
        enter / initialize()
        exit / cleanup()
    """
    trigger: str  # 'enter', 'exit', or custom
    action: str

    def render(self) -> str:
        """Render the state action."""
        return f"{self.trigger} / {self.action}"


@dataclass
class CompositeState(State):
    """
    Represents a composite state (contains nested states).

    Example:
        state Active {
            [*] --> Running
            Running --> Paused
            Paused --> Running
        }
    """
    states: List[State] = field(default_factory=list)
    transitions: List[Transition] = field(default_factory=list)
    actions: List[StateAction] = field(default_factory=list)

    def add_state(self, state: State) -> 'CompositeState':
        """Add a nested state."""
        self.states.append(state)
        return self

    def add_transition(self, transition: Transition) -> 'CompositeState':
        """Add a nested transition."""
        self.transitions.append(transition)
        return self

    def add_action(self, action: StateAction) -> 'CompositeState':
        """Add an action to the state."""
        self.actions.append(action)
        return self

    def render(self) -> str:
        """Render the composite state in Mermaid syntax."""
        lines = []
        lines.append(f"state {self.id} {{")

        for action in self.actions:
            lines.append(f"    {action.render()}")

        for state in self.states:
            lines.append(f"    {state.render()}")

        for transition in self.transitions:
            lines.append(f"    {transition.render()}")

        lines.append("}")
        return self._join_lines(lines)


@dataclass
class ConcurrentState(State):
    """
    Represents a concurrent state (parallel regions).

    Example:
        state Active {
            [*] --> Running
            Running --> Waiting
        }
        state Completed {
            [*] --> Success
            Success --> [*]
        }
    """
    regions: List[CompositeState] = field(default_factory=list)

    def add_region(self, region: CompositeState) -> 'ConcurrentState':
        """Add a parallel region."""
        self.regions.append(region)
        return self

    def render(self) -> str:
        """Render the concurrent state in Mermaid syntax."""
        lines = []
        for region in self.regions:
            region_lines = region.render().split(self.line_ending.value)
            lines.extend(region_lines)
        return self._join_lines(lines)


@dataclass
class StateNote:
    """
    Represents a note attached to a state.

    Example:
        note right of Waiting : Waiting for user input
    """
    state_id: str
    position: str = "right of"  # 'right of', 'left of'
    text: str = ""

    def render(self) -> str:
        """Render the state note."""
        return f"note {self.position} {self.state_id} : {self.text}"


class StateDiagram(Diagram):
    """
    Represents a Mermaid state diagram.

    Example:
        stateDiagram-v2
            [*] --> Still
            Still --> [*]
            Still --> Moving
            Moving --> Still
            Moving --> Crash
            Crash --> [*]
    """

    def __init__(
        self,
        use_v2_syntax: bool = True,
        config: Optional[DiagramConfig] = None,
        directive: Optional[Directive] = None,
        line_ending: LineEnding = LineEnding.LF
    ):
        """
        Initialize a state diagram.

        Args:
            use_v2_syntax: Whether to use stateDiagram-v2 syntax
            config: Diagram configuration
            directive: Directive for pre-render configuration
        """
        super().__init__(config, directive, line_ending=line_ending)
        self.use_v2_syntax = use_v2_syntax
        self.states: Dict[str, State] = {}
        self.transitions: List[Transition] = []
        self.notes: List[StateNote] = []
        self.composite_states: List[CompositeState] = []

    @property
    def diagram_type(self) -> DiagramType:
        """Return the diagram type."""
        return DiagramType.STATE

    def add_state(self, state: State) -> 'StateDiagram':
        """Add a state to the diagram."""
        self.states[state.id] = state
        return self

    def add_transition(self, transition: Transition) -> 'StateDiagram':
        """Add a transition to the diagram."""
        self.transitions.append(transition)
        return self

    def add_note(self, note: StateNote) -> 'StateDiagram':
        """Add a note to the diagram."""
        self.notes.append(note)
        return self

    def add_composite_state(self, state: CompositeState) -> 'StateDiagram':
        """Add a composite state to the diagram."""
        self.composite_states.append(state)
        return self

    def to_mermaid(self) -> str:
        """
        Generate Mermaid syntax for the state diagram.

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
        diagram_key = "stateDiagram-v2" if self.use_v2_syntax else "stateDiagram"
        lines.append(diagram_key)

        # Add simple states
        for state in self.states.values():
            if state.type == StateType.SIMPLE and not state.is_choice:
                lines.append(f"    {state.render()}")

        # Add choice states
        for state in self.states.values():
            if state.is_choice:
                lines.append(f"    state {state.id} <<choice>>")

        # Add fork/join states
        for state in self.states.values():
            if state.is_fork:
                lines.append(f"    state {state.id} <<fork>>")
            elif state.is_join:
                lines.append(f"    state {state.id} <<join>>")

        # Add composite states
        for state in self.composite_states:
            state_lines = state.render().split(self.line_ending.value)
            lines.extend(f"    {line}" for line in state_lines)

        # Add transitions
        for transition in self.transitions:
            lines.append(f"    {transition.render()}")

        # Add notes
        for note in self.notes:
            lines.append(f"    {note.render()}")

        return self._join_lines(lines)

    def __repr__(self) -> str:
        """String representation of the state diagram."""
        return f"StateDiagram(states={len(self.states)}, transitions={len(self.transitions)})"

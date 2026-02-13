#!/usr/bin/env python3
"""
Sanitize Mermaid Diagram Script

This script takes Mermaid diagram text and produces a Python object representation,
then converts it back to text with consistent formatting and configurable line endings.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, List

from mermaid.base import LineEnding
from mermaid import (
    Flowchart,
    FlowchartDirection,
    FlowchartNode,
    FlowchartNodeShape,
    FlowchartEdge,
    FlowchartEdgeType,
    SequenceDiagram,
    Participant,
    ParticipantType,
    Message,
    MessageArrow,
    Note,
    LoopBlock,
    AltBlock,
    OptBlock,
    ParallelBlock,
    ClassDiagram,
    Class,
    Relationship,
    RelationshipType,
    Visibility,
    Method,
    Property,
    StateDiagram,
    State,
    StateType,
    Transition,
    ERDiagram,
    Entity,
    Attribute,
    AttributeType,
    ERRelationship,
    RelationshipCardinality,
    UserJourney,
    Actor,
    Task,
    TaskSection,
    GanttChart,
    GanttSection,
    GanttTask,
    DateRange,
    TaskStatus,
    PieChart,
    PieSlice,
    Mindmap,
    MindmapNode,
    GitGraph,
    Commit,
    Branch,
    QuadrantChart,
    Point,
    Timeline,
    Event,
    C4Diagram,
    C4DiagramType,
    Person,
    System,
    Container,
    SystemBoundary,
    C4Relationship,
)


# =============================================================================
# Command Line Interface
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Sanitize Mermaid diagrams by converting to Python objects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (type/paste Mermaid text)
  python sanitize_mermaid.py

  # Pipe from stdin
  cat diagram.mmd | python sanitize_mermaid.py

  # Read from file, overwrite same file
  python sanitize_mermaid.py diagram.mmd

  # Read from input file, write to output file
  python sanitize_mermaid.py input.mmd output.mmd

  # Specify Windows-style line endings
  python sanitize_mermaid.py --line-ending crlf diagram.mmd
        """
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        help="Input Mermaid file to read"
    )

    parser.add_argument(
        "output_file",
        nargs="?",
        help="Output file to write (default: same as input)"
    )

    parser.add_argument(
        "--line-ending",
        "-l",
        choices=["lf", "crlf"],
        default="lf",
        help="Line ending style: 'lf' for Unix/Linux/macOS, 'crlf' for Windows (default: lf)"
    )

    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip overwrite confirmation prompts"
    )

    return parser.parse_args()


def parse_line_ending(value: str) -> LineEnding:
    """
    Convert line ending string to LineEnding enum.

    Args:
        value: Line ending string ("lf" or "crlf")

    Returns:
        LineEnding enum value
    """
    return LineEnding.CRLF if value.lower() == "crlf" else LineEnding.LF


# =============================================================================
# File Operations
# =============================================================================

def check_file_exists(file_path: Path) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return file_path.exists() and file_path.is_file()


def prompt_overwrite(file_path: Path) -> bool:
    """
    Prompt user to confirm file overwrite.

    Args:
        file_path: File that would be overwritten

    Returns:
        True if user confirms overwrite, False otherwise
    """
    response = input(f"File '{file_path}' exists. Overwrite? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def read_input_file(file_path: Path) -> str:
    """
    Read content from a file.

    Args:
        file_path: Path to file to read

    Returns:
        File contents as string
    """
    return file_path.read_text(encoding="utf-8")


def write_output_file(file_path: Path, content: str) -> None:
    """
    Write content to a file.

    Args:
        file_path: Path to file to write
        content: Content to write
    """
    # Use newline='' to preserve exact line endings without platform translation
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def read_interactive_input() -> str:
    """
    Read Mermaid text from interactive user input.

    User enters text line by line. Press Enter on an empty line
    (Ctrl+D on Unix, Ctrl+Z on Windows) to finish input.

    Returns:
        The entered text as a string
    """
    print("Enter Mermaid diagram text (press Ctrl+Z then Enter on Windows,")
    print("or Ctrl+D on Unix/Linux, or enter an empty line to finish):")
    print("-" * 40)

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    print("-" * 40)
    return "\n".join(lines)


def get_input_text(args: argparse.Namespace) -> Optional[str]:
    """
    Retrieve input text based on command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        Input text, or None if user cancelled
    """
    # Mode 1: No file specified - read from piped stdin or interactive input
    if args.input_file is None:
        if not sys.stdin.isatty():
            return sys.stdin.read()
        return read_interactive_input()

    input_path = Path(args.input_file)

    # Check input file exists for modes 2 and 3
    if not check_file_exists(input_path):
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        return None

    # Mode 2: One file specified - will overwrite same file
    if args.output_file is None:
        if not args.yes:
            if not prompt_overwrite(input_path):
                print("Cancelled.")
                return None
        return read_input_file(input_path)

    # Mode 3: Two files specified - read from first, write to second
    output_path = Path(args.output_file)

    if check_file_exists(output_path):
        if not args.yes:
            if not prompt_overwrite(output_path):
                print("Cancelled.")
                return None

    return read_input_file(input_path)


# =============================================================================
# Output Writing
# =============================================================================

def write_output(text: str, args: argparse.Namespace) -> None:
    """
    Write output to file or stdout based on command line arguments.

    Args:
        text: Output text
        args: Parsed command line arguments
    """
    # Mode 1: No file specified - print to stdout
    if args.input_file is None:
        print("\n" + "=" * 40)
        print("Sanitized Output:")
        print("=" * 40)
        print(text)
        return

    # Mode 2: One file specified - overwrite the same file
    if args.output_file is None:
        output_path = Path(args.input_file)
        write_output_file(output_path, text)
        print(f"Updated file: {output_path}")
        return

    # Mode 3: Two files specified - write to second file
    output_path = Path(args.output_file)
    write_output_file(output_path, text)
    print(f"Wrote to file: {output_path}")


# =============================================================================
# Diagram Type Detection
# =============================================================================

def detect_diagram_type(text: str) -> str:
    """
    Detect the type of Mermaid diagram from the text.

    Args:
        text: Mermaid diagram text

    Returns:
        Diagram type identifier (e.g., "flowchart", "sequence", "class")
    """
    # Strip frontmatter before detection
    _, text = extract_frontmatter(text)

    # Normalize text for detection
    lines = [line.strip() for line in text.strip().split("\n")]
    first_content_line = next((line for line in lines if line and not line.startswith("%%")), "")

    # Pattern matching for diagram type declarations
    patterns = {
        "flowchart": r"^(flowchart|graph)\s*(TD|TB|BT|RL|LR)?\s*$",
        "sequence": r"^sequenceDiagram\s*$",
        "class": r"^classDiagram\s*$",
        "state": r"^stateDiagram(-v2)?\s*$",
        "er": r"^erDiagram\s*$",
        "journey": r"^journey\s*$",
        "gantt": r"^gantt\s*$",
        "pie": r"^pie\s+.*$",
        "mindmap": r"^mindmap\s*$",
        "git": r"^gitGraph\s*$",
        "quadrant": r"^quadrantChart\s*$",
        "timeline": r"^timeline\s*$",
        "c4": r"^C4(Context|Container|Deployment|Component)\s*$",
        "zenuml": r"^zenuml\s*$",
        "sankey": r"^sankey-beta\s*$",
        "xychart": r"^xychart-beta\s*$",
        "block": r"^block(beta)?\s*:\s*.*$",
        "packet": r"^packet\s*$",
        "kanban": r"^kanban\s*$",
        "architecture": r"^architecture\s*$",
        "radar": r"^radar\s*$",
        "treemap": r"^treemap\s*$",
        "requirement": r"^requirementDiagram\s*$",
    }

    first_line_lower = first_content_line.lower()

    for diagram_type, pattern in patterns.items():
        if re.match(pattern, first_line_lower, re.IGNORECASE):
            return diagram_type

    # Default: try to detect from content
    if "-->" in text or "==>" in text:
        return "flowchart"
    if "->>" in text or "-->>" in text:
        return "sequence"

    return "unknown"


# =============================================================================
# Frontmatter Extraction
# =============================================================================

def extract_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from the beginning of Mermaid text.

    Frontmatter is delimited by ``---`` lines at the start of the text.
    Only simple ``key: value`` pairs are supported (no nested YAML).

    Args:
        text: Raw Mermaid diagram text

    Returns:
        Tuple of (frontmatter dict, remaining text with frontmatter stripped)
    """
    lines = text.split("\n")

    # Find the first non-empty line
    first_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_idx = i
            break

    if first_idx is None or lines[first_idx].strip() != "---":
        return {}, text

    # Look for closing ---
    closing_idx = None
    for i in range(first_idx + 1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break

    if closing_idx is None:
        return {}, text

    # Parse simple key: value pairs
    frontmatter: Dict[str, Any] = {}
    for line in lines[first_idx + 1 : closing_idx]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r'^(\w[\w-]*)\s*:\s*(.+)$', stripped)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            # Simple type coercion
            if value.lower() in ("true", "false"):
                frontmatter[key] = value.lower() == "true"
            elif re.match(r'^-?\d+$', value):
                frontmatter[key] = int(value)
            elif re.match(r'^-?\d+\.\d+$', value):
                frontmatter[key] = float(value)
            else:
                frontmatter[key] = value

    remaining = "\n".join(lines[:first_idx] + lines[closing_idx + 1 :])
    return frontmatter, remaining


# =============================================================================
# Text Preprocessing
# =============================================================================

def preprocess_text(text: str) -> List[str]:
    """
    Preprocess Mermaid text before parsing.

    Args:
        text: Raw Mermaid text

    Returns:
        List of non-empty, non-comment lines
    """
    lines = []
    for line in text.split("\n"):
        # Remove leading/trailing whitespace
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip comment lines
        if line.startswith("%%"):
            continue
        lines.append(line)
    return lines


def parse_indent(line: str) -> int:
    """
    Parse the indentation level of a line (number of leading spaces).

    Args:
        line: Line to parse

    Returns:
        Number of leading spaces (divided by 2 for Mermaid levels)
    """
    return len(line) - len(line.lstrip())


# =============================================================================
# Flowchart Parser
# =============================================================================

def parse_flowchart_direction(line: str) -> FlowchartDirection:
    """Parse flowchart direction from declaration line."""
    line_upper = line.upper()
    if "TD" in line_upper or "TB" in line_upper:
        return FlowchartDirection.TOP_DOWN
    elif "BT" in line_upper:
        return FlowchartDirection.BOTTOM_UP
    elif "RL" in line_upper:
        return FlowchartDirection.RIGHT_LEFT
    elif "LR" in line_upper:
        return FlowchartDirection.LEFT_RIGHT
    return FlowchartDirection.TOP_DOWN


def parse_flowchart_node_shape(text: str) -> tuple:
    """Parse node id, label, and shape from node definition."""
    text = text.strip()

    # Patterns for different shapes
    patterns = [
        # [text] - square/rectangle
        (r'\[([^\]]+)\]', FlowchartNodeShape.STADIUM),
        # ([text]) - rounded
        (r'\(([^)]+)\)', FlowchartNodeShape.ROUNDED),
        # ([text]) - circle
        (r'\(\(([^)]+)\)\)', FlowchartNodeShape.CIRCLE),
        # >text] - flag
        (r'>([^\]]+)\]', FlowchartNodeShape.FLAG),
        # {[text]} - hexagon
        (r'\{([^\}]+)\}', FlowchartNodeShape.HEXAGON),
        # {{text}} - parallelogram
        (r'\{\{([^\}]+)\}\}', FlowchartNodeShape.PARALLELOGRAM),
        # [/text] - parallelogram alternate
        (r'\[\/([^\/]+)\/\]', FlowchartNodeShape.PARALLELOGRAM),
        # [\text] - trapezoid
        (r'\[\\([^\\\]+)\\\]', FlowchartNodeShape.TRAPEZOID),
        # ((text)) - double circle
        (r'\(\(\(([^)]+)\)\)\)', FlowchartNodeShape.DOUBLE_CIRCLE),
    ]

    for pattern, shape in patterns:
        match = re.search(pattern, text)
        if match:
            label = match.group(1)
            # Extract ID from before the pattern
            id_match = re.match(r'^(\w+)', text[:match.start()].strip())
            node_id = id_match.group(1) if id_match else label.replace(" ", "_")
            return node_id, label, shape

    # Simple ID format
    return text, text, FlowchartNodeShape.ROUNDED


def parse_flowchart_edge_type(text: str) -> tuple:
    """Parse edge type and return from_node, to_node, type, label."""
    # Edge patterns: -->, ==>, --o, -.->, etc.
    arrow_patterns = [
        (r'([^<\s]+)\s*-->\s*([^:\s]+)(?::\s*(.+))?', FlowchartEdgeType.ARROW),
        (r'([^<\s]+)\s*==>\s*([^:\s]+)(?::\s*(.+))?', FlowchartEdgeType.BOLD_ARROW),
        (r'([^<\s]+)\s*--\.>\s*([^:\s]+)(?::\s*(.+))?', FlowchartEdgeType.DOTTED_ARROW),
        (r'([^<\s]+)\s*-\.\s*([^:\s]+)(?::\s*(.+))?', FlowchartEdgeType.DOTTED),
        (r'([^<\s]+)\s*===\s*([^:\s]+)(?::\s*(.+))?', FlowchartEdgeType.BOLD),
    ]

    for pattern, edge_type in arrow_patterns:
        match = re.match(pattern, text.strip())
        if match:
            from_node = match.group(1)
            to_node = match.group(2)
            label = match.group(3) if match.group(3) else None
            return from_node, to_node, edge_type, label

    return None, None, None, None


def parse_flowchart(text: str, line_ending: LineEnding) -> Flowchart:
    """Parse a flowchart diagram."""
    lines = preprocess_text(text)

    direction = FlowchartDirection.TOP_DOWN
    nodes = {}
    edges = []
    subgraphs = []
    current_subgraph = None

    for line in lines:
        # Check for diagram declaration
        if re.match(r'^(flowchart|graph)', line.lower()):
            direction = parse_flowchart_direction(line)
            continue

        # Check for subgraph
        if line.lower().startswith("subgraph "):
            subgraph_name = line[9:].strip()
            current_subgraph = {"name": subgraph_name, "nodes": [], "edges": []}
            continue

        if line.lower() == "end" and current_subgraph:
            subgraphs.append(current_subgraph)
            current_subgraph = None
            continue

        # Try to parse as edge
        from_node, to_node, edge_type, label = parse_flowchart_edge_type(line)
        if from_node:
            edges.append(FlowchartEdge(from_node, to_node, edge_type, label))
            continue

        # Try to parse as node
        node_id, node_label, node_shape = parse_flowchart_node_shape(line)
        nodes[node_id] = FlowchartNode(node_id, node_label, node_shape)

    flowchart = Flowchart(direction=direction, line_ending=line_ending)
    for node in nodes.values():
        flowchart.add_node(node)
    for edge in edges:
        flowchart.add_edge(edge)

    return flowchart


# =============================================================================
# Sequence Diagram Parser
# =============================================================================

def parse_sequence(text: str, line_ending: LineEnding) -> SequenceDiagram:
    """Parse a sequence diagram."""
    lines = preprocess_text(text)

    diagram = SequenceDiagram(line_ending=line_ending)
    participants = {}  # alias -> Participant mapping

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("sequencediagram"):
            continue

        # Parse participant declaration
        participant_match = re.match(
            r'participant\s+(")?(\w+)\1?\s+as\s+(\w+)',
            line, re.IGNORECASE
        )
        if participant_match:
            participant_type = ParticipantType.PARTICIPANT
            actor_match = re.match(r'actor\s+"?(\w+)"?\s+as\s+(\w+)', line, re.IGNORECASE)
            if actor_match:
                participant_type = ParticipantType.ACTOR
            name = participant_match.group(2)
            alias = participant_match.group(3)
            participant = Participant(id=alias, label=name, participant_type=participant_type)
            participants[alias] = participant
            diagram.add_participant(participant)
            continue

        # Simple participant: Participant as Alias
        simple_participant = re.match(r'(\w+)\s+as\s+(\w+)', line, re.IGNORECASE)
        if simple_participant:
            name = simple_participant.group(1)
            alias = simple_participant.group(2)
            participant = Participant(id=alias, label=name)
            participants[alias] = participant
            diagram.add_participant(participant)
            continue

        # Parse message: from -> to : label
        message_match = re.match(r'(\w+)\s*([-]+>|[-][>])\s*(\w+)\s*:\s*(.+)', line)
        if message_match:
            from_part = message_match.group(1)
            arrow_str = message_match.group(2)
            to_part = message_match.group(3)
            label = message_match.group(4)

            # Determine arrow type
            if "-->>" in arrow_str:
                arrow = MessageArrow.DASHED_OPEN
            elif "->>" in arrow_str:
                arrow = MessageArrow.OPEN
            elif "-->" in arrow_str:
                arrow = MessageArrow.DASHED
            else:
                arrow = MessageArrow.SOLID

            message = Message(from_participant=from_part, to_participant=to_part,
                            message=label, arrow=arrow)
            diagram.add_message(message)
            continue

        # Parse note
        note_match = re.match(r'note\s+(right|left)\s+of\s+(\w+)\s*:\s*(.+)', line, re.IGNORECASE)
        if note_match:
            position = note_match.group(1)
            participant = note_match.group(2)
            note_text = note_match.group(3)
            note = Note(participant_id=participant, position=position, text=note_text)
            diagram.add_note(note)
            continue

        # Parse loop/alt/opt blocks
        block_match = re.match(r'(loop|alt|opt|par|critical|break|rect)\s*(.+)?', line, re.IGNORECASE)
        if block_match:
            block_type = block_match.group(1).lower()
            block_text = block_match.group(2) or ""

            if block_type == "loop":
                block = LoopBlock(loop_text=block_text, line_ending=line_ending)
            elif block_type == "alt":
                block = AltBlock()
                block.add_condition(block_text)
            elif block_type == "opt":
                block = OptBlock(description=block_text)
            else:
                # Default to opt for other block types
                block = OptBlock(description=block_text)

            diagram.add_block(block)
            continue

        # End of block
        if line.lower() in ("end", "else"):
            continue

    return diagram


# =============================================================================
# Class Diagram Parser
# =============================================================================

def parse_class_diagram(text: str, line_ending: LineEnding) -> ClassDiagram:
    """Parse a class diagram."""
    lines = preprocess_text(text)

    diagram = ClassDiagram(line_ending=line_ending)
    classes = {}
    relationships = []

    current_class = None

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("classdiagram"):
            continue

        # Check for class definition
        class_match = re.match(r'class\s+(\w+)(?:\s*<\[(.+)\]>)?', line)
        if class_match:
            class_name = class_match.group(1)
            stereotype = class_match.group(2) if class_match.group(2) else None
            current_class = Class(id=class_name, label=class_name, stereotype=stereotype)
            classes[class_name] = current_class
            diagram.add_class(current_class)
            continue

        # End of class definition
        if line == "}" and current_class:
            current_class = None
            continue

        # Parse method inside class
        if current_class:
            method_match = re.match(r'\s*([+#~-])?\s*(\w+)\s*\(([^)]*)\)(?:\s*\*\s*(\d+))?', line)
            if method_match:
                visibility_str = method_match.group(1) or "+"
                visibility = {
                    "+": Visibility.PUBLIC,
                    "-": Visibility.PRIVATE,
                    "#": Visibility.PROTECTED,
                    "~": Visibility.PACKAGE,
                }.get(visibility_str, Visibility.PUBLIC)

                method_name = method_match.group(2)
                parameters = method_match.group(3) or ""
                cardinality = method_match.group(4)

                method = Method(
                    name=method_name,
                    visibility=visibility,
                    parameters=[p.strip() for p in parameters.split(",") if p.strip()],
                    return_type="void"
                )
                current_class.add_method(method)
                continue

            # Parse property
            prop_match = re.match(r'\s*([+#~-])?\s*(\w+)\s*(?::\s*(\w+))?(?:\s*\*\s*(\d+))?', line)
            if prop_match:
                visibility_str = prop_match.group(1) or "+"
                visibility = {
                    "+": Visibility.PUBLIC,
                    "-": Visibility.PRIVATE,
                    "#": Visibility.PROTECTED,
                    "~": Visibility.PACKAGE,
                }.get(visibility_str, Visibility.PUBLIC)

                prop_name = prop_match.group(2)
                prop_type = prop_match.group(3) or "Any"

                property_obj = Property(
                    name=prop_name,
                    data_type=prop_type,
                    visibility=visibility
                )
                current_class.add_property(property_obj)
                continue

        # Parse relationship: ClassA --|> ClassB
        rel_match = re.match(r'(\w+)\s+([<|*o+]+--|(--[>|*o+]+)\s+(\w+)(?::\s*(.+))?', line)
        if rel_match:
            from_class = rel_match.group(1)
            to_class = rel_match.group(3)
            label = rel_match.group(4) if rel_match.group(4) else ""

            # Determine relationship type
            rel_symbol = rel_match.group(2)
            if "|>" in rel_symbol or "<|" in rel_symbol:
                rel_type = RelationshipType.INHERITANCE
            elif "*--" in rel_symbol or "--*" in rel_symbol:
                rel_type = RelationshipType.COMPOSITION
            elif "o--" in rel_symbol or "--o" in rel_symbol:
                rel_type = RelationshipType.AGGREGATION
            elif "-->" in rel_symbol:
                rel_type = RelationshipType.DEPENDENCY
            else:
                rel_type = RelationshipType.ASSOCIATION

            relationship = Relationship(from_class, to_class, rel_type, label)
            relationships.append(relationship)
            diagram.add_relationship(relationship)
            continue

    return diagram


# =============================================================================
# State Diagram Parser
# =============================================================================

def parse_state_diagram(text: str, line_ending: LineEnding) -> StateDiagram:
    """Parse a state diagram."""
    lines = preprocess_text(text)

    use_v2 = "stateDiagram-v2" in text
    diagram = StateDiagram(use_v2_syntax=use_v2, line_ending=line_ending)
    states = {}
    transitions = []

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("statediagram"):
            continue

        # Parse state: [*] --> StateName
        state_match = re.match(r'\[\*\]\s*-->\s*(\w+)', line)
        if state_match:
            state_name = state_match.group(1)
            if state_name not in states:
                state = State(id=state_name)
                states[state_name] = state
                diagram.add_state(state)
            transitions.append(Transition("[*]", state_name))
            continue

        # Parse transition: StateA --> StateB : label
        trans_match = re.match(r'(\w+)\s*-->\s*(\w+)(?::\s*(.+))?', line)
        if trans_match:
            from_state = trans_match.group(1)
            to_state = trans_match.group(2)
            label = trans_match.group(3) if trans_match.group(3) else None

            # Add states if not exist
            if from_state not in states:
                state = State(id=from_state)
                states[from_state] = state
                diagram.add_state(state)
            if to_state not in states:
                state = State(id=to_state)
                states[to_state] = state
                diagram.add_state(state)

            transition = Transition(from_state, to_state, label)
            transitions.append(transition)
            diagram.add_transition(transition)
            continue

        # Parse state with label: StateName : Label
        label_match = re.match(r'(\w+)\s*:\s*(.+)', line)
        if label_match:
            state_id = label_match.group(1)
            state_label = label_match.group(2)
            state = State(id=state_id, label=state_label)
            states[state_id] = state
            diagram.add_state(state)
            continue

        # Simple state declaration
        if re.match(r'^\w+$', line):
            state_id = line.strip()
            if state_id not in states:
                state = State(id=state_id)
                states[state_id] = state
                diagram.add_state(state)

    return diagram


# =============================================================================
# ER Diagram Parser
# =============================================================================

def parse_er_diagram(text: str, line_ending: LineEnding) -> ERDiagram:
    """Parse an entity relationship diagram."""
    lines = preprocess_text(text)

    diagram = ERDiagram(line_ending=line_ending)

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("erdiagram"):
            continue

        # Parse relationship: EntityA {one|many} --| {one|many} EntityB : label
        rel_match = re.match(
            r'(\w+)\s+\{(one|many|zero_or_one)\}\s+--\|?\s*\|\s+\{(one|many|zero_or_one)\}\s+(\w+)(?::\s*(.+))?',
            line, re.IGNORECASE
        )
        if not rel_match:
            # Try simpler pattern: EntityA ||--|| EntityB
            rel_match = re.match(
                r'(\w+)\s+(\|\|?--o?\|?|o\|\|?--\|\|?|\|\|?--\|\|?)\s+(\w+)(?::\s*(.+))?',
                line
            )

        if rel_match:
            entity1 = rel_match.group(1)
            entity3 = rel_match.group(3) if len(rel_match.groups()) >= 3 else rel_match.group(2)
            label = rel_match.group(4) if len(rel_match.groups()) >= 4 else None

            # Determine cardinality from symbols
            cardinality1 = RelationshipCardinality.MANY
            cardinality2 = RelationshipCardinality.MANY

            relationship = ERRelationship(
                entity1_id=entity1,
                entity2_id=entity3,
                label=label or "",
                cardinality1=cardinality1,
                cardinality2=cardinality2
            )
            diagram.add_relationship(relationship)
            continue

        # Parse entity with attributes: Entity {
        entity_match = re.match(r'(\w+)\s+\{', line)
        if entity_match:
            entity_name = entity_match.group(1)
            entity = Entity(id=entity_name, label=entity_name)
            diagram.add_entity(entity)
            continue

    return diagram


# =============================================================================
# User Journey Parser
# =============================================================================

def parse_user_journey(text: str, line_ending: LineEnding) -> UserJourney:
    """Parse a user journey diagram."""
    lines = preprocess_text(text)

    diagram = UserJourney(line_ending=line_ending)
    current_section = None

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("journey"):
            continue

        # Parse title
        title_match = re.match(r'title\s+(.+)', line, re.IGNORECASE)
        if title_match:
            diagram.title = title_match.group(1)
            continue

        # Parse section
        section_match = re.match(r'section\s+(.+)', line, re.IGNORECASE)
        if section_match:
            current_section = section_match.group(1)
            continue

        # Parse task: Description: score: Actor
        task_match = re.match(r'(.+):\s*(\d+):\s*(.+)', line)
        if task_match:
            description = task_match.group(1)
            score = int(task_match.group(2))
            actor = task_match.group(3)

            task = Task(description=description, score=score, actor=actor)
            if current_section:
                diagram.add_task(current_section, task)
            continue

    return diagram


# =============================================================================
# Reusable Parsing Primitives
# =============================================================================

def try_parse_directive(line: str, keyword: str) -> Optional[str]:
    """
    Match a directive line like 'keyword value' (case-insensitive).

    Args:
        line: Line to check
        keyword: Directive keyword (e.g. "title", "dateFormat", "excludes")

    Returns:
        Captured value string, or None if no match
    """
    match = re.match(rf'{keyword}\s+(.+)', line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def try_parse_section(line: str) -> Optional[str]:
    """
    Match a 'section SectionName' line (case-insensitive).

    Returns:
        Section name, or None if no match
    """
    match = re.match(r'section\s+(.+)', line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def is_declaration(line: str, *keywords: str) -> bool:
    """
    Check if a line starts with any of the given keywords (case-insensitive).

    Args:
        line: Line to check
        keywords: One or more keywords to match against

    Returns:
        True if the line starts with any keyword
    """
    line_lower = line.lower()
    return any(line_lower.startswith(kw.lower()) for kw in keywords)


# Mapping from day.js format tokens to Python strptime tokens
_DAYJS_TO_STRPTIME = {
    'YYYY': '%Y',
    'YY': '%y',
    'MMMM': '%B',
    'MMM': '%b',
    'MM': '%m',
    'M': '%-m',
    'DD': '%d',
    'D': '%-d',
    'HH': '%H',
    'hh': '%I',
    'mm': '%M',
    'ss': '%S',
    'SSS': '%f',
    'A': '%p',
    'a': '%p',
}


def dayjs_to_strptime(date_format: str) -> str:
    """
    Convert a day.js format string to a Python strptime format string.

    Args:
        date_format: day.js format string (e.g. "YYYY-MM-DD", "DD/MM/YYYY", "HH:mm")

    Returns:
        Python strptime format string (e.g. "%Y-%m-%d", "%d/%m/%Y", "%H:%M")
    """
    result = date_format
    # Replace longest tokens first to avoid partial matches
    for dayjs_token, strptime_token in _DAYJS_TO_STRPTIME.items():
        result = result.replace(dayjs_token, strptime_token)
    return result


def is_date(s: str, strptime_format: Optional[str] = None) -> bool:
    """
    Check if a string matches a date format.

    Args:
        s: String to check
        strptime_format: Python strptime format string. If None, falls back to
                         matching YYYY-MM-DD pattern.
    """
    if strptime_format is not None:
        try:
            datetime.strptime(s, strptime_format)
            return True
        except ValueError:
            return False
    return re.match(r'^\d{4}-\d{2}-\d{2}$', s) is not None


def is_duration(s: str) -> bool:
    """Check if a string matches a duration pattern like 3d, 24h, 1w."""
    return re.match(r'^\d+[dwmyh]?$', s.lower()) is not None


def is_task_ref(s: str) -> bool:
    """Check if a string is a task reference (after ... or until ...)."""
    lower = s.lower()
    return lower.startswith('after ') or lower.startswith('until ')


# =============================================================================
# Gantt Chart Parser
# =============================================================================

_GANTT_STATUS_KEYWORDS = {'done', 'active', 'crit', 'milestone', 'vert'}


def _extract_gantt_task_statuses(parts: list) -> tuple:
    """
    First pass: extract status keywords from front of parts list.

    Args:
        parts: List of comma-separated task parts (after the colon)

    Returns:
        Tuple of (statuses list, index of first non-status part).
        If all parts are statuses, index equals len(parts).
    """
    statuses = []
    first_non_status = len(parts)
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.lower() in _GANTT_STATUS_KEYWORDS:
            statuses.append(part.lower())
        else:
            first_non_status = i
            break
    return statuses, first_non_status


def _classify_gantt_task_part(
    part: str, task_id: Optional[str], start_date: Optional[str],
    end_date: Optional[str], duration: Optional[str], index: int,
    strptime_format: Optional[str] = None
) -> dict:
    """
    Classify a single comma-separated part as date/duration/task-ref/task-id.

    Args:
        part: The part string to classify
        task_id: Current task_id (or None)
        start_date: Current start_date (or None)
        end_date: Current end_date (or None)
        duration: Current duration (or None)
        index: Position index in the parts list
        strptime_format: Python strptime format for date matching

    Returns:
        Dict with updated values for task_id, start_date, end_date, duration.
    """
    result = {
        'task_id': task_id,
        'start_date': start_date,
        'end_date': end_date,
        'duration': duration,
    }

    if not part:
        return result

    part_lower = part.lower()

    # Skip if it's a status keyword (already extracted)
    if part_lower in _GANTT_STATUS_KEYWORDS:
        return result

    # Duration pattern (e.g., 3d, 24h, 1w)
    if is_duration(part):
        result['duration'] = part
        return result

    # Task reference (after/until)
    if is_task_ref(part):
        if part_lower.startswith('after '):
            result['start_date'] = part_lower
        else:
            result['end_date'] = part_lower
        return result

    # Date/time value (checked against the diagram's dateFormat)
    if is_date(part, strptime_format):
        if result['start_date'] is None:
            result['start_date'] = part
        else:
            result['end_date'] = part
        return result

    # If no task_id yet and early in the list, treat as task ID
    if result['task_id'] is None and index < 4:
        result['task_id'] = part
        return result

    # Unrecognized — treat as date/time value as a last resort
    if result['start_date'] is None:
        result['start_date'] = part
    else:
        result['end_date'] = part

    return result


def _resolve_gantt_start(
    start_date: Optional[str], end_date: Optional[str], duration: Optional[str]
) -> Union[str, DateRange]:
    """
    Determine the start value for a GanttTask from parsed components.

    Returns:
        A string, DateRange, or empty string.
    """
    if (end_date is not None and
            start_date is not None and
            not start_date.startswith('after ')):
        return DateRange(start=start_date, end=end_date)

    if end_date is not None and end_date.startswith('until '):
        return end_date

    if duration is not None and start_date is None:
        return ""

    if start_date is None:
        return ""

    return start_date


def _parse_gantt_task_line(line: str, strptime_format: Optional[str] = None) -> Optional[GanttTask]:
    """
    Parse a full Gantt task line (must contain a colon).

    Args:
        line: A line like 'Task Name :done, des1, 2014-01-06, 2014-01-08'
        strptime_format: Python strptime format for date matching

    Returns:
        A GanttTask, or None if the line isn't a valid task.
    """
    if ':' not in line:
        return None

    parts = line.split(':', 1)
    if len(parts) != 2:
        return None

    task_name = parts[0].strip()
    rest = parts[1].strip()
    task_parts = [p.strip() for p in rest.split(',')]

    # First pass: extract statuses
    statuses, start_index = _extract_gantt_task_statuses(task_parts)

    # Second pass: classify remaining parts
    task_id = None
    start_date = None
    end_date = None
    duration = None

    for i in range(start_index, len(task_parts)):
        result = _classify_gantt_task_part(
            task_parts[i], task_id, start_date, end_date, duration, i,
            strptime_format
        )
        task_id = result['task_id']
        start_date = result['start_date']
        end_date = result['end_date']
        duration = result['duration']

    # Resolve start value
    start_value = _resolve_gantt_start(start_date, end_date, duration)

    return GanttTask(
        name=task_name,
        start=start_value,
        duration=duration,
        statuses=statuses,
        task_id=task_id,
    )


def parse_gantt(text: str, line_ending: LineEnding) -> GanttChart:
    """Parse a Gantt chart using composable sub-functions."""
    diagram = GanttChart(line_ending=line_ending)
    current_section = None
    strptime_format = None

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Preserve %% comment lines in their original position
        if line.startswith("%%"):
            if current_section:
                current_section.add_comment(line)
            else:
                diagram.header_comments.append(line)
            continue

        if is_declaration(line, "gantt"):
            continue

        title = try_parse_directive(line, "title")
        if title is not None:
            diagram.title = title
            continue

        date_format = try_parse_directive(line, "dateformat")
        if date_format is not None:
            diagram.date_format = date_format
            strptime_format = dayjs_to_strptime(date_format)
            continue

        axis_format = try_parse_directive(line, "axisformat")
        if axis_format is not None:
            diagram.axis_format = axis_format
            continue

        excludes = try_parse_directive(line, "excludes")
        if excludes is not None:
            diagram.set_excludes(excludes)
            continue

        weekend = try_parse_directive(line, "weekend")
        if weekend is not None:
            diagram.weekend = weekend
            continue

        section_name = try_parse_section(line)
        if section_name is not None:
            current_section = GanttSection(name=section_name)
            diagram.add_section(current_section)
            continue

        task = _parse_gantt_task_line(line, strptime_format)
        if task:
            if current_section:
                current_section.add_task(task)
            else:
                diagram.add_task(task)

    return diagram


# =============================================================================
# Pie Chart Parser
# =============================================================================

def parse_pie_chart(text: str, line_ending: LineEnding) -> PieChart:
    """Parse a pie chart."""
    lines = preprocess_text(text)

    diagram = PieChart(line_ending=line_ending)
    show_data = False

    for line in lines:
        # Parse showData or title directive
        if "showdata" in line.lower():
            show_data = True
            continue

        title_match = re.match(r'(.+?)\s*:\s*(\d+)', line)
        if title_match:
            diagram.add_slice(slice_data)
            continue

    return diagram


# =============================================================================
# Mindmap Parser
# =============================================================================

def parse_mindmap(text: str, line_ending: LineEnding) -> Mindmap:
    """Parse a mindmap."""
    lines = preprocess_text(text)

    diagram = Mindmap(line_ending=line_ending)

    # Parse indented structure
    root_node = None

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("mindmap"):
            continue

        # Determine level from indentation
        indent = parse_indent(line)
        level = indent // 2
        content = line.strip()

        if level == 0:
            root_node = MindmapNode(content=content)
            diagram.add_root(root_node)
        elif root_node:
            child = MindmapNode(content=content)
            root_node.add_child(child)

    return diagram


# =============================================================================
# Git Graph Parser
# =============================================================================

def parse_git_graph(text: str, line_ending: LineEnding) -> GitGraph:
    """Parse a git graph."""
    lines = preprocess_text(text)

    diagram = GitGraph(line_ending=line_ending)

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("gitgraph"):
            continue

        # Parse commit: commit id: "message"
        commit_match = re.match(r'commit\s+(?:id:\s*)"?([^"]+)"?', line)
        if commit_match:
            commit_hash = commit_match.group(1)
            commit = Commit(id=commit_hash)
            diagram.add_commit(commit)
            continue

        # Parse branch
        branch_match = re.match(r'branch\s+(\w+)', line)
        if branch_match:
            branch_name = branch_match.group(1)
            branch = Branch(name=branch_name)
            diagram.add_branch(branch)
            continue

        # Parse checkout
        checkout_match = re.match(r'checkout\s+(\w+)', line)
        if checkout_match:
            checkout = Checkout(branch=checkout_match.group(1))
            diagram.add_checkout(checkout)
            continue

    return diagram


# =============================================================================
# Quadrant Chart Parser
# =============================================================================

def parse_quadrant_chart(text: str, line_ending: LineEnding) -> QuadrantChart:
    """Parse a quadrant chart."""
    lines = preprocess_text(text)

    diagram = QuadrantChart(line_ending=line_ending)

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("quadrantchart"):
            continue

        # Parse title
        title_match = re.match(r'title\s+(.+)', line, re.IGNORECASE)
        if title_match:
            diagram.title = title_match.group(1)
            continue

        # Parse axis
        axis_match = re.match(r'(x-axis|y-axis)\s+(.+)', line, re.IGNORECASE)
        if axis_match:
            axis_type = axis_match.group(1).lower()
            axis_label = axis_match.group(2)
            if axis_type == "x-axis":
                diagram.x_axis_label = axis_label
            else:
                diagram.y_axis_label = axis_label
            continue

        # Parse quadrant
        quad_match = re.match(r'quadrant-(\d+)\s+(.+)', line, re.IGNORECASE)
        if quad_match:
            quad_num = int(quad_match.group(1))
            quad_label = quad_match.group(2)
            diagram.set_quadrant(quad_num, quad_label)
            continue

        # Parse point: Label: [x, y]
        point_match = re.match(r'(.+):\s*\[([0-9.]+),\s*([0-9.]+)\]', line)
        if point_match:
            label = point_match.group(1)
            x = float(point_match.group(2))
            y = float(point_match.group(3))
            diagram.add_point(label, x, y)
            continue

    return diagram


# =============================================================================
# Timeline Parser
# =============================================================================

def parse_timeline(text: str, line_ending: LineEnding) -> Timeline:
    """Parse a timeline diagram."""
    lines = preprocess_text(text)

    diagram = Timeline(line_ending=line_ending)
    current_date = None

    for line in lines:
        # Skip diagram declaration
        if line.lower().startswith("timeline"):
            continue

        # Parse title
        title_match = re.match(r'title\s+(.+)', line, re.IGNORECASE)
        if title_match:
            diagram.title = title_match.group(1)
            continue

        # Parse date: YYYY-MM-DD
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})\s*:\s*(.+)', line)
        if date_match:
            date_str = date_match.group(1)
            event_name = date_match.group(2)
            event = Event(date=date_str, name=event_name)
            diagram.add_event(event)
            continue

    return diagram


# =============================================================================
# C4 Diagram Parser
# =============================================================================

def parse_c4_diagram(text: str, line_ending: LineEnding) -> C4Diagram:
    """Parse a C4 diagram."""
    lines = preprocess_text(text)

    # Determine diagram type
    diagram_type = C4DiagramType.CONTEXT
    if "C4Container" in text:
        diagram_type = C4DiagramType.CONTAINER
    elif "C4Component" in text:
        diagram_type = C4DiagramType.COMPONENT
    elif "C4Deployment" in text:
        diagram_type = C4DiagramType.DEPLOYMENT

    diagram = C4Diagram(diagram_type=diagram_type, line_ending=line_ending)

    for line in lines:
        # Skip diagram declaration
        if line.startswith("C4"):
            continue

        # Parse person
        person_match = re.match(r'Person\s+(\w+)(?:\s+"([^"]+)")?', line)
        if person_match:
            person_id = person_match.group(1)
            person_label = person_match.group(2) or person_id
            person = Person(id=person_id, label=person_label)
            diagram.add_element(person)
            continue

        # Parse system
        system_match = re.match(r'System\s+(?:Ext\s+)?(\w+)(?:\s+"([^"]+)")?', line)
        if system_match:
            system_id = system_match.group(1)
            system_label = system_match.group(2) or system_id
            system = System(id=system_id, label=system_label, is_external=False)
            diagram.add_element(system)
            continue

        # Parse container
        container_match = re.match(r'Container\s+(?:Ext\s+)?(\w+)(?:\s+"([^"]+)")?', line)
        if container_match:
            container_id = container_match.group(1)
            container_label = container_match.group(2) or container_id
            container = Container(id=container_id, label=container_label, is_external=False)
            diagram.add_element(container)
            continue

        # Parse relationship
        rel_match = re.match(r'(\w+)\s+-[^>]*>\s+(\w+)\s*:\s*(.+)', line)
        if rel_match:
            from_id = rel_match.group(1)
            to_id = rel_match.group(2)
            label = rel_match.group(3)
            relationship = C4Relationship(from_id=from_id, to_id=to_id, label=label)
            diagram.add_relationship(relationship)
            continue

    return diagram


# =============================================================================
# Main Parser Entry Point
# =============================================================================

def parse_mermaid_text(text: str, line_ending: LineEnding) -> Optional[Union[
    Flowchart, SequenceDiagram, ClassDiagram, StateDiagram, ERDiagram,
    UserJourney, GanttChart, PieChart, Mindmap, GitGraph, QuadrantChart,
    Timeline, C4Diagram
]]:
    """
    Parse Mermaid text into a Python object.

    Args:
        text: Mermaid diagram text
        line_ending: Line ending style for output

    Returns:
        Python Mermaid diagram object, or None if parsing fails
    """
    # Extract frontmatter before parsing
    frontmatter, text = extract_frontmatter(text)

    diagram_type = detect_diagram_type(text)

    parsers = {
        "flowchart": parse_flowchart,
        "sequence": parse_sequence,
        "class": parse_class_diagram,
        "state": parse_state_diagram,
        "er": parse_er_diagram,
        "journey": parse_user_journey,
        "gantt": parse_gantt,
        "pie": parse_pie_chart,
        "mindmap": parse_mindmap,
        "git": parse_git_graph,
        "quadrant": parse_quadrant_chart,
        "timeline": parse_timeline,
        "c4": parse_c4_diagram,
    }

    parser = parsers.get(diagram_type)
    if parser:
        try:
            diagram = parser(text, line_ending)
            if diagram is not None and frontmatter:
                diagram.frontmatter = frontmatter
            return diagram
        except Exception as e:
            print(f"Warning: Error parsing {diagram_type} diagram: {e}", file=sys.stderr)

    # Fallback: return a simple flowchart
    print(f"Warning: Unknown or unsupported diagram type '{diagram_type}'", file=sys.stderr)
    return None


# =============================================================================
# Main Entry Point
# =============================================================================

def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_arguments()
    line_ending = parse_line_ending(args.line_ending)

    # Get input text
    input_text = get_input_text(args)

    if input_text is None:
        return 1

    if not input_text.strip():
        print("Error: No input provided.", file=sys.stderr)
        return 1

    print(f"Parsing with {line_ending.name} line endings...")

    # Parse the Mermaid text
    diagram = parse_mermaid_text(input_text, line_ending)

    if diagram is None:
        print("Error: Failed to parse diagram.", file=sys.stderr)
        return 1

    print(f"Successfully parsed: {type(diagram).__name__}")

    # Convert back to Mermaid text
    output_text = diagram.to_mermaid()

    # Write output
    write_output(output_text, args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

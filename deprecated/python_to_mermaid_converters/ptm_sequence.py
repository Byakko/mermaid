"""
Sequence diagram renderer for converting Python SequenceDiagram objects to Mermaid text.

Returns a list of content lines (no frontmatter, no comments -- those are
handled by python_to_mermaid.py using the raw input).
"""

from typing import List

from mermaid.base import LineEnding
from mermaid.sequence import (
    SequenceDiagram,
    Participant,
    Message,
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
    ActorLink,
    ActorLinks,
    CreateDirective,
    DestroyDirective,
)


# ---------------------------------------------------------------------------
# Block rendering helpers
# ---------------------------------------------------------------------------

def _render_block(block, indent: int, line_ending: LineEnding) -> List[str]:
    """Render any block type into a list of indented lines."""
    prefix = "    " * indent

    if isinstance(block, LoopBlock):
        lines = [f"{prefix}loop {block.loop_text}"]
        lines.extend(_render_block_body(block.messages, block.nested_blocks, indent, line_ending))
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, OptBlock):
        lines = [f"{prefix}opt {block.description}"]
        lines.extend(_render_block_body(block.messages, block.nested_blocks, indent, line_ending))
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, BreakBlock):
        lines = [f"{prefix}break {block.description}"]
        for msg in block.messages:
            lines.append(f"{prefix}    {msg.render()}")
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, AltBlock):
        lines = []
        for i, (option, is_else) in enumerate(block.options):
            keyword = "else" if is_else else "alt"
            lines.append(f"{prefix}{keyword} {option.description}")
            lines.extend(_render_block_body(option.messages, option.nested_blocks, indent, line_ending))
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, ParallelBlock):
        lines = []
        for i, action in enumerate(block.actions):
            keyword = "and" if i > 0 else "par"
            lines.append(f"{prefix}{keyword} {action.description}")
            lines.extend(_render_block_body(action.messages, action.nested_blocks, indent, line_ending))
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, CriticalBlock):
        lines = [f"{prefix}critical {block.action}"]
        for msg in block.messages:
            lines.append(f"{prefix}    {msg.render()}")
        for option in block.options:
            lines.append(f"{prefix}option {option.description}")
            for msg in option.messages:
                lines.append(f"{prefix}    {msg.render()}")
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, RectBlock):
        header = block.raw_header if block.raw_header is not None else f"rect {block.color}"
        lines = [f"{prefix}{header}"]
        for msg in block.messages:
            lines.append(f"{prefix}    {msg.render()}")
        lines.append(f"{prefix}end")
        return lines

    if isinstance(block, BoxGroup):
        lines = []
        # Header
        if block.raw_header is not None:
            lines.append(f"{prefix}{block.raw_header}")
        elif block.description and block.color:
            lines.append(f"{prefix}box {block.color} {block.description}")
        elif block.description:
            lines.append(f"{prefix}box {block.description}")
        elif block.color:
            lines.append(f"{prefix}box {block.color}")
        else:
            lines.append(f"{prefix}box")
        # Participants inside the box
        for p in block.participants:
            lines.append(f"{prefix}    {p.render()}")
        lines.append(f"{prefix}end")
        return lines

    return []


def _render_block_body(
    messages: list,
    nested_blocks: list,
    indent: int,
    line_ending: LineEnding,
) -> List[str]:
    """Render messages and nested blocks inside a block."""
    prefix = "    " * (indent + 1)
    lines = []
    for msg in messages:
        lines.append(f"{prefix}{msg.render()}")
    for nested in nested_blocks:
        lines.extend(_render_block(nested, indent + 1, line_ending))
    return lines


# ---------------------------------------------------------------------------
# Item rendering
# ---------------------------------------------------------------------------

def _render_item(item, indent: int, line_ending: LineEnding) -> List[str]:
    """Render a single ordered item into lines."""
    prefix = "    " * indent

    if isinstance(item, tuple):
        tag = item[0]
        if tag == 'autonumber':
            return [f"{prefix}autonumber"]
        if tag == 'raw':
            return [f"{prefix}{item[1]}"]
        return []

    if isinstance(item, Participant):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, Message):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, Activation):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, Note):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, CreateDirective):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, DestroyDirective):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, ActorLink):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, ActorLinks):
        return [f"{prefix}{item.render()}"]

    if isinstance(item, (LoopBlock, OptBlock, BreakBlock, AltBlock,
                         ParallelBlock, CriticalBlock, RectBlock, BoxGroup)):
        return _render_block(item, indent, line_ending)

    return []


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_sequence(diagram: SequenceDiagram) -> List[str]:
    """
    Render a SequenceDiagram object as a list of content lines.

    Frontmatter and comments are NOT included -- those are preserved
    from the raw input by python_to_mermaid.py.

    Args:
        diagram: The SequenceDiagram to render

    Returns:
        List of content lines
    """
    lines: List[str] = []

    # Directive
    if diagram.directive:
        lines.append(str(diagram.directive))

    # Declaration line
    lines.append("sequenceDiagram")

    # Render from ordered items if available
    if diagram.items:
        for item in diagram.items:
            lines.extend(_render_item(item, 1, diagram.line_ending))
    else:
        # Fallback for programmatically created diagrams without items
        if diagram.autonumber:
            lines.append("    autonumber")

        for box in diagram.box_groups:
            lines.extend(_render_block(box, 1, diagram.line_ending))

        for p in diagram.participants.values():
            lines.append(f"    {p.render()}")

        for msg in diagram.messages:
            lines.append(f"    {msg.render()}")

        for note in diagram.notes:
            lines.append(f"    {note.render()}")

        for act in diagram.activations:
            lines.append(f"    {act.render()}")

        for block in diagram.blocks:
            lines.extend(_render_block(block, 1, diagram.line_ending))

        for link in diagram.actor_links:
            lines.append(f"    {link.render()}")

    return lines

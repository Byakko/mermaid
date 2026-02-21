"""
Sequence diagram parser for converting Mermaid sequence text to Python objects.
"""

import re
from typing import Optional, List, Tuple, Any

from mermaid.base import LineEnding
from mermaid.sequence import (
    SequenceDiagram,
    Participant,
    ParticipantType,
    Message,
    MessageArrow,
    Activation,
    Note,
    NotePosition,
    LoopBlock,
    AltBlock,
    AltOption,
    OptBlock,
    ParallelBlock,
    CriticalBlock,
    CriticalOption,
    BreakBlock,
    RectBlock,
    BoxGroup,
    ActorLink,
    ActorLinks,
    CreateDirective,
    DestroyDirective,
)

from mermaid_to_python_converters.mtp_common import (
    is_declaration,
    try_parse_color,
    try_parse_block_open,
    is_skip_line,
    strip_keyword,
    accumulate_brackets,
)


# ---------------------------------------------------------------------------
# Arrow detection — ordered longest-first to avoid partial matches
# ---------------------------------------------------------------------------

_ARROW_PATTERNS: List[Tuple[str, MessageArrow]] = [
    ('<<-->>',  MessageArrow.DOTTED_BI_ARROW),
    ('<<->>',   MessageArrow.SOLID_BI_ARROW),
    ('-->>',    MessageArrow.DOTTED_ARROW),
    ('->>',     MessageArrow.SOLID_ARROW),
    ('-->',     MessageArrow.DOTTED_NO_ARROW),
    ('--x',     MessageArrow.DOTTED_CROSS),
    ('--)',     MessageArrow.DOTTED_OPEN_ARROW),
    ('->',      MessageArrow.SOLID_NO_ARROW),
    ('-x',      MessageArrow.SOLID_CROSS),
    ('-)',      MessageArrow.SOLID_OPEN_ARROW),
]

# Build a single regex that captures the arrow and splits sender/receiver.
# Group layout: (sender)(arrow)(activation_suffix?)(receiver): text
# Activation shorthand (+/-) appears between arrow and receiver: Alice->>+Bob
# We use re.escape on each literal arrow string to produce the regex alternation.
_ARROW_RE = re.compile(
    r'^([\w][\w ]*?)'                                   # from_participant (word chars/spaces, non-greedy)
    r'(' + '|'.join(re.escape(p) for p, _ in _ARROW_PATTERNS) + r')'  # arrow
    r'(\+|-)?'                                          # optional receiver activation/deactivation
    r'([\w][\w ]*?)'                                    # to_participant (word chars/spaces, non-greedy)
    r'\s*:\s*'                                          # colon separator
    r'(.*)$'                                            # message text
)

_ARROW_LOOKUP = {p: a for p, a in _ARROW_PATTERNS}


# ---------------------------------------------------------------------------
# Participant parsing
# ---------------------------------------------------------------------------

_PARTICIPANT_TYPES = {t.value: t for t in ParticipantType}


def _parse_participant_line(line: str) -> Optional[Participant]:
    """
    Parse a participant/actor declaration line.

    Handles:
        participant A
        actor Bob as "Bob the Builder"
        participant P as Person
        participant Alice@{ "type": "control" }
        participant API@{ "type": "boundary", "alias": "Public API" }
        participant API@{ "type": "boundary" } as Public API
    """
    for keyword, ptype in _PARTICIPANT_TYPES.items():
        if not is_declaration(line, keyword):
            continue

        rest = strip_keyword(line, keyword)
        if not rest:
            return None

        # Check for @{...} JSON metadata syntax
        meta_match = re.match(r'([\w-]+)@\{(.+)\}(.*)', rest, re.DOTALL)
        if meta_match:
            pid = meta_match.group(1)
            json_str = '{' + meta_match.group(2) + '}'
            after_meta = meta_match.group(3).strip()

            import json
            try:
                meta = json.loads(json_str)
            except json.JSONDecodeError:
                meta = {}

            # Extract type from metadata
            meta_type = meta.get('type', '').lower()
            if meta_type in _PARTICIPANT_TYPES:
                ptype = _PARTICIPANT_TYPES[meta_type]

            # Extract alias from metadata or trailing "as ..."
            label = meta.get('alias')
            raw_alias = None

            # Check for trailing "as Label" after the @{...}
            as_match = re.match(r'as\s+(.+)', after_meta)
            if as_match:
                raw_alias = as_match.group(1).strip()
                label = raw_alias.strip('"')
            elif label:
                raw_alias = label

            return Participant(id=pid, label=label, type=ptype,
                             raw_alias=raw_alias, raw_line=line)

        # Check for alias: id as Label  (with or without quotes)
        alias_match = re.match(r'([\w-]+)\s+as\s+(.+)', rest)
        if alias_match:
            pid = alias_match.group(1)
            raw_alias = alias_match.group(2).strip()
            label = raw_alias.strip('"')
            return Participant(id=pid, label=label, type=ptype, raw_alias=raw_alias)

        # Just an id
        pid = rest.split()[0]
        return Participant(id=pid, type=ptype)

    return None


# ---------------------------------------------------------------------------
# Message parsing
# ---------------------------------------------------------------------------

def _parse_message(line: str) -> Optional[Message]:
    """Parse a message line like ``Alice->>Bob: Hello``."""
    m = _ARROW_RE.match(line)
    if not m:
        return None

    from_p = m.group(1).strip()
    arrow_str = m.group(2)
    receiver_mod = m.group(3)
    to_p = m.group(4).strip()
    text = m.group(5).strip()

    arrow = _ARROW_LOOKUP.get(arrow_str, MessageArrow.SOLID_ARROW)

    return Message(
        from_participant=from_p,
        to_participant=to_p,
        text=text,
        arrow=arrow,
        activate_receiver=(receiver_mod == '+'),
        deactivate_receiver=(receiver_mod == '-'),
    )


# ---------------------------------------------------------------------------
# Note parsing
# ---------------------------------------------------------------------------

_NOTE_RE = re.compile(
    r'^Note\s+'
    r'(right\s+of|left\s+of|over)\s+'
    r'(.+?)'
    r'\s*:\s*'
    r'(.*)$',
    re.IGNORECASE,
)


def _parse_note(line: str) -> Optional[Note]:
    """Parse a Note line."""
    m = _NOTE_RE.match(line)
    if not m:
        return None

    pos_str = m.group(1).lower().replace('  ', ' ')
    position = NotePosition(pos_str)

    participants_raw = m.group(2).strip()
    if ',' in participants_raw:
        participants = [p.strip() for p in participants_raw.split(',')]
    else:
        participants = participants_raw

    text = m.group(3).strip()

    return Note(position=position, participants=participants, text=text,
                raw_participants=participants_raw)


# ---------------------------------------------------------------------------
# Link parsing
# ---------------------------------------------------------------------------

def _parse_link(line: str) -> Optional[ActorLink]:
    """Parse ``link Actor: Label @ URL``."""
    m = re.match(r'^link\s+([\w-]+)\s*:\s*(.+?)\s*@\s*(.+)$', line, re.IGNORECASE)
    if m:
        return ActorLink(actor_id=m.group(1), label=m.group(2).strip().strip('"'), url=m.group(3).strip())
    return None


def _parse_links(line: str) -> Optional[ActorLinks]:
    """Parse ``links Actor: { ... }``."""
    m = re.match(r'^links\s+([\w-]+)\s*:\s*(.+)$', line, re.IGNORECASE)
    if m:
        import json
        try:
            data = json.loads(m.group(2))
            return ActorLinks(actor_id=m.group(1), links=data)
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# Create / Destroy
# ---------------------------------------------------------------------------

def _parse_create(line: str) -> Optional[CreateDirective]:
    """Parse ``create participant B`` or ``create actor B as Label``."""
    m = re.match(r'^create\s+(participant|actor)\s+([\w-]+)(?:\s+as\s+(.+))?$', line, re.IGNORECASE)
    if m:
        ptype = ParticipantType(m.group(1).lower())
        pid = m.group(2)
        label = m.group(3).strip().strip('"') if m.group(3) else None
        return CreateDirective(participant_id=pid, participant_type=ptype, label=label)
    return None


def _parse_destroy(line: str) -> Optional[str]:
    """Parse ``destroy B``, return participant id."""
    m = re.match(r'^destroy\s+([\w-]+)\s*$', line, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Block parsing (recursive)
# ---------------------------------------------------------------------------

def _parse_block_body(
    lines: List[str],
    start: int,
    diagram: SequenceDiagram,
) -> Tuple[List[Any], int]:
    """
    Parse lines inside a block until ``end`` is reached (respecting nesting).

    Returns (items_list, next_line_index).
    """
    items: List[Any] = []
    i = start

    while i < len(lines):
        line = lines[i].strip()

        if is_skip_line(line):
            i += 1
            continue

        if line.lower() == 'end':
            return items, i + 1

        # Nested block openers — check before message parsing
        parsed_item, next_i = _try_parse_block(lines, i, diagram)
        if parsed_item is not None:
            items.append(parsed_item)
            i = next_i
            continue

        # Section dividers inside blocks (else, and, option)
        if is_declaration(line, 'else', 'and', 'option'):
            # Push back — caller handles these
            return items, i

        # Standard items
        item = _parse_line_item(line, diagram)
        if item is not None:
            items.append(item)

        i += 1

    return items, i


def _try_parse_block(
    lines: List[str],
    i: int,
    diagram: SequenceDiagram,
) -> Tuple[Optional[Any], int]:
    """
    Try to parse a block starting at line i.

    Returns (block_object, next_index) or (None, i) if not a block opener.
    """
    line = lines[i].strip()

    # --- loop ---
    desc = try_parse_block_open(line, 'loop')
    if desc is not None:
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        block = LoopBlock(loop_text=desc)
        for item in body:
            if isinstance(item, Message):
                block.add_message(item)
            else:
                block.nested_blocks.append(item)
        return block, next_i

    # --- opt ---
    desc = try_parse_block_open(line, 'opt')
    if desc is not None:
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        block = OptBlock(description=desc)
        for item in body:
            if isinstance(item, Message):
                block.add_message(item)
            else:
                block.nested_blocks.append(item)
        return block, next_i

    # --- break ---
    desc = try_parse_block_open(line, 'break')
    if desc is not None:
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        block = BreakBlock(description=desc)
        for item in body:
            if isinstance(item, Message):
                block.add_message(item)
        return block, next_i

    # --- alt / else ---
    desc = try_parse_block_open(line, 'alt')
    if desc is not None:
        block = AltBlock()
        # First option
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        option = AltOption(description=desc)
        for item in body:
            if isinstance(item, Message):
                option.add_message(item)
            else:
                option.add_nested_block(item)
        block.add_option(option, is_else=False)

        # Subsequent else clauses
        while next_i < len(lines):
            eline = lines[next_i].strip()
            else_desc = try_parse_block_open(eline, 'else')
            if else_desc is None:
                break
            body, next_i = _parse_block_body(lines, next_i + 1, diagram)
            option = AltOption(description=else_desc)
            for item in body:
                if isinstance(item, Message):
                    option.add_message(item)
                else:
                    option.add_nested_block(item)
            block.add_option(option, is_else=True)

        # Consume the 'end'
        if next_i < len(lines) and lines[next_i].strip().lower() == 'end':
            next_i += 1

        return block, next_i

    # --- par / and ---
    desc = try_parse_block_open(line, 'par')
    if desc is not None:
        block = ParallelBlock()
        # First action
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        first = AltOption(description=desc)
        for item in body:
            if isinstance(item, Message):
                first.add_message(item)
            else:
                first.add_nested_block(item)
        block.actions.append(first)

        # Subsequent 'and' clauses
        while next_i < len(lines):
            aline = lines[next_i].strip()
            and_desc = try_parse_block_open(aline, 'and')
            if and_desc is None:
                break
            body, next_i = _parse_block_body(lines, next_i + 1, diagram)
            action = AltOption(description=and_desc)
            for item in body:
                if isinstance(item, Message):
                    action.add_message(item)
                else:
                    action.add_nested_block(item)
            block.actions.append(action)

        if next_i < len(lines) and lines[next_i].strip().lower() == 'end':
            next_i += 1

        return block, next_i

    # --- critical / option ---
    desc = try_parse_block_open(line, 'critical')
    if desc is not None:
        block = CriticalBlock(action=desc)
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        for item in body:
            if isinstance(item, Message):
                block.messages.append(item)

        # 'option' clauses
        while next_i < len(lines):
            oline = lines[next_i].strip()
            opt_desc = try_parse_block_open(oline, 'option')
            if opt_desc is None:
                break
            obody, next_i = _parse_block_body(lines, next_i + 1, diagram)
            msgs = [item for item in obody if isinstance(item, Message)]
            block.add_option(opt_desc, msgs)

        if next_i < len(lines) and lines[next_i].strip().lower() == 'end':
            next_i += 1

        return block, next_i

    # --- rect ---
    desc = try_parse_block_open(line, 'rect')
    if desc is not None:
        color = try_parse_color(desc)
        if color is None:
            from mermaid.base import Color
            color = Color(name=desc)
        body, next_i = _parse_block_body(lines, i + 1, diagram)
        block = RectBlock(color=color, raw_header=line)
        for item in body:
            if isinstance(item, Message):
                block.add_message(item)
        return block, next_i

    # --- box ---
    desc = try_parse_block_open(line, 'box')
    if desc is not None:
        box = _parse_box_header(desc)
        box.raw_header = line
        # Parse participant declarations inside the box
        bi = i + 1
        while bi < len(lines):
            bline = lines[bi].strip()
            if is_skip_line(bline):
                bi += 1
                continue
            if bline.lower() == 'end':
                bi += 1
                break
            p = _parse_participant_line(bline)
            if p:
                box.add_participant(p)
                diagram.participants[p.id] = p
            bi += 1
        return box, bi

    return None, i


def _parse_box_header(desc: str) -> BoxGroup:
    """Parse the header after ``box`` keyword (color and/or description)."""
    from mermaid.base import Color

    desc = desc.strip()
    if not desc:
        return BoxGroup()

    # Try color at the start: rgb(...), rgba(...), #hex, or named color
    color = None
    remaining = desc

    # rgb/rgba prefix
    m = re.match(r'(rgba?\([^)]+\))\s*(.*)', desc)
    if m:
        color = try_parse_color(m.group(1))
        remaining = m.group(2).strip()
    else:
        # Hex color prefix
        m = re.match(r'(#[0-9a-fA-F]{3,8})\s*(.*)', desc)
        if m:
            color = try_parse_color(m.group(1))
            remaining = m.group(2).strip()
        else:
            # Named color: only if it's a single word followed by more text,
            # or the entire desc is a known simple word
            words = desc.split(None, 1)
            if len(words) == 2:
                # First word could be a color name
                color = try_parse_color(words[0])
                remaining = words[1]
            else:
                # Single word — treat as description, not color
                remaining = desc

    return BoxGroup(color=color, description=remaining if remaining else None)


# ---------------------------------------------------------------------------
# Single-line item parsing
# ---------------------------------------------------------------------------

def _parse_line_item(line: str, diagram: SequenceDiagram) -> Optional[Any]:
    """Parse a single non-block line into a diagram item."""

    # Activation / deactivation
    if is_declaration(line, 'activate'):
        pid = strip_keyword(line, 'activate')
        act = Activation(participant=pid, is_activate=True)
        diagram.add_activation(act)
        return act

    if is_declaration(line, 'deactivate'):
        pid = strip_keyword(line, 'deactivate')
        act = Activation(participant=pid, is_activate=False)
        diagram.add_activation(act)
        return act

    # Note
    note = _parse_note(line)
    if note:
        diagram.add_note(note)
        return note

    # Create directive
    create = _parse_create(line)
    if create:
        return create

    # Destroy directive
    destroy_id = _parse_destroy(line)
    if destroy_id:
        return DestroyDirective(participant_id=destroy_id)

    # Actor link(s)
    alink = _parse_link(line)
    if alink:
        diagram.add_actor_link(alink)
        return alink

    alinks = _parse_links(line)
    if alinks:
        diagram.add_actor_link(alinks)
        return alinks

    # Message (try last — most greedy pattern)
    msg = _parse_message(line)
    if msg:
        diagram.add_message(msg)
        # Ensure participants exist
        if msg.from_participant not in diagram.participants:
            diagram.participants[msg.from_participant] = Participant(id=msg.from_participant)
        if msg.to_participant not in diagram.participants:
            diagram.participants[msg.to_participant] = Participant(id=msg.to_participant)
        return msg

    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_sequence(text: str, line_ending: LineEnding) -> SequenceDiagram:
    """
    Parse a Mermaid sequence diagram from text.

    Args:
        text: Mermaid sequence diagram text (frontmatter already stripped)
        line_ending: Line ending style

    Returns:
        A SequenceDiagram object
    """
    diagram = SequenceDiagram(line_ending=line_ending)

    lines = text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if is_skip_line(line):
            i += 1
            continue

        # Declaration line
        if is_declaration(line, 'sequenceDiagram'):
            i += 1
            continue

        # Autonumber
        if line.lower() == 'autonumber':
            diagram.autonumber = True
            diagram.items.append(('autonumber',))
            i += 1
            continue

        # Participant / actor declarations (handle multi-line @{...} syntax)
        if '@{' in line:
            full_stmt, next_i = accumulate_brackets(lines, i)
            p = _parse_participant_line(full_stmt)
            if p:
                diagram.participants[p.id] = p
                diagram.items.append(p)
                i = next_i
                continue
            # Not a participant — store as raw
            diagram.items.append(('raw', full_stmt))
            i = next_i
            continue

        p = _parse_participant_line(line)
        if p:
            diagram.participants[p.id] = p
            diagram.items.append(p)
            i += 1
            continue

        # Block constructs
        block, next_i = _try_parse_block(lines, i, diagram)
        if block is not None:
            if isinstance(block, BoxGroup):
                diagram.add_box_group(block)
            else:
                diagram.add_block(block)
            diagram.items.append(block)
            i = next_i
            continue

        # Single-line items
        item = _parse_line_item(line, diagram)
        if item is not None:
            diagram.items.append(item)
            i += 1
            continue

        # Unknown line — store as raw for round-tripping
        diagram.items.append(('raw', line))
        i += 1

    return diagram

"""
Flowchart parser for converting Mermaid flowchart text to Python objects.
"""

import re
from typing import Optional, List, Tuple, Any

from mermaid.flowchart import (
    Flowchart,
    FlowchartDirection,
    FlowchartNode,
    FlowchartNodeShape,
    FlowchartEdge,
    FlowchartSubgraph,
)
from mermaid.base import LineEnding

from mermaid_to_python_converters.mtp_common import is_declaration


# ---------------------------------------------------------------------------
# Node shape patterns, ordered from most specific to least specific.
# Each tuple: (regex matching shape brackets, FlowchartNodeShape enum value)
# ---------------------------------------------------------------------------

_SHAPE_PATTERNS: List[Tuple[str, FlowchartNodeShape]] = [
    (r'\(\(\((.*?)\)\)\)', FlowchartNodeShape.DOUBLE_CIRCLE),
    (r'\(\((.*?)\)\)',     FlowchartNodeShape.CIRCLE),
    (r'\(\[(.*?)\]\)',     FlowchartNodeShape.STADIUM),
    (r'\[\((.*?)\)\]',     FlowchartNodeShape.CYLINDER),
    (r'\[\[(.*?)\]\]',     FlowchartNodeShape.SUBROUTINE),
    (r'\{\{(.*?)\}\}',     FlowchartNodeShape.HEXAGON),
    (r'\[/(.*?)/\]',       FlowchartNodeShape.PARALLELOGRAM),
    (r'\[\\(.*?)\\\]',     FlowchartNodeShape.PARALLELOGRAM_ALT),
    (r'\[/(.*?)\\]',       FlowchartNodeShape.TRAPEZOID),
    (r'\[\\(.*?)/\]',      FlowchartNodeShape.TRAPEZOID_ALT),
    (r'\((.*?)\)',          FlowchartNodeShape.ROUNDED),
    (r'\[(.*?)\]',          FlowchartNodeShape.RECTANGLE),
    (r'>(.*?)\]',           FlowchartNodeShape.ASYMMETRIC),
    (r'\{(.*?)\}',          FlowchartNodeShape.RHOMBUS),
]

_COMPILED_SHAPES = [(re.compile(r'^' + p, re.DOTALL), s) for p, s in _SHAPE_PATTERNS]


# ---------------------------------------------------------------------------
# Arrow / link detection
# ---------------------------------------------------------------------------

# Individual arrow patterns ordered by specificity (longest first).
# Inline text label patterns (e.g. -. text .->) must come before
# bare arrow patterns so they match as a single unit.
_ARROW_PATTERNS = [
    # Inline text label arrows
    r'-\.\s+.*?\s+\.->',                     # -. text .->
    r'--\s+.*?\s+-->',                        # -- text -->
    r'--\s+.*?\s+---',                        # -- text ---
    r'==\s+.*?\s+==>',                        # == text ==>
    # Bidirectional
    r'<-\.+->', r'<-{2,}>', r'<=+>',
    # Dotted
    r'-\.+->',  r'-\.+-',
    # Thick
    r'={2,}>',  r'={3,}',
    # Solid with head/cross/circle
    r'-{2,}>',  r'-{2,}x',  r'-{2,}o',
    # Solid open
    r'-{3,}',
    # Invisible
    r'~{3,}',
]

_ARROW_RE = re.compile('(' + '|'.join(_ARROW_PATTERNS) + ')')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_node_expr(text: str):
    """
    Parse a node expression like ``id1[text]:::cls`` from the start of *text*.

    Returns
    -------
    tuple (node_id, shape, label, remaining_text, class_name)
        *node_id* is ``None`` when nothing could be parsed.
    """
    text = text.strip()

    id_match = re.match(r'([\w][\w-]*)', text)
    if not id_match:
        return None, None, None, text, None

    node_id = id_match.group(1)
    rest = text[id_match.end():]

    shape = None
    label = None
    for pattern, shape_type in _COMPILED_SHAPES:
        m = pattern.match(rest)
        if m:
            shape = shape_type
            label = m.group(1)
            rest = rest[m.end():]
            break

    class_name = None
    class_match = re.match(r':::([\w-]+)', rest)
    if class_match:
        class_name = class_match.group(1)
        rest = rest[class_match.end():]

    return node_id, shape, label, rest, class_name


def _find_arrow(text: str):
    """Return ``(start, end, arrow_str)`` for the first arrow in *text*, or ``None``."""
    m = _ARROW_RE.search(text)
    if m:
        return m.start(), m.end(), m.group(1)
    return None


def _accumulate_statement(lines: List[str], start_idx: int):
    """
    Accumulate a potentially multi-line statement by tracking bracket depth.

    Returns ``(accumulated_text_stripped, next_index)``.
    """
    first = lines[start_idx]
    depth = sum(1 for c in first if c in '([{') - sum(1 for c in first if c in ')]}')

    if depth <= 0:
        return first.strip(), start_idx + 1

    parts = [first]
    idx = start_idx + 1
    while idx < len(lines) and depth > 0:
        line = lines[idx]
        depth += sum(1 for c in line if c in '([{') - sum(1 for c in line if c in ')]}')
        parts.append(line)
        idx += 1

    result = '\n'.join(parts)
    return result.strip(), idx


def _ensure_node(node_id, shape, label, class_name, diagram: Flowchart):
    """Register a node in the diagram if it doesn't already exist, or update if new shape info."""
    if node_id not in diagram.nodes:
        node = FlowchartNode(
            id=node_id,
            shape=shape or FlowchartNodeShape.RECTANGLE,
            label=label,
            class_name=class_name,
        )
        diagram.nodes[node_id] = node
    elif shape is not None:
        existing = diagram.nodes[node_id]
        if existing.label is None and label is not None:
            existing.label = label
            existing.shape = shape


def _parse_edges_for_model(line: str, diagram: Flowchart):
    """
    Best-effort parsing of an edge line into diagram.edges and diagram.nodes.

    This populates the structured model but does NOT affect the items list
    (edge lines are stored as raw text for rendering).
    """
    parts: List[str] = []
    arrows: List[str] = []
    labels: List[Optional[str]] = []
    remaining = line

    while True:
        arrow_info = _find_arrow(remaining)
        if arrow_info is None:
            parts.append(remaining.strip())
            break

        start, end, arrow_str = arrow_info
        parts.append(remaining[:start].strip())

        # Check for pipe label immediately after arrow: -->|text|
        after = remaining[end:]
        lbl = None
        lbl_match = re.match(r'\|([^|]*)\|', after)
        if lbl_match:
            lbl = lbl_match.group(1)
            after = after[lbl_match.end():]

        labels.append(lbl)
        arrows.append(arrow_str)
        remaining = after

    # Create edges between consecutive parts, handling & operator
    for i in range(len(arrows)):
        left_exprs = [n.strip() for n in parts[i].split('&')]
        right_exprs = [n.strip() for n in parts[i + 1].split('&')] if i + 1 < len(parts) else []

        for left_expr in left_exprs:
            if not left_expr:
                continue
            lid, lshape, llabel, _, lcls = _parse_node_expr(left_expr)
            if lid:
                _ensure_node(lid, lshape, llabel, lcls, diagram)

            for right_expr in right_exprs:
                if not right_expr:
                    continue
                rid, rshape, rlabel, _, rcls = _parse_node_expr(right_expr)
                if rid:
                    _ensure_node(rid, rshape, rlabel, rcls, diagram)

                if lid and rid:
                    edge = FlowchartEdge(
                        start=lid,
                        end=rid,
                        label=labels[i],
                        raw_arrow=arrows[i],
                    )
                    diagram.edges.append(edge)


def _parse_statement(line: str, diagram: Flowchart, context_items: list):
    """
    Parse a line as edge(s) or standalone node(s).
    Populates ``diagram.nodes``, ``diagram.edges``, and *context_items*.

    Edge lines are stored as raw text in *context_items* (preserving exact
    formatting for round-tripping), while still populating the structured
    model best-effort.
    """
    arrow_info = _find_arrow(line)

    if arrow_info is None:
        # Standalone node
        node_id, shape, label, _rest, class_name = _parse_node_expr(line)
        if node_id:
            node = FlowchartNode(
                id=node_id,
                shape=shape or FlowchartNodeShape.RECTANGLE,
                label=label,
                class_name=class_name,
            )
            diagram.nodes[node_id] = node
            context_items.append(node)
        return

    # Edge line — store raw for rendering, parse for model
    context_items.append(("raw", line))
    _parse_edges_for_model(line, diagram)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_flowchart(text: str, line_ending: LineEnding) -> Flowchart:
    """
    Parse a Mermaid flowchart from text.

    Args:
        text: Mermaid flowchart text (frontmatter already stripped)
        line_ending: Line ending style

    Returns:
        A Flowchart object
    """
    diagram = Flowchart(line_ending=line_ending)

    lines = text.split("\n")
    i = 0
    subgraph_stack: List[Tuple[FlowchartSubgraph, list]] = []

    while i < len(lines):
        line = lines[i].strip()

        if not line or line.startswith("%%"):
            i += 1
            continue

        # ---- Declaration line ----
        if is_declaration(line, "flowchart", "graph"):
            m = re.match(r'(flowchart|graph)\s*(TD|TB|BT|RL|LR)?\s*$', line, re.IGNORECASE)
            if m:
                diagram.keyword = m.group(1)
                raw_dir = m.group(2)
                diagram.raw_direction = raw_dir
                dir_str = (raw_dir or "TB").upper()
                if dir_str == "TD":
                    dir_str = "TB"
                try:
                    diagram.direction = FlowchartDirection(dir_str)
                except ValueError:
                    pass
            i += 1
            continue

        # Current context (top-level or innermost subgraph)
        current_items = subgraph_stack[-1][1] if subgraph_stack else diagram.items

        # ---- subgraph ----
        if line.lower().startswith("subgraph"):
            rest = line[len("subgraph"):].strip()
            sg_id = rest
            sg_title = None

            bracket_match = re.match(r'([\w-]+)\s*\[(.*?)\]', rest)
            if bracket_match:
                sg_id = bracket_match.group(1)
                sg_title = bracket_match.group(2)
            elif ' ' in rest:
                parts = rest.split(None, 1)
                sg_id = parts[0]
                sg_title = parts[1] if len(parts) > 1 else None

            sg = FlowchartSubgraph(id=sg_id, title=sg_title, raw_header=line)
            current_items.append(sg)
            if subgraph_stack:
                subgraph_stack[-1][0].subgraphs.append(sg)
            else:
                diagram.subgraphs.append(sg)

            subgraph_stack.append((sg, sg.items))
            i += 1
            continue

        # ---- end ----
        if line.lower() == "end":
            if subgraph_stack:
                subgraph_stack.pop()
            i += 1
            continue

        # ---- direction (inside subgraph) ----
        dir_match = re.match(r'direction\s+(TB|TD|BT|RL|LR)', line, re.IGNORECASE)
        if dir_match and subgraph_stack:
            dir_str = dir_match.group(1).upper()
            if dir_str == "TD":
                dir_str = "TB"
            try:
                subgraph_stack[-1][0].direction = FlowchartDirection(dir_str)
            except ValueError:
                pass
            current_items.append(("direction", dir_match.group(1)))
            i += 1
            continue

        # ---- Style / class / click statements (pass through as raw) ----
        if re.match(r'(classDef|class|style|linkStyle|click)\s', line, re.IGNORECASE):
            current_items.append(("raw", line))
            i += 1
            continue

        # ---- @{...} syntax (new-style nodes, edge styling — pass through) ----
        if '@{' in line:
            full_stmt, next_i = _accumulate_statement(lines, i)
            current_items.append(("raw", full_stmt.strip()))
            i = next_i
            continue

        # ---- Accumulate multi-line statement and parse ----
        full_stmt, next_i = _accumulate_statement(lines, i)
        _parse_statement(full_stmt, diagram, current_items)
        i = next_i

    return diagram

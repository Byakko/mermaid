"""
Flowchart renderer for converting Python Flowchart objects to Mermaid text.

Returns a list of content lines (no frontmatter, no comments -- those are
handled by python_to_mermaid.py using the raw input).
"""

from typing import List, Set

from mermaid.flowchart import (
    Flowchart,
    FlowchartNode,
    FlowchartNodeShape,
    FlowchartEdge,
    FlowchartSubgraph,
)


def _render_node(node: FlowchartNode) -> str:
    """Render a node with its shape definition."""
    text = node.get_label_text()
    prefix = FlowchartNodeShape.get_prefix(node.shape)
    suffix = FlowchartNodeShape.get_suffix(node.shape)
    result = f"{node.id}{prefix}{text}{suffix}"
    if node.class_name:
        result += f":::{node.class_name}"
    return result


def _render_node_ref(node_id: str, nodes: dict, rendered: Set[str]) -> str:
    """Render a node reference -- full definition on first occurrence, just ID after."""
    if node_id in rendered:
        return node_id
    rendered.add(node_id)
    node = nodes.get(node_id)
    if node and node.label is not None:
        return _render_node(node)
    return node_id


def _render_edge(edge: FlowchartEdge, nodes: dict, rendered: Set[str]) -> str:
    """Render an edge with inline node definitions on first occurrence."""
    left = _render_node_ref(edge.start, nodes, rendered)
    right = _render_node_ref(edge.end, nodes, rendered)

    arrow = edge.raw_arrow or "-->"

    if edge.label is not None:
        return f"{left} {arrow}|{edge.label}| {right}"
    else:
        return f"{left} {arrow} {right}"


def _render_items(items: list, nodes: dict, rendered: Set[str], indent: int) -> List[str]:
    """Render a list of ordered items with proper indentation."""
    lines: List[str] = []
    prefix = "    " * indent

    for item in items:
        if isinstance(item, FlowchartNode):
            rendered.add(item.id)
            lines.append(f"{prefix}{_render_node(item)}")
        elif isinstance(item, FlowchartEdge):
            lines.append(f"{prefix}{_render_edge(item, nodes, rendered)}")
        elif isinstance(item, FlowchartSubgraph):
            sg = item
            if sg.raw_header:
                lines.append(f"{prefix}{sg.raw_header}")
            elif sg.title:
                lines.append(f"{prefix}subgraph {sg.id}[{sg.title}]")
            else:
                lines.append(f"{prefix}subgraph {sg.id}")
            if sg.items:
                lines.extend(_render_items(sg.items, nodes, rendered, indent + 1))
            else:
                # Fallback for subgraphs without ordered items
                if sg.direction:
                    lines.append(f"{prefix}    direction {sg.direction.value}")
                for node in sg.nodes:
                    rendered.add(node.id)
                    lines.append(f"{prefix}    {_render_node(node)}")
                for edge in sg.edges:
                    lines.append(f"{prefix}    {_render_edge(edge, nodes, rendered)}")
            lines.append(f"{prefix}end")
        elif isinstance(item, tuple):
            if item[0] == "raw":
                lines.append(f"{prefix}{item[1]}")
            elif item[0] == "direction":
                lines.append(f"{prefix}direction {item[1]}")

    return lines


def render_flowchart(chart: Flowchart) -> List[str]:
    """
    Render a Flowchart object as a list of content lines.

    Frontmatter and comments are NOT included -- those are preserved
    from the raw input by python_to_mermaid.py.

    Args:
        chart: The Flowchart to render

    Returns:
        List of content lines
    """
    lines: List[str] = []

    # Directive
    if chart.directive:
        lines.append(str(chart.directive))

    # Declaration line
    keyword = getattr(chart, 'keyword', 'flowchart')
    dir_str = getattr(chart, 'raw_direction', None) or chart.direction.value
    lines.append(f"{keyword} {dir_str}")

    # Render body
    rendered: Set[str] = set()

    if chart.items:
        lines.extend(_render_items(chart.items, chart.nodes, rendered, 1))
    else:
        # Fallback for programmatically created charts without items
        for node in chart.nodes.values():
            rendered.add(node.id)
            lines.append(f"    {_render_node(node)}")
        for edge in chart.edges:
            lines.append(f"    {_render_edge(edge, chart.nodes, rendered)}")

    return lines

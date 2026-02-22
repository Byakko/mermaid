"""
Pie chart renderer for converting Python PieChart objects to Mermaid text.

Returns a list of content lines (no frontmatter, no comments — those are
handled by python_to_mermaid.py using the raw input).
"""

from typing import List

from mermaid import PieChart, PieSlice, ShowData


def render_pie_slice(pie_slice: PieSlice) -> str:
    """
    Render a single PieSlice as a Mermaid slice line.

    Args:
        pie_slice: The PieSlice to render

    Returns:
        Mermaid syntax string like: "Label" : 42.5
    """
    # Format value: use int if whole number, otherwise float
    if pie_slice.value == int(pie_slice.value):
        value_str = str(int(pie_slice.value))
    else:
        value_str = str(pie_slice.value)
    return f'"{pie_slice.label}" : {value_str}'


def render_pie_chart(chart: PieChart) -> List[str]:
    """
    Render a PieChart object as a list of content lines.

    Frontmatter and comments are NOT included — those are preserved
    from the raw input by python_to_mermaid.py.

    Args:
        chart: The PieChart to render

    Returns:
        List of content lines
    """
    lines: List[str] = []

    # Add directive if present
    if chart.directive:
        lines.append(str(chart.directive))

    # Build the declaration line(s)
    if chart.title_inline:
        # All on one line: pie [showData] [title ...]
        decl = chart.diagram_type.value
        if chart.show_data and chart.show_data != ShowData.NONE:
            decl += f" {chart.show_data.value}"
        if chart.title:
            decl += f" title {chart.title}"
        lines.append(decl)
    else:
        # Separate lines
        decl = chart.diagram_type.value
        if chart.show_data and chart.show_data != ShowData.NONE:
            decl += f" {chart.show_data.value}"
        lines.append(decl)
        if chart.title:
            lines.append(f"    title {chart.title}")

    # Add slices
    for pie_slice in chart.slices:
        lines.append(f"    {render_pie_slice(pie_slice)}")

    return lines

"""
Convert Python diagram objects back to Mermaid text.
"""

from mermaid import GanttChart
from mermaid.base import Diagram, DiagramType

from python_to_mermaid_converters.ptm_gantt import render_gantt


def python_to_mermaid(diagram: Diagram) -> str:
    """
    Convert a Python Mermaid diagram object to Mermaid text.

    Uses standalone converter functions for supported diagram types.
    Currently only gantt charts have a dedicated converter; other types
    fall back to the object's to_mermaid() method.

    Args:
        diagram: A Mermaid diagram object

    Returns:
        Mermaid diagram text
    """
    if isinstance(diagram, GanttChart):
        return render_gantt(diagram)

    # Fallback for diagram types without a dedicated converter yet
    return diagram.to_mermaid()

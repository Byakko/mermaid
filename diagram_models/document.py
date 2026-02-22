"""
document.py
===========
The top-level Document wrapper.

One document contains optional frontmatter and exactly one diagram.
As new diagram types are implemented, add them to the DiagramNode union.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from .gantt import GanttDiagram, GanttProjectMetadata


# Union of all supported diagram types.
# Extend this as new diagram types are added.
DiagramNode = Union[
    GanttDiagram,
    # FlowchartDiagram,   (future)
    # SequenceDiagram,    (future)
    # PieChartDiagram,    (future)
    # TimelineDiagram,    (future)
]


@dataclass
class Document:
    """
    Top-level document.  Wraps optional frontmatter and exactly one diagram.

    frontmatter: raw YAML text between --- markers, stored unparsed.
    version:     schema version string for forward compatibility.
    """
    diagram: DiagramNode
    version: Optional[str] = None
    frontmatter: Optional[str] = None
    ganttproject: Optional[GanttProjectMetadata] = None

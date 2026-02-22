"""
Convert diagram_models Python objects to a GanttProject .gan XML file.
"""

import sys
from typing import Optional

from diagram_models import Document
from diagram_models.gantt import GanttDiagram

from python_to_gan_converters.ptg_gantt import render_gantt_project


# Maps diagram model types to their renderer functions.
_RENDERERS = {
    GanttDiagram: render_gantt_project,
}


def python_to_gan(doc: Document) -> Optional[str]:
    """
    Convert a diagram_models Document to a GanttProject .gan XML string.

    Args:
        doc: A Document object

    Returns:
        .gan XML text, or None if no renderer is available.
    """
    renderer = _RENDERERS.get(type(doc.diagram))
    if renderer is None:
        print(
            f"Warning: No renderer for diagram type '{type(doc.diagram).__name__}'",
            file=sys.stderr,
        )
        return None

    try:
        return renderer(doc.diagram, doc.ganttproject)
    except Exception as e:
        print(f"Warning: Error rendering .gan: {e}", file=sys.stderr)
        return None

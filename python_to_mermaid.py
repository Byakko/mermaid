"""
Convert diagram_models Python objects to Mermaid text.
"""

import sys
from typing import Optional

from diagram_models import Document
from diagram_models.gantt import GanttDiagram

from python_to_mermaid_converters.ptm_gantt import render_gantt


# Maps diagram model types to their renderer functions.
_RENDERERS = {
    GanttDiagram: render_gantt,
}


def python_to_mermaid(doc: Document) -> Optional[str]:
    """
    Convert a diagram_models Document to Mermaid text.

    Frontmatter, comments, and directives are all encoded in the Document
    and rendered directly — no raw input preservation needed.

    Args:
        doc: A Document object

    Returns:
        Mermaid diagram text, or None if no renderer is available.
    """
    renderer = _RENDERERS.get(type(doc.diagram))
    if renderer is None:
        print(
            f"Warning: No renderer for diagram type '{type(doc.diagram).__name__}'",
            file=sys.stderr,
        )
        return None

    lines = []

    if doc.frontmatter is not None:
        lines.append("---")
        lines.append(doc.frontmatter)
        lines.append("---")

    lines.extend(renderer(doc.diagram))

    return "\n".join(lines)

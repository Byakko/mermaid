"""
Convert diagram_models Python objects to AST JSON.
"""

import json
import sys
from typing import Optional

from diagram_models import Document
from diagram_models.gantt import GanttDiagram, GanttProjectMetadata

from python_to_json_converters.ptj_gantt import render_gantt


# Maps diagram model types to their renderer functions.
# Each renderer receives the diagram object and returns a plain dict.
_RENDERERS = {
    GanttDiagram: render_gantt,
}


def python_to_json(doc: Document, indent: int = 2) -> Optional[str]:
    """
    Convert a diagram_models Document to AST JSON text.

    Args:
        doc:    A Document object
        indent: JSON indentation level (default 2)

    Returns:
        JSON string conforming to schema/schema.graphql, or None if conversion fails.
    """
    renderer = _RENDERERS.get(type(doc.diagram))
    if renderer is None:
        print(
            f"Warning: No renderer for diagram type '{type(doc.diagram).__name__}'",
            file=sys.stderr,
        )
        return None

    try:
        diagram_dict = renderer(doc.diagram)
        result = {
            "version": doc.version,
            "frontmatter": doc.frontmatter,
            "diagram": diagram_dict,
        }
        if doc.ganttproject is not None:
            gp = doc.ganttproject
            result["ganttproject"] = {
                "kind": "GANTT_PROJECT_METADATA",
                "name": gp.name,
                "locale": gp.locale,
                "version": gp.version,
                "working_days": [d.value for d in gp.working_days],
            }
        return json.dumps(result, indent=indent)
    except Exception as e:
        print(f"Warning: Error rendering diagram: {e}", file=sys.stderr)
        return None

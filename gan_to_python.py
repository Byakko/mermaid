"""
Convert a GanttProject .gan file to diagram_models Python objects.
"""

import sys
from typing import Optional

from diagram_models import Document
from gan_to_python_converters.gtp_gantt import parse_gantt_project


def gan_to_python(text: str) -> Optional[Document]:
    """
    Parse a GanttProject .gan XML string into a diagram_models Document.

    Args:
        text: Raw .gan XML text

    Returns:
        A Document object, or None if parsing fails.
    """
    try:
        return parse_gantt_project(text)
    except Exception as e:
        print(f"Warning: Error parsing .gan file: {e}", file=sys.stderr)
        return None

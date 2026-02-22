"""
Convert Mermaid diagram text to diagram_models Python objects.
"""

import sys
from typing import Optional

from diagram_models import Document
from mermaid_to_python_converters.mtp_gantt import parse_gantt


# Maps diagram type keywords to their parser functions.
_PARSERS = {
    "gantt": parse_gantt,
}


def _extract_frontmatter(text: str) -> tuple[Optional[str], str]:
    """
    Strip YAML frontmatter from the start of the text.

    Returns (content_between_delimiters, remaining_text).
    Returns (None, original_text) if no frontmatter is present.
    """
    lines = text.split("\n")
    first_idx = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first_idx is None or lines[first_idx].strip() != "---":
        return None, text

    close_idx = next(
        (i for i in range(first_idx + 1, len(lines)) if lines[i].strip() == "---"),
        None,
    )
    if close_idx is None:
        return None, text

    content = "\n".join(lines[first_idx + 1 : close_idx]).strip()
    remaining = "\n".join(lines[:first_idx] + lines[close_idx + 1 :])
    return content, remaining


def _detect_diagram_type(text: str) -> Optional[str]:
    """Return the diagram type keyword from the first content line."""
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("%%"):
            return line.split()[0].lower()
    return None


def mermaid_to_python(text: str) -> Optional[Document]:
    """
    Parse Mermaid text into a diagram_models Document.

    Args:
        text: Raw Mermaid diagram text (may include frontmatter)

    Returns:
        A Document object, or None if the diagram type is unsupported.
    """
    frontmatter, body = _extract_frontmatter(text)

    diagram_type = _detect_diagram_type(body)
    parser = _PARSERS.get(diagram_type)

    if parser is None:
        print(f"Warning: Unknown or unsupported diagram type '{diagram_type}'", file=sys.stderr)
        return None

    try:
        diagram = parser(body)
        return Document(diagram=diagram, frontmatter=frontmatter, version="1.0")
    except Exception as e:
        print(f"Warning: Error parsing {diagram_type} diagram: {e}", file=sys.stderr)
        return None

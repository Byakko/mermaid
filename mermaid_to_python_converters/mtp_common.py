"""
Common parsing primitives for converting Mermaid text to Python objects.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Frontmatter Extraction
# =============================================================================

def extract_frontmatter(text: str) -> Tuple[Optional[str], str]:
    """
    Extract YAML frontmatter from the beginning of Mermaid text.

    Frontmatter is delimited by ``---`` lines at the start of the text.
    The raw text between the delimiters is preserved as-is (including
    indentation and nested structure) so it can be round-tripped without
    needing a full YAML parser.

    Args:
        text: Raw Mermaid diagram text

    Returns:
        Tuple of (raw frontmatter string including ``---`` delimiters, or
        None if no frontmatter found; remaining text with frontmatter stripped)
    """
    lines = text.split("\n")

    # Find the first non-empty line
    first_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_idx = i
            break

    if first_idx is None or lines[first_idx].strip() != "---":
        return None, text

    # Look for closing ---
    closing_idx = None
    for i in range(first_idx + 1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break

    if closing_idx is None:
        return None, text

    # Preserve the raw frontmatter block (including --- delimiters)
    raw = "\n".join(lines[first_idx : closing_idx + 1])

    remaining = "\n".join(lines[:first_idx] + lines[closing_idx + 1 :])
    return raw, remaining


# =============================================================================
# Diagram Type Detection
# =============================================================================

def detect_diagram_type(text: str) -> str:
    """
    Detect the type of Mermaid diagram from the text.

    Args:
        text: Mermaid diagram text

    Returns:
        Diagram type identifier (e.g., "flowchart", "sequence", "class")
    """
    # Strip frontmatter before detection
    _, text = extract_frontmatter(text)

    # Normalize text for detection
    lines = [line.strip() for line in text.strip().split("\n")]
    first_content_line = next((line for line in lines if line and not line.startswith("%%")), "")

    # Pattern matching for diagram type declarations
    patterns = {
        "flowchart": r"^(flowchart|graph)\s*(TD|TB|BT|RL|LR)?\s*$",
        "sequence": r"^sequenceDiagram\s*$",
        "class": r"^classDiagram\s*$",
        "state": r"^stateDiagram(-v2)?\s*$",
        "er": r"^erDiagram\s*$",
        "journey": r"^journey\s*$",
        "gantt": r"^gantt\s*$",
        "pie": r"^pie(\s+.*)?$",
        "mindmap": r"^mindmap\s*$",
        "git": r"^gitGraph\s*$",
        "quadrant": r"^quadrantChart\s*$",
        "timeline": r"^timeline\s*$",
        "c4": r"^C4(Context|Container|Deployment|Component)\s*$",
        "zenuml": r"^zenuml\s*$",
        "sankey": r"^sankey-beta\s*$",
        "xychart": r"^xychart-beta\s*$",
        "block": r"^block(beta)?\s*:\s*.*$",
        "packet": r"^packet\s*$",
        "kanban": r"^kanban\s*$",
        "architecture": r"^architecture\s*$",
        "radar": r"^radar\s*$",
        "treemap": r"^treemap\s*$",
        "requirement": r"^requirementDiagram\s*$",
    }

    first_line_lower = first_content_line.lower()

    for diagram_type, pattern in patterns.items():
        if re.match(pattern, first_line_lower, re.IGNORECASE):
            return diagram_type

    # Default: try to detect from content
    if "-->" in text or "==>" in text:
        return "flowchart"
    if "->>" in text or "-->>" in text:
        return "sequence"

    return "unknown"


# =============================================================================
# Small Helpers
# =============================================================================

def is_skip_line(line: str) -> bool:
    """Return True if *line* is empty or a Mermaid comment (``%%``)."""
    return not line or line.startswith("%%")


def strip_quotes(s: str) -> str:
    """Remove surrounding double-quotes from *s*, if present."""
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def strip_keyword(line: str, keyword: str) -> str:
    """Return the text after *keyword* at the start of *line*, stripped."""
    return line[len(keyword):].strip()


def split_colon_parts(line: str) -> List[str]:
    """Split *line* on ``':'`` and strip each part."""
    return [p.strip() for p in line.split(':')]


def accumulate_brackets(
    lines: List[str],
    start_idx: int,
    open_chars: str = '({[',
    close_chars: str = ')}]',
    joiner: str = ' ',
) -> Tuple[str, int]:
    """
    Accumulate a potentially multi-line statement by tracking bracket depth.

    Args:
        joiner: String used to join accumulated lines (``' '`` for most
                parsers; ``'\\n'`` for flowchart to preserve multi-line labels).

    Returns ``(accumulated_text_stripped, next_index)``.
    """
    first = lines[start_idx]
    depth = sum(1 for c in first if c in open_chars) - sum(1 for c in first if c in close_chars)

    if depth <= 0:
        return first.strip(), start_idx + 1

    parts = [first]
    idx = start_idx + 1
    while idx < len(lines) and depth > 0:
        line = lines[idx]
        depth += sum(1 for c in line if c in open_chars) - sum(1 for c in line if c in close_chars)
        parts.append(line)
        idx += 1

    if joiner == ' ':
        return joiner.join(p.strip() for p in parts), idx
    return joiner.join(parts).strip(), idx


# =============================================================================
# Reusable Parsing Primitives
# =============================================================================

def try_parse_directive(line: str, keyword: str) -> Optional[str]:
    """
    Match a directive line like 'keyword value' (case-insensitive).

    Args:
        line: Line to check
        keyword: Directive keyword (e.g. "title", "dateFormat", "excludes")

    Returns:
        Captured value string, or None if no match
    """
    match = re.match(rf'{keyword}\s+(.+)', line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def try_parse_section(line: str) -> Optional[str]:
    """
    Match a 'section SectionName' line (case-insensitive).

    Returns:
        Section name, or None if no match
    """
    match = re.match(r'section\s+(.+)', line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def is_declaration(line: str, *keywords: str) -> bool:
    """
    Check if a line starts with any of the given keywords (case-insensitive).

    Args:
        line: Line to check
        keywords: One or more keywords to match against

    Returns:
        True if the line starts with any keyword
    """
    line_lower = line.lower()
    return any(line_lower.startswith(kw.lower()) for kw in keywords)


# Mapping from day.js format tokens to Python strptime tokens
_DAYJS_TO_STRPTIME = {
    'YYYY': '%Y',
    'YY': '%y',
    'MMMM': '%B',
    'MMM': '%b',
    'MM': '%m',
    'M': '%-m',
    'DD': '%d',
    'D': '%-d',
    'HH': '%H',
    'hh': '%I',
    'mm': '%M',
    'ss': '%S',
    'SSS': '%f',
    'A': '%p',
    'a': '%p',
}


def dayjs_to_strptime(date_format: str) -> str:
    """
    Convert a day.js format string to a Python strptime format string.

    Args:
        date_format: day.js format string (e.g. "YYYY-MM-DD", "DD/MM/YYYY", "HH:mm")

    Returns:
        Python strptime format string (e.g. "%Y-%m-%d", "%d/%m/%Y", "%H:%M")
    """
    result = date_format
    # Replace longest tokens first to avoid partial matches
    for dayjs_token, strptime_token in _DAYJS_TO_STRPTIME.items():
        result = result.replace(dayjs_token, strptime_token)
    return result


def is_date(s: str, strptime_format: Optional[str] = None) -> bool:
    """
    Check if a string matches a date format.

    Args:
        s: String to check
        strptime_format: Python strptime format string. If None, falls back to
                         matching YYYY-MM-DD pattern.
    """
    if strptime_format is not None:
        try:
            datetime.strptime(s, strptime_format)
            return True
        except ValueError:
            return False
    return re.match(r'^\d{4}-\d{2}-\d{2}$', s) is not None


def is_duration(s: str) -> bool:
    """Check if a string matches a duration pattern like 3d, 24h, 1w."""
    return re.match(r'^\d+[dwmyh]?$', s.lower()) is not None


def is_task_ref(s: str) -> bool:
    """Check if a string is a task reference (after ... or until ...)."""
    lower = s.lower()
    return lower.startswith('after ') or lower.startswith('until ')


# =============================================================================
# Color Parsing
# =============================================================================

def try_parse_color(text: str) -> Optional['Color']:
    """
    Try to parse a color value from text.

    Supports rgb(...), rgba(...), hex (#...), and named colors.

    Args:
        text: Text that may contain a color value

    Returns:
        A Color object, or None if no color pattern matched
    """
    from mermaid.base import Color

    text = text.strip()

    # rgb(r, g, b)
    m = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', text)
    if m:
        return Color(rgb=(int(m.group(1)), int(m.group(2)), int(m.group(3))))

    # rgba(r, g, b, a)
    m = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)', text)
    if m:
        return Color(rgba=(int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4))))

    # Hex color
    m = re.match(r'#[0-9a-fA-F]{3,8}', text)
    if m:
        return Color(hex=m.group(0))

    # Named color (simple word)
    m = re.match(r'[a-zA-Z]+', text)
    if m:
        return Color(name=m.group(0))

    return None


# =============================================================================
# Block Keyword Matching
# =============================================================================

def try_parse_block_open(line: str, keyword: str) -> Optional[str]:
    """
    Match a block-opening line like 'keyword Description text'.

    Used for sequence diagram constructs (loop, alt, opt, par, critical,
    break, rect, box) and potentially other diagram types with similar
    ``keyword [description]`` ... ``end`` block syntax.

    Args:
        line: Line to check
        keyword: Block keyword (e.g. "loop", "alt", "opt")

    Returns:
        The description text after the keyword, or None if no match.
        Returns empty string if keyword matched with no description.
    """
    m = re.match(rf'{keyword}(?:\s+(.*))?$', line, re.IGNORECASE)
    if m:
        return (m.group(1) or '').strip()
    return None

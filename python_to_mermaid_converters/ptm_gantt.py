"""
ptm2_gantt.py
=============
Render a diagram_models GanttDiagram to Mermaid text lines.
"""

from __future__ import annotations

import re
from datetime import date, time
from typing import List

from diagram_models.common import (
    AbsoluteDate,
    Comment,
    ConstraintRef,
    DependencyType,
    ImplicitEnd,
    ImplicitStart,
    TimeOfDay,
)
from diagram_models.gantt import (
    GanttDiagram,
    GanttDirective,
    GanttDirectiveName,
    GanttElementType,
    GanttSection,
    GanttTask,
)


# ─────────────────────────────────────────────────────────────────────────────
# Directive name → Mermaid keyword
# ─────────────────────────────────────────────────────────────────────────────

_DIRECTIVE_KEYWORDS = {
    GanttDirectiveName.TITLE:         "title",
    GanttDirectiveName.DATE_FORMAT:   "dateFormat",
    GanttDirectiveName.AXIS_FORMAT:   "axisFormat",
    GanttDirectiveName.TICK_INTERVAL: "tickInterval",
    GanttDirectiveName.EXCLUDES:      "excludes",
    GanttDirectiveName.WEEKEND:       "weekend",
}


# ─────────────────────────────────────────────────────────────────────────────
# Date formatting: day.js tokens → Python strftime
# ─────────────────────────────────────────────────────────────────────────────

_DAYJS_TOKENS = [
    ("YYYY", "%Y"),
    ("MM",   "%m"),   # month (uppercase M)
    ("DD",   "%d"),
    ("HH",   "%H"),
    ("mm",   "%M"),   # minute (lowercase m)
    ("ss",   "%S"),
]
_DAYJS_PATTERN = re.compile("|".join(re.escape(k) for k, _ in _DAYJS_TOKENS))
_DAYJS_MAP = dict(_DAYJS_TOKENS)


def _dayjs_to_strftime(fmt: str) -> str:
    return _DAYJS_PATTERN.sub(lambda m: _DAYJS_MAP[m.group()], fmt)


def _format_date_value(iso_str: str, date_format: str) -> str:
    """Format an ISO 8601 date or time string using the diagram's dateFormat."""
    strfmt = _dayjs_to_strftime(date_format)
    if "H" in date_format or "mm" in date_format:
        return time.fromisoformat(iso_str).strftime(strfmt)
    return date.fromisoformat(iso_str).strftime(strfmt)


# ─────────────────────────────────────────────────────────────────────────────
# Duration: ISO 8601 → Mermaid shorthand
# ─────────────────────────────────────────────────────────────────────────────

_DUR_PATTERNS = [
    (re.compile(r"^P(\d+)W$"),  "{0}w"),
    (re.compile(r"^P(\d+)D$"),  "{0}d"),
    (re.compile(r"^PT(\d+)H$"), "{0}h"),
    (re.compile(r"^PT(\d+)M$"), "{0}m"),
    (re.compile(r"^PT(\d+)S$"), "{0}s"),
]


def _iso_dur_to_mermaid(iso: str) -> str:
    for pattern, template in _DUR_PATTERNS:
        m = pattern.match(iso)
        if m:
            return template.format(m.group(1))
    raise ValueError(f"Cannot convert ISO duration to Mermaid: {iso!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Start / End value rendering
# ─────────────────────────────────────────────────────────────────────────────

def _render_start_value(start, date_format: str) -> str:
    if isinstance(start, (AbsoluteDate, TimeOfDay)):
        return _format_date_value(start.value, date_format)
    if isinstance(start, ConstraintRef) and start.dependency_type == DependencyType.FS:
        return "after " + " ".join(start.task_ids)
    raise ValueError(f"Cannot render start condition: {start!r}")


def _render_end_value(end, date_format: str) -> str:
    if isinstance(end, (AbsoluteDate, TimeOfDay)):
        return _format_date_value(end.value, date_format)
    if isinstance(end, ConstraintRef) and end.dependency_type == DependencyType.SF:
        return "until " + " ".join(end.task_ids)
    raise ValueError(f"Cannot render end condition: {end!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Element rendering
# ─────────────────────────────────────────────────────────────────────────────

def _render_task(task: GanttTask, date_format: str, indent: str) -> str:
    tokens = []

    # Element type keyword (TASK is implicit — no keyword needed)
    if task.element_type == GanttElementType.MILESTONE:
        tokens.append("milestone")
    elif task.element_type == GanttElementType.VERT:
        tokens.append("vert")

    # Status keywords
    for s in task.statuses:
        tokens.append(s.value.lower())

    # Optional task ID
    if task.id is not None:
        tokens.append(task.id)

    # Start (omitted for ImplicitStart)
    if not isinstance(task.start, ImplicitStart):
        tokens.append(_render_start_value(task.start, date_format))

    # Duration (takes precedence; emitted when present)
    if task.duration is not None:
        tokens.append(_iso_dur_to_mermaid(task.duration))
    elif not isinstance(task.end, ImplicitEnd):
        # End constraint (only when no duration; omitted for ImplicitEnd)
        tokens.append(_render_end_value(task.end, date_format))

    return f"{indent}{task.name} :{', '.join(tokens)}"


def _render_comment(comment: Comment, indent: str) -> str:
    return f"{indent}%% {comment.text}"


# ─────────────────────────────────────────────────────────────────────────────
# Top-level render
# ─────────────────────────────────────────────────────────────────────────────

def _get_date_format(diagram: GanttDiagram) -> str:
    for entry in diagram.header:
        if isinstance(entry, GanttDirective) and entry.name == GanttDirectiveName.DATE_FORMAT:
            return entry.value
    return "YYYY-MM-DD"


def render_gantt(diagram: GanttDiagram) -> List[str]:
    """
    Render a GanttDiagram object as a list of Mermaid text lines.

    Args:
        diagram: The GanttDiagram to render

    Returns:
        List of lines starting with "gantt".
    """
    lines: List[str] = ["gantt"]
    date_format = _get_date_format(diagram)

    # Header: directives and comments in source order
    for entry in diagram.header:
        if isinstance(entry, GanttDirective):
            keyword = _DIRECTIVE_KEYWORDS[entry.name]
            lines.append(f"    {keyword} {entry.value}")
        elif isinstance(entry, Comment):
            lines.append(_render_comment(entry, "    "))

    # Body: sections, sectionless tasks, and comments
    for element in diagram.elements:
        if isinstance(element, GanttSection):
            lines.append(f"    section {element.name}")
            for item in element.elements:
                if isinstance(item, GanttTask):
                    lines.append(_render_task(item, date_format, "        "))
                elif isinstance(item, Comment):
                    lines.append(_render_comment(item, "        "))
        elif isinstance(element, GanttTask):
            lines.append(_render_task(element, date_format, "    "))
        elif isinstance(element, Comment):
            lines.append(_render_comment(element, "    "))

    return lines

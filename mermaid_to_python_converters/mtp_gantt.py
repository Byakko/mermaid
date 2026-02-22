"""
mtp2_gantt.py
=============
Parse Mermaid gantt text into diagram_models objects.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from diagram_models.common import (
    AbsoluteDate,
    Comment,
    ConstraintRef,
    DependencyCombination,
    DependencyType,
    ImplicitEnd,
    ImplicitStart,
    RelativeDuration,
    TimeOfDay,
)
from diagram_models.gantt import (
    GanttDiagram,
    GanttDirective,
    GanttDirectiveName,
    GanttElementType,
    GanttSection,
    GanttTask,
    GanttTaskStatus,
)


# ─────────────────────────────────────────────────────────────────────────────
# Directive keyword → enum mapping
# ─────────────────────────────────────────────────────────────────────────────

_KEYWORD_TO_DIRECTIVE = {
    "title":        GanttDirectiveName.TITLE,
    "dateformat":   GanttDirectiveName.DATE_FORMAT,
    "axisformat":   GanttDirectiveName.AXIS_FORMAT,
    "tickinterval": GanttDirectiveName.TICK_INTERVAL,
    "excludes":     GanttDirectiveName.EXCLUDES,
    "weekend":      GanttDirectiveName.WEEKEND,
}

_STATUS_KEYWORDS      = {"done", "active", "crit"}
_ELEMENT_TYPE_KEYWORDS = {"milestone", "vert"}

_DUR_RE      = re.compile(r"^\d+[smhdw]$", re.IGNORECASE)
_TASK_REF_RE = re.compile(r"^(after|until)\s+(.+)", re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────────────
# day.js format → Python strptime
# ─────────────────────────────────────────────────────────────────────────────

_DAYJS_TOKENS = [
    ("YYYY", "%Y"), ("MM", "%m"), ("DD", "%d"),
    ("HH",   "%H"), ("mm", "%M"), ("ss", "%S"),
]
_DAYJS_PATTERN = re.compile("|".join(re.escape(k) for k, _ in _DAYJS_TOKENS))
_DAYJS_MAP = dict(_DAYJS_TOKENS)


def _dayjs_to_strptime(fmt: str) -> str:
    return _DAYJS_PATTERN.sub(lambda m: _DAYJS_MAP[m.group()], fmt)


def _is_time_format(date_format: str) -> bool:
    """True if the dateFormat uses hours/minutes rather than calendar dates."""
    return "H" in date_format


# ─────────────────────────────────────────────────────────────────────────────
# Value classification helpers
# ─────────────────────────────────────────────────────────────────────────────

# Common date patterns to try when no dateFormat directive was found
_FALLBACK_DATE_FMTS = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"]


def _is_date(s: str, strptime_fmt: Optional[str]) -> bool:
    fmts = [strptime_fmt] if strptime_fmt else _FALLBACK_DATE_FMTS
    for fmt in fmts:
        try:
            datetime.strptime(s, fmt)
            return True
        except ValueError:
            continue
    return False


def _is_duration(s: str) -> bool:
    return bool(_DUR_RE.match(s))


def _is_task_ref(s: str) -> bool:
    return bool(_TASK_REF_RE.match(s))


# ─────────────────────────────────────────────────────────────────────────────
# Value conversion helpers
# ─────────────────────────────────────────────────────────────────────────────

def _mermaid_dur_to_iso(s: str) -> str:
    """Convert a Mermaid duration shorthand (30d, 24h, 2m …) to ISO 8601."""
    m = re.match(r"^(\d+)([smhdw])$", s, re.IGNORECASE)
    if not m:
        raise ValueError(f"Cannot parse Mermaid duration: {s!r}")
    n, unit = m.group(1), m.group(2).lower()
    return {"w": f"P{n}W", "d": f"P{n}D", "h": f"PT{n}H",
            "m": f"PT{n}M", "s": f"PT{n}S"}[unit]


def _mermaid_date_to_iso(s: str, strptime_fmt: Optional[str], is_time: bool) -> str:
    """
    Parse a Mermaid date/time string and return an ISO 8601 string.

    For time-based formats (HH:mm) produces HH:MM:SS.
    For date-based formats produces YYYY-MM-DD.
    """
    fmts = [strptime_fmt] if strptime_fmt else _FALLBACK_DATE_FMTS
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%H:%M:%S") if is_time else dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s   # last resort: store as-is


# ─────────────────────────────────────────────────────────────────────────────
# Task line parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_task_line(
    line: str,
    strptime_fmt: Optional[str],
    is_time: bool,
) -> Optional[GanttTask]:
    """
    Parse a Mermaid task line of the form:
        Name : [keywords,] [id,] [start,] end

    Returns a GanttTask, or None if the line has no colon.
    """
    if ":" not in line:
        return None

    name, _, rest = line.partition(":")
    name = name.strip()
    parts = [p.strip() for p in rest.split(",")]

    # ── First pass: consume leading element-type and status keywords ──────────
    element_type = GanttElementType.TASK
    statuses: list[GanttTaskStatus] = []
    start_idx = len(parts)

    for i, part in enumerate(parts):
        lower = part.lower()
        if lower in _ELEMENT_TYPE_KEYWORDS:
            element_type = GanttElementType[lower.upper()]
        elif lower in _STATUS_KEYWORDS:
            statuses.append(GanttTaskStatus[lower.upper()])
        else:
            start_idx = i
            break

    # ── Second pass: classify remaining parts ─────────────────────────────────
    task_id = None
    raw_start = None   # ("date", str) | ("after", [str])
    raw_end   = None   # ("date", str) | ("until", [str])
    raw_dur   = None   # str (Mermaid shorthand)

    for part in parts[start_idx:]:
        if not part:
            continue

        if _is_duration(part):
            raw_dur = part

        elif _is_task_ref(part):
            m = _TASK_REF_RE.match(part)
            verb = m.group(1).lower()
            ids  = m.group(2).strip().split()
            if verb == "after":
                raw_start = ("after", ids)
            else:
                raw_end = ("until", ids)

        elif _is_date(part, strptime_fmt):
            if raw_start is None:
                raw_start = ("date", part)
            else:
                raw_end = ("date", part)

        elif task_id is None:
            task_id = part

    # ── Build typed start / end conditions ────────────────────────────────────
    if raw_start is None:
        start = ImplicitStart()
    elif raw_start[0] == "after":
        start = ConstraintRef(
            task_ids=raw_start[1],
            dependency_type=DependencyType.FS,
            combination=DependencyCombination.ALL_OF,
        )
    else:  # date
        iso = _mermaid_date_to_iso(raw_start[1], strptime_fmt, is_time)
        start = TimeOfDay(iso) if is_time else AbsoluteDate(iso)

    if raw_end is not None and raw_end[0] == "until":
        end = ConstraintRef(
            task_ids=raw_end[1],
            dependency_type=DependencyType.SF,
            combination=DependencyCombination.ALL_OF,
        )
    elif raw_end is not None:  # date end
        iso = _mermaid_date_to_iso(raw_end[1], strptime_fmt, is_time)
        end = TimeOfDay(iso) if is_time else AbsoluteDate(iso)
    elif raw_dur is not None:
        end = RelativeDuration(_mermaid_dur_to_iso(raw_dur))
    else:
        end = ImplicitEnd()

    return GanttTask(
        name=name,
        element_type=element_type,
        statuses=statuses,
        start=start,
        end=end,
        id=task_id,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Top-level parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_gantt(text: str) -> GanttDiagram:
    """
    Parse Mermaid gantt text (frontmatter already stripped) into a GanttDiagram.

    Directives and preamble comments go into diagram.header in source order.
    Sections, sectionless tasks, and body comments go into diagram.elements.
    """
    diagram = GanttDiagram()
    current_section: Optional[GanttSection] = None
    in_body = False          # True once we've seen the first section or task
    strptime_fmt: Optional[str] = None
    is_time = False

    for raw_line in text.split("\n"):
        line = raw_line.strip()

        if not line:
            continue

        # "gantt" declaration line
        if line.lower() == "gantt":
            continue

        # Stand-alone comment  (%% text)
        if line.startswith("%%"):
            node = Comment(text=line[2:].strip())
            if in_body:
                target = current_section.elements if current_section else diagram.elements
                target.append(node)
            else:
                diagram.header.append(node)
            continue

        # Section header
        m = re.match(r"section\s+(.+)", line, re.IGNORECASE)
        if m:
            in_body = True
            current_section = GanttSection(name=m.group(1).strip())
            diagram.elements.append(current_section)
            continue

        # Directive (only recognised before the body begins)
        if not in_body:
            matched = False
            for keyword, directive_name in _KEYWORD_TO_DIRECTIVE.items():
                m = re.match(rf"{keyword}\s+(.+)", line, re.IGNORECASE)
                if m:
                    value = m.group(1).strip()
                    diagram.header.append(GanttDirective(name=directive_name, value=value))
                    if directive_name == GanttDirectiveName.DATE_FORMAT:
                        strptime_fmt = _dayjs_to_strptime(value)
                        is_time = _is_time_format(value)
                    matched = True
                    break
            if matched:
                continue

        # Task line (must contain a colon)
        if ":" in line:
            in_body = True
            task = _parse_task_line(line, strptime_fmt, is_time)
            if task is not None:
                target = current_section.elements if current_section else diagram.elements
                target.append(task)

    return diagram

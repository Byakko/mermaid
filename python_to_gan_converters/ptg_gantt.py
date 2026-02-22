"""
ptg_gantt.py
============
Render a diagram_models GanttDiagram (+ optional GanttProjectMetadata) to a
GanttProject .gan XML string.

GanttProject .gan dependency storage
--------------------------------------
Dependencies are stored on the PREDECESSOR task as <depend> children:

    <task id="Y" ...>
        <depend id="X" type="T" difference="D" hardness="Strong"/>
    </task>

means: task X depends on task Y  (Y is predecessor, X is successor).

This is the inverse of how our AST stores them: a ConstraintRef on task X's
start/end lists Y as a task_id (Y is predecessor, X owns the ref).

Rendering therefore requires a two-pass approach:
  1. Build a predecessor→successors map by scanning every task's start/end.
  2. When emitting each task element, append the relevant <depend> children.

Dependency type integers (GanttProject):
    1 = SS  Start-to-Start
    2 = FS  Finish-to-Start  (most common)
    3 = FF  Finish-to-Finish
    4 = SF  Start-to-Finish

Start date resolution
----------------------
GanttProject requires a `start` date attribute on every task.  When a task's
start condition is an AbsoluteDate this is trivial.  When it is a ConstraintRef
a simple topological scheduler computes the date from predecessor start/end
dates.  Tasks that cannot be resolved (cycles, missing predecessors) fall back
to 2000-01-01.
"""

import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Optional

from diagram_models.common import (
    AbsoluteDate,
    ConstraintRef,
    DependencyType,
)
from diagram_models.gantt import (
    DayOfWeek,
    GanttDiagram,
    GanttDirective,
    GanttDirectiveName,
    GanttElementType,
    GanttProjectMetadata,
    GanttTask,
    GanttTaskStatus,
)


# ─────────────────────────────────────────────────────────────────────────────
# Constants and lookup tables
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_VERSION = "3.3.3322"
_DEFAULT_LOCALE  = "en"
_FALLBACK_DATE   = date(2000, 1, 1)

# DependencyType → GanttProject integer
_DEP_TYPE_INT: dict[DependencyType, int] = {
    DependencyType.SS: 1,
    DependencyType.FS: 2,
    DependencyType.FF: 3,
    DependencyType.SF: 4,
}

# DayOfWeek → Python weekday() integer (0 = Monday)
_DAY_WEEKDAY: dict[DayOfWeek, int] = {
    DayOfWeek.MON: 0,
    DayOfWeek.TUE: 1,
    DayOfWeek.WED: 2,
    DayOfWeek.THU: 3,
    DayOfWeek.FRI: 4,
    DayOfWeek.SAT: 5,
    DayOfWeek.SUN: 6,
}

_DEFAULT_WORKING_WEEKDAYS = {0, 1, 2, 3, 4}  # Mon-Fri

# Fixed boilerplate blocks
_TASK_PROPERTIES = [
    ("tpd0", "type",         "default", "icon"),
    ("tpd1", "priority",     "default", "icon"),
    ("tpd2", "info",         "default", "icon"),
    ("tpd3", "name",         "default", "text"),
    ("tpd4", "begindate",    "default", "date"),
    ("tpd5", "enddate",      "default", "date"),
    ("tpd6", "duration",     "default", "int"),
    ("tpd7", "completion",   "default", "int"),
    ("tpd8", "coordinator",  "default", "text"),
    ("tpd9", "predecessorsr","default", "text"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Date / duration helpers
# ─────────────────────────────────────────────────────────────────────────────

def _working_weekdays(ganttproject: Optional[GanttProjectMetadata]) -> set[int]:
    if ganttproject and ganttproject.working_days:
        return {_DAY_WEEKDAY[d] for d in ganttproject.working_days}
    return _DEFAULT_WORKING_WEEKDAYS


def _add_working_days(start: date, days: int, working: set[int]) -> date:
    """Advance `start` by `days` working days (may be negative for lead time)."""
    step = 1 if days >= 0 else -1
    remaining = abs(days)
    current = start
    while remaining > 0:
        current += timedelta(days=step)
        if current.weekday() in working:
            remaining -= 1
    return current


def _duration_to_days(iso: str) -> int:
    """Extract integer day count from a P{n}D ISO 8601 duration. Returns 1 on failure."""
    m = re.match(r'^P(\d+)D$', iso)
    return int(m.group(1)) if m else 1


def _lag_to_days(lag: Optional[str]) -> int:
    """Convert a signed ISO 8601 duration string to an integer day count."""
    if not lag:
        return 0
    negative = lag.startswith('-')
    m = re.match(r'^-?P(\d+)D$', lag)
    if not m:
        return 0
    days = int(m.group(1))
    return -days if negative else days


# ─────────────────────────────────────────────────────────────────────────────
# Topological start-date scheduler
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_start_dates(
    tasks: list[GanttTask],
    working: set[int],
) -> dict[str, date]:
    """
    Compute a concrete start date for every task.

    Tasks with an AbsoluteDate start are trivially resolved.
    Tasks with a ConstraintRef start are resolved after their predecessors,
    using simple FS/SS arithmetic.
    Unresolvable tasks (cycles, unknown predecessors) fall back to _FALLBACK_DATE.
    """
    tasks_by_id: dict[str, GanttTask] = {t.id: t for t in tasks if t.id is not None}
    resolved: dict[str, date] = {}
    in_progress: set[str] = set()  # cycle detection

    def resolve(task_id: str) -> date:
        if task_id in resolved:
            return resolved[task_id]
        if task_id in in_progress:
            print(f"Warning: dependency cycle detected at task {task_id!r}", file=sys.stderr)
            return _FALLBACK_DATE
        task = tasks_by_id.get(task_id)
        if task is None:
            return _FALLBACK_DATE

        in_progress.add(task_id)

        if isinstance(task.start, AbsoluteDate):
            d = date.fromisoformat(task.start.value)

        elif isinstance(task.start, ConstraintRef):
            ref = task.start
            candidate_dates: list[date] = []
            for pred_id in ref.task_ids:
                pred_start = resolve(pred_id)
                pred_task  = tasks_by_id.get(pred_id)
                if ref.dependency_type == DependencyType.FS and pred_task:
                    # Successor starts after predecessor finishes
                    if pred_task.duration is not None:
                        dur = _duration_to_days(pred_task.duration)
                        pred_end = _add_working_days(pred_start, dur, working)
                    else:
                        pred_end = pred_start
                    candidate_dates.append(pred_end)
                else:
                    # SS (and unhandled types): align with predecessor start
                    candidate_dates.append(pred_start)

            d = max(candidate_dates) if candidate_dates else _FALLBACK_DATE

            # Apply lag
            lag_days = _lag_to_days(ref.lag)
            if lag_days:
                d = _add_working_days(d, lag_days, working)

        else:
            d = _FALLBACK_DATE

        in_progress.discard(task_id)
        resolved[task_id] = d
        return d

    for task in tasks:
        if task.id is not None:
            resolve(task.id)

    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# Integer ID assignment
# ─────────────────────────────────────────────────────────────────────────────

def _assign_int_ids(tasks: list[GanttTask]) -> dict[Optional[str], int]:
    """
    Map each task's string id to a unique integer for .gan output.
    Tasks whose id is already a non-negative integer string keep their value
    (preserving round-trip fidelity).  Others are assigned sequentially.
    """
    used: set[int] = set()
    mapping: dict[Optional[str], int] = {}
    counter = [0]

    def next_free() -> int:
        while counter[0] in used:
            counter[0] += 1
        n = counter[0]
        used.add(n)
        counter[0] += 1
        return n

    # First pass: assign existing integer ids.
    for task in tasks:
        if task.id is not None:
            try:
                n = int(task.id)
                if n >= 0:
                    used.add(n)
                    mapping[task.id] = n
            except ValueError:
                pass

    # Second pass: assign sequential ids to remaining tasks.
    for task in tasks:
        if task.id not in mapping:
            mapping[task.id] = next_free()

    return mapping


# ─────────────────────────────────────────────────────────────────────────────
# Predecessor map builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_predecessor_map(
    tasks: list[GanttTask],
) -> dict[Optional[str], list[tuple[Optional[str], DependencyType, Optional[str]]]]:
    """
    Build predecessor_id → [(successor_id, dep_type, lag), ...].

    Scans every task's start (FS/SS) and end (FF/SF) ConstraintRef fields.
    This is the inverse of how ConstraintRef is stored in the AST.
    """
    pred_map: dict[Optional[str], list] = {}
    for task in tasks:
        for condition, is_start in [(task.start, True), (task.end, False)]:
            if isinstance(condition, ConstraintRef):
                for pred_id in condition.task_ids:
                    pred_map.setdefault(pred_id, []).append(
                        (task.id, condition.dependency_type, condition.lag)
                    )
    return pred_map


# ─────────────────────────────────────────────────────────────────────────────
# Helper: collect tasks (flattening sections)
# ─────────────────────────────────────────────────────────────────────────────

def _collect_tasks(diagram: GanttDiagram) -> list[GanttTask]:
    tasks: list[GanttTask] = []
    for element in diagram.elements:
        if isinstance(element, GanttTask):
            tasks.append(element)
        elif hasattr(element, "elements"):  # GanttSection
            for item in element.elements:
                if isinstance(item, GanttTask):
                    tasks.append(item)
    return tasks


# ─────────────────────────────────────────────────────────────────────────────
# XML building helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_views(root: ET.Element) -> None:
    gantt_view = ET.SubElement(root, "view")
    gantt_view.set("zooming-state", "default:2")
    gantt_view.set("id", "gantt-chart")
    for fid, fname, w, order in [
        ("tpd3", "Name",       "237", "0"),
        ("tpd4", "Begin date", "89",  "1"),
        ("tpd5", "End date",   "89",  "2"),
    ]:
        f = ET.SubElement(gantt_view, "field")
        f.set("id", fid); f.set("name", fname)
        f.set("width", w); f.set("order", order)
    for opt_id in ("filter.completedTasks", "filter.dueTodayTasks",
                   "filter.overdueTasks",   "filter.inProgressTodayTasks"):
        o = ET.SubElement(gantt_view, "option")
        o.set("id", opt_id); o.set("value", "false")

    res_view = ET.SubElement(root, "view")
    res_view.set("id", "resource-table")
    for fid, fname, w, order in [("0", "Name", "211", "0"), ("1", "Default role", "86", "1")]:
        f = ET.SubElement(res_view, "field")
        f.set("id", fid); f.set("name", fname)
        f.set("width", w); f.set("order", order)


def _build_calendars(root: ET.Element, working: set[int]) -> None:
    cals   = ET.SubElement(root, "calendars")
    dtypes = ET.SubElement(cals,   "day-types")
    ET.SubElement(dtypes, "day-type").set("id", "0")
    ET.SubElement(dtypes, "day-type").set("id", "1")

    week = ET.SubElement(dtypes, "default-week")
    week.set("id", "1"); week.set("name", "default")
    for attr, wd in [("sun", 6), ("mon", 0), ("tue", 1),
                     ("wed", 2), ("thu", 3), ("fri", 4), ("sat", 5)]:
        week.set(attr, "0" if wd in working else "1")

    ET.SubElement(dtypes, "only-show-weekends").set("value", "false")
    ET.SubElement(dtypes, "overriden-day-types")
    ET.SubElement(dtypes, "days")


def _build_tasks_block(
    root:        ET.Element,
    tasks:       list[GanttTask],
    int_ids:     dict[Optional[str], int],
    starts:      dict[str, date],
    pred_map:    dict,
    working:     set[int],
) -> None:
    tasks_elem = ET.SubElement(root, "tasks")
    tasks_elem.set("empty-milestones", "true")

    props = ET.SubElement(tasks_elem, "taskproperties")
    for pid, pname, ptype, pvtype in _TASK_PROPERTIES:
        tp = ET.SubElement(props, "taskproperty")
        tp.set("id", pid); tp.set("name", pname)
        tp.set("type", ptype); tp.set("valuetype", pvtype)

    for task in tasks:
        int_id = int_ids[task.id]
        task_elem = ET.SubElement(tasks_elem, "task")
        task_elem.set("id",   str(int_id))
        if task.uid:
            task_elem.set("uid", task.uid)
        task_elem.set("name", task.name)
        task_elem.set("meeting", "true" if task.element_type == GanttElementType.MILESTONE else "false")

        # Start date
        start_date = starts.get(task.id, _FALLBACK_DATE)
        task_elem.set("start", start_date.isoformat())

        # Duration (working days)
        dur = _duration_to_days(task.duration) if task.duration is not None else 1
        task_elem.set("duration", str(dur))

        # Percent complete
        pct = task.percent_complete if task.percent_complete is not None else 0
        task_elem.set("complete", str(pct))
        task_elem.set("expand", "true")

        # <depend> elements — successors of this task
        for succ_id, dep_type, lag in pred_map.get(task.id, []):
            succ_int = int_ids.get(succ_id)
            if succ_int is None:
                continue
            dep_elem = ET.SubElement(task_elem, "depend")
            dep_elem.set("id",         str(succ_int))
            dep_elem.set("type",       str(_DEP_TYPE_INT.get(dep_type, 2)))
            dep_elem.set("difference", str(_lag_to_days(lag)))
            dep_elem.set("hardness",   "Strong")


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def render_gantt_project(
    diagram:     GanttDiagram,
    ganttproject: Optional[GanttProjectMetadata] = None,
) -> str:
    """
    Render a GanttDiagram (and optional GanttProjectMetadata) to a .gan XML string.

    Args:
        diagram:      The GanttDiagram to render.
        ganttproject: Optional metadata from a prior .gan import; supplies
                      project name, locale, version, and working_days.

    Returns:
        A .gan XML string ready to open in GanttProject.
    """
    # ── Resolve project-level metadata ───────────────────────────────────────
    gp       = ganttproject
    name     = (gp.name    if gp and gp.name    else None) or _title_from_header(diagram) or "Untitled"
    locale   =  gp.locale  if gp and gp.locale  else _DEFAULT_LOCALE
    version  =  gp.version if gp and gp.version else _DEFAULT_VERSION
    working  = _working_weekdays(gp)

    # ── Collect and prepare tasks ─────────────────────────────────────────────
    tasks    = _collect_tasks(diagram)
    int_ids  = _assign_int_ids(tasks)
    starts   = _resolve_start_dates(tasks, working)
    pred_map = _build_predecessor_map(tasks)

    # Remap string pred_map keys to the same string ids tasks use
    # (pred_map keys come from ConstraintRef.task_ids which are string ids)

    # ── Build XML tree ────────────────────────────────────────────────────────
    root = ET.Element("project")
    root.set("name",                     name)
    root.set("company",                  "")
    root.set("webLink",                  "http://")
    root.set("view-date",                date.today().isoformat())
    root.set("view-index",               "0")
    root.set("gantt-divider-location",   "416")
    root.set("resource-divider-location","300")
    root.set("version",                  version)
    root.set("locale",                   locale)

    ET.SubElement(root, "description")
    _build_views(root)
    root.append(ET.Comment(" "))
    _build_calendars(root, working)
    _build_tasks_block(root, tasks, int_ids, starts, pred_map, working)

    for tag in ("resources", "allocations", "vacations", "previous"):
        ET.SubElement(root, tag)
    ET.SubElement(root, "roles").set("roleset-name", "Default")

    # ── Serialise ─────────────────────────────────────────────────────────────
    ET.indent(root, space="    ")
    tree = ET.ElementTree(root)
    from io import StringIO
    buf = StringIO()
    tree.write(buf, encoding="unicode", xml_declaration=True)
    return buf.getvalue()


def _title_from_header(diagram: GanttDiagram) -> Optional[str]:
    for entry in diagram.header:
        if isinstance(entry, GanttDirective) and entry.name == GanttDirectiveName.TITLE:
            return entry.value
    return None

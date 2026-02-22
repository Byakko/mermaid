"""
gtp_gantt.py
============
Convert a GanttProject .gan XML file to diagram_models objects.

GanttProject .gan dependency semantics
---------------------------------------
The <depend> element is stored on the PREDECESSOR task and lists successors:

    <task id="Y" ...>
        <depend id="X" type="T" difference="D"/>
    </task>

means: task X depends on task Y  (Y is predecessor, X is successor).

Dependency type integers:
    1 = FS  Finish-to-Start   (most common)
    2 = SS  Start-to-Start
    3 = FF  Finish-to-Finish
    4 = SF  Start-to-Finish

FS/SS dependencies constrain the successor's START  → stored in start field.
FF/SF dependencies constrain the successor's END    → stored in end field.

`difference` is the lag in working days (may be negative for lead time).
The GanttProjectMetadata.working_days field records the working-day calendar
needed to interpret these durations precisely.
"""

import sys
import xml.etree.ElementTree as ET
from typing import Optional

from diagram_models import Document
from diagram_models.common import (
    AbsoluteDate,
    ConstraintRef,
    DependencyCombination,
    DependencyType,
    ImplicitEnd,
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
# Lookup tables
# ─────────────────────────────────────────────────────────────────────────────

_DEP_TYPE: dict[int, DependencyType] = {
    1: DependencyType.SS,  # Start-to-Start
    2: DependencyType.FS,  # Finish-to-Start (most common; confirmed by date analysis)
    3: DependencyType.FF,  # Finish-to-Finish
    4: DependencyType.SF,  # Start-to-Finish
}

# Attribute name on <default-week> → DayOfWeek enum
# Value "0" = working day, "1" = non-working day
_DAY_ATTRS: dict[str, DayOfWeek] = {
    "mon": DayOfWeek.MON,
    "tue": DayOfWeek.TUE,
    "wed": DayOfWeek.WED,
    "thu": DayOfWeek.THU,
    "fri": DayOfWeek.FRI,
    "sat": DayOfWeek.SAT,
    "sun": DayOfWeek.SUN,
}

# FS and SS constrain the start of the successor task.
_START_TYPES = {DependencyType.FS, DependencyType.SS}
# FF and SF constrain the end of the successor task.
_END_TYPES   = {DependencyType.FF, DependencyType.SF}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_working_days(root: ET.Element) -> list[DayOfWeek]:
    """Return working days from <default-week>. Defaults to Mon-Fri if absent."""
    default_week = root.find(".//calendars/day-types/default-week")
    if default_week is None:
        return [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED, DayOfWeek.THU, DayOfWeek.FRI]
    return [
        day for attr, day in _DAY_ATTRS.items()
        if default_week.get(attr) == "0"  # "0" = working
    ]


def _lag_to_iso(difference: int) -> Optional[str]:
    """Convert a GanttProject lag integer (working days) to a signed ISO 8601 duration."""
    if difference == 0:
        return None
    if difference > 0:
        return f"P{difference}D"
    return f"-P{abs(difference)}D"


def _make_constraint_ref(
    deps: list[tuple[str, DependencyType, Optional[str]]],
    label: str,
) -> Optional[ConstraintRef]:
    """
    Build a ConstraintRef from a list of (predecessor_id, dep_type, lag) tuples.
    Warns if types or lags are mixed across multiple predecessors.
    """
    if not deps:
        return None

    types = {d[1] for d in deps}
    if len(types) > 1:
        print(
            f"Warning: mixed dependency types {[t.value for t in types]} "
            f"for task {label!r} {label}; using {deps[0][1].value}",
            file=sys.stderr,
        )

    lags = {d[2] for d in deps}
    if len(lags) > 1:
        print(
            f"Warning: mixed lag values {lags} for task {label!r}; using {deps[0][2]}",
            file=sys.stderr,
        )

    return ConstraintRef(
        task_ids=[d[0] for d in deps],
        dependency_type=deps[0][1],
        combination=DependencyCombination.ALL_OF,
        lag=deps[0][2],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_gantt_project(text: str) -> Document:
    """
    Parse a GanttProject .gan XML string into a Document.

    The returned Document contains:
      - diagram:      GanttDiagram with tasks; project name as TITLE directive
      - ganttproject: GanttProjectMetadata with name, locale, version, working_days
    """
    root = ET.fromstring(text)

    # ── Project-level metadata ────────────────────────────────────────────────
    project_name = root.get("name") or ""
    locale       = root.get("locale")
    version      = root.get("version")
    working_days = _parse_working_days(root)

    ganttproject_meta = GanttProjectMetadata(
        name=project_name or None,
        locale=locale,
        version=version,
        working_days=working_days,
    )

    # ── First pass: build successor map from <depend> elements ───────────────
    # successor_map[X] = [(Y_id, dep_type, lag), ...]
    # means task X depends on task Y.
    task_elems = root.findall(".//tasks/task")

    successor_map: dict[str, list[tuple[str, DependencyType, Optional[str]]]] = {}

    for task_elem in task_elems:
        pred_id = task_elem.get("id", "")
        for depend in task_elem.findall("depend"):
            succ_id    = depend.get("id", "")
            type_int   = int(depend.get("type", "1"))
            difference = int(depend.get("difference", "0"))
            dep_type   = _DEP_TYPE.get(type_int, DependencyType.FS)
            lag        = _lag_to_iso(difference)
            successor_map.setdefault(succ_id, []).append((pred_id, dep_type, lag))

    # ── Second pass: build GanttTask objects ──────────────────────────────────
    tasks: list[GanttTask] = []

    for task_elem in task_elems:
        task_id       = task_elem.get("id", "")
        name          = task_elem.get("name", "")
        start_str     = task_elem.get("start")
        duration_days = int(task_elem.get("duration", "1"))
        complete_str  = task_elem.get("complete")
        is_milestone  = task_elem.get("meeting", "false").lower() == "true"
        uid           = task_elem.get("uid")

        element_type = GanttElementType.MILESTONE if is_milestone else GanttElementType.TASK

        # Statuses derived from percent complete.
        complete = int(complete_str) if complete_str is not None else None
        statuses: list[GanttTaskStatus] = []
        if complete == 100:
            statuses.append(GanttTaskStatus.DONE)
        elif complete and complete > 0:
            statuses.append(GanttTaskStatus.ACTIVE)

        # Partition predecessors into start-constraining and end-constraining.
        all_deps = successor_map.get(task_id, [])
        start_deps = [(pid, dt, lg) for pid, dt, lg in all_deps if dt in _START_TYPES]
        end_deps   = [(pid, dt, lg) for pid, dt, lg in all_deps if dt in _END_TYPES]

        start = (
            _make_constraint_ref(start_deps, task_id)
            or AbsoluteDate(start_str)
            if start_str else None
        )
        # Fallback to ImplicitStart only if no start date either (shouldn't happen in valid .gan)
        if start is None:
            from diagram_models.common import ImplicitStart
            start = ImplicitStart()

        end = _make_constraint_ref(end_deps, task_id) or ImplicitEnd()

        tasks.append(GanttTask(
            name=name,
            element_type=element_type,
            start=start,
            duration=f"P{duration_days}D",
            end=end,
            statuses=statuses,
            id=task_id,
            uid=uid,
            percent_complete=complete,
        ))

    # ── Assemble diagram ──────────────────────────────────────────────────────
    header = []
    if project_name:
        header.append(GanttDirective(name=GanttDirectiveName.TITLE, value=project_name))

    diagram = GanttDiagram(header=header, elements=tasks)

    return Document(
        diagram=diagram,
        ganttproject=ganttproject_meta,
        version="1.0",
    )

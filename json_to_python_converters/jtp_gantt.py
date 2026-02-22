"""
jtp_gantt.py
============
Convert a Gantt AST JSON dict to a diagram_models GanttDiagram object.
"""

from diagram_models.common import (
    AbsoluteDate,
    AbsoluteDateTime,
    Comment,
    ConstraintRef,
    DependencyCombination,
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
    GanttTaskStatus,
)


def _parse_start(data: dict):
    kind = data["kind"]
    if kind == "IMPLICIT_START":
        return ImplicitStart()
    if kind == "ABSOLUTE_DATE":
        return AbsoluteDate(data["value"])
    if kind == "ABSOLUTE_DATETIME":
        return AbsoluteDateTime(data["value"])
    if kind == "TIME_OF_DAY":
        return TimeOfDay(data["value"])
    if kind == "CONSTRAINT_REF":
        return ConstraintRef(
            task_ids=data["task_ids"],
            dependency_type=DependencyType(data["dependency_type"]),
            combination=DependencyCombination(data["combination"]),
            lag=data.get("lag"),
        )
    raise ValueError(f"Unknown start kind: {kind!r}")


def _parse_end(data: dict):
    kind = data["kind"]
    if kind == "IMPLICIT_END":
        return ImplicitEnd()
    if kind == "ABSOLUTE_DATE":
        return AbsoluteDate(data["value"])
    if kind == "ABSOLUTE_DATETIME":
        return AbsoluteDateTime(data["value"])
    if kind == "TIME_OF_DAY":
        return TimeOfDay(data["value"])
    if kind == "CONSTRAINT_REF":
        return ConstraintRef(
            task_ids=data["task_ids"],
            dependency_type=DependencyType(data["dependency_type"]),
            combination=DependencyCombination(data["combination"]),
            lag=data.get("lag"),
        )
    raise ValueError(f"Unknown end kind: {kind!r}")


def _parse_task(data: dict) -> GanttTask:
    return GanttTask(
        name=data["name"],
        element_type=GanttElementType(data["element_type"]),
        start=_parse_start(data["start"]),
        end=_parse_end(data["end"]),
        statuses=[GanttTaskStatus(s) for s in data.get("statuses", [])],
        id=data.get("id"),
        trailing_comment=data.get("trailing_comment"),
        duration=data.get("duration"),
        percent_complete=data.get("percent_complete"),
        uid=data.get("uid"),
    )


def _parse_comment(data: dict) -> Comment:
    return Comment(
        text=data["text"],
        id=data.get("id"),
        trailing_comment=data.get("trailing_comment"),
    )


def _parse_header_element(data: dict):
    kind = data["kind"]
    if kind == "GANTT_DIRECTIVE":
        return GanttDirective(
            name=GanttDirectiveName(data["name"]),
            value=data["value"],
        )
    if kind == "COMMENT":
        return _parse_comment(data)
    raise ValueError(f"Unknown header element kind: {kind!r}")


def _parse_section_element(data: dict):
    kind = data["kind"]
    if kind == "GANTT_TASK":
        return _parse_task(data)
    if kind == "COMMENT":
        return _parse_comment(data)
    raise ValueError(f"Unknown section element kind: {kind!r}")


def _parse_top_level_element(data: dict):
    kind = data["kind"]
    if kind == "GANTT_SECTION":
        return GanttSection(
            name=data["name"],
            elements=[_parse_section_element(e) for e in data.get("elements", [])],
            id=data.get("id"),
            trailing_comment=data.get("trailing_comment"),
        )
    return _parse_section_element(data)


def parse_gantt(data: dict) -> GanttDiagram:
    """
    Convert a Gantt diagram sub-dict (the value of the 'diagram' key in AST JSON)
    to a GanttDiagram object.

    Args:
        data: dict with kind == "GANTT_DIAGRAM"

    Returns:
        A GanttDiagram object.
    """
    return GanttDiagram(
        header=[_parse_header_element(e) for e in data.get("header", [])],
        elements=[_parse_top_level_element(e) for e in data.get("elements", [])],
        id=data.get("id"),
        trailing_comment=data.get("trailing_comment"),
    )

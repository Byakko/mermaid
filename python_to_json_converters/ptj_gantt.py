"""
ptj_gantt.py
============
Convert a diagram_models GanttDiagram object to a Gantt AST JSON dict.
"""

from diagram_models.common import (
    AbsoluteDate,
    AbsoluteDateTime,
    Comment,
    ConstraintRef,
    ImplicitEnd,
    ImplicitStart,
    TimeOfDay,
)
from diagram_models.gantt import (
    GanttDiagram,
    GanttDirective,
    GanttSection,
    GanttTask,
)


def _render_start(start) -> dict:
    if isinstance(start, ImplicitStart):
        return {"kind": "IMPLICIT_START"}
    if isinstance(start, AbsoluteDate):
        return {"kind": "ABSOLUTE_DATE", "value": start.value}
    if isinstance(start, AbsoluteDateTime):
        return {"kind": "ABSOLUTE_DATETIME", "value": start.value}
    if isinstance(start, TimeOfDay):
        return {"kind": "TIME_OF_DAY", "value": start.value}
    if isinstance(start, ConstraintRef):
        d = {
            "kind": "CONSTRAINT_REF",
            "task_ids": start.task_ids,
            "dependency_type": start.dependency_type.value,
            "combination": start.combination.value,
        }
        if start.lag is not None:
            d["lag"] = start.lag
        return d
    raise ValueError(f"Unknown start type: {type(start).__name__}")


def _render_end(end) -> dict:
    if isinstance(end, ImplicitEnd):
        return {"kind": "IMPLICIT_END"}
    if isinstance(end, AbsoluteDate):
        return {"kind": "ABSOLUTE_DATE", "value": end.value}
    if isinstance(end, AbsoluteDateTime):
        return {"kind": "ABSOLUTE_DATETIME", "value": end.value}
    if isinstance(end, TimeOfDay):
        return {"kind": "TIME_OF_DAY", "value": end.value}
    if isinstance(end, ConstraintRef):
        d = {
            "kind": "CONSTRAINT_REF",
            "task_ids": end.task_ids,
            "dependency_type": end.dependency_type.value,
            "combination": end.combination.value,
        }
        if end.lag is not None:
            d["lag"] = end.lag
        return d
    raise ValueError(f"Unknown end type: {type(end).__name__}")


def _render_task(task: GanttTask) -> dict:
    d = {
        "kind": "GANTT_TASK",
        "name": task.name,
        "element_type": task.element_type.value,
        "statuses": [s.value for s in task.statuses],
        "start": _render_start(task.start),
        "end": _render_end(task.end),
    }
    if task.id is not None:
        d["id"] = task.id
    if task.trailing_comment is not None:
        d["trailing_comment"] = task.trailing_comment
    if task.duration is not None:
        d["duration"] = task.duration
    if task.percent_complete is not None:
        d["percent_complete"] = task.percent_complete
    if task.uid is not None:
        d["uid"] = task.uid
    return d


def _render_comment(comment: Comment) -> dict:
    d = {"kind": "COMMENT", "text": comment.text}
    if comment.id is not None:
        d["id"] = comment.id
    if comment.trailing_comment is not None:
        d["trailing_comment"] = comment.trailing_comment
    return d


def _render_header_element(element) -> dict:
    if isinstance(element, GanttDirective):
        return {
            "kind": "GANTT_DIRECTIVE",
            "name": element.name.value,
            "value": element.value,
        }
    if isinstance(element, Comment):
        return _render_comment(element)
    raise ValueError(f"Unknown header element type: {type(element).__name__}")


def _render_section_element(element) -> dict:
    if isinstance(element, GanttTask):
        return _render_task(element)
    if isinstance(element, Comment):
        return _render_comment(element)
    raise ValueError(f"Unknown section element type: {type(element).__name__}")


def _render_top_level_element(element) -> dict:
    if isinstance(element, GanttSection):
        d = {
            "kind": "GANTT_SECTION",
            "name": element.name,
            "elements": [_render_section_element(e) for e in element.elements],
        }
        if element.id is not None:
            d["id"] = element.id
        if element.trailing_comment is not None:
            d["trailing_comment"] = element.trailing_comment
        return d
    return _render_section_element(element)


def render_gantt(diagram: GanttDiagram) -> dict:
    """
    Convert a GanttDiagram object to the diagram sub-dict for AST JSON output.
    The caller wraps this in the top-level Document envelope (version, frontmatter).

    Args:
        diagram: A GanttDiagram object

    Returns:
        A plain dict with kind == "GANTT_DIAGRAM", ready for json.dumps().
    """
    d = {
        "kind": "GANTT_DIAGRAM",
        "header": [_render_header_element(e) for e in diagram.header],
        "elements": [_render_top_level_element(e) for e in diagram.elements],
    }
    if diagram.id is not None:
        d["id"] = diagram.id
    if diagram.trailing_comment is not None:
        d["trailing_comment"] = diagram.trailing_comment
    return d

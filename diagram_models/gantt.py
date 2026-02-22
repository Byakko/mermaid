"""
gantt.py
========
AST node types for Gantt diagrams.

These mirror the Gantt types in schema/schema.graphql.
All classes are pure data containers (dataclasses).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from .common import Comment, EndCondition, StartCondition


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class GanttDirectiveName(Enum):
    """Names of the directives that can appear in a Gantt preamble."""
    TITLE         = "TITLE"
    DATE_FORMAT   = "DATE_FORMAT"
    AXIS_FORMAT   = "AXIS_FORMAT"
    TICK_INTERVAL = "TICK_INTERVAL"
    EXCLUDES      = "EXCLUDES"
    WEEKEND       = "WEEKEND"


class GanttElementType(Enum):
    """The structural type of a Gantt element."""
    TASK      = "TASK"       # regular scheduled bar
    MILESTONE = "MILESTONE"  # zero-duration point marker (diamond in most renderers)
    VERT      = "VERT"       # vertical reference line; duration is a spacing offset


class GanttTaskStatus(Enum):
    """Work state and styling flags. Multiple can apply to one task."""
    DONE   = "DONE"    # work is complete
    ACTIVE = "ACTIVE"  # work is in progress
    CRIT   = "CRIT"    # on the critical path; rendered with urgency styling


# ─────────────────────────────────────────────────────────────────────────────
# Preamble / header
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GanttDirective:
    """
    A single directive from the Gantt preamble (title, dateFormat, etc.).
    value is always the raw string from the source.

    Examples:
      title A Gantt Diagram  → GanttDirective(TITLE, "A Gantt Diagram")
      excludes weekends      → GanttDirective(EXCLUDES, "weekends")
      weekend friday         → GanttDirective(WEEKEND, "friday")
    """
    name: GanttDirectiveName
    value: str
    kind: str = field(default="GANTT_DIRECTIVE", init=False)


GanttHeaderElement = Union[GanttDirective, Comment]


# ─────────────────────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GanttTask:
    """
    A single Gantt chart task, milestone, or vertical reference line.

    element_type distinguishes what kind of thing this is (TASK / MILESTONE / VERT).
    statuses holds work-state flags (DONE / ACTIVE / CRIT); may be empty.
    """
    name: str
    element_type: GanttElementType
    start: StartCondition
    end: EndCondition
    statuses: list[GanttTaskStatus] = field(default_factory=list)
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    kind: str = field(default="GANTT_TASK", init=False)


# ─────────────────────────────────────────────────────────────────────────────
# Section
# ─────────────────────────────────────────────────────────────────────────────

GanttSectionElement = Union[GanttTask, Comment]


@dataclass
class GanttSection:
    """A named group of tasks within a Gantt chart."""
    name: str
    elements: list[GanttSectionElement] = field(default_factory=list)
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    kind: str = field(default="GANTT_SECTION", init=False)


# ─────────────────────────────────────────────────────────────────────────────
# Diagram
# ─────────────────────────────────────────────────────────────────────────────

GanttTopLevelElement = Union[GanttSection, GanttTask, Comment]


@dataclass
class GanttDiagram:
    """
    A complete Gantt chart.

    header holds the ordered sequence of directives and comments from the
    preamble, preserving their original order for faithful round-tripping.

    elements holds the body: sections, sectionless tasks, and stand-alone
    comments that appear after the preamble.
    """
    header: list[GanttHeaderElement] = field(default_factory=list)
    elements: list[GanttTopLevelElement] = field(default_factory=list)
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    kind: str = field(default="GANTT_DIAGRAM", init=False)

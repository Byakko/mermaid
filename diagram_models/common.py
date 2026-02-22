"""
common.py
=========
Shared AST node types used across all diagram kinds.

These mirror the shared types in schema/schema.graphql.
All classes are pure data containers (dataclasses).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class DependencyType(Enum):
    """CPM scheduling relationship between tasks."""
    FS = "FS"   # Finish-to-Start  — this task begins after referenced task(s) finish
    SS = "SS"   # Start-to-Start   — this task begins when referenced task(s) begin
    FF = "FF"   # Finish-to-Finish — this task ends when referenced task(s) end
    SF = "SF"   # Start-to-Finish  — this task ends when referenced task(s) begin


class DependencyCombination(Enum):
    """How multiple task_ids in a ConstraintRef are combined."""
    ALL_OF = "ALL_OF"   # wait for / align with all referenced tasks
    ANY_OF = "ANY_OF"   # wait for / align with the first to satisfy the condition


# ─────────────────────────────────────────────────────────────────────────────
# Date / time value types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AbsoluteDate:
    """A calendar date string in ISO 8601 format, e.g. '2024-01-01'."""
    value: str
    kind: str = field(default="ABSOLUTE_DATE", init=False)


@dataclass
class AbsoluteDateTime:
    """A full date + time string in ISO 8601 format, e.g. '2024-01-01T09:00:00Z'."""
    value: str
    kind: str = field(default="ABSOLUTE_DATETIME", init=False)


@dataclass
class TimeOfDay:
    """A time-of-day string in ISO 8601 format, e.g. '17:49:00'."""
    value: str
    kind: str = field(default="TIME_OF_DAY", init=False)


@dataclass
class RelativeDuration:
    """An ISO 8601 duration string, e.g. 'P30D', 'PT24H', 'P1W'."""
    value: str
    kind: str = field(default="RELATIVE_DURATION", init=False)


# ─────────────────────────────────────────────────────────────────────────────
# Implicit start / end markers
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ImplicitStart:
    """No start constraint specified; element begins after the previous one."""
    kind: str = field(default="IMPLICIT_START", init=False)


@dataclass
class ImplicitEnd:
    """No end constraint specified; semantics left to the renderer."""
    kind: str = field(default="IMPLICIT_END", init=False)


# ─────────────────────────────────────────────────────────────────────────────
# Constraint reference (dependency on named task(s))
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConstraintRef:
    """
    A scheduling dependency on one or more named tasks.

    lag is an ISO 8601 duration string. Positive values add delay after the
    anchor point; negative values (e.g. '-P1D') represent lead time (overlap).
    None means zero lag.

    Examples:
      after a1        → ConstraintRef(["a1"], FS, ALL_OF)
      after a1 a2     → ConstraintRef(["a1", "a2"], FS, ALL_OF)
      until isadded   → ConstraintRef(["isadded"], SF, ALL_OF)
    """
    task_ids: list[str]
    dependency_type: DependencyType
    combination: DependencyCombination
    lag: Optional[str] = None
    kind: str = field(default="CONSTRAINT_REF", init=False)


# ─────────────────────────────────────────────────────────────────────────────
# Stand-alone comment
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Comment:
    """
    A stand-alone comment line (Mermaid: %% text).

    Can appear as a member of any element array so it sits naturally
    in the ordered list. Trailing/inline comments on other elements
    are handled by the trailing_comment field on that element.
    """
    text: str
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    kind: str = field(default="COMMENT", init=False)


# ─────────────────────────────────────────────────────────────────────────────
# Start / End condition type aliases
# ─────────────────────────────────────────────────────────────────────────────

StartCondition = Union[
    ImplicitStart,
    AbsoluteDate,
    AbsoluteDateTime,
    TimeOfDay,
    ConstraintRef,
]

EndCondition = Union[
    ImplicitEnd,
    AbsoluteDate,
    AbsoluteDateTime,
    TimeOfDay,
    ConstraintRef,
]

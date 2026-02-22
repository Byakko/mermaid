"""
validate_json.py
================
Validate a diagram AST JSON file through three steps:

  1. Pydantic — structural validation: required fields, type coercion,
     enum membership, ISO 8601 duration format.
  2. Round-trip — JSON -> diagram_models Python objects -> JSON.
     Exercises both the json_to_python and python_to_json converters.
  3. Comparison — the round-tripped JSON must equal the original
     (compared as parsed dicts, so key order doesn't matter).

Usage:
    python validate_json.py <path/to/file.json>
    python validate_json.py test_json/test_gantt_1.json
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class DependencyType(str, Enum):
    FS = "FS"
    SS = "SS"
    FF = "FF"
    SF = "SF"


class DependencyCombination(str, Enum):
    ALL_OF = "ALL_OF"
    ANY_OF = "ANY_OF"


class GanttDirectiveName(str, Enum):
    TITLE         = "TITLE"
    DATE_FORMAT   = "DATE_FORMAT"
    AXIS_FORMAT   = "AXIS_FORMAT"
    TICK_INTERVAL = "TICK_INTERVAL"
    EXCLUDES      = "EXCLUDES"
    WEEKEND       = "WEEKEND"


class GanttElementType(str, Enum):
    TASK      = "TASK"
    MILESTONE = "MILESTONE"
    VERT      = "VERT"


class GanttTaskStatus(str, Enum):
    DONE   = "DONE"
    ACTIVE = "ACTIVE"
    CRIT   = "CRIT"


# ─────────────────────────────────────────────────────────────────────────────
# Shared node
# ─────────────────────────────────────────────────────────────────────────────

class Comment(BaseModel):
    kind:             Literal["COMMENT"]
    text:             str
    id:               Optional[str] = None
    trailing_comment: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Date / time value types
# ─────────────────────────────────────────────────────────────────────────────

class AbsoluteDate(BaseModel):
    kind:  Literal["ABSOLUTE_DATE"]
    value: str


class AbsoluteDateTime(BaseModel):
    kind:  Literal["ABSOLUTE_DATETIME"]
    value: str


class TimeOfDay(BaseModel):
    kind:  Literal["TIME_OF_DAY"]
    value: str


_ISO_DUR = re.compile(
    r"^P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?!$)(\d+H)?(\d+M)?(\d+S)?)?$"
)


class RelativeDuration(BaseModel):
    kind:  Literal["RELATIVE_DURATION"]
    value: str

    @field_validator("value")
    @classmethod
    def validate_iso_duration(cls, v: str) -> str:
        if not _ISO_DUR.match(v):
            raise ValueError(f"Not a valid ISO 8601 duration: {v!r}")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Implicit markers
# ─────────────────────────────────────────────────────────────────────────────

class ImplicitStart(BaseModel):
    kind: Literal["IMPLICIT_START"]


class ImplicitEnd(BaseModel):
    kind: Literal["IMPLICIT_END"]


# ─────────────────────────────────────────────────────────────────────────────
# Constraint reference
# ─────────────────────────────────────────────────────────────────────────────

class ConstraintRef(BaseModel):
    kind:            Literal["CONSTRAINT_REF"]
    task_ids:        list[str]
    dependency_type: DependencyType
    combination:     DependencyCombination

    @model_validator(mode="after")
    def task_ids_non_empty(self) -> ConstraintRef:
        if not self.task_ids:
            raise ValueError("task_ids must not be empty")
        return self


# ─────────────────────────────────────────────────────────────────────────────
# Start / End condition unions  (discriminated on `kind`)
# ─────────────────────────────────────────────────────────────────────────────

StartCondition = Annotated[
    Union[ImplicitStart, AbsoluteDate, AbsoluteDateTime, TimeOfDay, ConstraintRef],
    Field(discriminator="kind"),
]

EndCondition = Annotated[
    Union[ImplicitEnd, AbsoluteDate, AbsoluteDateTime, TimeOfDay, RelativeDuration, ConstraintRef],
    Field(discriminator="kind"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Gantt preamble
# ─────────────────────────────────────────────────────────────────────────────

class GanttDirective(BaseModel):
    kind:  Literal["GANTT_DIRECTIVE"]
    name:  GanttDirectiveName
    value: str


GanttHeaderElement = Annotated[
    Union[GanttDirective, Comment],
    Field(discriminator="kind"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Gantt body elements
# ─────────────────────────────────────────────────────────────────────────────

class GanttTask(BaseModel):
    kind:             Literal["GANTT_TASK"]
    name:             str
    element_type:     GanttElementType
    statuses:         list[GanttTaskStatus]
    start:            StartCondition
    end:              EndCondition
    id:               Optional[str] = None
    trailing_comment: Optional[str] = None


GanttSectionElement = Annotated[
    Union[GanttTask, Comment],
    Field(discriminator="kind"),
]


class GanttSection(BaseModel):
    kind:             Literal["GANTT_SECTION"]
    name:             str
    elements:         list[GanttSectionElement]
    id:               Optional[str] = None
    trailing_comment: Optional[str] = None


GanttTopLevelElement = Annotated[
    Union[GanttSection, GanttTask, Comment],
    Field(discriminator="kind"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Gantt diagram
# ─────────────────────────────────────────────────────────────────────────────

class GanttDiagram(BaseModel):
    kind:             Literal["GANTT_DIAGRAM"]
    header:           list[GanttHeaderElement]
    elements:         list[GanttTopLevelElement]
    id:               Optional[str] = None
    trailing_comment: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Document root
# Extend diagram union here as new diagram types are implemented.
# ─────────────────────────────────────────────────────────────────────────────

class Document(BaseModel):
    version:     Optional[str] = None
    frontmatter: Optional[str] = None
    diagram:     GanttDiagram  # Union[GanttDiagram, ...] when more types exist


# ─────────────────────────────────────────────────────────────────────────────
# Validation steps
# ─────────────────────────────────────────────────────────────────────────────

def _step_pydantic(data: dict) -> list[str]:
    """Pydantic structural validation. Returns list of error strings (empty = pass)."""
    try:
        Document.model_validate(data)
        return []
    except Exception as exc:
        return str(exc).splitlines()


def _step_round_trip(json_text: str) -> tuple[Optional[str], list[str]]:
    """
    JSON -> Python objects -> JSON.
    Returns (round_tripped_json_or_None, error_lines).
    """
    from json_to_python import json_to_python
    from python_to_json import python_to_json

    py_doc = json_to_python(json_text)
    if py_doc is None:
        return None, ["json_to_python returned None (unsupported or malformed)"]

    rt_json = python_to_json(py_doc)
    if rt_json is None:
        return None, ["python_to_json returned None (no renderer available)"]

    return rt_json, []


def _step_compare(original: dict, rt_json: str) -> list[str]:
    """
    Compare original dict to round-tripped JSON (parsed as dict).
    Returns list of error strings (empty = pass).
    """
    try:
        rt_data = json.loads(rt_json)
    except json.JSONDecodeError as e:
        return [f"Round-tripped output is not valid JSON: {e}"]

    if original == rt_data:
        return []

    # Produce a readable diff on pretty-printed forms.
    orig_lines = json.dumps(original, indent=2, sort_keys=True).splitlines(keepends=True)
    rt_lines   = json.dumps(rt_data,  indent=2, sort_keys=True).splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, rt_lines, fromfile="original", tofile="round-trip", n=3))
    if diff:
        return ["Round-tripped JSON differs from original:"] + [l.rstrip("\n") for l in diff]
    return ["Round-trip mismatch (dicts differ but pretty-printed forms are identical)"]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python validate_json.py <path/to/file.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    passed = failed = 0

    def ok(label: str) -> None:
        nonlocal passed
        print(f"  PASS  {label}")
        passed += 1

    def fail(label: str, errors: list[str]) -> None:
        nonlocal failed
        print(f"  FAIL  {label}")
        for e in errors:
            print(f"        {e}")
        failed += 1

    print(f"Validating {path}\n")

    # Load the file.
    try:
        json_text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"  FAIL  JSON parse\n        {e}")
        sys.exit(1)

    ok("JSON parse")

    # Step 1: Pydantic validation.
    errs = _step_pydantic(data)
    if errs:
        fail("Pydantic validation", errs)
    else:
        ok("Pydantic validation")

    # Step 2: Round-trip conversion.
    rt_json, errs = _step_round_trip(json_text)
    if errs:
        fail("Round-trip conversion", errs)
    else:
        ok("Round-trip conversion  (JSON -> Python -> JSON)")

    # Step 3: Comparison (only if round-trip succeeded).
    if rt_json is not None:
        errs = _step_compare(data, rt_json)
        if errs:
            fail("Round-trip comparison", errs)
        else:
            ok("Round-trip comparison  (output == original)")

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

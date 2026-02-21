"""
validate.py
===========
Pydantic v2 models that mirror schema.graphql, plus a test runner that
validates hand-crafted AST JSON for every test_gantt_*.mmd file.

Usage:
    python schema/validate.py

The models also serve as the runtime validation layer for the pipeline:
    from schema.validate import Document
    doc = Document.model_validate(json_dict)
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# ─────────────────────────────────────────────────────────────────────────────
# ISODuration validator
# ─────────────────────────────────────────────────────────────────────────────

_ISO_DUR = re.compile(
    r"^P(?!$)(\d+Y)?(\d+M)?(\d+W)?(\d+D)?(T(?!$)(\d+H)?(\d+M)?(\d+S)?)?$"
)


def _check_iso_duration(v: str) -> str:
    if not _ISO_DUR.match(v):
        raise ValueError(f"Not a valid ISO 8601 duration: {v!r}")
    return v


# ─────────────────────────────────────────────────────────────────────────────
# Date / time value types
# ─────────────────────────────────────────────────────────────────────────────


class AbsoluteDate(BaseModel):
    kind: Literal["ABSOLUTE_DATE"]
    value: date


class AbsoluteDateTime(BaseModel):
    kind: Literal["ABSOLUTE_DATETIME"]
    value: datetime


class TimeOfDay(BaseModel):
    kind: Literal["TIME_OF_DAY"]
    value: time


class RelativeDuration(BaseModel):
    kind: Literal["RELATIVE_DURATION"]
    value: str

    @field_validator("value")
    @classmethod
    def validate_iso_duration(cls, v: str) -> str:
        return _check_iso_duration(v)


# ─────────────────────────────────────────────────────────────────────────────
# Implicit start / end markers
# ─────────────────────────────────────────────────────────────────────────────


class ImplicitStart(BaseModel):
    kind: Literal["IMPLICIT_START"]


class ImplicitEnd(BaseModel):
    kind: Literal["IMPLICIT_END"]


# ─────────────────────────────────────────────────────────────────────────────
# Dependency / constraint reference
# ─────────────────────────────────────────────────────────────────────────────


class DependencyType(str, Enum):
    FS = "FS"
    SS = "SS"
    FF = "FF"
    SF = "SF"


class DependencyCombination(str, Enum):
    ALL_OF = "ALL_OF"
    ANY_OF = "ANY_OF"


class ConstraintRef(BaseModel):
    kind: Literal["CONSTRAINT_REF"]
    task_ids: list[str]
    dependency_type: DependencyType
    combination: DependencyCombination

    @model_validator(mode="after")
    def task_ids_non_empty(self) -> ConstraintRef:
        if not self.task_ids:
            raise ValueError("task_ids must not be empty")
        return self


# ─────────────────────────────────────────────────────────────────────────────
# Start / End condition unions  (discriminated on `kind`)
# ─────────────────────────────────────────────────────────────────────────────

StartCondition = Annotated[
    Union[
        ImplicitStart,
        AbsoluteDate,
        AbsoluteDateTime,
        TimeOfDay,
        ConstraintRef,
    ],
    Field(discriminator="kind"),
]

EndCondition = Annotated[
    Union[
        ImplicitEnd,
        AbsoluteDate,
        AbsoluteDateTime,
        TimeOfDay,
        RelativeDuration,
        ConstraintRef,
    ],
    Field(discriminator="kind"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Comment
# ─────────────────────────────────────────────────────────────────────────────


class Comment(BaseModel):
    kind: Literal["COMMENT"]
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    text: str


# ─────────────────────────────────────────────────────────────────────────────
# Gantt task
# ─────────────────────────────────────────────────────────────────────────────


class GanttElementType(str, Enum):
    TASK = "TASK"
    MILESTONE = "MILESTONE"
    VERT = "VERT"


class GanttTaskStatus(str, Enum):
    DONE = "DONE"
    ACTIVE = "ACTIVE"
    CRIT = "CRIT"


class GanttTask(BaseModel):
    kind: Literal["GANTT_TASK"]
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    name: str
    element_type: GanttElementType
    statuses: list[GanttTaskStatus]
    start: StartCondition
    end: EndCondition


# ─────────────────────────────────────────────────────────────────────────────
# Gantt section
# ─────────────────────────────────────────────────────────────────────────────

GanttSectionElement = Annotated[
    Union[GanttTask, Comment],
    Field(discriminator="kind"),
]


class GanttSection(BaseModel):
    kind: Literal["GANTT_SECTION"]
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    name: str
    elements: list[GanttSectionElement]


# ─────────────────────────────────────────────────────────────────────────────
# Gantt diagram
# ─────────────────────────────────────────────────────────────────────────────

GanttTopLevelElement = Annotated[
    Union[GanttSection, GanttTask, Comment],
    Field(discriminator="kind"),
]


class ExcludeKind(str, Enum):
    WEEKENDS = "WEEKENDS"
    DATE = "DATE"
    DAY_NAME = "DAY_NAME"


class ExcludeEntry(BaseModel):
    kind: Literal["EXCLUDE_ENTRY"]
    type: ExcludeKind
    value: Optional[str] = None


class WeekendDay(str, Enum):
    SUNDAY = "SUNDAY"
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"


class GanttDiagram(BaseModel):
    kind: Literal["GANTT_DIAGRAM"]
    id: Optional[str] = None
    trailing_comment: Optional[str] = None
    title: Optional[str] = None
    date_format: Optional[str] = None
    axis_format: Optional[str] = None
    tick_interval: Optional[str] = None
    excludes: Optional[list[ExcludeEntry]] = None
    weekend: Optional[WeekendDay] = None
    elements: list[GanttTopLevelElement]


# ─────────────────────────────────────────────────────────────────────────────
# Document root
# ─────────────────────────────────────────────────────────────────────────────

DiagramNode = Annotated[
    Union[GanttDiagram],  # extend as more diagram types are added
    Field(discriminator="kind"),
]


class Document(BaseModel):
    version: Optional[str] = None
    frontmatter: Optional[str] = None
    diagram: DiagramNode


# ═════════════════════════════════════════════════════════════════════════════
# Test data — one AST JSON per test_gantt_*.mmd file
# ═════════════════════════════════════════════════════════════════════════════

# Shorthand helpers to keep test data concise
def _date(v):   return {"kind": "ABSOLUTE_DATE",     "value": v}
def _tod(v):    return {"kind": "TIME_OF_DAY",        "value": v}
def _dur(v):    return {"kind": "RELATIVE_DURATION",  "value": v}
def _imp_s():   return {"kind": "IMPLICIT_START"}
def _imp_e():   return {"kind": "IMPLICIT_END"}
def _after(*ids): return {"kind": "CONSTRAINT_REF", "task_ids": list(ids), "dependency_type": "FS", "combination": "ALL_OF"}
def _until(*ids): return {"kind": "CONSTRAINT_REF", "task_ids": list(ids), "dependency_type": "SF", "combination": "ALL_OF"}
def _task(name, start, end, *, id=None, element_type="TASK", statuses=None, comment=None):
    return {
        "kind": "GANTT_TASK",
        "id": id,
        "trailing_comment": comment,
        "name": name,
        "element_type": element_type,
        "statuses": statuses or [],
        "start": start,
        "end": end,
    }
def _section(name, *elements):
    return {"kind": "GANTT_SECTION", "name": name, "elements": list(elements)}
def _comment(text):
    return {"kind": "COMMENT", "text": text}
def _exclude(type_, value=None):
    return {"kind": "EXCLUDE_ENTRY", "type": type_, "value": value}
def _doc(diagram, *, frontmatter=None):
    return {"version": "1.0", "frontmatter": frontmatter, "diagram": diagram}
def _gantt(elements, *, title=None, date_format=None, axis_format=None, tick_interval=None, excludes=None, weekend=None):
    return {
        "kind": "GANTT_DIAGRAM",
        "title": title,
        "date_format": date_format,
        "axis_format": axis_format,
        "tick_interval": tick_interval,
        "excludes": excludes,
        "weekend": weekend,
        "elements": elements,
    }


TEST_CASES: dict[str, dict] = {

    # ─── test_gantt_1.mmd ────────────────────────────────────────────────────
    # Two sections, basic absolute date + duration tasks, one FS dependency.
    "test_gantt_1": _doc(_gantt(
        title="A Gantt Diagram",
        date_format="YYYY-MM-DD",
        elements=[
            _section("Section",
                _task("A task",       _date("2014-01-01"), _dur("P30D"), id="a1"),
                _task("Another task", _after("a1"),        _dur("P20D")),
            ),
            _section("Another",
                _task("Task in Another", _date("2014-01-12"), _dur("P12D")),
                _task("another task",    _imp_s(),            _dur("P24D")),
            ),
        ],
    )),

    # ─── test_gantt_2.mmd ────────────────────────────────────────────────────
    # Excludes, stand-alone comment, combined statuses (crit+done),
    # date-to-date tasks (end=AbsoluteDate), 24h duration, milestone,
    # SF dependency (until), implicit starts.
    "test_gantt_2": _doc(_gantt(
        date_format="YYYY-MM-DD",
        title="Adding GANTT diagram functionality to mermaid",
        excludes=[_exclude("WEEKENDS")],
        elements=[
            _comment(
                "(`excludes` accepts specific dates in YYYY-MM-DD format, "
                "days of the week (\"sunday\") or \"weekends\", but not the word \"weekdays\".)"
            ),
            _section("A section",
                _task("Completed task", _date("2014-01-06"), _date("2014-01-08"), id="des1", statuses=["DONE"]),
                _task("Active task",    _date("2014-01-09"), _dur("P3D"),          id="des2", statuses=["ACTIVE"]),
                _task("Future task",    _after("des2"),      _dur("P5D"),          id="des3"),
                _task("Future task2",   _after("des3"),      _dur("P5D"),          id="des4"),
            ),
            _section("Critical tasks",
                _task("Completed task in the critical line", _date("2014-01-06"), _dur("PT24H"), statuses=["CRIT", "DONE"]),
                _task("Implement parser and jison",          _after("des1"),      _dur("P2D"),   statuses=["CRIT", "DONE"]),
                _task("Create tests for parser",             _imp_s(),            _dur("P3D"),   statuses=["CRIT", "ACTIVE"]),
                _task("Future task in critical line",        _imp_s(),            _dur("P5D"),   statuses=["CRIT"]),
                _task("Create tests for renderer",           _imp_s(),            _dur("P2D")),
                _task("Add to mermaid",                      _imp_s(),            _until("isadded")),
                _task("Functionality added",                 _date("2014-01-25"), _dur("P0D"),   id="isadded", element_type="MILESTONE"),
            ),
            _section("Documentation",
                _task("Describe gantt syntax",            _after("des1"), _dur("P3D"),    id="a1",   statuses=["ACTIVE"]),
                _task("Add gantt diagram to demo page",   _after("a1"),   _dur("PT20H")),
                _task("Add another diagram to demo page", _after("a1"),   _dur("PT48H"),  id="doc1"),
            ),
            _section("Last section",
                _task("Describe gantt syntax",            _after("doc1"), _dur("P3D")),
                _task("Add gantt diagram to demo page",   _imp_s(),       _dur("PT20H")),
                _task("Add another diagram to demo page", _imp_s(),       _dur("PT48H")),
            ),
        ],
    )),

    # ─── test_gantt_3.mmd ────────────────────────────────────────────────────
    # Sectionless tasks, multi-ID FS ref ("after b a"), multi-ID SF ref ("until b c").
    "test_gantt_3": _doc(_gantt(
        elements=[
            _task("apple",  _date("2017-07-20"), _dur("P1W"),           id="a"),
            _task("banana", _date("2017-07-23"), _dur("P1D"),           id="b",  statuses=["CRIT"]),
            _task("cherry", _after("b", "a"),    _dur("P1D"),           id="c",  statuses=["ACTIVE"]),
            _task("kiwi",   _date("2017-07-20"), _until("b", "c"),     id="d"),
        ],
    )),

    # ─── test_gantt_4.mmd ────────────────────────────────────────────────────
    # excludes weekends + weekend friday override.
    "test_gantt_4": _doc(_gantt(
        title="A Gantt Diagram Excluding Fri - Sat weekends",
        date_format="YYYY-MM-DD",
        excludes=[_exclude("WEEKENDS")],
        weekend="FRIDAY",
        elements=[
            _section("Section",
                _task("A task",       _date("2024-01-01"), _dur("P30D"), id="a1"),
                _task("Another task", _after("a1"),        _dur("P20D")),
            ),
        ],
    )),

    # ─── test_gantt_5.mmd ────────────────────────────────────────────────────
    # Time-axis chart (dateFormat HH:mm), TimeOfDay starts, minute durations,
    # MILESTONE status.
    "test_gantt_5": _doc(_gantt(
        date_format="HH:mm",
        axis_format="%H:%M",
        elements=[
            _task("Initial milestone", _tod("17:49:00"), _dur("PT2M"),  id="m1", element_type="MILESTONE"),
            _task("Task A",            _imp_s(),         _dur("PT10M")),
            _task("Task B",            _imp_s(),         _dur("PT5M")),
            _task("Final milestone",   _tod("18:08:00"), _dur("PT4M"),  id="m2", element_type="MILESTONE"),
        ],
    )),

    # ─── test_gantt_6.mmd ────────────────────────────────────────────────────
    # Time-axis chart, VERT status (vertical reference line markers).
    "test_gantt_6": _doc(_gantt(
        date_format="HH:mm",
        axis_format="%H:%M",
        elements=[
            _task("Initial vert", _tod("17:30:00"), _dur("PT2M"),  id="v1", element_type="VERT"),
            _task("Task A",       _imp_s(),         _dur("PT3M")),
            _task("Task B",       _imp_s(),         _dur("PT8M")),
            _task("Final vert",   _tod("17:58:00"), _dur("PT4M"),  id="v2", element_type="VERT"),
        ],
    )),

    # ─── test_gantt_7.mmd ────────────────────────────────────────────────────
    # YAML frontmatter block (displayMode: compact).
    "test_gantt_7": _doc(
        _gantt(
            title="A Gantt Diagram",
            date_format="YYYY-MM-DD",
            elements=[
                _section("Section",
                    _task("A task",       _date("2014-01-01"), _dur("P30D"), id="a1"),
                    _task("Another task", _date("2014-01-20"), _dur("P25D"), id="a2"),
                    _task("Another one",  _date("2014-02-10"), _dur("P20D"), id="a3"),
                ),
            ],
        ),
        frontmatter="displayMode: compact",
    ),

    # ─── test_gantt_8.mmd ────────────────────────────────────────────────────
    # Stand-alone comment node injected between directives and first section.
    "test_gantt_8": _doc(_gantt(
        title="A Gantt Diagram",
        date_format="YYYY-MM-DD",
        elements=[
            _comment("This is a comment"),
            _section("Section",
                _task("A task",       _date("2014-01-01"), _dur("P30D"), id="a1"),
                _task("Another task", _after("a1"),        _dur("P20D")),
            ),
            _section("Another",
                _task("Task in Another", _date("2014-01-12"), _dur("P12D")),
                _task("another task",    _imp_s(),            _dur("P24D")),
            ),
        ],
    )),
}


# ═════════════════════════════════════════════════════════════════════════════
# Runner
# ═════════════════════════════════════════════════════════════════════════════


def run_tests() -> bool:
    passed = 0
    failed = 0

    for name, data in sorted(TEST_CASES.items()):
        try:
            doc = Document.model_validate(data)
            # Round-trip: ensure model serialises back cleanly
            Document.model_validate(doc.model_dump())
            print(f"  PASS  {name}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {name}")
            # Indent the error for readability
            for line in str(exc).splitlines():
                print(f"        {line}")
            failed += 1

    print()
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def validate_file(path: Path) -> bool:
    """Validate a single JSON file against the Document model."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"  JSON parse error: {exc}")
        return False

    try:
        Document.model_validate(data)
        print(f"  PASS  {path}")
        return True
    except Exception as exc:
        print(f"  FAIL  {path}")
        for line in str(exc).splitlines():
            print(f"        {line}")
        return False


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if args:
        # File mode: validate each path supplied on the command line
        ok = all(validate_file(Path(p)) for p in args)
    else:
        # Test-suite mode: validate the built-in test cases
        print("Validating AST test cases against Pydantic models ...\n")
        ok = run_tests()

    # Optionally dump JSON Schema for the Document model
    if "--schema" in flags:
        print("\nJSON Schema (generated from Pydantic models):\n")
        print(json.dumps(Document.model_json_schema(), indent=2))

    sys.exit(0 if ok else 1)

# Mermaid AST GraphQL Schema — Plan

## Purpose

Define a language-agnostic, formal GraphQL SDL schema that acts as the **source of truth** for diagram ASTs.  Parsers emit JSON that conforms to this schema; renderers consume it.  The schema is not tied to Mermaid syntax — it represents the *structure* of a diagram, not its textual encoding.

```
User Input
   ↓
Parser (Mermaid / MS Project / …)
   ↓
AST JSON  ←─── canonicalized against this schema
   ↓
Schema validation
   ↓
Semantic validation
   ↓
Storage

AST JSON
   ↓
Renderer Interface
   ↓
[ Mermaid Renderer ]
[ MS Project Renderer ]
[ Future Renderers ]
```

The initial schema covers **Gantt charts only**, with shared primitives factored out for future diagram types.

---

## File Layout

```
schema/
  PLAN.md       ← this file
  schema.graphql ← single file containing the full schema
```

A single file is used rather than splitting by concern.  Multi-file SDL is a development-time convention that requires tooling (graphql-tools, Apollo Server, etc.) to assemble before use.  When distributed for code generation (Apollo iOS, Apollo Kotlin) or used as a formal spec reference, the schema is always a single artifact anyway.  At this schema's size there is no organisational benefit to splitting.

---

## Core Design Principles

### Strongly typed discriminator (not a string)

Every JSON node carries `kind: ElementKind!` where `ElementKind` is a schema-controlled enum — not a free string.  This lets consumers exhaustively switch on element types and enables tooling to flag unknown values.

```graphql
enum ElementKind {
  # Shared
  COMMENT

  # Date/time value types
  ABSOLUTE_DATE        # calendar date only
  ABSOLUTE_DATETIME    # full date + time
  TIME_OF_DAY          # time only (e.g. HH:mm)
  RELATIVE_DURATION    # an amount of time

  # Dependency/constraint value types
  IMPLICIT_START       # no start constraint specified
  IMPLICIT_END         # no end constraint specified
  CONSTRAINT_REF       # dependency on one or more tasks

  # Gantt structural types
  GANTT_DIAGRAM
  GANTT_SECTION
  GANTT_TASK

  # Gantt config value types
  EXCLUDE_ENTRY
}
```

New diagram types add their own values here.

### Interface hierarchy

```graphql
# Every JSON node has a kind discriminator.
interface ASTNode {
  kind: ElementKind!
}

# Structural diagram elements can be referenced by ID and may have
# a trailing inline comment.  Extends ASTNode.
interface DiagramElement implements ASTNode {
  kind:             ElementKind!
  id:               ID
  trailing_comment: String
}
```

Value types (dates, durations, refs) implement `ASTNode`.
Structural elements (tasks, sections, comments) implement `DiagramElement`.

### Ordering via arrays

Every ordered collection is an array.  Order is semantically significant and must be preserved in all diagram types.

### Comments

Stand-alone comments are injected as members of the relevant element-array union — they can appear at any position in the list.  Trailing/inline comments are a `trailing_comment: String` field on the element they annotate.

### Frontmatter

Stored as a raw text block.  Parsing the YAML content is left to the consumer.

### Strongly typed date/time

Three distinct concrete types cover the date/time space:

| Type | Scalar | Example |
|---|---|---|
| `AbsoluteDate` | `Date` (ISO 8601 date) | `"2024-01-01"` |
| `AbsoluteDateTime` | `DateTime` (ISO 8601 datetime) | `"2024-01-01T09:00:00Z"` |
| `TimeOfDay` | `Time` (ISO 8601 time) | `"17:49:00"` |

Duration / relative time uses ISO 8601 duration strings:

| Type | Scalar | Example |
|---|---|---|
| `RelativeDuration` | `ISODuration` | `"P30D"`, `"PT24H"`, `"P1W"` |

Parsers convert source-format dates (Mermaid `dateFormat`, MS Project column types) into the appropriate `AbsoluteDate`/`AbsoluteDateTime`/`TimeOfDay` type at ingestion time.

### Dependency model (start/end conditions, no nulls)

Start and end are never null.  Both use explicit union types, and dependency relationships between tasks are first-class:

```
StartCondition = ImplicitStart | AbsoluteDate | AbsoluteDateTime | TimeOfDay | ConstraintRef
EndCondition   = ImplicitEnd   | AbsoluteDate | AbsoluteDateTime | TimeOfDay | RelativeDuration | ConstraintRef
```

`ConstraintRef` encodes all four CPM relationship types:

| DependencyType | Meaning |
|---|---|
| `FS` | Finish-to-Start — this task starts after referenced task(s) finish |
| `SS` | Start-to-Start  — this task starts when referenced task(s) start |
| `FF` | Finish-to-Finish — this task ends when referenced task(s) end |
| `SF` | Start-to-Finish — this task ends when referenced task(s) start |

The field position (`start` vs `end`) plus the `dependency_type` on `ConstraintRef` fully identifies the relationship.  Mermaid's `after` maps to FS; Mermaid's `until` maps to SF.

---

## Schema (schema.graphql)

```graphql
# ─── Document root ───────────────────────────────────────────────────────────

type Document {
  version:     String
  frontmatter: String       # raw YAML block between --- markers, unparsed
  diagram:     DiagramNode!
}

union DiagramNode =
  | GanttDiagram
  # FlowchartDiagram (future)
  # SequenceDiagram  (future)
  # PieChartDiagram  (future)
  # TimelineDiagram  (future)

# ─── Scalars ────────────────────────────────────────────────────────────────

scalar Date         # ISO 8601 date:     "2024-01-01"
scalar DateTime     # ISO 8601 datetime: "2024-01-01T09:00:00Z"
scalar Time         # ISO 8601 time:     "17:49:00"
scalar ISODuration  # ISO 8601 duration: "P30D" | "PT24H" | "P1W2D"

# ─── Interfaces ─────────────────────────────────────────────────────────────

interface ASTNode {
  kind: ElementKind!
}

interface DiagramElement implements ASTNode {
  kind:             ElementKind!
  id:               ID
  trailing_comment: String
}

# ─── ElementKind enum ────────────────────────────────────────────────────────

enum ElementKind {
  COMMENT

  ABSOLUTE_DATE
  ABSOLUTE_DATETIME
  TIME_OF_DAY
  RELATIVE_DURATION

  IMPLICIT_START
  IMPLICIT_END
  CONSTRAINT_REF

  GANTT_DIAGRAM
  GANTT_SECTION
  GANTT_TASK
  EXCLUDE_ENTRY
}

# ─── Comment ─────────────────────────────────────────────────────────────────

"""
A stand-alone comment line (Mermaid: %% text).
Can appear as a member of any element-array union.
"""
type Comment implements DiagramElement & ASTNode {
  kind:             ElementKind!   # always COMMENT
  id:               ID
  trailing_comment: String
  text:             String!
}

# ─── Date/time value types ───────────────────────────────────────────────────

type AbsoluteDate implements ASTNode {
  kind:  ElementKind!   # always ABSOLUTE_DATE
  value: Date!
}

type AbsoluteDateTime implements ASTNode {
  kind:  ElementKind!   # always ABSOLUTE_DATETIME
  value: DateTime!
}

type TimeOfDay implements ASTNode {
  kind:  ElementKind!   # always TIME_OF_DAY
  value: Time!
}

type RelativeDuration implements ASTNode {
  kind:  ElementKind!   # always RELATIVE_DURATION
  value: ISODuration!
}

# ─── Implicit start/end markers ──────────────────────────────────────────────

"""
No start constraint was specified in the source.
Semantics: the scheduler or renderer determines the start
(typically: starts immediately after the previous element in the list).
"""
type ImplicitStart implements ASTNode {
  kind: ElementKind!   # always IMPLICIT_START
}

"""
No end constraint was specified in the source.
Semantics: the scheduler or renderer determines the end.
"""
type ImplicitEnd implements ASTNode {
  kind: ElementKind!   # always IMPLICIT_END
}

# ─── Dependency / constraint reference ───────────────────────────────────────

"""
Expresses a dependency on one or more tasks.

dependency_type encodes the CPM relationship:
  FS — Finish-to-Start  (default in Mermaid "after")
  SS — Start-to-Start
  FF — Finish-to-Finish
  SF — Start-to-Finish  (Mermaid "until")

When placed in `start`: the dependent side is this task's start.
When placed in `end`:   the dependent side is this task's end.

combination determines how multiple task_ids are resolved:
  ALL_OF — wait for / align with all referenced tasks (Mermaid default for "after a b")
  ANY_OF — wait for / align with the first to satisfy the condition
"""
type ConstraintRef implements ASTNode {
  kind:            ElementKind!          # always CONSTRAINT_REF
  task_ids:        [ID!]!
  dependency_type: DependencyType!
  combination:     DependencyCombination!
}

enum DependencyType {
  FS   # Finish-to-Start
  SS   # Start-to-Start
  FF   # Finish-to-Finish
  SF   # Start-to-Finish
}

enum DependencyCombination {
  ALL_OF
  ANY_OF
}

# ─── Start / End condition unions ─────────────────────────────────────────────

"""Start of a task or event."""
union StartCondition =
  | ImplicitStart
  | AbsoluteDate
  | AbsoluteDateTime
  | TimeOfDay
  | ConstraintRef

"""End of a task or event."""
union EndCondition =
  | ImplicitEnd
  | AbsoluteDate
  | AbsoluteDateTime
  | TimeOfDay
  | RelativeDuration
  | ConstraintRef
```

# ─── Gantt ───────────────────────────────────────────────────────────────────

type GanttDiagram implements DiagramElement & ASTNode {
  kind:             ElementKind!    # always GANTT_DIAGRAM
  id:               ID
  trailing_comment: String
  title:            String
  date_format:      String          # raw dateFormat directive value (day.js tokens)
  axis_format:      String          # raw axisFormat directive value (strftime tokens)
  excludes:         [ExcludeEntry!]
  weekend:          WeekendDay
  elements:         [GanttTopLevelElement!]!
}

union GanttTopLevelElement =
  | GanttSection
  | GanttTask
  | Comment

type GanttSection implements DiagramElement & ASTNode {
  kind:             ElementKind!    # always GANTT_SECTION
  id:               ID
  trailing_comment: String
  name:             String!
  elements:         [GanttSectionElement!]!
}

union GanttSectionElement =
  | GanttTask
  | Comment

"""
A single Gantt task.  Milestones and vert markers are tasks with MILESTONE
or VERT in their statuses array.
"""
type GanttTask implements DiagramElement & ASTNode {
  kind:             ElementKind!          # always GANTT_TASK
  id:               ID
  trailing_comment: String
  name:             String!
  statuses:         [GanttTaskStatus!]!   # empty list = no status keywords
  start:            StartCondition!
  end:              EndCondition!
}

enum GanttTaskStatus {
  DONE
  ACTIVE
  CRIT
  MILESTONE
  VERT
}

# ─── Excludes ────────────────────────────────────────────────────────────────

"""One token from the space-separated excludes directive."""
type ExcludeEntry implements ASTNode {
  kind:  ElementKind!   # always EXCLUDE_ENTRY
  type:  ExcludeKind!
  value: String         # null for WEEKENDS; date or day-name string otherwise
}

enum ExcludeKind {
  WEEKENDS
  DATE
  DAY_NAME
}

enum WeekendDay {
  SUNDAY
  MONDAY
  TUESDAY
  WEDNESDAY
  THURSDAY
  FRIDAY
  SATURDAY
}
```

---

## Mermaid Syntax → AST Mapping

| Mermaid source | AST `start` | AST `end` |
|---|---|---|
| `:a1, 2024-01-01, 30d` | `AbsoluteDate("2024-01-01")` | `RelativeDuration("P30D")` |
| `:after a1, 20d` | `ConstraintRef(task_ids:["a1"], FS, ALL_OF)` | `RelativeDuration("P20D")` |
| `:done, des1, 2014-01-06, 2014-01-08` | `AbsoluteDate("2014-01-06")` | `AbsoluteDate("2014-01-08")` |
| `:active, c, after b a, 1d` | `ConstraintRef(task_ids:["b","a"], FS, ALL_OF)` | `RelativeDuration("P1D")` |
| `:d, 2017-07-20, until b c` | `AbsoluteDate("2017-07-20")` | `ConstraintRef(task_ids:["b","c"], SF, ALL_OF)` |
| `:milestone, m1, 17:49, 2m` | `TimeOfDay("17:49:00")` | `RelativeDuration("PT2M")` |
| `(no start or end specified)` | `ImplicitStart` | `ImplicitEnd` |

### Test case coverage

| File | Features exercised |
|---|---|
| test_gantt_1.mmd | Section, AbsoluteDate + RelativeDuration, ConstraintRef FS |
| test_gantt_2.mmd | Combined statuses (CRIT+DONE), stand-alone Comment in elements, zero-duration milestone, ConstraintRef SF (until) |
| test_gantt_3.mmd | Sectionless tasks, multi-ID ConstraintRef FS ("after b a"), multi-ID ConstraintRef SF ("until b c") |
| test_gantt_4.mmd | ExcludeEntry WEEKENDS, WeekendDay.FRIDAY |
| test_gantt_5.mmd | TimeOfDay start values (HH:mm), MILESTONE status |
| test_gantt_6.mmd | VERT status |
| test_gantt_7.mmd | Raw frontmatter string (displayMode: compact) |
| test_gantt_8.mmd | Stand-alone Comment node in elements array |

---

## Example JSON Instance

```json
{
  "version": "1.0",
  "frontmatter": "displayMode: compact",
  "diagram": {
    "kind": "GANTT_DIAGRAM",
    "id": null,
    "trailing_comment": null,
    "title": "A Gantt Diagram",
    "date_format": "YYYY-MM-DD",
    "axis_format": null,
    "excludes": [
      { "kind": "EXCLUDE_ENTRY", "type": "WEEKENDS", "value": null }
    ],
    "weekend": null,
    "elements": [
      {
        "kind": "GANTT_SECTION",
        "id": null,
        "trailing_comment": null,
        "name": "Critical tasks",
        "elements": [
          {
            "kind": "COMMENT",
            "id": null,
            "trailing_comment": null,
            "text": "completed items first"
          },
          {
            "kind": "GANTT_TASK",
            "id": "des1",
            "trailing_comment": null,
            "name": "Completed task in the critical line",
            "statuses": ["CRIT", "DONE"],
            "start": { "kind": "ABSOLUTE_DATE",  "value": "2014-01-06" },
            "end":   { "kind": "ABSOLUTE_DATE",  "value": "2014-01-08" }
          },
          {
            "kind": "GANTT_TASK",
            "id": "des2",
            "trailing_comment": null,
            "name": "Active task",
            "statuses": ["ACTIVE"],
            "start": { "kind": "ABSOLUTE_DATE",     "value": "2014-01-09" },
            "end":   { "kind": "RELATIVE_DURATION", "value": "P3D" }
          },
          {
            "kind": "GANTT_TASK",
            "id": "isadded",
            "trailing_comment": null,
            "name": "Functionality added",
            "statuses": ["MILESTONE"],
            "start": { "kind": "ABSOLUTE_DATE",     "value": "2014-01-25" },
            "end":   { "kind": "RELATIVE_DURATION", "value": "P0D" }
          },
          {
            "kind": "GANTT_TASK",
            "id": null,
            "trailing_comment": null,
            "name": "Add to mermaid",
            "statuses": [],
            "start": { "kind": "IMPLICIT_START" },
            "end": {
              "kind":            "CONSTRAINT_REF",
              "task_ids":        ["isadded"],
              "dependency_type": "SF",
              "combination":     "ALL_OF"
            }
          },
          {
            "kind": "GANTT_TASK",
            "id": null,
            "trailing_comment": null,
            "name": "Starts after both b and a",
            "statuses": ["ACTIVE"],
            "start": {
              "kind":            "CONSTRAINT_REF",
              "task_ids":        ["b", "a"],
              "dependency_type": "FS",
              "combination":     "ALL_OF"
            },
            "end": { "kind": "RELATIVE_DURATION", "value": "P1D" }
          }
        ]
      }
    ]
  }
}
```

---

## Deferred Decisions

- **`lag` on `ConstraintRef`** — Omitted for now.  Will be added when a file format that uses it (e.g. MS Project) is integrated, at which point the appropriate type (scalar vs object) will be clearer.

- **Timeline label inheritance** — When `TimelineDiagram` is added, entries that inherit a label from the previous entry will need a flag (e.g. `inherits_label: Boolean`).  No action required now, noted for that design session.

---

## Next Steps

1. Write `schema/schema.graphql` (the single SDL file, content mirrors the schema block above).
2. Implement an AST serializer in the existing Python parser pipeline that emits JSON matching this schema.
3. Add runtime validation (Pydantic model or JSON Schema generated from the SDL).
4. Implement a Gantt renderer that reads AST JSON and produces Mermaid output.
5. Extend the `ElementKind` enum and `DiagramNode` union as other diagram types are added.

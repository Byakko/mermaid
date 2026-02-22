# Mermaid AST Pipeline

A language-agnostic AST pipeline for Mermaid diagrams. Currently supports Gantt charts.

```
.mmd text  <-->  diagram_models (Python)  <-->  AST JSON
```

Every representation is interconvertible. Full round-trips in both directions are verified for all test cases.

---

## Key Files

| File / Directory | Purpose |
|---|---|
| `schema/schema.graphql` | GraphQL SDL — source of truth for the AST shape |
| `diagram_models/` | Pure Python dataclasses mirroring the schema |
| `test_json/test_gantt_*.json` | Hand-verified AST JSON for each test diagram |
| `test_mermaid/test_gantt_*.mmd` | Corresponding Mermaid source files |

---

## Scripts

### Conversion

Low-level entry points used by other scripts and importable as modules.

| Script | Input | Output |
|---|---|---|
| `mermaid_to_python.py` | Mermaid text | `Document` |
| `python_to_mermaid.py` | `Document` | Mermaid text |
| `json_to_python.py` | AST JSON text | `Document` |
| `python_to_json.py` | `Document` | AST JSON text |

### Sanitize

Normalize formatting by round-tripping through Python objects. Accepts a file path, stdin, or interactive input; writes to a file or stdout.

| Script | Round-trip |
|---|---|
| `sanitize_json.py` | JSON → Python → JSON |
| `sanitize_mermaid.py` | Mermaid → Python → JSON → Python → Mermaid |

All sanitize scripts support the same three I/O modes and flags:

```bash
# Pipe from stdin, output to stdout
cat diagram.mmd | python sanitize_mermaid.py

# Read file, overwrite in place (prompts unless -y)
python sanitize_mermaid.py diagram.mmd

# Read from one file, write to another
python sanitize_mermaid.py input.mmd output.mmd --line-ending crlf
```

### Validate

Report pass/fail for each check; exit code 1 if anything fails.

| Script | Input | Checks |
|---|---|---|
| `validate_schema.py` | *(none)* | SDL structure; schema ↔ `diagram_models` alignment |
| `validate_json.py` | JSON file | Pydantic validation; JSON → Python → JSON round-trip |
| `validate_mermaid.py` | `.mmd` file | Mermaid → Python → JSON pipeline; Pydantic validation; JSON round-trip |

---

## Converters

| Directory | Purpose |
|---|---|
| `mermaid_to_python_converters/` | Diagram-type parsers: Mermaid text → Python objects |
| `python_to_mermaid_converters/` | Diagram-type renderers: Python objects → Mermaid text |
| `json_to_python_converters/` | Diagram-type parsers: JSON dict → Python objects |
| `python_to_json_converters/` | Diagram-type renderers: Python objects → JSON dict |

---

## Grand Round-Trip

```python
from mermaid_to_python import mermaid_to_python
from python_to_mermaid import python_to_mermaid
from json_to_python import json_to_python
from python_to_json import python_to_json

# Mermaid -> Python -> JSON -> Python -> Mermaid
doc  = mermaid_to_python(mmd_text)
j    = python_to_json(doc)
doc2 = json_to_python(j)
out  = python_to_mermaid(doc2)   # semantically identical to mmd_text

# JSON -> Python -> Mermaid -> Python -> JSON
doc  = json_to_python(json_text)
mmd  = python_to_mermaid(doc)
doc2 = mermaid_to_python(mmd)
out  = python_to_json(doc2)      # identical to json_text
```

---

## Design Decisions

### Header array instead of named directive fields

`GanttDiagram` has a `header: list[GanttHeaderElement]` rather than separate `title`, `date_format`, `axis_format`, … fields.

```json
"header": [
  { "kind": "GANTT_DIRECTIVE", "name": "TITLE",       "value": "A Gantt Diagram" },
  { "kind": "COMMENT",         "text": "some note" },
  { "kind": "GANTT_DIRECTIVE", "name": "DATE_FORMAT",  "value": "YYYY-MM-DD" }
]
```

**Why:** Named nullable fields lose the distinction between "directive was absent" and "directive was present with no value" — a meaningful difference in GraphQL. The array avoids this entirely: if a directive wasn't in the source, it simply isn't in the array. It also preserves the exact position of preamble comments.

### Typed start / end conditions

Instead of raw strings, every task's `start` and `end` are discriminated union objects:

```
StartCondition = ImplicitStart | AbsoluteDate | TimeOfDay | ConstraintRef(FS)
EndCondition   = ImplicitEnd   | AbsoluteDate | TimeOfDay | RelativeDuration | ConstraintRef(SF)
```

`ConstraintRef` encodes `after` (Finish-to-Start) and `until` (Start-to-Finish) dependencies with full support for multiple task IDs.

### GanttElementType separate from GanttTaskStatus

`element_type` (TASK / MILESTONE / VERT) describes *what the element is*. `statuses` (DONE / ACTIVE / CRIT) describe *its work state*.

### ISO 8601 in the AST

Dates are stored as ISO 8601 strings (`2024-01-01`, `17:49:00`) and durations as ISO 8601 duration strings (`P30D`, `PT24H`). Conversion to/from Mermaid's own formats (`30d`, `24h`, `HH:mm`) happens at the parser/renderer boundary.

### Comments as first-class AST nodes

`Comment` objects appear directly inside `header` and `elements` arrays, preserving their position in the source. No raw-input preservation is needed for round-tripping.

### Pure data model

`diagram_models` classes are plain Python dataclasses with no methods. The `kind` field (e.g. `"GANTT_TASK"`) is set automatically and never needs to be passed by the caller.

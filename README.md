# Mermaid AST Pipeline

A language-agnostic AST pipeline for diagram formats. Parse, convert, and render diagrams across multiple formats via a shared Python object model and JSON AST.

```
.mmd (Mermaid)  <-->  diagram_models (Python)  <-->  AST JSON  <-->  .gan (GanttProject)
```

---

## Supported Diagram Types

| Diagram type | Mermaid | AST JSON | GanttProject .gan |
|---|:---:|:---:|:---:|
| Gantt        | read/write | read/write | read/write |
| Flowchart    | read/write | — | — |
| Sequence     | read/write | — | — |
| Pie chart    | read/write | — | — |
| Timeline     | read/write | — | — |

---

## Scripts

### Conversion

Low-level converters. Each accepts/returns Python objects and is importable as a module.

| Script | Input | Output |
|---|---|---|
| `mermaid_to_python.py` | Mermaid text | `Document` |
| `python_to_mermaid.py` | `Document` | Mermaid text |
| `json_to_python.py` | AST JSON text | `Document` |
| `python_to_json.py` | `Document` | AST JSON text |
| `gan_to_python.py` | GanttProject `.gan` XML | `Document` |
| `python_to_gan.py` | `Document` | GanttProject `.gan` XML |

### Sanitize

Normalize formatting by round-tripping through Python objects and back. Accepts a file path, stdin, or interactive input; writes to a file or stdout.

| Script | Round-trip |
|---|---|
| `sanitize_json.py` | JSON → Python → JSON |
| `sanitize_mermaid.py` | Mermaid → Python → JSON → Python → Mermaid |
| `sanitize_gan.py` | `.gan` → Python → JSON → Python → `.gan` |

All sanitize scripts share the same I/O modes and flags:

```bash
# Pipe from stdin, output to stdout
cat diagram.mmd | python sanitize_mermaid.py

# Read file, overwrite in place (prompts unless -y)
python sanitize_mermaid.py diagram.mmd

# Read from one file, write to another
python sanitize_mermaid.py input.mmd output.mmd --line-ending crlf
```

### Validate

Report pass/fail for each pipeline step; exit code 1 if anything fails.

| Script | Input | Checks |
|---|---|---|
| `validate_schema.py` | *(none)* | SDL structure; schema ↔ `diagram_models` alignment |
| `validate_json.py` | `.json` file | Pydantic validation; JSON → Python → JSON round-trip |
| `validate_mermaid.py` | `.mmd` file | Mermaid → Python → JSON pipeline; Pydantic validation; JSON round-trip |
| `validate_gan.py` | `.gan` file | `.gan` → Python → JSON pipeline; Pydantic validation; JSON round-trip; `.gan` render |

---

## Converters

Converter modules live in format-specific directories and are called by the top-level scripts above.

| Directory | Purpose |
|---|---|
| `mermaid_to_python_converters/` | Mermaid text → Python objects |
| `python_to_mermaid_converters/` | Python objects → Mermaid text |
| `json_to_python_converters/` | AST JSON → Python objects |
| `python_to_json_converters/` | Python objects → AST JSON |
| `gan_to_python_converters/` | GanttProject `.gan` XML → Python objects |
| `python_to_gan_converters/` | Python objects → GanttProject `.gan` XML |

---

## Key Files

| File / Directory | Purpose |
|---|---|
| `schema/schema.graphql` | GraphQL SDL — source of truth for the AST shape |
| `diagram_models/` | Pure Python dataclasses mirroring the schema |
| `test_json/test_gantt_*.json` | Hand-verified AST JSON for each Gantt test case |
| `test_mermaid/test_gantt_*.mmd` | Corresponding Mermaid source files |
| `test_ganttproject/test_gantt_1.gan` | GanttProject round-trip test file |

---

## Known Limitations

- **JSON and .gan pipelines are Gantt-only.** Other diagram types (flowchart, sequence, pie, timeline) support Mermaid read/write only.
- **Mermaid has no lag/lead syntax.** Gantt dependency lag (`ConstraintRef.lag`) is preserved through the JSON and `.gan` pipelines but is silently dropped when rendering to Mermaid.
- **Mermaid cannot express both a duration and an end constraint on the same task.** When a task has both (possible after a `.gan` import), the Mermaid renderer emits the duration only; the constraint is preserved in JSON and `.gan`.
- **`test_pie_chart_2.mmd`** — known pre-existing round-trip failure.
- **`test_timeline_7.mmd`, `test_timeline_8.mmd`** — whitespace normalization differences expected (continuation lines folded, indentation standardized).

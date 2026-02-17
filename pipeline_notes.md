# Schedule Pipeline Design Notes

## The Problem

The goal is a construction schedule that:
- Can be viewed/shared via web Mermaid renderers (connected to GitHub)
- Can be edited reliably by AI
- Can be optimized using CPM (pyCritical)
- Is flexible enough to swap components later

## Source of Truth

The source of truth should be in whatever format AI edits most reliably. Mermaid syntax is fragile — whitespace-sensitive, positional fields, implicit ordering. JSON is a strong candidate because LLMs are heavily trained on it, validation is trivial, and errors are caught instantly.

Mermaid `.mmd` files become **build artifacts** — generated output that gets pushed to GitHub for rendering, never hand-edited.

## Pipeline

```
schedule.json  (source of truth — AI edits this)
      ↓
  parse JSON → Python objects → pyCritical → updated Python objects
      ↓
  write back to schedule.json  (updated dates/slack/critical path)
      ↓
  render to .mmd → push to GitHub → view in web renderer
```

When editing via the web renderer (copy/paste back locally):
```
  edited .mmd text → parse to Python objects → write to schedule.json
```

## Why All the Converters

The converter architecture (mtp_*, ptm_*, and eventually JSON serialization) exists to give flexibility at each boundary:

- **Mermaid text ↔ Python objects**: mtp_/ptm_ converters (already built for gantt and pie)
- **JSON ↔ Python objects**: to be built — mostly mechanical serialization of the dataclasses
- **Python objects → pyCritical format**: adapter that extracts task IDs, dependencies, durations into pyCritical's list format and maps CPM results back

Each conversion is isolated. If pyCritical gets swapped for a different optimizer, only the adapter changes. If JSON gets swapped for YAML or something else, only the serialization layer changes. The Python objects are the hub that everything converts to/from.

## JSON Schema (TODO)

Needs to capture everything from `GanttChart` / `GanttTask` dataclasses:
- Tasks: name, id, start, duration, dependencies (`after` references), statuses
- Sections: name + ordered task list
- Chart-level settings: title, dateFormat, axisFormat, excludes, weekend
- Enough metadata for faithful Mermaid round-tripping (line endings, directives, etc.)

## Open Questions

- Should the JSON include pyCritical outputs (ES/EF/LS/LF/Slack) as read-only fields, or keep those transient? Storing them would let the AI see slack when deciding what to change.
- How to handle the web-edit path — if someone edits Mermaid in the web renderer and pastes it back, the JSON needs to be updated. This is just the mtp_ parser → JSON serialization, but it should be a single command.
- Whether `crit` status on tasks should be auto-set from CPM results (zero slack = critical path) on every optimization run.

# sanitize_mermaid

A command-line tool that parses Mermaid diagram text into structured Python objects and re-emits it with consistent formatting.

## Supported Diagram Types

flowchart, sequence, class, state, er, journey, gantt, pie, mindmap, git, quadrant, timeline, c4, zenuml, sankey, xychart, block, kanban

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Pipe from stdin
cat diagram.mmd | python sanitize_mermaid.py

# Interactive mode (type/paste, then Ctrl+D / Ctrl+Z to finish)
python sanitize_mermaid.py

# Read from file, overwrite in place
python sanitize_mermaid.py diagram.mmd

# Read from input file, write to output file
python sanitize_mermaid.py input.mmd output.mmd

# Skip overwrite confirmation
python sanitize_mermaid.py -y diagram.mmd

# Use Windows-style line endings
python sanitize_mermaid.py --line-ending crlf diagram.mmd
```

### Options

| Flag | Description |
|------|-------------|
| `-l`, `--line-ending` | Line ending style: `lf` (default) or `crlf` |
| `-y`, `--yes` | Skip overwrite confirmation prompts |

## YAML Frontmatter

Diagrams may include a YAML frontmatter block before the diagram declaration. Simple `key: value` pairs between `---` markers are parsed, preserved, and re-emitted in the output.

```
---
displayMode: compact
---
gantt
    title A Gantt Diagram
    ...
```

## Comments

Gantt charts support `%%` comment lines. Comments are preserved in their original position during round-tripping.

```
gantt
    title A Gantt Diagram
    %% This is a comment
    dateFormat YYYY-MM-DD
```

## Gantt Chart Reference

### Directives

| Directive | Description |
|-----------|-------------|
| `title` | Set the chart title |
| `dateFormat` | Date input format using day.js tokens (e.g. `YYYY-MM-DD`, `HH:mm`) |
| `axisFormat` | Axis display format using strftime tokens (e.g. `%Y-%m-%d`, `%H:%M`) |
| `excludes` | Exclude dates or named periods (e.g. `weekends`, `2024-01-01`) |
| `weekend` | Override which day is treated as the weekend (e.g. `friday`) |
| `section` | Start a named section that groups subsequent tasks |

### Task Status Keywords

| Keyword | Description |
|---------|-------------|
| `done` | Mark a task as completed |
| `active` | Mark a task as in progress |
| `crit` | Mark a task as critical |
| `milestone` | Zero-duration milestone marker |
| `vert` | Vertical line marker on the timeline |

Multiple status keywords can be combined on a single task (e.g. `done, crit`).

### Task Syntax

```
Task name : [statuses], [task_id], [start], [end or duration]
```

- **statuses** -- zero or more status keywords, comma-separated
- **task_id** -- optional identifier used by `after` / `until` references
- **start** -- an absolute date, `after <id>`, or omitted to follow the previous task
- **end or duration** -- an absolute date or a duration (`3d`, `1w`, `24h`, `2m`, `1y`)

### Task References

| Reference | Description |
|-----------|-------------|
| `after <task_id>` | Start after the referenced task ends |
| `until <task_id>` | End when the referenced task starts |

# pyCritical Library Notes

Package: `pycritical` (v1.7.2, Nov 2025)
GitHub: https://github.com/Valdecy/pyCritical
Import: `from pyCritical.src.cpm_pert import ...`

## API Surface

Six functions total, in two families:

| Function | Input format | Returns |
|---|---|---|
| `critical_path_method(dataset)` | simple CPM | DataFrame |
| `critical_path_method_dep(dataset)` | CPM with dep types + lags | DataFrame |
| `pert_method(dataset)` | simple PERT | (DataFrame, duration, std_dev) |
| `pert_method_dep(dataset)` | PERT with dep types + lags | (DataFrame, duration, std_dev) |
| `gantt_chart(dataset, dates, ...)` | matplotlib plot (simple) | — |
| `gantt_chart_dep(dataset, dates, ...)` | matplotlib plot (dep) | — |

Plus two probability helpers: `date_prob(date, mean, std)` and `date_required(prob, mean, std)` for PERT schedule risk analysis.

## Input Formats

### Simple (no dependency types)

```python
# [task_id, [predecessor_ids], duration]
dataset = [
    ['A', [],          5],
    ['B', ['A'],       3],
    ['C', ['A'],       7],
    ['D', ['B', 'C'],  2],
]
```

All dependencies are implicitly **Finish-to-Start with zero lag**.

### With dependency types and lags (`_dep` variants)

```python
# [task_id, [(pred_id, dep_type, lag), ...], duration]
dataset = [
    ['A', [],                              5],
    ['B', [('A', 'FS', 0)],               3],
    ['C', [('A', 'SS', 2)],               7],
    ['D', [('B', 'FS', 0), ('C', 'FF', 1)], 2],
]
```

Dependency types: `"FS"`, `"SS"`, `"FF"`, `"SF"` — standard CPM types.
Lag is a numeric offset (can be negative).

### PERT variants

Same structure but duration is replaced with three-point estimate:

```python
# Simple PERT: [task_id, [predecessors], optimistic, most_likely, pessimistic]
['A', [], 3, 5, 9]

# PERT with deps: [task_id, [(pred_id, dep_type, lag), ...], optimistic, most_likely, pessimistic]
['A', [('B', 'FS', 0)], 3, 5, 9]
```

## Output Format

All methods return a **pandas DataFrame** indexed by task ID:

```
     ES    EF    LS    LF  Slack
A   0.0   5.0   0.0   5.0    0.0
B   5.0   8.0   9.0  12.0    4.0
C   5.0  12.0   5.0  12.0    0.0
D  12.0  14.0  12.0  14.0    0.0
```

- **ES/EF**: Earliest Start / Earliest Finish
- **LS/LF**: Latest Start / Latest Finish
- **Slack**: LF - EF (zero = critical path)

PERT methods return a tuple: `(dataframe, expected_project_duration, project_std_dev)`.

Durations are in abstract time units (not calendar dates). The library has no concept of calendar dates, weekends, or holidays.

## Mapping to/from Mermaid Gantt

### What maps cleanly

- **Task IDs**: Mermaid `task_id` → pyCritical task ID (first element)
- **Dependencies**: Mermaid `after task1` → pyCritical predecessor list
- **Duration**: Mermaid `30d` → numeric duration (need to parse the unit)

### Gaps to bridge

1. **Calendar dates → abstract time**: pyCritical works in unitless time. Mermaid gantt uses real dates (`2024-01-01`) and durations (`30d`). The adapter must:
   - Convert calendar-anchored tasks to relative offsets from project start
   - Convert pyCritical output (ES/EF in abstract units) back to calendar dates
   - Account for `excludes weekends` and similar — pyCritical doesn't handle this, so non-working days need to be factored in during the date conversion step

2. **Dependency types**: Mermaid gantt only supports `after <id>` which is Finish-to-Start. pyCritical supports FS/SS/FF/SF with lags. If we want richer dependency modeling, the Mermaid representation will lose that information on round-trip (unless we encode it in comments or extend the format).

3. **Tasks without explicit dependencies**: Mermaid allows tasks with just a start date and no `after` clause. These are "pinned" tasks — they need to be handled as having no predecessors in pyCritical, with their start date converted to an ES constraint.

4. **Sections**: pyCritical has no concept of sections/groups. Sections are purely visual in Mermaid and should be preserved through the round-trip but are irrelevant to CPM calculation.

5. **Multiple statuses**: Mermaid tasks can be `crit, active, done`, etc. These are display hints and don't affect scheduling. They could potentially be *set* from pyCritical output (e.g., marking tasks with zero slack as `crit`).

### Likely adapter shape

```
GanttChart → extract_tasks() → pyCritical dataset
                                      ↓
                              critical_path_method()
                                      ↓
                              DataFrame (ES/EF/LS/LF/Slack)
                                      ↓
                         apply_schedule(gantt, dataframe)
                                      ↓
                              updated GanttChart
```

The adapter would live outside both the converter modules and pyCritical — probably something like `schedule_optimizer.py` or similar.

## Construction-specific considerations

- Construction schedules heavily use **SS and FF dependencies with lags** (e.g., "start electrical rough-in 2 days after framing starts"). The `_dep` variants of pyCritical will be needed, not the simple ones.
- **Weather days / holidays**: Need a calendar-aware date conversion layer. pyCritical won't help here.
- The `excludes` field on `GanttChart` ("weekends", specific dates) is the Mermaid mechanism for this — the adapter should respect it when converting between abstract time and calendar dates.
- Marking critical path tasks as `crit` status in Mermaid after CPM analysis would give visual feedback in rendered diagrams.

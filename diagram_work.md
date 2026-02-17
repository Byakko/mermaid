# Diagram Converter Work Tracker

Reference docs for all diagram types: https://mermaid.js.org/intro/syntax-reference.html

## Diagram Checklist

All diagram types have Python object definitions in `mermaid/`. Each diagram
needs its converter modules written and tested from scratch.

- [x] Gantt (`mermaid/gantt.py`) - mtp + ptm converters done
- [ ] Flowchart (`mermaid/flowchart.py`)
- [ ] Sequence (`mermaid/sequence.py`)
- [ ] Class Diagram (`mermaid/class_diagram.py`)
- [ ] State Diagram (`mermaid/state_diagram.py`)
- [ ] ER Diagram (`mermaid/er_diagram.py`)
- [ ] User Journey (`mermaid/user_journey.py`)
- [x] Pie Chart (`mermaid/pie_chart.py`) - mtp + ptm converters done
- [ ] Mindmap (`mermaid/mindmap.py`)
- [ ] Git Graph (`mermaid/git_graph.py`)
- [ ] Quadrant Chart (`mermaid/quadrant_chart.py`)
- [ ] Timeline (`mermaid/timeline.py`)
- [ ] C4 Diagram (`mermaid/c4_diagram.py`)
- [ ] Kanban (`mermaid/kanban.py`)
- [ ] Block Diagram (`mermaid/block_diagram.py`)
- [ ] Packet (`mermaid/packet.py`)
- [ ] Architecture (`mermaid/architecture.py`)
- [ ] Sankey (`mermaid/sankey.py`)
- [ ] XY Chart (`mermaid/xy_chart.py`)
- [ ] ZenUML (`mermaid/zenuml.py`)
- [ ] Requirement Diagram (`mermaid/requirement_diagram.py`)
- [ ] Radar Chart (`mermaid/radar_chart.py`)
- [ ] Treemap (`mermaid/treemap.py`)

## Process: Adding Converter Support for a Diagram Type

This documents the process we followed for gantt and pie chart, and will follow for each subsequent diagram type. The goal is to create standalone converter modules that `sanitize_mermaid.py` uses, working one diagram type at a time.

### Directory Structure

```
mermaid_to_python_converters/     # text -> python object
    __init__.py
    mtp_common.py                 # shared parsing primitives
    mtp_gantt.py                  # gantt-specific parser
    mtp_<diagram>.py              # one file per diagram type

python_to_mermaid_converters/     # python object -> text
    __init__.py
    ptm_common.py                 # shared rendering utilities
    ptm_gantt.py                  # gantt-specific renderer
    ptm_<diagram>.py              # one file per diagram type

mermaid_to_python.py              # entry point: routes to mtp_* parsers
python_to_mermaid.py              # entry point: routes to ptm_* renderers
sanitize_mermaid.py               # CLI script using the above two
```

### Step-by-step Process

1. **Study the Mermaid syntax** using the reference at https://mermaid.js.org/intro/syntax-reference.html and find the specific page for the diagram type

2. **Create `mtp_<diagram>.py`** in `mermaid_to_python_converters/`
   - Write the parser for converting mermaid text to Python objects
   - Import shared primitives from `mtp_common.py`
   - Import diagram classes from `mermaid` package
   - Parsers skip comments — they are not stored on diagram objects
   - Add any new shared primitives to `mtp_common.py` if needed

3. **Create `ptm_<diagram>.py`** in `python_to_mermaid_converters/`
   - Write standalone renderer functions from scratch (e.g., `render_<type>()`)
   - The renderer returns `List[str]` of content lines only — no frontmatter, no comments, no joined string
   - Comments and frontmatter are handled upstream by `python_to_mermaid.py`, so the renderer never needs to deal with them
   - Import shared utilities from `ptm_common.py` if needed

4. **Test incrementally** — a full round-trip test won't work until both the parser and renderer are correct, so:
   - Test the parser in isolation first with known mermaid inputs
   - Test the renderer in isolation by constructing objects manually
   - Then test the full round-trip

5. **Wire up the entry points**
   - Add the new parser to the `parsers` dict in `mermaid_to_python.py`
   - Add the diagram class → renderer function mapping to the `_RENDERERS` dict in `python_to_mermaid.py`

6. **Clean up the diagram objects**
   - In `mermaid/<diagram>.py`: remove any `render()` methods from data objects (e.g., `GanttTask.render()`, `PieSlice.render()`) and remove `to_mermaid()` from the diagram class
   - Remove any comment-storage fields from diagram objects — comments are preserved by `python_to_mermaid.py` using `raw_input`

7. **Verify** that `sanitize_mermaid.py` works end-to-end with the new diagram type

### Key Design Notes

- Functions are standalone — they operate on diagram objects but live outside them
- `mtp_common.py` holds parsing primitives shared across diagram types
- `ptm_common.py` holds shared rendering utilities (e.g., `join_lines`)
- Comments and frontmatter are preserved by `python_to_mermaid.py` using `raw_input` from the original text — individual converters never see them
- Renderers return `List[str]` (content lines only), not joined strings
- `python_to_mermaid.py` uses a `_RENDERERS` dict mapping diagram class → renderer function
- Each diagram type gets its own `mtp_` and `ptm_` file — no monolithic modules

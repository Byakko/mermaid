# Diagram Converter Work Tracker

Reference docs for all diagram types: https://mermaid.js.org/intro/syntax-reference.html

## Diagram Checklist

All diagram types have Python object definitions in `mermaid/`. None of the
parsers in `sanitize_mermaid.py` are fully working — they are incomplete
reference code. Each diagram needs its converter modules written and tested
from scratch.

- [x] Gantt (`mermaid/gantt.py`) - mtp + ptm converters done
- [ ] Flowchart (`mermaid/flowchart.py`)
- [ ] Sequence (`mermaid/sequence.py`)
- [ ] Class Diagram (`mermaid/class_diagram.py`)
- [ ] State Diagram (`mermaid/state_diagram.py`)
- [ ] ER Diagram (`mermaid/er_diagram.py`)
- [ ] User Journey (`mermaid/user_journey.py`)
- [ ] Pie Chart (`mermaid/pie_chart.py`)
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

This documents the process we followed for gantt and will follow for each subsequent diagram type. The goal is to extract standalone converter modules that `sanitize_mermaid_2.py` uses, working one diagram type at a time.

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
sanitize_mermaid_2.py             # CLI script using the above two
```

### Step-by-step Process

For each diagram type, the work is the same. `sanitize_mermaid.py` has
incomplete/broken parser code that can be used as a starting reference, but
none of it works as-is. Each converter must be written and tested properly.

1. **Study the Mermaid syntax** using the reference at https://mermaid.js.org/intro/syntax-reference.html and find the specific page for the diagram type

2. **Create `mtp_<diagram>.py`** in `mermaid_to_python_converters/`
   - Write the parser for converting mermaid text to Python objects
   - Use `sanitize_mermaid.py` as a reference starting point, but expect to fix and complete the code
   - Import shared primitives from `mtp_common.py`
   - Import diagram classes from `mermaid` package
   - Add any new shared primitives to `mtp_common.py` if needed

3. **Create `ptm_<diagram>.py`** in `python_to_mermaid_converters/`
   - Extract the `render()` methods from each dataclass and the `to_mermaid()` method from the diagram class in `mermaid/<diagram>.py`
   - Rewrite them as standalone functions (e.g., `render_<type>_task()`, `render_<type>()`)
   - Import shared utilities from `ptm_common.py`

4. **Test incrementally** — a full round-trip test won't work until both the parser and renderer are correct, so:
   - Test the parser in isolation first with known mermaid inputs
   - Test the renderer in isolation by constructing objects manually
   - Then test the full round-trip

5. **Wire up the entry points**
   - Add the new parser to the `parsers` dict in `mermaid_to_python.py`
   - Add an `isinstance` branch in `python_to_mermaid.py`

6. **Comment out the original code**
   - In `sanitize_mermaid.py`: comment out the parser functions and the entry in the `parsers` dict
   - In `mermaid/<diagram>.py`: replace `render()` and `to_mermaid()` bodies with `NotImplementedError` stubs that point to the new location
   - Note: `to_mermaid()` is abstract on `Diagram`, so the stub must remain as a concrete method (not deleted), otherwise the class can't be instantiated

7. **Verify** that `sanitize_mermaid_2.py` works end-to-end with the new diagram type

### Key Design Notes

- Functions are standalone — they operate on diagram objects but live outside them
- `mtp_common.py` holds parsing primitives shared across diagram types
- `ptm_common.py` holds rendering utilities shared across diagram types (`join_lines`, `render_config`)
- `sanitize_mermaid.py` is progressively hollowed out but never deleted — it remains as reference
- `sanitize_mermaid_2.py` is the replacement CLI that imports from the converter modules
- Each diagram type gets its own `mtp_` and `ptm_` file — no monolithic modules

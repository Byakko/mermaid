"""
validate_gan.py
===============
Validate a GanttProject .gan file through the full pipeline:

  1. GAN parse      — gan_to_python:   .gan XML  -> diagram_models Document
  2. JSON render    — python_to_json:  Document  -> AST JSON
  3. Pydantic       — structural validation of the rendered JSON
  4. Round-trip     — JSON -> Python objects -> JSON (via json_to_python / python_to_json)
  5. Comparison     — round-tripped JSON must equal the rendered JSON
  6. GAN render     — json_to_python + python_to_gan: JSON -> Document -> .gan XML

Usage:
    python validate_gan.py <path/to/file.gan>
    python validate_gan.py test_ganttproject/test_gantt_1.gan
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from gan_to_python import gan_to_python
from json_to_python import json_to_python
from python_to_gan import python_to_gan
from python_to_json import python_to_json
from validate_json import _step_compare, _step_pydantic, _step_round_trip


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python validate_gan.py <path/to/file.gan>")
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
        gan_text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Step 1: GAN parse.
    doc = gan_to_python(gan_text)
    if doc is None:
        fail("GAN parse", ["gan_to_python returned None (unsupported or malformed)"])
        print(f"\nResults: {passed} passed, {failed} failed")
        sys.exit(1)
    ok(f"GAN parse  ({type(doc.diagram).__name__})")

    # Step 2: JSON render.
    json_text = python_to_json(doc)
    if json_text is None:
        fail("JSON render", ["python_to_json returned None (no renderer available)"])
        print(f"\nResults: {passed} passed, {failed} failed")
        sys.exit(1)
    ok("JSON render")

    # Parse the rendered JSON into a dict for the remaining steps.
    data = json.loads(json_text)

    # Step 3: Pydantic validation.
    errs = _step_pydantic(data)
    if errs:
        fail("Pydantic validation", errs)
    else:
        ok("Pydantic validation")

    # Step 4: Round-trip (JSON -> Python -> JSON).
    rt_json, errs = _step_round_trip(json_text)
    if errs:
        fail("Round-trip conversion", errs)
    else:
        ok("Round-trip conversion  (JSON -> Python -> JSON)")

    # Step 5: Comparison.
    if rt_json is not None:
        errs = _step_compare(data, rt_json)
        if errs:
            fail("Round-trip comparison", errs)
        else:
            ok("Round-trip comparison  (output == rendered JSON)")

    # Step 6: GAN render (JSON -> Python -> .gan).
    gan_src = rt_json if rt_json is not None else json_text
    doc2 = json_to_python(gan_src)
    if doc2 is None:
        fail("GAN render", ["json_to_python returned None"])
    else:
        gan_out = python_to_gan(doc2)
        if gan_out is None:
            fail("GAN render", ["python_to_gan returned None (no renderer available)"])
        else:
            ok("GAN render  (JSON -> Python -> .gan)")

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

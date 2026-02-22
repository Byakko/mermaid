"""
validate_schema.py
==================
Validates schema/schema.graphql structurally, then checks that the
diagram_models Python package is consistent with it.

No external dependencies are required for the structural checks.
If graphql-core is installed it is used for deeper SDL validation.

Usage:
    python validate_schema.py

Optional deeper validation:
    pip install graphql-core
    python validate_schema.py
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Union, get_args, get_origin

SCHEMA_FILE = Path(__file__).parent / "schema" / "schema.graphql"
BUILTIN_SCALARS = {"String", "Int", "Float", "Boolean", "ID"}

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight SDL parser
# ─────────────────────────────────────────────────────────────────────────────

def _strip_sdl(sdl: str) -> str:
    """Remove triple-quoted docstrings and line comments."""
    sdl = re.sub(r'""".*?"""', '', sdl, flags=re.DOTALL)
    return re.sub(r'#[^\n]*', '', sdl)


def _parse_sdl(sdl: str) -> dict:
    """
    Parse a GraphQL SDL file and return a dict with keys:
      types      : {name: [field_name, ...]}   object types only
      interfaces : {name: [field_name, ...]}
      enums      : {name: [value, ...]}
      unions     : {name: [member_name, ...]}
      scalars    : set of names
    """
    clean = _strip_sdl(sdl)
    result: dict = {
        "types": {}, "interfaces": {}, "enums": {}, "unions": {}, "scalars": set()
    }

    # ── scalars ──────────────────────────────────────────────────────────────
    for m in re.finditer(r'\bscalar\s+(\w+)', clean):
        result["scalars"].add(m.group(1))

    # ── unions ───────────────────────────────────────────────────────────────
    # Stop at the next top-level keyword.
    union_re = re.compile(
        r'\bunion\s+(\w+)\s*=(.*?)(?=\b(?:type|interface|enum|union|scalar)\b|$)',
        re.DOTALL,
    )
    for m in union_re.finditer(clean):
        name, rhs = m.group(1), m.group(2)
        # Members are CamelCase identifiers; strip | separators.
        members = re.findall(r'\b([A-Z]\w*)\b', rhs)
        result["unions"][name] = members

    # ── types and interfaces ──────────────────────────────────────────────────
    # Collect { body } blocks for each keyword-name declaration.
    decl_re = re.compile(r'\b(type|interface|enum)\s+(\w+)[^{]*\{')
    pos = 0
    for m in decl_re.finditer(clean):
        keyword, name = m.group(1), m.group(2)
        brace_open = m.end() - 1  # points at the opening {
        # Walk to the matching closing brace.
        depth, i = 0, brace_open
        while i < len(clean):
            if clean[i] == '{':
                depth += 1
            elif clean[i] == '}':
                depth -= 1
                if depth == 0:
                    body = clean[brace_open + 1:i]
                    break
            i += 1
        else:
            continue  # unclosed brace — skip

        if keyword in ('type', 'interface'):
            field_names = re.findall(r'^\s*(\w+)\s*(?:\([^)]*\))?\s*:', body, re.MULTILINE)
            if keyword == 'type':
                result["types"][name] = field_names
            else:
                result["interfaces"][name] = field_names
        elif keyword == 'enum':
            # Enum values are ALL_CAPS identifiers on their own line.
            values = re.findall(r'^\s*([A-Z_]+)\s*$', body, re.MULTILINE)
            result["enums"][name] = values

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Structural schema checks (no external deps)
# ─────────────────────────────────────────────────────────────────────────────

def _all_defined(parsed: dict) -> set[str]:
    return (
        set(parsed["types"])
        | set(parsed["interfaces"])
        | set(parsed["enums"])
        | set(parsed["unions"])
        | parsed["scalars"]
        | BUILTIN_SCALARS
    )


def check_schema_structure(parsed: dict) -> list[str]:
    errors: list[str] = []
    defined = _all_defined(parsed)

    # Union members must reference defined types.
    for union_name, members in parsed["unions"].items():
        for member in members:
            if member not in defined:
                errors.append(
                    f"Union {union_name!r}: member '{member}' is not defined"
                )

    # Interface fields must be present on all implementing types.
    # Detect implementations from the SDL: "type X implements A & B".
    clean = _strip_sdl(SCHEMA_FILE.read_text(encoding="utf-8"))
    impl_re = re.compile(r'\btype\s+(\w+)\s+implements\s+([\w\s&]+?)\s*\{')
    for m in impl_re.finditer(clean):
        type_name = m.group(1)
        ifaces = re.findall(r'\w+', m.group(2).replace('&', ' '))
        type_fields = set(parsed["types"].get(type_name, []))
        for iface in ifaces:
            for required in parsed["interfaces"].get(iface, []):
                if required not in type_fields:
                    errors.append(
                        f"Type {type_name!r} implements {iface!r} "
                        f"but is missing field '{required}'"
                    )

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# Collect Python model types from diagram_models
# ─────────────────────────────────────────────────────────────────────────────

def collect_models() -> tuple[dict, dict, dict, dict]:
    """
    Returns (dataclasses_map, enums_map, unions_map, all_vars).

    all_vars is a flat name→object dict across all modules, used for
    detecting single-member unions that Python collapses to a plain class.
    """
    import diagram_models.common as c_mod
    import diagram_models.gantt as g_mod
    import diagram_models.document as d_mod

    dataclasses_map: dict = {}
    enums_map: dict = {}
    unions_map: dict = {}
    all_vars: dict = {}

    for mod in (c_mod, g_mod, d_mod):
        for name, obj in vars(mod).items():
            if name.startswith('_'):
                continue
            all_vars[name] = obj
            if inspect.isclass(obj) and dataclasses.is_dataclass(obj):
                dataclasses_map[name] = obj
            elif inspect.isclass(obj) and issubclass(obj, Enum) and obj is not Enum:
                enums_map[name] = obj
            elif get_origin(obj) is Union:
                unions_map[name] = obj

    return dataclasses_map, enums_map, unions_map, all_vars


# ─────────────────────────────────────────────────────────────────────────────
# Schema <-> model mapping checks
# ─────────────────────────────────────────────────────────────────────────────

def check_kind_discriminators(parsed: dict, dataclasses_map: dict) -> list[str]:
    """
    Every Python dataclass with a `kind` default must name a value in
    ElementKind, and every ElementKind value must have a matching dataclass.
    """
    element_kind_values = set(parsed["enums"].get("ElementKind", []))
    if not element_kind_values:
        return ["ElementKind enum not found in schema"]

    errors: list[str] = []

    # Forward: dataclass kind → ElementKind
    kind_defaults: set[str] = set()
    for cls_name, cls in dataclasses_map.items():
        for f in dataclasses.fields(cls):
            if f.name == "kind" and f.default is not dataclasses.MISSING:
                kind_defaults.add(f.default)
                if f.default not in element_kind_values:
                    errors.append(
                        f"{cls_name}.kind = {f.default!r} "
                        f"is not a value in schema ElementKind"
                    )

    # Reverse: ElementKind → dataclass
    for val in element_kind_values:
        if val not in kind_defaults:
            errors.append(
                f"ElementKind.{val} has no corresponding Python dataclass"
            )

    return errors


def check_enum_alignment(parsed: dict, enums_map: dict) -> list[str]:
    """
    For each schema enum (excluding ElementKind) that has a same-named Python
    enum, the set of values must match exactly.
    """
    errors: list[str] = []
    for enum_name, gql_values in parsed["enums"].items():
        if enum_name == "ElementKind":
            continue
        py_enum = enums_map.get(enum_name)
        if py_enum is None:
            continue
        schema_set = set(gql_values)
        python_set = {m.name for m in py_enum}
        for v in sorted(schema_set - python_set):
            errors.append(f"{enum_name}: schema value '{v}' not in Python enum")
        for v in sorted(python_set - schema_set):
            errors.append(f"{enum_name}: Python enum value '{v}' not in schema")
    return errors


def check_object_fields(parsed: dict, dataclasses_map: dict) -> list[str]:
    """
    For each schema object type that has a same-named Python dataclass,
    every schema field name must exist on the Python class.
    """
    errors: list[str] = []
    for type_name, schema_fields in parsed["types"].items():
        py_cls = dataclasses_map.get(type_name)
        if py_cls is None:
            continue
        py_field_names = {f.name for f in dataclasses.fields(py_cls)}
        for field_name in schema_fields:
            if field_name not in py_field_names:
                errors.append(
                    f"{type_name}: schema field '{field_name}' "
                    f"not found on Python dataclass"
                )
    return errors


def check_union_members(parsed: dict, unions_map: dict, all_vars: dict) -> list[str]:
    """
    For each schema union that has a same-named Python Union alias (or a
    single-type alias that Python has collapsed to a plain class), the set
    of member type names must match.
    """
    errors: list[str] = []
    for union_name, schema_members in parsed["unions"].items():
        schema_set = set(schema_members)

        py_value = all_vars.get(union_name)
        if py_value is None:
            continue

        if get_origin(py_value) is Union:
            python_set = {cls.__name__ for cls in get_args(py_value)}
        elif inspect.isclass(py_value):
            # Single-member union collapsed to a plain class by Python's typing.
            python_set = {py_value.__name__}
        else:
            continue

        for m in sorted(schema_set - python_set):
            errors.append(f"{union_name}: schema member '{m}' not in Python Union")
        for m in sorted(python_set - schema_set):
            errors.append(f"{union_name}: Python Union member '{m}' not in schema")

    return errors


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
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

    # ── Section 1: Schema structural validation ───────────────────────────────
    print("Schema structural validation\n")

    try:
        sdl = SCHEMA_FILE.read_text(encoding="utf-8")
        ok("schema file readable")
    except Exception as e:
        fail("schema file readable", [str(e)])
        sys.exit(1)

    try:
        parsed = _parse_sdl(sdl)
        ok(
            f"SDL parsed  "
            f"({len(parsed['types'])} types, "
            f"{len(parsed['interfaces'])} interfaces, "
            f"{len(parsed['enums'])} enums, "
            f"{len(parsed['unions'])} unions, "
            f"{len(parsed['scalars'])} scalars)"
        )
    except Exception as e:
        fail("SDL parsed", [str(e)])
        sys.exit(1)

    # Optional: graphql-core deep validation
    try:
        from graphql import assert_valid_schema, build_schema  # type: ignore
        try:
            assert_valid_schema(build_schema(sdl))
            ok("GraphQL SDL valid (graphql-core)")
        except Exception as e:
            fail("GraphQL SDL valid (graphql-core)", str(e).splitlines())
    except ImportError:
        print("  NOTE  graphql-core not installed — skipping deep SDL check")
        print("        pip install graphql-core  for full type-reference validation")

    errs = check_schema_structure(parsed)
    if errs:
        fail("schema internal consistency", errs)
    else:
        ok("schema internal consistency")

    # ── Section 2: Schema <-> diagram_models mapping ────────────────────────────
    print()
    print("Schema <-> diagram_models mapping\n")

    try:
        dc_map, enum_map, union_map, all_vars = collect_models()
        ok(
            f"diagram_models importable  "
            f"({len(dc_map)} dataclasses, "
            f"{len(enum_map)} enums, "
            f"{len(union_map)} Union aliases)"
        )
    except Exception as e:
        fail("diagram_models importable", [str(e)])
        sys.exit(1)

    errs = check_kind_discriminators(parsed, dc_map)
    if errs:
        fail("kind discriminators <-> ElementKind", errs)
    else:
        ok("kind discriminators <-> ElementKind")

    errs = check_enum_alignment(parsed, enum_map)
    if errs:
        fail("enum values schema <-> Python", errs)
    else:
        ok("enum values schema <-> Python")

    errs = check_object_fields(parsed, dc_map)
    if errs:
        fail("object type fields schema <-> Python", errs)
    else:
        ok("object type fields schema <-> Python")

    errs = check_union_members(parsed, union_map, all_vars)
    if errs:
        fail("union members schema <-> Python", errs)
    else:
        ok("union members schema <-> Python")

    print(f"\nResults: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

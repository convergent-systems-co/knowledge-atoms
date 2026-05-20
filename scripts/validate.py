#!/usr/bin/env python3
"""Validate the knowledge-atoms catalog.

Walks `atoms/`, `schemas/`, `knowledge-bases/`, and `rules/` and asserts:

  1. Every `schemas/*.schema.json` parses as JSON and declares Draft 2020-12.
  2. Every `atoms/<type>/*.json` validates against:
       a. `schemas/knowledge-atom.schema.json` (base contract)
       b. `schemas/<type>.schema.json` (per-type contract, when present)
     plus per-atom invariants:
       - `id` matches the filename stem.
       - `type` matches the parent directory name.
  3. Every `knowledge-bases/<name>/composition.yml` parses as YAML and
     validates against `schemas/composition.schema.json`. Every `ref:` it
     names resolves to an atom file actually present on disk
     (version-stripped).
  4. Every `rules/<type>/*.json` parses as JSON.

Exit 0 on full pass; exit 1 on any failure; exit 2 on missing dependency.

Per Code.md §1: every `except` here makes an explicit decision — report
loudly and continue collecting errors so the run produces a complete map,
not a single first failure.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft202012Validator
except ImportError:
    print("error: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

try:
    import yaml
except ImportError:
    print("error: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO / "schemas"
ATOMS_DIR = REPO / "atoms"
KB_DIR = REPO / "knowledge-bases"
RULES_DIR = REPO / "rules"

BASE_SCHEMA_PATH = SCHEMAS_DIR / "knowledge-atom.schema.json"
COMPOSITION_SCHEMA_PATH = SCHEMAS_DIR / "composition.schema.json"

REF_PATTERN = re.compile(
    r"^knowledge-atoms://(atoms|rules)/([a-z-]+)/([a-z0-9-]+)@([0-9]+\.[0-9]+\.[0-9]+)$"
)


def _load_json(path: Path, errors: list[str]) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"{path.relative_to(REPO)}: invalid JSON ({e})")
        return None
    except OSError as e:
        errors.append(f"{path.relative_to(REPO)}: read failed ({e})")
        return None


def _load_yaml(path: Path, errors: list[str]) -> dict | None:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        errors.append(f"{path.relative_to(REPO)}: invalid YAML ({e})")
        return None
    except OSError as e:
        errors.append(f"{path.relative_to(REPO)}: read failed ({e})")
        return None


def _check_schemas() -> tuple[dict[str, Draft202012Validator], list[str]]:
    """Returns (per-type validator map, errors)."""
    errors: list[str] = []
    validators: dict[str, Draft202012Validator] = {}

    if not BASE_SCHEMA_PATH.exists():
        errors.append(f"missing base schema: {BASE_SCHEMA_PATH.relative_to(REPO)}")
        return validators, errors

    base = _load_json(BASE_SCHEMA_PATH, errors)
    if base is None:
        return validators, errors
    if base.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append(f"{BASE_SCHEMA_PATH.relative_to(REPO)}: $schema must be Draft 2020-12")
    validators["__base__"] = Draft202012Validator(base)

    if COMPOSITION_SCHEMA_PATH.exists():
        comp = _load_json(COMPOSITION_SCHEMA_PATH, errors)
        if comp is not None:
            validators["__composition__"] = Draft202012Validator(comp)

    for schema_path in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        if schema_path.name in {"knowledge-atom.schema.json", "composition.schema.json"}:
            continue
        if schema_path.name == "federation-manifest.schema.json":
            doc = _load_json(schema_path, errors)
            if doc is not None:
                validators["__federation__"] = Draft202012Validator(doc)
            continue
        type_name = schema_path.name.removesuffix(".schema.json")
        doc = _load_json(schema_path, errors)
        if doc is None:
            continue
        if doc.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{schema_path.relative_to(REPO)}: $schema must be Draft 2020-12")
        validators[type_name] = Draft202012Validator(doc)

    return validators, errors


def _check_atoms(validators: dict[str, Draft202012Validator]) -> tuple[list[str], int]:
    errors: list[str] = []
    count = 0
    if not ATOMS_DIR.exists():
        errors.append(f"missing atoms/ directory")
        return errors, count

    base_validator = validators.get("__base__")
    for path in sorted(ATOMS_DIR.rglob("*.json")):
        count += 1
        rel = path.relative_to(REPO)
        data = _load_json(path, errors)
        if data is None:
            continue

        per_atom_errors: list[str] = []

        if base_validator is not None:
            for err in base_validator.iter_errors(data):
                loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
                per_atom_errors.append(f"base-schema: {err.message} at {loc}")

        parent = path.parent.name
        type_validator = validators.get(parent)
        if type_validator is not None:
            for err in type_validator.iter_errors(data):
                loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
                per_atom_errors.append(f"{parent}-schema: {err.message} at {loc}")

        stem = path.stem
        if data.get("id") != stem:
            per_atom_errors.append(f"id={data.get('id')!r} != filename stem {stem!r}")
        if data.get("type") != parent:
            per_atom_errors.append(f"type={data.get('type')!r} != parent dir {parent!r}")

        if per_atom_errors:
            print(f"FAIL {rel}")
            for e in per_atom_errors:
                print(f"     {e}")
            errors.extend(f"{rel}: {e}" for e in per_atom_errors)
        else:
            print(f"OK   {rel}")

    return errors, count


def _atom_exists(ref: str) -> bool:
    """Resolve `knowledge-atoms://<kind>/<type>/<id>@<version>` to a file on disk.

    Version is stripped — we verify the atom exists; deeper version-pinning
    is the resolver's job (script/resolve_refs.py for #9).
    """
    match = REF_PATTERN.match(ref)
    if not match:
        return False
    kind, type_name, atom_id, _version = match.groups()
    root = ATOMS_DIR if kind == "atoms" else RULES_DIR
    return (root / type_name / f"{atom_id}.json").exists()


def _check_compositions(validators: dict[str, Draft202012Validator]) -> tuple[list[str], int]:
    errors: list[str] = []
    count = 0
    if not KB_DIR.exists():
        return errors, count

    comp_validator = validators.get("__composition__")

    for path in sorted(KB_DIR.rglob("composition.yml")):
        count += 1
        rel = path.relative_to(REPO)
        data = _load_yaml(path, errors)
        if data is None:
            continue
        per: list[str] = []
        if comp_validator is not None:
            for err in comp_validator.iter_errors(data):
                loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
                per.append(f"composition-schema: {err.message} at {loc}")
        # Check refs resolve
        for ent in data.get("entities", []) or []:
            ref = ent.get("ref", "")
            if not _atom_exists(ref):
                per.append(f"unresolved entity ref: {ref}")
        for rel_entry in data.get("relationships", []) or []:
            ref = rel_entry.get("ref", "")
            if not _atom_exists(ref):
                per.append(f"unresolved relationship ref: {ref}")
        for rule in data.get("rules", []) or []:
            ref = rule.get("ref", "")
            if not _atom_exists(ref):
                per.append(f"unresolved rule ref: {ref}")
        ch = data.get("contradiction_handling")
        if isinstance(ch, dict):
            ref = ch.get("ref", "")
            if not _atom_exists(ref):
                per.append(f"unresolved contradiction_handling ref: {ref}")

        if per:
            print(f"FAIL {rel}")
            for e in per:
                print(f"     {e}")
            errors.extend(f"{rel}: {e}" for e in per)
        else:
            print(f"OK   {rel}")

    return errors, count


def _check_rules() -> tuple[list[str], int]:
    errors: list[str] = []
    count = 0
    if not RULES_DIR.exists():
        return errors, count
    for path in sorted(RULES_DIR.rglob("*.json")):
        count += 1
        rel = path.relative_to(REPO)
        data = _load_json(path, errors)
        if data is None:
            continue
        # Per-rule minimum: must have id, type, version
        missing = [k for k in ("id", "type", "version") if k not in data]
        if missing:
            print(f"FAIL {rel}")
            print(f"     missing keys: {missing}")
            errors.append(f"{rel}: missing keys {missing}")
        elif data.get("id") != path.stem:
            print(f"FAIL {rel}")
            msg = f"id={data.get('id')!r} != filename stem {path.stem!r}"
            print(f"     {msg}")
            errors.append(f"{rel}: {msg}")
        elif data.get("type") != path.parent.name:
            print(f"FAIL {rel}")
            msg = f"type={data.get('type')!r} != parent dir {path.parent.name!r}"
            print(f"     {msg}")
            errors.append(f"{rel}: {msg}")
        else:
            print(f"OK   {rel}")
    return errors, count


def main() -> int:
    print(f"== knowledge-atoms validator (repo: {REPO}) ==\n")

    validators, schema_errs = _check_schemas()
    if schema_errs:
        print("\n-- SCHEMA ERRORS --")
        for e in schema_errs:
            print(f"  {e}")

    print("\n-- atoms/ --")
    atom_errs, atom_count = _check_atoms(validators)

    print("\n-- rules/ --")
    rule_errs, rule_count = _check_rules()

    print("\n-- knowledge-bases/ --")
    comp_errs, comp_count = _check_compositions(validators)

    all_errs = schema_errs + atom_errs + rule_errs + comp_errs
    print(
        f"\nsummary: {atom_count} atom(s), {rule_count} rule(s), "
        f"{comp_count} composition(s), {len(all_errs)} error(s)"
    )
    return 1 if all_errs else 0


if __name__ == "__main__":
    sys.exit(main())

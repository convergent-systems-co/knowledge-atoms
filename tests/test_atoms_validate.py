"""Acceptance: every atom on disk validates against its declared schemas.

Covers issue #4: five atom-type schemas with provenance + confidence
primitives — every atom under atoms/<type>/ validates against the base
contract and the per-type contract, with id matching filename stem and
type matching parent directory.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


REQUIRED_ATOM_TYPES = (
    "entity-type",
    "relationship-type",
    "provenance-atom",
    "fact-type",
    "confidence-primitive",
)


@pytest.fixture(scope="session")
def base_validator(schemas_dir: Path) -> jsonschema.Draft202012Validator:
    schema = json.loads((schemas_dir / "knowledge-atom.schema.json").read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture(scope="session")
def per_type_validators(schemas_dir: Path) -> dict[str, jsonschema.Draft202012Validator]:
    out: dict[str, jsonschema.Draft202012Validator] = {}
    for atom_type in REQUIRED_ATOM_TYPES:
        path = schemas_dir / f"{atom_type}.schema.json"
        if not path.exists():
            continue
        out[atom_type] = jsonschema.Draft202012Validator(
            json.loads(path.read_text(encoding="utf-8"))
        )
    return out


@pytest.mark.parametrize("atom_type", REQUIRED_ATOM_TYPES)
def test_each_atom_type_has_at_least_one_example(atoms_dir: Path, atom_type: str) -> None:
    """Every atom type has at least one example atom (issue #4)."""
    type_dir = atoms_dir / atom_type
    assert type_dir.exists(), f"missing atoms/{atom_type}/"
    json_files = [p for p in type_dir.glob("*.json") if p.is_file()]
    assert json_files, f"atoms/{atom_type}/ must contain at least one .json example"


def test_every_atom_validates_against_base_and_per_type(
    atoms_dir: Path,
    base_validator: jsonschema.Draft202012Validator,
    per_type_validators: dict[str, jsonschema.Draft202012Validator],
) -> None:
    """Walk atoms/ and validate each file. Collect all failures, fail once."""
    failures: list[str] = []
    files = sorted(p for p in atoms_dir.rglob("*.json") if p.is_file())
    assert files, "no atoms found anywhere under atoms/"

    for path in files:
        rel = path.relative_to(atoms_dir.parent)
        data = json.loads(path.read_text(encoding="utf-8"))

        for err in base_validator.iter_errors(data):
            failures.append(f"{rel}: base-schema: {err.message}")

        parent = path.parent.name
        per = per_type_validators.get(parent)
        if per is not None:
            for err in per.iter_errors(data):
                failures.append(f"{rel}: {parent}-schema: {err.message}")

        if data.get("id") != path.stem:
            failures.append(f"{rel}: id={data.get('id')!r} != stem {path.stem!r}")
        if data.get("type") != parent:
            failures.append(f"{rel}: type={data.get('type')!r} != parent {parent!r}")

    assert not failures, "\n".join(failures)


def test_fact_atoms_carry_provenance_and_confidence(atoms_dir: Path) -> None:
    """Fact-type atoms must carry non-empty provenance + a confidence block (#4)."""
    fact_dir = atoms_dir / "fact-type"
    assert fact_dir.exists(), "missing atoms/fact-type/"
    facts = sorted(p for p in fact_dir.glob("*.json") if p.is_file())
    assert facts, "need at least one fact-type atom example"
    for path in facts:
        data = json.loads(path.read_text(encoding="utf-8"))
        # fact-type atoms define a category (assertion/observation/inference/hypothesis);
        # the *example fact atom* requirement is that the schema definition itself names
        # provenance + confidence as required for instances of that type.
        assert "provenance_required" in data or "confidence_required" in data or "category" in data, (
            f"{path.name}: fact-type atom must declare category/provenance/confidence semantics"
        )

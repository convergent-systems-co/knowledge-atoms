"""Acceptance: schema files exist, parse, declare Draft 2020-12.

Covers issues #3 (composition), #4 (five atom-type schemas + base),
#8 (federation manifest).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


REQUIRED_SCHEMAS = [
    "knowledge-atom.schema.json",
    "composition.schema.json",
    "entity-type.schema.json",
    "relationship-type.schema.json",
    "provenance-atom.schema.json",
    "fact-type.schema.json",
    "confidence-primitive.schema.json",
    "federation-manifest.schema.json",
]


@pytest.mark.parametrize("schema_name", REQUIRED_SCHEMAS)
def test_schema_present_and_parses_as_2020_12(schemas_dir: Path, schema_name: str) -> None:
    """Every required schema exists and declares Draft 2020-12."""
    path = schemas_dir / schema_name
    assert path.exists(), f"missing {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("$schema") == "https://json-schema.org/draft/2020-12/schema", (
        f"{schema_name} must declare $schema = Draft 2020-12"
    )
    assert data.get("$id", "").startswith("https://knowledge-atoms.com/schemas/")
    assert data.get("type") == "object"


def test_base_schema_requires_provenance_and_confidence_definitions(schemas_dir: Path) -> None:
    """The base schema MUST define provenance and confidence shapes (issue #4)."""
    base = json.loads((schemas_dir / "knowledge-atom.schema.json").read_text(encoding="utf-8"))
    props = base.get("properties", {})
    assert "provenance" in props, "base schema must define a provenance property"
    assert "confidence" in props, "base schema must define a confidence property"

    confidence_props = props["confidence"].get("properties", {})
    assert "value" in confidence_props
    assert confidence_props["value"].get("minimum") == 0
    assert confidence_props["value"].get("maximum") == 1
    assert "basis" in confidence_props

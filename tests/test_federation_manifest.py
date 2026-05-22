"""Acceptance: federation manifest schema + example validates (issue #8)."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml


@pytest.fixture(scope="session")
def federation_validator(schemas_dir: Path) -> jsonschema.Draft202012Validator:
    schema = json.loads(
        (schemas_dir / "federation-manifest.schema.json").read_text(encoding="utf-8")
    )
    return jsonschema.Draft202012Validator(schema)


def test_federation_manifest_schema_declares_required_fields(schemas_dir: Path) -> None:
    schema = json.loads(
        (schemas_dir / "federation-manifest.schema.json").read_text(encoding="utf-8")
    )
    required = set(schema.get("required", []))
    # The minimum a federation manifest needs to be useful:
    for must_have in ("base_id", "base_uri", "version", "atoms_checksum", "trust"):
        assert must_have in required, f"federation manifest must require {must_have!r}"


def test_example_federation_manifest_validates(
    kb_dir: Path, federation_validator: jsonschema.Draft202012Validator
) -> None:
    path = kb_dir / "mnemosyne" / "federation.yml"
    assert path.exists(), f"missing {path}"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = list(federation_validator.iter_errors(data))
    assert not errors, "\n".join(e.message for e in errors)


def test_manifest_atoms_checksum_is_present_and_hex(kb_dir: Path) -> None:
    """Checksum must be a real hex digest so receivers can verify integrity."""
    path = kb_dir / "mnemosyne" / "federation.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    cs = data.get("atoms_checksum", "")
    assert isinstance(cs, str) and len(cs) >= 32, "atoms_checksum must be a hex digest (>=32 chars)"
    int(cs, 16)  # raises if not hex

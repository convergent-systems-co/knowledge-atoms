"""Acceptance: Mnemosyne's internal model expressed in knowledge-atoms (issue #5).

The composition at knowledge-bases/mnemosyne/composition.yml must:
  - parse as YAML
  - validate against schemas/composition.schema.json
  - reference at least Conversation, Turn, Topic, Fact, Source entities
  - resolve every ref to a real atom file on disk
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import jsonschema
import pytest
import yaml


REF_RE = re.compile(
    r"^knowledge-atoms://(atoms|rules)/([a-z-]+)/([a-z0-9-]+)@([0-9]+\.[0-9]+\.[0-9]+)$"
)


@pytest.fixture(scope="session")
def composition_validator(schemas_dir: Path) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(
        json.loads((schemas_dir / "composition.schema.json").read_text(encoding="utf-8"))
    )


@pytest.fixture(scope="session")
def mnemosyne_composition(kb_dir: Path) -> dict:
    path = kb_dir / "mnemosyne" / "composition.yml"
    assert path.exists(), f"missing {path}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_mnemosyne_composition_validates(
    mnemosyne_composition: dict,
    composition_validator: jsonschema.Draft202012Validator,
) -> None:
    errors = list(composition_validator.iter_errors(mnemosyne_composition))
    assert not errors, "\n".join(e.message for e in errors)


def test_mnemosyne_covers_required_domain_entities(mnemosyne_composition: dict) -> None:
    """Mnemosyne is cross-session semantic memory; it needs at minimum these entities."""
    aliases = {e.get("alias", "") for e in mnemosyne_composition.get("entities", [])}
    required = {"Conversation", "Turn", "Topic", "Fact", "Source"}
    missing = required - aliases
    assert not missing, f"mnemosyne composition missing required aliases: {missing}"


def test_every_mnemosyne_ref_resolves(mnemosyne_composition: dict, repo_root: Path) -> None:
    """Every ref: in the composition must resolve to a file on disk."""
    unresolved: list[str] = []
    for ent in mnemosyne_composition.get("entities", []):
        _assert_ref_resolves(ent.get("ref", ""), repo_root, unresolved)
    for rel in mnemosyne_composition.get("relationships", []):
        _assert_ref_resolves(rel.get("ref", ""), repo_root, unresolved)
    for rule in mnemosyne_composition.get("rules", []) or []:
        _assert_ref_resolves(rule.get("ref", ""), repo_root, unresolved)
    ch = mnemosyne_composition.get("contradiction_handling") or {}
    if "ref" in ch:
        _assert_ref_resolves(ch["ref"], repo_root, unresolved)
    assert not unresolved, "unresolved refs:\n" + "\n".join(unresolved)


def _assert_ref_resolves(ref: str, repo: Path, sink: list[str]) -> None:
    m = REF_RE.match(ref)
    if not m:
        sink.append(f"malformed ref: {ref!r}")
        return
    kind, type_name, atom_id, _version = m.groups()
    root = repo / ("atoms" if kind == "atoms" else "rules")
    candidate = root / type_name / f"{atom_id}.json"
    if not candidate.exists():
        sink.append(f"missing file for {ref!r} (looked at {candidate.relative_to(repo)})")

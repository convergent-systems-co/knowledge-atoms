"""Acceptance: export/import round-trip preserves content + provenance + confidence (issue #6).

The success criterion from GOALS.md §v0.1:
  "Two Mnemosyne instances merge knowledge bases via export/import without
   loss of provenance or contradiction information."

We test the round-trip on the real atoms/ tree (no mocks) and verify
bit-for-bit equality after a re-export.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def export_module(scripts_on_path):  # noqa: ARG001 -- side-effect fixture
    return importlib.import_module("export")


@pytest.fixture(scope="session")
def import_module(scripts_on_path):  # noqa: ARG001 -- side-effect fixture
    return importlib.import_module("import_catalog")


def test_export_produces_canonical_json(tmp_path: Path, export_module) -> None:
    """Exporter writes a JSON file with sorted keys for deterministic diffs."""
    out = tmp_path / "catalog.json"
    export_module.export_catalog(out)
    assert out.exists()
    raw = out.read_text(encoding="utf-8")
    # Re-export to a second location and compare bytes
    out2 = tmp_path / "catalog2.json"
    export_module.export_catalog(out2)
    assert raw == out2.read_text(encoding="utf-8"), (
        "exporter is non-deterministic; bytes differ between two runs on identical input"
    )


def test_roundtrip_preserves_content(tmp_path: Path, export_module, import_module) -> None:
    """export -> import -> export must be byte-identical."""
    out1 = tmp_path / "catalog1.json"
    export_module.export_catalog(out1)
    catalog = import_module.import_catalog(out1)
    out2 = tmp_path / "catalog2.json"
    export_module.export_catalog_from_dict(catalog, out2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_roundtrip_preserves_provenance_and_confidence(
    tmp_path: Path, export_module, import_module
) -> None:
    """Provenance arrays and confidence blocks survive round-trip bit-identically."""
    out = tmp_path / "catalog.json"
    export_module.export_catalog(out)
    data = json.loads(out.read_text(encoding="utf-8"))

    # Find at least one atom that carries provenance and one that carries confidence
    has_prov = False
    has_conf = False
    for atom in data.get("atoms", []):
        if atom.get("provenance"):
            has_prov = True
            for p in atom["provenance"]:
                assert "ref" in p and "captured_at" in p
        if atom.get("confidence"):
            has_conf = True
            c = atom["confidence"]
            assert "value" in c and "basis" in c
            assert 0 <= c["value"] <= 1

    assert has_prov, "round-trip catalog has no provenance to test against"
    assert has_conf, "round-trip catalog has no confidence to test against"

    # Re-import and re-export should preserve those values
    catalog = import_module.import_catalog(out)
    out2 = tmp_path / "catalog2.json"
    export_module.export_catalog_from_dict(catalog, out2)
    assert out.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")

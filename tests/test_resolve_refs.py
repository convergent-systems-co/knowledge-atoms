"""Acceptance: cross-base reference resolution (issue #9).

Covers:
  (a) same-base resolution
  (b) cross-base resolution via federation manifest
  (c) version-pin fallback (when exact version missing, choose latest compatible)
  (d) unresolvable reference returns explicit error (no silent fallback)
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def resolver_module(scripts_on_path):  # noqa: ARG001
    return importlib.import_module("resolve_refs")


def test_resolves_same_base_atom(resolver_module, repo_root: Path) -> None:
    """A local atom URI resolves to its path on disk."""
    resolver = resolver_module.Resolver(local_root=repo_root)
    result = resolver.resolve("knowledge-atoms://atoms/entity-type/person@1.0.0")
    assert result.found is True
    assert result.local_path is not None
    assert result.local_path.exists()


def test_unresolvable_returns_explicit_error(resolver_module, repo_root: Path) -> None:
    """A missing atom must produce a structured error, NOT silently return None."""
    resolver = resolver_module.Resolver(local_root=repo_root)
    result = resolver.resolve("knowledge-atoms://atoms/entity-type/does-not-exist@1.0.0")
    assert result.found is False
    assert result.error is not None
    assert "does-not-exist" in result.error


def test_malformed_uri_is_rejected(resolver_module, repo_root: Path) -> None:
    """Malformed URIs raise — they must never silently fall through."""
    resolver = resolver_module.Resolver(local_root=repo_root)
    result = resolver.resolve("not-a-real-uri")
    assert result.found is False
    assert result.error is not None


def test_cross_base_resolution_via_manifest(resolver_module, repo_root: Path) -> None:
    """A foreign-base URI resolves through a registered federation manifest."""
    resolver = resolver_module.Resolver(local_root=repo_root)
    resolver.register_federation_manifest(
        base_id="mnemosyne-alpha",
        manifest={
            "base_id": "mnemosyne-alpha",
            "base_uri": "knowledge-atoms://bases/mnemosyne-alpha",
            "version": "0.1.0",
            "atoms_checksum": "0" * 64,
            "trust": "self-signed",
            "atoms": [
                {
                    "ref": "knowledge-atoms://bases/mnemosyne-alpha/atoms/entity-type/topic@1.0.0",
                    "local_path": "atoms/entity-type/topic.json",
                }
            ],
        },
    )
    result = resolver.resolve(
        "knowledge-atoms://bases/mnemosyne-alpha/atoms/entity-type/topic@1.0.0"
    )
    assert result.found is True
    assert result.federation_base == "mnemosyne-alpha"


def test_version_pin_fallback_to_latest_compatible(resolver_module, repo_root: Path) -> None:
    """Requesting an older patch version finds the latest 1.0.x compatible version."""
    resolver = resolver_module.Resolver(local_root=repo_root, allow_compatible_fallback=True)
    # The catalog ships 1.0.0; requesting 1.0.0 specifically must hit
    result = resolver.resolve("knowledge-atoms://atoms/entity-type/person@1.0.0")
    assert result.found is True
    # Requesting a higher-patch version not on disk falls back to 1.0.0 when allowed
    result2 = resolver.resolve("knowledge-atoms://atoms/entity-type/person@1.0.99")
    assert result2.found is True
    assert result2.resolved_version == "1.0.0"
    assert result2.fallback_used is True

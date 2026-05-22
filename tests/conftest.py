"""Shared fixtures for the knowledge-atoms acceptance suite."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO / "scripts"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO


@pytest.fixture(scope="session")
def schemas_dir() -> Path:
    return REPO / "schemas"


@pytest.fixture(scope="session")
def atoms_dir() -> Path:
    return REPO / "atoms"


@pytest.fixture(scope="session")
def kb_dir() -> Path:
    return REPO / "knowledge-bases"


@pytest.fixture(scope="session")
def rules_dir() -> Path:
    return REPO / "rules"


@pytest.fixture(scope="session")
def scripts_on_path() -> None:
    """Make `scripts/` importable without packaging."""
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

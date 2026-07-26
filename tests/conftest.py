"""Gemeinsame Test-Fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from au.core.config import Config, load_config


@pytest.fixture(scope="session")
def cfg() -> Config:
    """Projektkonfiguration aus der Repowurzel."""
    return load_config(Path(__file__).resolve().parent.parent)


@pytest.fixture(scope="session")
def has_backend(cfg: Config) -> bool:
    return cfg.scsynth_path() is not None


@pytest.fixture(autouse=True)
def _skip_without_backend(request: pytest.FixtureRequest) -> Iterator[None]:
    """Tests mit der Marke ``audio`` werden ohne scsynth uebersprungen."""
    if request.node.get_closest_marker("audio"):
        config: Config = request.getfixturevalue("cfg")
        if config.scsynth_path() is None:
            pytest.skip("scsynth nicht verfuegbar — Audio-Test uebersprungen")
    yield


@pytest.fixture
def render_dir(tmp_path: Path) -> Path:
    d = tmp_path / "renders"
    d.mkdir(parents=True, exist_ok=True)
    return d

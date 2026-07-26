"""Ende-zu-Ende-Test des CLI-/Studio-Kurzschlusses (au compose / au serve).

Deckt den Pfad ab, den die Weboberflaeche tatsaechlich nutzt: ein Prompt
erzeugt DNA, Blueprint, geloeste Layer und einen hoerbaren, gerenderten Track
in einem einzigen Aufruf.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from au.core.config import get_config
from au.core.registry import load_registry
from au.integrator.compose import compose_track

pytestmark = [pytest.mark.audio, pytest.mark.slow]


def test_compose_track_produces_audible_output(tmp_path: Path) -> None:
    # Modulkatalog kommt aus der echten Projektwurzel (au/modules); nur die
    # Renderausgabe wandert in ein isoliertes Testverzeichnis.
    cfg = get_config()
    registry = load_registry(cfg, strict=True)
    progress: list[str] = []

    result = compose_track(
        "Ein kaltes, metallisches Album über eine verlassene Raumstation.",
        tmp_path / "out",
        duration_s=25.0,
        max_slots=3,
        seed_root=1,
        registry=registry,
        cfg=cfg,
        on_progress=progress.append,
    )

    assert progress, "on_progress sollte Fortschrittsmeldungen liefern"
    assert result.track.mix_path.is_file()

    data, sr = sf.read(str(result.track.mix_path), dtype="float64", always_2d=True)
    peak = float(np.max(np.abs(data)))
    assert 0.01 < peak < 0.95, f"Mix ist stumm oder übersteuert (peak={peak})"
    assert len(result.recipes) == 3
    assert len(result.track.stem_paths) >= 4


def test_compose_track_is_mostly_audible_not_sparse_silence(tmp_path: Path) -> None:
    """Regressionstest fuer einen echten Fund: fruehe Versionen steuerten
    JEDE Rolle -- auch foundation/harmonic_drone, die den Track tragen
    sollten -- ueber duennes Poisson-Sampling an. Ergebnis war ueberwiegend
    Stille mit vereinzelten 'Piepsern'. Kontinuierliche Rollen laufen seither
    ueber au.dsl.pattern.sustained_events statt Poisson-Dichte."""
    cfg = get_config()
    registry = load_registry(cfg, strict=True)

    result = compose_track(
        "Ein kaltes, metallisches Album über eine verlassene Raumstation.",
        tmp_path / "coverage",
        duration_s=45.0,
        max_slots=6,
        seed_root=3,
        registry=registry,
        cfg=cfg,
    )

    data, sr = sf.read(str(result.track.mix_path), dtype="float64", always_2d=True)
    mono = np.mean(np.abs(data), axis=1)
    window = sr
    n_windows = len(mono) // window
    audible_windows = sum(
        1
        for i in range(n_windows)
        if np.sqrt(np.mean(mono[i * window : (i + 1) * window] ** 2)) > 0.002
    )
    coverage = audible_windows / n_windows
    assert coverage > 0.6, f"Nur {coverage:.0%} der Sekunden hoerbar -- ueberwiegend Stille"


def test_compose_track_is_deterministic(tmp_path: Path) -> None:
    cfg = get_config()
    registry = load_registry(cfg, strict=True)

    r1 = compose_track(
        "Ein helles Glasalbum.",
        tmp_path / "a",
        duration_s=20.0,
        max_slots=2,
        seed_root=7,
        registry=registry,
        cfg=cfg,
    )
    r2 = compose_track(
        "Ein helles Glasalbum.",
        tmp_path / "b",
        duration_s=20.0,
        max_slots=2,
        seed_root=7,
        registry=registry,
        cfg=cfg,
    )

    from au.core.hashing import sha256_audio

    assert sha256_audio(r1.track.mix_path) == sha256_audio(r2.track.mix_path)

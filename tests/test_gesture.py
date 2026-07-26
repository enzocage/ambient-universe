"""Phase-2-Akzeptanz: L3-Gesten.

Aus plan.md Phase 2: "32 Instanzen jeder Geste sind paarweise unterscheidbar
(Varianzindex > 0.15) und artefaktfrei" sowie "spectral_travel jeder Geste
ueber Schwelle".
"""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from au.analysis.metrics import (
    clip_ratio,
    dc_offset,
    detect_clicks,
    spectral_travel,
    windowed_centroids,
)
from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.dsl.gesture import generate_default_gesture
from au.render.gesture import render_gesture

pytestmark = [pytest.mark.audio, pytest.mark.slow]

_MIN_OCTAVE_TRAVEL = 0.18
_MIN_PAIRWISE_DISTANCE = 0.15
_INSTANCES = 32


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=True)


@pytest.fixture(scope="module")
def bell_instances(
    registry: Registry, tmp_path_factory: pytest.TempPathFactory
) -> list[np.ndarray]:
    """Rendert 32 Gesteninstanzen einmal fuer das ganze Testmodul."""
    out_dir = tmp_path_factory.mktemp("gestures")
    manifest = registry.get("gen.object.modal_bell")
    series = []
    for i in range(_INSTANCES):
        seed = SeedPath.root(9000 + i)
        spec = generate_default_gesture(list(manifest.macros), duration_s=6.0, seed=seed)
        out = out_dir / f"g_{i}.wav"
        render_gesture("gen.object.modal_bell", spec, registry, out, seed=seed)
        data, sr = sf.read(str(out), dtype="float64", always_2d=True)
        series.append((data, sr))
    return series


def test_every_instance_is_artifact_free(bell_instances: list) -> None:
    for data, sr in bell_instances:
        clicks = detect_clicks(data, sr)
        assert clicks.count == 0, f"{clicks.count} Klick(s) bei {clicks.positions_s}"
        assert clip_ratio(data) == 0.0
        assert abs(dc_offset(data)) < 1e-3


def test_every_instance_exceeds_spectral_travel_threshold(bell_instances: list) -> None:
    shortfalls = []
    for i, (data, sr) in enumerate(bell_instances):
        centroids = windowed_centroids(data, sr, window_s=0.5)
        travel = spectral_travel(centroids)
        if travel < _MIN_OCTAVE_TRAVEL:
            shortfalls.append((i, travel))
    assert not shortfalls, f"Gesten unter der Bewegungsschwelle: {shortfalls}"


def test_instances_are_pairwise_distinguishable(bell_instances: list) -> None:
    """Keine zwei Instanzen duerfen wie eine identische Wiederholung wirken."""
    series = [windowed_centroids(data, sr, window_s=0.5) for data, sr in bell_instances]
    min_len = min(len(s) for s in series)
    matrix = np.array([s[:min_len] for s in series])
    scale = matrix.std() + 1e-9

    n = len(matrix)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            d = np.linalg.norm(matrix[i] - matrix[j]) / (scale * np.sqrt(min_len))
            distances.append(d)
    distances = np.array(distances)

    below = distances < _MIN_PAIRWISE_DISTANCE
    assert not below.any(), (
        f"{below.sum()} von {len(distances)} Paaren unter der Unterscheidbarkeits-"
        f"schwelle {_MIN_PAIRWISE_DISTANCE} (kleinste Distanz {distances.min():.3f})"
    )

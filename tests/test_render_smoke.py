"""Phase-0-Akzeptanz: NRT-Rendering, Determinismus, Renderleistung.

Akzeptanzkriterien aus plan.md, Phase 0:
  * `au doctor` meldet alle Abhaengigkeiten gruen
  * `pytest -k smoke` rendert 10 s NRT-Sinus; SHA-256 ueber 3 Laeufe identisch
  * Renderzeit 60 s Audio <= 6 s Wallclock (Referenzpatch)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import soundfile as sf

from au.core.config import Config
from au.render.probe import render_probe

pytestmark = [pytest.mark.audio, pytest.mark.smoke]

# Referenzpatch-Budget aus plan.md Phase 0.
_PERF_BUDGET_S = 6.0
_PERF_DURATION_S = 60.0


def test_renders_a_sine(render_dir: Path, cfg: Config) -> None:
    result = render_probe(render_dir / "sine.wav", duration=10.0, kind="sine", cfg=cfg)

    assert result.exit_code == 0
    assert result.path.is_file()
    assert result.path.stat().st_size > 0

    info = sf.info(str(result.path))
    assert info.samplerate == cfg.audio.sample_rate
    assert info.channels == cfg.audio.channels
    # scsynth rendert blockweise; eine Blockgroesse Ueberhang ist erwartbar.
    expected = 10.0 * cfg.audio.sample_rate
    assert expected <= info.frames <= expected + cfg.audio.block_size


def test_render_is_deterministic(render_dir: Path, cfg: Config) -> None:
    """Gleicher Score, gleicher Seed, gleiche Backend-Version -> gleicher Hash."""
    hashes = {
        render_probe(render_dir / f"det_{i}.wav", duration=10.0, kind="sine", cfg=cfg).audio_sha256
        for i in range(3)
    }
    assert len(hashes) == 1, f"Rendering ist nicht deterministisch: {hashes}"


def test_seeded_stack_is_deterministic(render_dir: Path, cfg: Config) -> None:
    """Auch der seed-gesteuerte Referenzscore muss reproduzierbar sein."""
    hashes = {
        render_probe(
            render_dir / f"stack_{i}.wav", duration=5.0, kind="stack", cfg=cfg
        ).audio_sha256
        for i in range(3)
    }
    assert len(hashes) == 1, f"Seed-gesteuertes Rendering ist nicht deterministisch: {hashes}"


def test_container_hash_is_not_a_reproducibility_criterion(render_dir: Path, cfg: Config) -> None:
    """Haelt den Befund fest, warum ``audio_sha256`` existiert.

    libsndfile schreibt bei Float-WAVs einen ``PEAK``-Chunk mit Zeitstempel in
    den Header. Zwei bit-identische Renderings koennen daher verschiedene
    Dateihashes haben. Dieser Test dokumentiert die Trennung: der Audioinhalt
    ist stabil, auch wenn der Container es nicht sein muss.
    """
    import numpy as np

    a = render_probe(render_dir / "hdr_a.wav", duration=2.0, kind="sine", cfg=cfg)
    b = render_probe(render_dir / "hdr_b.wav", duration=2.0, kind="sine", cfg=cfg)

    assert a.audio_sha256 == b.audio_sha256, "Der Audioinhalt muss stabil sein"

    data_a, _ = sf.read(str(a.path), dtype="float64", always_2d=True)
    data_b, _ = sf.read(str(b.path), dtype="float64", always_2d=True)
    assert np.array_equal(data_a, data_b), "Abtastwerte muessen bit-identisch sein"


def test_signal_is_audible_and_clean(render_dir: Path, cfg: Config) -> None:
    """Ein stiller oder uebersteuerter Render waere ein bestandener Hash und trotzdem falsch."""
    import numpy as np

    result = render_probe(render_dir / "clean.wav", duration=10.0, kind="sine", cfg=cfg)
    data, _ = sf.read(str(result.path), dtype="float64", always_2d=True)

    peak = float(np.max(np.abs(data)))
    assert peak > 0.05, f"Rendering ist praktisch stumm (Spitze {peak:.4f})"
    assert peak < 1.0, f"Rendering uebersteuert (Spitze {peak:.4f})"

    dc = float(np.mean(data))
    assert abs(dc) < 1e-3, f"Gleichanteil zu hoch: {dc:.6f}"


def test_render_meets_performance_budget(render_dir: Path, cfg: Config) -> None:
    result = render_probe(render_dir / "perf.wav", duration=_PERF_DURATION_S, kind="stack", cfg=cfg)
    assert result.wallclock_s <= _PERF_BUDGET_S, (
        f"{_PERF_DURATION_S:.0f}s Audio brauchten {result.wallclock_s:.2f}s "
        f"(Budget {_PERF_BUDGET_S:.0f}s, entspricht {result.realtime_factor:.1f}x Echtzeit)"
    )

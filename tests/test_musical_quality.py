"""Tests fuer die erweiterte musikalische Qualitaet, Motive, Harmonie und Quality-Gate."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from au.analysis.metrics import analyze_musical_quality
from au.core.seeds import SeedPath
from au.dsl.field import HarmonicField
from au.dsl.harmony import generate_structured_chord_timeline
from au.dsl.motif import generate_motif, generate_phrase
from au.dsl.section import generate_section_arrangement
from au.integrator.compose import compose_track


def test_motif_and_phrase_generation() -> None:
    seed = SeedPath.root(42)
    field = HarmonicField(root_midi=48.0, mode="aeolian")

    motif = generate_motif("m1", field, seed, length=4)
    assert len(motif.notes) == 4
    assert motif.duration_s > 0.0

    phrase = generate_phrase("p1", motif, seed, repetitions=3, pause_s=2.0)
    assert len(phrase.segments) == 3
    assert phrase.total_duration_s > motif.duration_s * 3


def test_structured_chord_timeline() -> None:
    seed = SeedPath.root(100)
    field = HarmonicField(root_midi=60.0, mode="ionian")

    prog = generate_structured_chord_timeline(60.0, field, seed=seed)
    assert len(prog.timeline.chords) >= 3
    assert len(prog.section_roots) >= 3
    assert prog.timeline.chords[0].time_s == 0.0


def test_section_arrangement() -> None:
    sec = generate_section_arrangement(60.0)
    assert sec.intro[1] == pytest.approx(10.8)
    assert sec.build[0] == pytest.approx(10.8)
    assert sec.peak[1] == pytest.approx(48.0)
    assert sec.outro == pytest.approx((48.0, 60.0))

    assert sec.is_active_in_section("foundation", 5.0) is True
    assert sec.is_active_in_section("signal_motif", 5.0) is False
    assert sec.is_active_in_section("signal_motif", 30.0) is True



def test_musical_quality_report_silence_rejection() -> None:
    # 10 Sekunden Stille
    silent_signal = np.zeros((44100 * 10, 2), dtype=np.float64)
    report = analyze_musical_quality(silent_signal, 44100)

    assert report.accepted is False
    assert any("Zu viel Stille" in r for r in report.reasons)


@pytest.mark.audio
def test_full_60s_track_musical_quality(tmp_path: Path) -> None:
    """Rendert einen realen 60-Sekunden-Track und analysiert die WAV-Datei objektiv."""
    result = compose_track(
        prompt="Schwerelose Schwebende Klänge und warme Flächen",
        output_dir=tmp_path,
        duration_s=60.0,
        seed_root=12345,
    )

    assert result.track.mix_path.exists()
    assert result.quality_report.accepted is True
    assert result.quality_report.active_signal_ratio >= 0.75
    assert -25.0 <= result.quality_report.lufs_estimated <= -10.0
    assert result.quality_report.harmonic_energy_ratio >= 0.12
    assert result.quality_report.peak_dbfs <= 0.0

"""Phase-3-Akzeptanz: L4-Klangelement.

Aus plan.md Phase 3:
  * Handgeschriebenes Rezept -> 3 Audition-Renderings in < 60s (hier: solo)
  * Transposition -7/0/+7 Halbtoene: Gate in allen drei Faellen bestanden
  * MIDI-Export in DAWs lesbar
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from au.analysis.metrics import clip_ratio, dc_offset, first_visible_loop_s
from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.field import HarmonicField
from au.modules.io.midi_export import export_midi
from au.render.audition import render_audition_solo
from au.render.element import generate_events, render_element

pytestmark = pytest.mark.audio


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=True)


@pytest.fixture
def recipe() -> ElementRecipe:
    return ElementRecipe(
        id="elm_test_bell",
        name="Test Bell",
        voice_module_id="gen.object.modal_bell",
        field=HarmonicField(root_midi=57, mode="dorian"),
        lambda_per_min=8.0,
        duration_s=20.0,
    )


def test_element_renders_within_budget(recipe: ElementRecipe, registry: Registry) -> None:
    seed = SeedPath.root(1).child("element", recipe.id)
    started = time.perf_counter()
    result, events = render_element(recipe, registry, Path(".au_cache/t_elm.wav"), seed=seed)
    wallclock = time.perf_counter() - started
    assert wallclock < 60.0, f"Rendering brauchte {wallclock:.1f}s"
    assert result.path.is_file()
    assert isinstance(events, list)


def test_events_stay_within_the_field(recipe: ElementRecipe, registry: Registry) -> None:
    seed = SeedPath.root(2).child("element", recipe.id)
    _, events = render_element(recipe, registry, Path(".au_cache/t_elm2.wav"), seed=seed)
    allowed = set(recipe.field.degrees())
    assert all(e.degree in allowed for e in events)


@pytest.mark.parametrize("semitones", [-7.0, 0.0, 7.0])
def test_transposition_preserves_audibility(
    recipe: ElementRecipe, registry: Registry, semitones: float
) -> None:
    """Akzeptanzkriterium: Transposition -7/0/+7 besteht in allen drei Faellen."""
    transposed = recipe.transposed(semitones)
    seed = SeedPath.root(3).child("element", recipe.id, str(semitones))
    out = Path(f".au_cache/t_transpose_{semitones}.wav")
    result, events = render_element(transposed, registry, out, seed=seed)

    data, _sr = sf.read(str(result.path), dtype="float64", always_2d=True)
    peak = float(np.max(np.abs(data)))
    assert peak > 0.005, f"Element bei {semitones:+.0f} HT praktisch stumm ({peak})"
    assert clip_ratio(data) == 0.0
    assert abs(dc_offset(data)) < 1e-3

    if events:
        expected_root = recipe.field.root_midi + semitones
        assert abs(transposed.field.root_midi - expected_root) < 1e-6


def test_solo_audition_normalizes_to_target_level(
    recipe: ElementRecipe, registry: Registry
) -> None:
    seed = SeedPath.root(4).child("element", recipe.id)
    result = render_audition_solo(
        recipe, registry, Path(".au_cache/t_audition.wav"), seed=seed, target_rms_dbfs=-23.0
    )
    if result.rms > 1e-6:
        measured_dbfs = 20.0 * np.log10(result.rms)
        assert abs(measured_dbfs - (-23.0)) < 1.0, f"RMS bei {measured_dbfs:.1f} dBFS statt -23"


def test_midi_export_is_readable(recipe: ElementRecipe, registry: Registry) -> None:
    seed = SeedPath.root(5).child("element", recipe.id)
    events = generate_events(recipe, seed)
    out = Path(".au_cache/t_element.mid")
    export_midi(events, recipe, out)

    import mido

    midi_file = mido.MidiFile(str(out))
    note_ons = [m for m in midi_file.tracks[0] if m.type == "note_on"]
    assert len(note_ons) == len(events)
    for msg in note_ons:
        assert 0 <= msg.note <= 127
        assert 1 <= msg.velocity <= 127


def test_loop_detector_flags_short_repetition() -> None:
    """Gegenprobe: der Detektor muss eine offensichtliche 2s-Schleife finden."""
    sr = 8000
    t = np.linspace(0, 10, sr * 10, endpoint=False)
    looped = np.sin(2 * np.pi * 220 * (t % 2.0))
    assert first_visible_loop_s(looped, sr, max_lag_s=5.0) is not None


def test_loop_detector_is_quiet_on_noise() -> None:
    rng = np.random.default_rng(0)
    noise = rng.standard_normal(8000 * 10)
    assert first_visible_loop_s(noise, 8000, max_lag_s=5.0) is None

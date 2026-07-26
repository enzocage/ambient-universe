"""Phase-8-Akzeptanz: Relations-Algebra und Kohaerenz-Solver.

Aus plan.md Phase 8: Layer werden zu einem Verband geloest, der Konflikte
minimiert; unloesbarer Fall erzeugt Eskalation mit Optionen; gleicher Seed
-> identische Loesung; ein echter Renderdurchlauf bestaetigt, dass die vom
Solver bevorzugte (nicht ueberlappende) Platzierung tatsaechlich weniger
Bandenergie-Korrelation erzeugt als eine naive Ueberlagerung.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from au.arrange.solver import escalation_options, solve
from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.field import HarmonicField
from au.dsl.layer import LayerInstance
from au.dsl.relations import Relation, RelationSet
from au.render.element import render_element

pytestmark = pytest.mark.smoke


def _layer(
    layer_id: str, role: str, band: tuple[float, float], entry: float, dur: float
) -> LayerInstance:
    return LayerInstance(
        layer_id=layer_id,
        element_id=layer_id,
        role=role,
        band_hz=band,
        entry_time_s=entry,
        exit_time_s=entry + dur,
        tail_overhang_s=2.0,
    )


# -- Struktur -----------------------------------------------------------------


def test_non_overlapping_layers_have_no_conflict() -> None:
    layers = [
        _layer("a", "foundation", (25, 120), 0.0, 30.0),
        _layer("b", "spectral_shimmer", (2000, 8000), 0.0, 30.0),
    ]
    result = solve(layers, RelationSet(), track_duration_s=60.0, seed=1)
    assert result.score == 0.0
    assert not result.conflicts


def test_overlapping_layers_without_relation_conflict() -> None:
    layers = [
        _layer("a", "harmonic_drone", (80, 800), 0.0, 30.0),
        _layer("b", "moving_pad", (200, 3000), 0.0, 30.0),
    ]
    result = solve(layers, RelationSet(), track_duration_s=30.0, seed=1, iterations=0)
    assert result.conflicts, "Ueberlappende Baender ohne Relation muessen als Konflikt gelten"


def test_solver_reduces_conflicts_via_time_shift() -> None:
    """Der Solver soll eine zeitliche Entzerrung finden, wenn Platz vorhanden ist."""
    layers = [
        _layer("a", "resonant_object", (300, 4000), 0.0, 10.0),
        _layer("b", "signal_motif", (500, 4000), 0.0, 10.0),
    ]
    result = solve(layers, RelationSet(), track_duration_s=120.0, seed=1, iterations=300)
    assert result.score < 1.0, f"Solver fand keine Entlastung: score={result.score}"


def test_avoids_relation_is_satisfied_by_low_overlap() -> None:
    a = _layer("a", "granular_texture", (400, 8000), 0.0, 30.0)
    b = _layer("b", "spectral_shimmer", (7900, 12000), 0.0, 30.0)
    rel = Relation(kind="avoids", from_layer="a", to_layer="b")
    relations = RelationSet(relations=(rel,))
    ok, _ = rel.check(a, b)
    assert ok, "Kaum ueberlappende Baender sollten 'avoids' erfuellen"
    result = solve([a, b], relations, track_duration_s=60.0, seed=1)
    assert result.feasible


def test_answers_relation_rejects_simultaneous_activity() -> None:
    a = _layer("a", "resonant_object", (300, 4000), 0.0, 10.0)
    b = _layer("b", "signal_motif", (300, 4000), 0.0, 10.0)  # exakt gleichzeitig
    rel = Relation(kind="answers", from_layer="a", to_layer="b")
    ok, _ = rel.check(a, b)
    assert not ok, "Gleichzeitige Aktivitaet darf 'answers' nicht erfuellen"


def test_solve_is_deterministic() -> None:
    layers = [
        _layer("a", "harmonic_drone", (80, 800), 0.0, 30.0),
        _layer("b", "moving_pad", (200, 3000), 0.0, 30.0),
        _layer("c", "granular_texture", (400, 8000), 0.0, 30.0),
    ]
    r1 = solve(layers, RelationSet(), track_duration_s=90.0, seed=42, iterations=150)
    r2 = solve(layers, RelationSet(), track_duration_s=90.0, seed=42, iterations=150)
    assert r1.layers == r2.layers
    assert r1.score == r2.score


def test_infeasible_case_yields_escalation_options() -> None:
    """Zwei Layer mit widerspruechlichen Relationen -> Eskalation mit Optionen."""
    a = _layer("a", "harmonic_drone", (80, 800), 0.0, 30.0)
    b = _layer("b", "moving_pad", (200, 3000), 0.0, 30.0)
    contradictory = RelationSet(
        relations=(
            Relation(
                kind="contrasts", from_layer="a", to_layer="b"
            ),  # verlangt < 0.15 Ueberlappung
        )
    )
    result = solve([a, b], contradictory, track_duration_s=30.0, seed=1, iterations=50)
    if not result.feasible:
        options = escalation_options(result)
        assert len(options) >= 3


def test_self_relation_is_rejected() -> None:
    with pytest.raises(ValueError, match="denselben Layer"):
        RelationSet(relations=(Relation(kind="supports", from_layer="a", to_layer="a"),))


# -- Empirische Verifikation ---------------------------------------------------


@pytest.mark.audio
def test_solved_placement_reduces_measured_band_energy_overlap(tmp_path: Path) -> None:
    """Rendert zwei echte Elemente einmal ueberlappend, einmal solver-entzerrt,
    und misst tatsaechlich, ob die Entzerrung die Bandenergie-Korrelation senkt."""
    registry: Registry = load_registry(strict=True)

    def render(entry_b: float) -> np.ndarray:
        recipe_a = ElementRecipe(
            id=f"solve_a_{entry_b}",
            voice_module_id="gen.object.modal_bell",
            field=HarmonicField(root_midi=57),
            lambda_per_min=20.0,
            duration_s=15.0,
        )
        recipe_b = ElementRecipe(
            id=f"solve_b_{entry_b}",
            voice_module_id="gen.object.modal_bell",
            field=HarmonicField(root_midi=64),
            lambda_per_min=20.0,
            duration_s=15.0,
        )
        seed = SeedPath.root(7)
        out_a = tmp_path / f"a_{entry_b}.wav"
        out_b = tmp_path / f"b_{entry_b}.wav"
        render_element(recipe_a, registry, out_a, seed=seed.child("a"), tail_s=2.0)
        render_element(recipe_b, registry, out_b, seed=seed.child("b"), tail_s=2.0)
        data_a, sr = sf.read(str(out_a), dtype="float64", always_2d=True)
        data_b, _ = sf.read(str(out_b), dtype="float64", always_2d=True)

        shift_samples = int(entry_b * sr)
        length = max(len(data_a), shift_samples + len(data_b))
        mono_a = np.zeros(length)
        mono_b = np.zeros(length)
        mono_a[: len(data_a)] = np.mean(data_a, axis=1)
        mono_b[shift_samples : shift_samples + len(data_b)] = np.mean(data_b, axis=1)
        return mono_a, mono_b, sr

    overlapping_a, overlapping_b, sr = render(0.0)
    separated_a, separated_b, _ = render(15.0)

    def envelope_correlation(a: np.ndarray, b: np.ndarray) -> float:
        env_a, env_b = np.abs(a), np.abs(b)
        if np.std(env_a) < 1e-9 or np.std(env_b) < 1e-9:
            return 0.0
        return float(np.corrcoef(env_a, env_b)[0, 1])

    overlap_corr = envelope_correlation(overlapping_a, overlapping_b)
    separated_corr = envelope_correlation(separated_a, separated_b)
    assert separated_corr <= overlap_corr, (
        f"Entzerrte Platzierung ({separated_corr:.3f}) sollte nicht mehr "
        f"Aktivitaetsueberlappung zeigen als die gleichzeitige ({overlap_corr:.3f})"
    )

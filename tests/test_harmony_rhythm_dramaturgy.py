"""Tests fuer Harmonik-Engine, Rhythmus-Controller, Dramaturgie-Organizer.

Diese drei Module stellen die album-/trackweite Konsistenz her, die
unabhaengige Element-Ziehungen allein nicht liefern koennen: gemeinsame
Akkordfolge (Harmonik), gemeinsames Zeitraster (Rhythmus), gemeinsamer
Intensitaetsbogen (Dramaturgie).
"""

from __future__ import annotations

import numpy as np
import pytest

from au.core.seeds import SeedPath
from au.dsl.dramaturgy import generate_arc
from au.dsl.element import ElementRecipe
from au.dsl.field import HarmonicField
from au.dsl.harmony import generate_chord_timeline
from au.dsl.pattern import poisson_density_events, sustained_events
from au.dsl.rhythm import Clock, tempo_from_character

pytestmark = pytest.mark.smoke

# -- Harmonik -----------------------------------------------------------------


def test_chord_timeline_covers_the_full_duration_without_gaps() -> None:
    field = HarmonicField(root_midi=57, mode="dorian")
    timeline = generate_chord_timeline(90.0, field, seed=SeedPath.root(1))
    assert timeline.chords[0].time_s == 0.0
    for a, b in zip(timeline.chords, timeline.chords[1:], strict=False):
        assert abs((a.time_s + a.duration_s) - b.time_s) < 1e-6, "Luecke zwischen Akkorden"
    last = timeline.chords[-1]
    assert abs((last.time_s + last.duration_s) - 90.0) < 1e-6


def test_chord_timeline_is_deterministic() -> None:
    field = HarmonicField(root_midi=57, mode="dorian")
    a = generate_chord_timeline(60.0, field, seed=SeedPath.root(5))
    b = generate_chord_timeline(60.0, field, seed=SeedPath.root(5))
    assert a.chords == b.chords


def test_degrees_at_returns_the_active_chord() -> None:
    field = HarmonicField(root_midi=57, mode="dorian")
    timeline = generate_chord_timeline(60.0, field, seed=SeedPath.root(2))
    first_chord = timeline.chords[0]
    mid_time = first_chord.time_s + first_chord.duration_s / 2
    assert timeline.degrees_at(mid_time) == first_chord.degrees


def test_shared_chords_coordinate_two_independent_elements() -> None:
    """Der eigentliche Zweck: zwei Elemente, die zur selben Zeit klingen und
    dieselbe Akkordfolge nutzen, muessen konsistente Stufen ziehen."""
    field = HarmonicField(root_midi=57, mode="dorian")
    timeline = generate_chord_timeline(60.0, field, seed=SeedPath.root(3))

    events_a = poisson_density_events(
        60.0, lambda_per_min=20.0, field=field, seed=SeedPath.root(10), chords=timeline
    )
    events_b = sustained_events(60.0, field=field, seed=SeedPath.root(11), chords=timeline)

    for event in events_a:
        allowed = timeline.degrees_at(event.time_s)
        assert event.degree in allowed, f"Event bei {event.time_s}s ausserhalb des Akkords"
    for event in events_b:
        allowed = timeline.degrees_at(event.time_s)
        assert event.degree in allowed


# -- Rhythmus -------------------------------------------------------------------


def test_clock_quantizes_toward_the_grid() -> None:
    clock = Clock(bpm=60.0, subdivision=4)  # Rasterschritt = 0.25s
    quantized = clock.quantize(1.12, strength=1.0)
    assert abs(quantized - 1.0) < 1e-9


def test_clock_partial_strength_moves_only_part_way() -> None:
    clock = Clock(bpm=60.0, subdivision=4)  # Rasterschritt 0.25s, naechster Punkt 1.0
    original = 1.12
    half = clock.quantize(original, strength=0.5)
    full = clock.quantize(original, strength=1.0)
    assert full == pytest.approx(1.0)
    assert original > half > full, (
        "Halbe Staerke muss strikt zwischen Original und vollem Snap liegen"
    )


def test_poisson_events_are_pulled_toward_the_grid() -> None:
    field = HarmonicField(root_midi=57, mode="dorian")
    clock = Clock(bpm=60.0, subdivision=2)  # Rasterschritt = 0.5s
    events = poisson_density_events(
        120.0,
        lambda_per_min=30.0,
        field=field,
        seed=SeedPath.root(4),
        clock=clock,
        quantize_strength=1.0,
    )
    assert events, "Testparameter sollten Ereignisse erzeugen"
    step = clock.grid_step_s
    for event in events:
        nearest_grid = round(event.time_s / step) * step
        assert abs(event.time_s - nearest_grid) < 1e-6


def test_tempo_from_character_stays_in_ambient_range() -> None:
    slow = tempo_from_character(0.0, 0.0)
    fast = tempo_from_character(1.0, 1.0)
    assert 30.0 <= slow <= fast <= 96.0


# -- Dramaturgie ----------------------------------------------------------------


def test_arc_starts_and_ends_at_zero() -> None:
    arc = generate_arc(120.0, seed=SeedPath.root(1))
    assert arc.intensities[0] == 0.0
    assert arc.intensities[-1] == 0.0
    assert arc.times_s[0] == 0.0
    assert arc.times_s[-1] == 120.0


def test_arc_has_at_least_one_real_peak() -> None:
    arc = generate_arc(120.0, seed=SeedPath.root(2))
    assert max(arc.intensities) > 0.5


def test_arc_is_deterministic() -> None:
    a = generate_arc(90.0, seed=SeedPath.root(9))
    b = generate_arc(90.0, seed=SeedPath.root(9))
    assert a == b


def test_arc_interpolates_monotonically_between_breakpoints() -> None:
    arc = generate_arc(100.0, seed=SeedPath.root(3))
    a_t, b_t = arc.times_s[0], arc.times_s[1]
    a_v, b_v = arc.intensities[0], arc.intensities[1]
    mid = arc.intensity_at((a_t + b_t) / 2)
    lo, hi = sorted((a_v, b_v))
    assert lo - 1e-9 <= mid <= hi + 1e-9


def test_arc_sample_returns_n_points_covering_the_duration() -> None:
    arc = generate_arc(60.0, seed=SeedPath.root(1))
    points = arc.sample(20)
    assert len(points) == 20
    times = np.array([t for t, _ in points])
    assert times[0] == pytest.approx(0.0)
    assert times[-1] == pytest.approx(60.0)


# -- Verdrahtung in den Score (structural, nicht nur Modell-Ebene) -------------


@pytest.mark.audio
def test_intensity_curve_is_actually_scheduled_into_the_score() -> None:
    """Belegt die Verdrahtung direkt im OSC-Bundle statt indirekt ueber
    Audioanalyse: eine 4s-Fenster-Centroid-Messung war gegen die eigene
    Wavetable-/Unison-Drift der Stimme zu unempfindlich, um eine langsame
    Makro-Rampe zuverlaessig zu erkennen (realer Befund bei der Verifikation
    dieses Features). Die tatsaechlich geplanten Steuerwerte sind eindeutig."""
    from au.core.registry import load_registry
    from au.dsl.dramaturgy import DramaturgyArc
    from au.render.compiler import compile_graph
    from au.render.element import _element_graph, build_element_score, generate_events

    registry = load_registry(strict=True)
    recipe = ElementRecipe(
        id="dram_wiring_test",
        voice_module_id="gen.drone.wavetable_resonator",
        field=HarmonicField(root_midi=45),
        pattern_kind="sustained",
        duration_s=40.0,
        macro="brightness",
        voice_macros={"brightness": 0.3},
    )
    seed = SeedPath.root(1).child("dram_wiring_test")
    graph = _element_graph(recipe.voice_module_id)
    compiled = compile_graph(graph, registry, name="dram_wiring", seed=seed)
    events = generate_events(recipe, seed)

    rising = DramaturgyArc(times_s=(0.0, 40.0), intensities=(0.0, 1.0))
    curve = rising.sample(10)
    score = build_element_score(
        compiled.synthdef,
        dict(compiled.controls),
        events,
        recipe,
        tail_s=2.0,
        intensity_curve=curve,
    )

    scheduled: list[tuple[float, float]] = []
    for bundle in score.iterate_osc_bundles():
        for msg in bundle.contents:
            if getattr(msg, "address", None) == "/n_set":
                contents = msg.contents
                if len(contents) >= 3 and contents[1] == "voice_brightness":
                    scheduled.append((bundle.timestamp, float(contents[2])))

    assert len(scheduled) >= 10, "Erwarte mindestens einen Set-Befehl je Kurvenpunkt"
    values = [v for _, v in scheduled]
    assert values == sorted(values), "Werte muessen mit der steigenden Intensitaet mitsteigen"
    assert values[-1] - values[0] > 0.3, "Der Hub sollte deutlich hoerbar sein, nicht nur messbar"

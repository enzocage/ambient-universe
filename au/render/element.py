"""Rendert ein L4-Klangelement: Pattern + Feld + Stimme -> eine Audiodatei.

Jedes Notenereignis ist eine eigene Synth-Instanz mit eigener Tonhoehe
(``mod.ctrl.constant`` -> ``voice.pitch``) und eigener Huellkurve (Attack/
Release ueber die ``amplitude``-Kontrolle). Mehrere Ereignisse ueberlappen im
selben Score — das ist im NRT-Modus unproblematisch, jede Synth-Instanz laeuft
unabhaengig.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from au.core.config import Config, get_config
from au.core.graph import Edge, Node, PatchGraph
from au.core.ports import PortType
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.pattern import NoteEvent, euclid_sparse_events, poisson_density_events, sustained_events
from au.render.backend import RenderResult, render_score
from au.render.compiler import compile_graph

if TYPE_CHECKING:  # pragma: no cover
    import supriya

    from au.core.registry import Registry
    from au.dsl.harmony import ChordTimeline
    from au.dsl.rhythm import Clock


def _element_graph(voice_module_id: str) -> PatchGraph:
    """Ein Element ist strukturell: Tonhoehenquelle -> Stimme."""
    return PatchGraph(
        level=4,
        nodes=[
            Node(node_id="pitch", module_id="mod.ctrl.constant"),
            Node(node_id="voice", module_id=voice_module_id),
        ],
        edges=[Edge(src=("pitch", "out"), dst=("voice", "pitch"), kind=PortType.CTRL)],
        exports={"out": ("voice", "out")},
    )


def generate_events(
    recipe: ElementRecipe,
    seed: SeedPath,
    *,
    chords: ChordTimeline | None = None,
    clock: Clock | None = None,
) -> list[NoteEvent]:
    """Erzeugt die Ereignisse eines Rezepts.

    ``chords``/``clock`` sind Trackkontext, kein Bestandteil des Rezepts
    selbst (ein Element bleibt dadurch eigenstaendig transponierbar und
    wiederverwendbar, plan.md 4.4) -- ``compose_track`` reicht sie ein, wenn
    eine geteilte Harmonik-/Rhythmus-Engine fuer den Track existiert.
    """
    if recipe.pattern_kind == "sustained":
        return sustained_events(recipe.duration_s, field=recipe.field, seed=seed, chords=chords)
    if recipe.pattern_kind == "poisson":
        return poisson_density_events(
            recipe.duration_s,
            lambda_per_min=recipe.lambda_per_min,
            field=recipe.field,
            seed=seed,
            chords=chords,
            clock=clock,
        )
    return euclid_sparse_events(
        recipe.duration_s,
        pulses=recipe.euclid_pulses,
        steps=recipe.euclid_steps,
        step_duration_s=recipe.euclid_step_s,
        field=recipe.field,
        seed=seed,
        chords=chords,
        clock=clock,
    )


def build_element_score(
    compiled: supriya.SynthDef,
    controls: dict[str, float],
    events: list[NoteEvent],
    recipe: ElementRecipe,
    *,
    tail_s: float = 8.0,
    intensity_curve: list[tuple[float, float]] | None = None,
    intensity_depth: float = 0.35,
) -> supriya.Score:
    """Baut den Score: ein Synth pro Ereignis, jeweils eigene Huellkurve.

    ``tail_s`` haengt der Renderdauer an, damit Nachhall/Ausklang des letzten
    Ereignisses nicht abgeschnitten wird — genau die "Nachhall vergessen"-
    Falle, vor der plan.md (MI-L5-Direktive) ausdruecklich warnt.

    ``intensity_curve``: (Zeit, Intensitaet 0..1)-Punkte des Dramaturgie-
    Organizers (au.dsl.dramaturgy). Wenn gesetzt, wird an jedem Punkt das
    Makro ``recipe.macro`` auf allen zu diesem Zeitpunkt aktiven Synths
    proportional zur Intensitaet angehoben (``intensity_depth`` begrenzt den
    Hub, damit der Bogen fuehlbar bleibt, ohne das Klangbild zu sprengen).
    """
    import supriya

    score = supriya.Score()
    with score.at(0.0):
        score.add_synthdefs(compiled)

    macro_control = f"voice_{recipe.macro}"
    # Der Pitch-Konstantenknoten exponiert sein Makro "level" — dessen
    # Kontrollwert liegt wie jedes Makro in [0, 1], nicht in MIDI-Einheiten.
    # Die Rueckrechnung geschieht hier, nicht im Modul, damit das Modul ein
    # gewoehnliches Makro bleibt und keine Sonderrolle braucht.
    pitch_control = "pitch_level"
    base_macro = controls.get(macro_control, 0.5)

    active_synths: list[tuple[NoteEvent, Any]] = []

    for event in events:
        pitch = event.pitch_midi(recipe.field)
        pitch_fraction = max(0.0, min(1.0, pitch / 127.0))
        attack = min(recipe.attack_s, event.duration_s * 0.4)
        release = min(recipe.release_s, event.duration_s * 0.4)
        release_start = max(attack, event.duration_s - release)

        values = dict(controls)
        values[pitch_control] = pitch_fraction
        values["amplitude"] = 0.0
        values[macro_control] = min(1.0, base_macro + 0.1 * event.velocity)

        with score.at(event.time_s):
            synth = score.add_synth(compiled, **values)  # type: ignore[arg-type]
        with score.at(event.time_s + attack):
            synth.set(amplitude=event.velocity)
        with score.at(event.time_s + release_start):
            synth.set(amplitude=event.velocity)
        with score.at(event.time_s + event.duration_s):
            synth.set(amplitude=0.0)
        active_synths.append((event, synth))

    if intensity_curve:
        for t, intensity in intensity_curve:
            target = max(0.0, min(1.0, base_macro + (intensity - 0.5) * 2.0 * intensity_depth))
            for event, synth in active_synths:
                if event.time_s <= t <= event.time_s + event.duration_s:
                    with score.at(t):
                        synth.set(**{macro_control: target})

    end = recipe.duration_s + tail_s
    with score.at(end):
        score.do_nothing()
    return score


def render_element(
    recipe: ElementRecipe,
    registry: Registry,
    output_path: Path,
    *,
    seed: SeedPath,
    cfg: Config | None = None,
    tail_s: float = 8.0,
    chords: ChordTimeline | None = None,
    clock: Clock | None = None,
    intensity_curve: list[tuple[float, float]] | None = None,
) -> tuple[RenderResult, list[NoteEvent]]:
    """Rendert ein Element solo in eine Audiodatei."""
    c = cfg or get_config()
    graph = _element_graph(recipe.voice_module_id)
    compiled = compile_graph(graph, registry, name=f"elm_{recipe.id}", seed=seed, cfg=c)

    controls = dict(compiled.controls)
    for macro, value in recipe.voice_macros.items():
        control_name = f"voice_{macro}"
        if control_name in controls:
            controls[control_name] = max(0.0, min(1.0, value))

    events = generate_events(recipe, seed, chords=chords, clock=clock)
    score = build_element_score(
        compiled.synthdef, controls, events, recipe, tail_s=tail_s, intensity_curve=intensity_curve
    )
    duration = recipe.duration_s + tail_s
    result = render_score(score, output_path, duration=duration, cfg=c)
    return result, events

"""Rendert ein L4-Klangelement: Pattern + Feld + Stimme -> eine Audiodatei.

Jedes Notenereignis ist eine eigene Synth-Instanz mit eigener Tonhoehe
(``mod.ctrl.constant`` -> ``voice.pitch``) und eigener Huellkurve (Attack/
Release ueber die ``amplitude``-Kontrolle). Mehrere Ereignisse ueberlappen im
selben Score — das ist im NRT-Modus unproblematisch, jede Synth-Instanz laeuft
unabhaengig.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from au.core.config import Config, get_config
from au.core.graph import Edge, Node, PatchGraph
from au.core.ports import PortType
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.pattern import NoteEvent, euclid_sparse_events, poisson_density_events
from au.render.backend import RenderResult, render_score
from au.render.compiler import compile_graph

if TYPE_CHECKING:  # pragma: no cover
    import supriya

    from au.core.registry import Registry


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


def generate_events(recipe: ElementRecipe, seed: SeedPath) -> list[NoteEvent]:
    if recipe.pattern_kind == "poisson":
        return poisson_density_events(
            recipe.duration_s,
            lambda_per_min=recipe.lambda_per_min,
            field=recipe.field,
            seed=seed,
        )
    return euclid_sparse_events(
        recipe.duration_s,
        pulses=recipe.euclid_pulses,
        steps=recipe.euclid_steps,
        step_duration_s=recipe.euclid_step_s,
        field=recipe.field,
        seed=seed,
    )


def build_element_score(
    compiled: supriya.SynthDef,
    controls: dict[str, float],
    events: list[NoteEvent],
    recipe: ElementRecipe,
    *,
    tail_s: float = 8.0,
) -> supriya.Score:
    """Baut den Score: ein Synth pro Ereignis, jeweils eigene Huellkurve.

    ``tail_s`` haengt der Renderdauer an, damit Nachhall/Ausklang des letzten
    Ereignisses nicht abgeschnitten wird — genau die "Nachhall vergessen"-
    Falle, vor der plan.md (MI-L5-Direktive) ausdruecklich warnt.
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

    for event in events:
        pitch = event.pitch_midi(recipe.field)
        pitch_fraction = max(0.0, min(1.0, pitch / 127.0))
        attack = min(recipe.attack_s, event.duration_s * 0.4)
        release = min(recipe.release_s, event.duration_s * 0.4)
        release_start = max(attack, event.duration_s - release)

        values = dict(controls)
        values[pitch_control] = pitch_fraction
        values["amplitude"] = 0.0
        values[macro_control] = min(1.0, controls.get(macro_control, 0.5) + 0.1 * event.velocity)

        with score.at(event.time_s):
            synth = score.add_synth(compiled, **values)  # type: ignore[arg-type]
        with score.at(event.time_s + attack):
            synth.set(amplitude=event.velocity)
        with score.at(event.time_s + release_start):
            synth.set(amplitude=event.velocity)
        with score.at(event.time_s + event.duration_s):
            synth.set(amplitude=0.0)

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

    events = generate_events(recipe, seed)
    score = build_element_score(compiled.synthdef, controls, events, recipe, tail_s=tail_s)
    duration = recipe.duration_s + tail_s
    result = render_score(score, output_path, duration=duration, cfg=c)
    return result, events

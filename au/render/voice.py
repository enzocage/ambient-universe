"""Rendern einzelner Stimmen und Graphen (L1/L2).

Diese Schicht steht zwischen dem SynthDef-Compiler und dem NRT-Backend. Sie
baut aus einem kompilierten Graphen einen Score — entweder mit festen
Makrostellungen (Vorhoeren) oder mit einer Rampe ueber ein Makro (Sweep-Test).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from au.core.config import Config, get_config
from au.core.graph import PatchGraph
from au.core.seeds import SeedPath
from au.render.backend import RenderResult, render_score
from au.render.compiler import CompiledSynthDef, compile_graph

if TYPE_CHECKING:  # pragma: no cover
    import supriya

    from au.core.registry import Registry


@dataclass(frozen=True, slots=True)
class MacroRamp:
    """Eine lineare Fahrt eines Makros ueber die gesamte Renderdauer."""

    control: str
    start: float = 0.0
    end: float = 1.0
    steps: int = 240
    """Stuetzstellen. Der Compiler glaettet ohnehin; die Rampe muss nur fein
    genug sein, dass die Glaettung nicht zwischen den Stufen einrastet."""


def build_score(
    compiled: CompiledSynthDef,
    *,
    duration: float,
    settings: dict[str, float] | None = None,
    ramp: MacroRamp | None = None,
) -> supriya.Score:
    """Baut einen NRT-Score aus einer kompilierten SynthDef.

    Args:
        settings: Feste Steuerwerte, etwa ``{"drone_brightness": 0.8}``.
        ramp: Optional eine Makrofahrt. Sie wird in Stufen gesetzt; die
            Glaettung des Compilers macht daraus eine stetige Bewegung.
    """
    import supriya

    score = supriya.Score()
    values = dict(compiled.controls)
    if settings:
        values.update(settings)
    if ramp is not None:
        values[ramp.control] = ramp.start

    with score.at(0.0):
        score.add_synthdefs(compiled.synthdef)
        synth = score.add_synth(compiled.synthdef, **values)  # type: ignore[arg-type]

    if ramp is not None:
        for index in range(1, ramp.steps + 1):
            fraction = index / ramp.steps
            moment = duration * fraction
            with score.at(moment):
                synth.set(**{ramp.control: ramp.start + (ramp.end - ramp.start) * fraction})

    with score.at(duration):
        score.do_nothing()
    return score


@dataclass(frozen=True, slots=True)
class Breakpoint:
    """Ein Stuetzpunkt (Zeit in Sekunden, Wert) einer Automationskurve."""

    time_s: float
    value: float


@dataclass(frozen=True, slots=True)
class AutomationTrack:
    """Eine ueber die Zeit interpolierte Steuerung eines Controls.

    ``points`` muss nach ``time_s`` aufsteigend sortiert sein und die
    Renderdauer abdecken (erster Punkt bei 0, letzter bei ``duration``) —
    das stellt der Aufrufer sicher, nicht diese Klasse.
    """

    control: str
    points: tuple[Breakpoint, ...]

    def value_at(self, t: float) -> float:
        pts = self.points
        if t <= pts[0].time_s:
            return pts[0].value
        if t >= pts[-1].time_s:
            return pts[-1].value
        for a, b in itertools.pairwise(pts):
            if a.time_s <= t <= b.time_s:
                span = b.time_s - a.time_s
                frac = (t - a.time_s) / span if span > 0 else 0.0
                return a.value + (b.value - a.value) * frac
        return pts[-1].value


def build_automated_score(
    compiled: CompiledSynthDef,
    *,
    duration: float,
    tracks: list[AutomationTrack],
    settings: dict[str, float] | None = None,
    steps_per_second: float = 8.0,
) -> supriya.Score:
    """Baut einen Score mit mehreren gleichzeitig automatisierten Controls.

    Verallgemeinert :func:`build_score`: statt einer einzelnen linearen Rampe
    treibt jede Spur ihre eigene, stueckweise lineare Kurve. Das ist die
    Grundlage der L3-Geste (plan.md 4.3): Amplitude und mindestens ein Makro
    bewegen sich unabhaengig ueber die Ereignisdauer.
    """
    import supriya

    score = supriya.Score()
    values = dict(compiled.controls)
    if settings:
        values.update(settings)
    for track in tracks:
        values[track.control] = track.points[0].value

    with score.at(0.0):
        score.add_synthdefs(compiled.synthdef)
        synth = score.add_synth(compiled.synthdef, **values)  # type: ignore[arg-type]

    step_count = max(1, round(duration * steps_per_second))
    for index in range(1, step_count + 1):
        moment = duration * index / step_count
        updates = {t.control: t.value_at(moment) for t in tracks}
        with score.at(moment):
            synth.set(**updates)

    with score.at(duration):
        score.do_nothing()
    return score


def render_graph(
    graph: PatchGraph,
    registry: Registry,
    output_path: Path,
    *,
    duration: float,
    seed: SeedPath,
    name: str = "au_graph",
    settings: dict[str, float] | None = None,
    ramp: MacroRamp | None = None,
    cfg: Config | None = None,
) -> tuple[RenderResult, CompiledSynthDef]:
    """Uebersetzt einen Graphen und rendert ihn offline in eine Datei."""
    c = cfg or get_config()
    compiled = compile_graph(graph, registry, name=name, seed=seed, cfg=c)
    score = build_score(compiled, duration=duration, settings=settings, ramp=ramp)
    result = render_score(score, output_path, duration=duration, cfg=c)
    return result, compiled


def single_voice_graph(module_id: str, node_id: str = "voice", **params: Any) -> PatchGraph:
    """Kuerzel fuer den haeufigsten Fall: eine Stimme allein."""
    from au.core.graph import Node

    return PatchGraph(
        level=2,
        nodes=[Node(node_id=node_id, module_id=module_id, params=params)],
        exports={"out": (node_id, "out")},
    )

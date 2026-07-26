"""Rendert eine L3-Geste auf einer L2-Stimme.

Verbindet :mod:`au.dsl.gesture` (die Spezifikation) mit dem Compiler und dem
Automations-Score: Amplitude folgt der Huellkurve, das gewaehlte Makro folgt
seiner Trajektorie. Beides laeuft ueber denselben Mechanismus
(:class:`au.render.voice.AutomationTrack`), damit Attack/Release und
Makrobewegung frei zueinander phasenversetzt sein koennen.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from au.core.config import Config, get_config
from au.core.seeds import SeedPath
from au.dsl.gesture import GestureSpec
from au.render.backend import RenderResult, render_score
from au.render.compiler import compile_graph
from au.render.voice import AutomationTrack, Breakpoint, single_voice_graph

if TYPE_CHECKING:  # pragma: no cover
    from au.core.registry import Registry


def _to_tracks(spec: GestureSpec) -> list[AutomationTrack]:
    amplitude = AutomationTrack(
        control="amplitude",
        points=tuple(Breakpoint(p.time_s, p.value) for p in spec.amplitude_points()),
    )
    macro = AutomationTrack(
        control=f"voice_{spec.macro}",
        points=tuple(Breakpoint(p.time_s, p.value) for p in spec.macro_points),
    )
    return [amplitude, macro]


def render_gesture(
    module_id: str,
    spec: GestureSpec,
    registry: Registry,
    output_path: Path,
    *,
    seed: SeedPath,
    cfg: Config | None = None,
) -> RenderResult:
    """Rendert eine Geste auf der angegebenen Stimme in eine Audiodatei."""
    c = cfg or get_config()
    graph = single_voice_graph(module_id, "voice")
    compiled = compile_graph(graph, registry, name="gesture_voice", seed=seed, cfg=c)
    from au.render.voice import build_automated_score

    score = build_automated_score(compiled, duration=spec.duration_s, tracks=_to_tracks(spec))
    return render_score(score, output_path, duration=spec.duration_s, cfg=c)

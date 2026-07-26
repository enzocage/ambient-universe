"""Makro-Sweep-Testharness (plan.md Phase 2, Akzeptanzkriterium).

Prueft fuer eine Stimme und ein Makro, dass eine Fahrt von 0 nach 1 ueber die
volle Renderdauer artefaktfrei bleibt: keine Klicks, kein Clipping, kein
Gleichanteil, keine nennenswerte Energie oberhalb der Nyquist-Reserve. Das ist
das *Makroversprechen* aus plan.md 4.2 messbar gemacht, nicht nur behauptet.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from au.analysis.metrics import (
    ClickReport,
    clip_ratio,
    dc_offset,
    detect_clicks,
    high_frequency_energy_ratio,
    peak,
    rms,
)
from au.core.config import Config, get_config
from au.core.knowledge import dsp_rules
from au.core.seeds import SeedPath
from au.render.voice import MacroRamp, render_graph, single_voice_graph

if TYPE_CHECKING:  # pragma: no cover
    from au.core.registry import Registry


@dataclass(frozen=True, slots=True)
class SweepResult:
    """Messwerte einer einzelnen Makrofahrt."""

    module_id: str
    macro: str
    duration_s: float
    clicks: ClickReport
    clip_fraction: float
    dc: float
    high_freq_ratio: float
    peak_level: float
    rms_level: float

    def problems(
        self,
        *,
        max_clip_fraction: float = 0.0,
        max_dc: float = 1e-3,
        max_high_freq_ratio: float = 1e-3,
    ) -> list[str]:
        """Menschenlesbare Liste der verletzten Kriterien; leer = bestanden."""
        issues: list[str] = []
        if self.clicks.count > 0:
            issues.append(
                f"{self.clicks.count} Klick(s) bei {self.macro}-Sweep, "
                f"erste bei {self.clicks.positions_s} s"
            )
        if self.clip_fraction > max_clip_fraction:
            issues.append(
                f"Clipping ueber {max_clip_fraction:.4%} der Samples "
                f"({self.clip_fraction:.4%}) bei {self.macro}"
            )
        if abs(self.dc) > max_dc:
            issues.append(f"Gleichanteil {self.dc:+.2e} bei {self.macro} ueber {max_dc:.0e}")
        if self.high_freq_ratio > max_high_freq_ratio:
            issues.append(
                f"{self.high_freq_ratio:.2%} Energie oberhalb der Nyquist-Reserve "
                f"bei {self.macro} (Grenze {max_high_freq_ratio:.2%})"
            )
        return issues

    @property
    def ok(self) -> bool:
        return not self.problems()


def sweep_macro(
    module_id: str,
    macro: str,
    registry: Registry,
    *,
    duration: float = 30.0,
    seed: SeedPath | None = None,
    output_dir: Path | None = None,
    cfg: Config | None = None,
) -> SweepResult:
    """Fuehrt eine Makrofahrt 0 -> 1 durch und misst das Ergebnis.

    Der Deckel und die Rate der Rampenschritte richten sich nach der
    Glaettungszeit des Compilers: 240 Stuetzstellen ueber 30 s sind 125 ms
    Abstand — deutlich unter der kuerzesten deklarierten Glaettung, damit die
    Fahrt kontinuierlich wirkt statt gestuft.
    """
    c = cfg or get_config()
    s = seed or SeedPath.root(0).child("sweep", module_id, macro)
    manifest = registry.get(module_id)
    if macro not in manifest.macros:
        raise ValueError(
            f"{module_id} kennt kein Makro {macro!r} (bekannt: {sorted(manifest.macros)})"
        )

    graph = single_voice_graph(module_id, "voice")
    out_dir = output_dir or (c.cache_dir / "sweeps")
    out_dir.mkdir(parents=True, exist_ok=True)
    control = f"voice_{macro}"
    out_path = out_dir / f"sweep_{module_id.replace('.', '_')}_{macro}.wav"

    result, _compiled = render_graph(
        graph,
        registry,
        out_path,
        duration=duration,
        seed=s,
        name=f"sweep_{macro}",
        ramp=MacroRamp(control=control, start=0.0, end=1.0, steps=int(duration * 8)),
        cfg=c,
    )

    import soundfile as sf

    data, _ = sf.read(str(result.path), dtype="float64", always_2d=True)
    rules = dsp_rules(c)
    nyquist_guard = rules.safety.nyquist_guard

    return SweepResult(
        module_id=module_id,
        macro=macro,
        duration_s=duration,
        clicks=detect_clicks(data, c.audio.sample_rate),
        clip_fraction=clip_ratio(data),
        dc=dc_offset(data),
        high_freq_ratio=high_frequency_energy_ratio(
            data, c.audio.sample_rate, cutoff_ratio=nyquist_guard
        ),
        peak_level=peak(data),
        rms_level=rms(data),
    )


def sweep_all_macros(
    module_id: str,
    registry: Registry,
    *,
    duration: float = 30.0,
    cfg: Config | None = None,
) -> dict[str, SweepResult]:
    """Sweept jedes Makro einer Stimme; Reihenfolge alphabetisch (deterministisch)."""
    manifest = registry.get(module_id)
    return {
        macro: sweep_macro(module_id, macro, registry, duration=duration, cfg=cfg)
        for macro in sorted(manifest.macros)
    }

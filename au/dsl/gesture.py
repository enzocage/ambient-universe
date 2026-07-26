"""L3 — Geste / Artikulation (plan.md Paragraph 4.3).

Eine Geste beschreibt, wie ein einzelnes Klangereignis ueber seine Dauer
atmet: eine Amplitudenhuellkurve (Attack/Halten/Release) und mindestens eine
Makrotrajektorie, die eine messbare Spektralbewegung erzeugt. Ohne diese
Bewegung waere das Ereignis ein Standbildton — laut plan.md ein Fehler, kein
Stilmittel.

Diese Phase deckt eine Trajektorie pro Geste ab (das Pflichtmakro, ueber das
sich die Geste entwickelt); mehrere gleichzeitige Trajektorien und Mikrodrift
als eigenes Signal folgen mit dem vollen L4-Ausbau (Phase 3).
"""

from __future__ import annotations

from typing import Self

import numpy as np
from pydantic import BaseModel, Field, model_validator

from au.core.knowledge import DspRules, dsp_rules
from au.core.seeds import SeedPath


class Breakpoint(BaseModel):
    model_config = {"frozen": True}

    time_s: float = Field(ge=0.0)
    value: float = Field(ge=0.0, le=1.0)


class GestureSpec(BaseModel):
    """Ausgangskontrakt L3 -> L4 (verkuerzt auf eine Trajektorie, s. Modulkopf)."""

    model_config = {"frozen": True}

    duration_s: float = Field(gt=0.0)
    attack_s: float = Field(ge=0.0)
    release_s: float = Field(ge=0.0)
    macro: str
    macro_points: tuple[Breakpoint, ...] = Field(min_length=2)
    seed: int = 0
    impulsive: bool = False

    @model_validator(mode="after")
    def _points_span_the_duration(self) -> Self:
        if abs(self.macro_points[0].time_s) > 1e-6:
            raise ValueError("Der erste Stuetzpunkt muss bei t=0 liegen")
        if abs(self.macro_points[-1].time_s - self.duration_s) > 1e-6:
            raise ValueError("Der letzte Stuetzpunkt muss bei t=duration_s liegen")
        times = [p.time_s for p in self.macro_points]
        if times != sorted(times):
            raise ValueError("Stuetzpunkte muessen aufsteigend sortiert sein")
        return self

    @model_validator(mode="after")
    def _envelope_fits(self) -> Self:
        if self.attack_s + self.release_s > self.duration_s:
            raise ValueError(
                f"attack ({self.attack_s}s) + release ({self.release_s}s) "
                f"ueberschreitet die Gestendauer ({self.duration_s}s)"
            )
        return self

    @property
    def spectral_travel_intent(self) -> float:
        """Betrag der beabsichtigten Makrobewegung — eine grobe Vorabschaetzung,
        die tatsaechliche Messung erfolgt am gerenderten Audio."""
        values = [p.value for p in self.macro_points]
        return max(values) - min(values)

    def amplitude_points(self) -> tuple[Breakpoint, ...]:
        release_start = max(self.attack_s, self.duration_s - self.release_s)
        return (
            Breakpoint(time_s=0.0, value=0.0),
            Breakpoint(time_s=self.attack_s, value=1.0),
            Breakpoint(time_s=release_start, value=1.0),
            Breakpoint(time_s=self.duration_s, value=0.0),
        )


def generate_default_gesture(
    available_macros: list[str],
    *,
    duration_s: float,
    seed: SeedPath,
    rules: DspRules | None = None,
    macro: str = "brightness",
    impulsive: bool = False,
) -> GestureSpec:
    """Erzeugt eine seedgesteuerte, aber immer artikulierte Standardgeste.

    Start- und Zielwert der Trajektorie liegen immer mindestens
    ``dsp_rules.envelopes.min_spectral_travel`` auseinander (mit Reserve) —
    das ist die Einloesung der L3-Invariante "kein Standbildton" auf
    Konstruktionsebene, nicht erst bei der Messung.
    """
    r = rules or dsp_rules()
    rng = np.random.default_rng(seed.child("gesture").value & 0xFFFF_FFFF)

    chosen_macro = macro if macro in available_macros else available_macros[0]

    base_attack = r.envelopes.impulsive_min_attack_ms if impulsive else r.envelopes.min_attack_ms
    attack = min(duration_s * 0.25, (base_attack / 1000.0) * rng.uniform(1.0, 2.5))
    release = min(duration_s * 0.35, attack * rng.uniform(2.0, 6.0))
    if attack + release > duration_s:
        scale = duration_s / (attack + release) * 0.9
        attack, release = attack * scale, release * scale

    min_travel = max(0.35, r.envelopes.min_spectral_travel * 1.8)
    span = rng.uniform(min_travel, min(0.95, min_travel + 0.35))
    start = rng.uniform(0.02, 1.0 - span - 0.02)
    direction = 1.0 if rng.random() < 0.5 else -1.0
    end = start + direction * span
    if not (0.0 <= end <= 1.0):
        direction *= -1.0
        end = start + direction * span
    end = float(np.clip(end, 0.0, 1.0))

    mid_time = duration_s * rng.uniform(0.35, 0.65)
    mid_value = float(np.clip(start + (end - start) * rng.uniform(0.3, 0.7), 0.0, 1.0))

    points = (
        Breakpoint(time_s=0.0, value=float(start)),
        Breakpoint(time_s=mid_time, value=mid_value),
        Breakpoint(time_s=duration_s, value=float(end)),
    )
    return GestureSpec(
        duration_s=duration_s,
        attack_s=attack,
        release_s=release,
        macro=chosen_macro,
        macro_points=points,
        seed=int(seed.value & 0xFFFF_FFFF),
        impulsive=impulsive,
    )

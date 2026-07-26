"""L4 — Klangelement (plan.md Paragraph 4.4 und 10.2, verkuerzte Fassung).

Diese Phase deckt den Kern des Kontrakts ab: ein Element bindet genau eine
Stimme (L2) an genau eine feldrelative Ansteuerung (Pattern + Feld) und liefert
eine eigenstaendig anhoerbare Einheit. Die volle Rezeptstruktur aus plan.md
10.2 (Formungskette, Effektkette, mehrere Relationen) folgt mit dem Ausbau von
L5/L6; hier steht bewusst nur, was fuer eine funktionierende Vorhoer-Kette
noetig ist — Rezept, keine gerenderte Datei, damit spaetere Transposition und
Rekombination moeglich bleiben (plan.md Paragraph 10.3).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from au.dsl.field import HarmonicField

PatternKind = Literal["poisson", "euclid", "sustained"]
"""``sustained`` traegt eine durchgehende Flaeche (Fundament, Drone, Atmo,
Pad) statt diskreter Ereignisse -- ohne diesen Modus bleiben genau die
Rollen stumm, die den Track eigentlich tragen sollen (siehe
au.dsl.pattern.sustained_events)."""


class ElementRecipe(BaseModel):
    """Ein vorhoerbares, transponierbares, ablegbares Klangelement."""

    model_config = {"frozen": True}

    id: str
    name: str = ""
    voice_module_id: str
    voice_params: dict[str, float | str] = Field(default_factory=dict)
    voice_macros: dict[str, float] = Field(default_factory=dict)
    """Ueberschreibt die Makro-Grundstellung der Stimme (0..1 je Makro). Der
    Angriffspunkt des Editor-Agenten (Phase 6): 'waermer' aendert hier
    ``brightness``, nicht die Rezeptstruktur."""

    field: HarmonicField = Field(default_factory=HarmonicField)
    pattern_kind: PatternKind = "poisson"
    lambda_per_min: float = 3.0
    """Nur fuer ``pattern_kind == "poisson"``."""
    euclid_pulses: int = 5
    euclid_steps: int = 16
    euclid_step_s: float = 3.0
    """Nur fuer ``pattern_kind == "euclid"``."""

    duration_s: float = Field(default=45.0, gt=0.0)
    attack_s: float = 1.5
    release_s: float = 4.0
    macro: str = "brightness"
    """Welches Makro die Geste jedes Ereignisses traegt."""

    seed_root: int = 0

    tags: tuple[str, ...] = ()
    thesis: str = ""

    def transposed(self, semitones: float) -> ElementRecipe:
        """Neue, um ``semitones`` verschobene Fassung — das Original bleibt
        unveraendert (plan.md 4.4: eingefrorene Elemente sind unveraenderlich)."""
        return self.model_copy(update={"field": self.field.transposed(semitones)})

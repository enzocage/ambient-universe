"""L7/L8 — Sektion und Track (plan.md Paragraph 4.7 und 4.8, verkuerzte Fassung).

Diese Phase deckt die Zeitgliederung und den Formbogen ab. Die volle
Uebergangspalette (9 Operatoren mit eigener DSP-Kette) und die Identitaets-
stabilitaetspruefung je Sektion folgen mit dem weiteren Ausbau; hier stehen
Sektionsgrenzen als Zeitfenster und der Bogen als messbare Zielkurve, die
gegen das tatsaechliche Rendering geprueft wird (nicht nur behauptet).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au.dsl.layer import LayerInstance

ArcShape = Literal["emergence", "arch", "descent", "plateau_with_event"]

#: Rollen -> Stem-Eimer (plan.md 4.8: mindestens diese Aufteilung ist Pflicht).
STEM_BUCKETS: dict[str, str] = {
    "foundation": "foundation",
    "subharmonic_pulse": "foundation",
    "harmonic_drone": "harmonic",
    "moving_pad": "harmonic",
    "granular_texture": "texture",
    "atmospheric_noise": "texture",
    "spectral_shimmer": "texture",
    "resonant_object": "objects",
    "signal_motif": "objects",
    "contrast_layer": "objects",
    "negative_layer": "objects",
}


class Section(BaseModel):
    """Ein Zeitabschnitt mit eigener Identitaet."""

    model_config = {"frozen": True}

    section_id: str
    start_s: float = Field(ge=0.0)
    end_s: float
    layer_ids: tuple[str, ...]

    @model_validator(mode="after")
    def _ends_after_start(self) -> Section:
        if self.end_s <= self.start_s:
            raise ValueError(f"Sektion {self.section_id}: end_s muss nach start_s liegen")
        return self

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


class TrackPlan(BaseModel):
    """Ein vollstaendiger Track: Sektionen, Layer, Bogenform."""

    model_config = {"frozen": True}

    track_id: str
    duration_s: float = Field(gt=0.0)
    arc_shape: ArcShape = "emergence"
    sections: tuple[Section, ...]
    layers: tuple[LayerInstance, ...]

    @model_validator(mode="after")
    def _has_at_least_one_section(self) -> TrackPlan:
        if not self.sections:
            raise ValueError("Ein Track braucht mindestens eine Sektion")
        return self

    @model_validator(mode="after")
    def _sections_cover_the_track_in_order(self) -> TrackPlan:
        ordered = sorted(self.sections, key=lambda s: s.start_s)
        if [s.section_id for s in ordered] != [s.section_id for s in self.sections]:
            raise ValueError("Sektionen muessen in zeitlicher Reihenfolge deklariert sein")
        for a, b in zip(ordered, ordered[1:], strict=False):
            if b.start_s < a.end_s - 1e-6:
                raise ValueError(f"Sektionen {a.section_id} und {b.section_id} ueberlappen")
        if ordered[-1].end_s > self.duration_s + 1e-6:
            raise ValueError("Die letzte Sektion reicht ueber die Trackdauer hinaus")
        return self

    def layers_in(self, section: Section) -> list[LayerInstance]:
        wanted = set(section.layer_ids)
        return [layer for layer in self.layers if layer.layer_id in wanted]


class SectionArrangement(BaseModel):
    """Geplante Zeitabschnitte fuer den musikalischen Verlauf eines Tracks."""

    model_config = {"frozen": True}

    intro: tuple[float, float]
    build: tuple[float, float]
    peak: tuple[float, float]
    outro: tuple[float, float]

    def is_active_in_section(self, role: str, t: float) -> bool:
        """Prueft, ob eine Rolle zum Zeitpunkt t dramaturgisch aktiv sein soll."""
        if role in ("foundation", "harmonic_drone"):
            return True
        if role in ("atmospheric_noise", "space_noise_elements"):
            return t < self.outro[1]
        if role in ("subharmonic_pulse", "moving_pad"):
            return self.build[0] <= t <= self.outro[0]
        if role in ("signal_motif", "resonant_object", "granular_texture", "arpeggiator", "bass_sequence"):
            return self.peak[0] <= t <= self.peak[1]
        return True


def generate_section_arrangement(duration_s: float) -> SectionArrangement:
    """Erzeugt 4 musikalische Phasen (Intro, Aufbau, Hoehepunkt, Outro)."""
    t_intro = duration_s * 0.18
    t_build = duration_s * 0.42
    t_peak = duration_s * 0.80
    return SectionArrangement(
        intro=(0.0, t_intro),
        build=(t_intro, t_build),
        peak=(t_build, t_peak),
        outro=(t_peak, duration_s),
    )


"""L3/L4 — Motive und Phrasen: Wiederkehrende melodische und rhythmische Figuren.

Ein Motiv ist eine kurze, zusammenhaengende Folge von Tonhoehen-Abstaenden (im
Sinne von Stufenindizes im HarmonicField), Dauer-Verhaeltnissen und Velocity-
Konturen. Eine Phrase ordnet ein oder mehrere Motive zu einer musikalischen
Aussage mit Wiederholung, Variation, Transposition und Pausen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

from au.core.seeds import SeedPath
from au.dsl.field import HarmonicField

VariationType = Literal["exact", "transposed", "inverted", "rhythmic_stretch", "fragment"]


class NoteOffset(BaseModel):
    """Ein relativer Notenschritt innerhalb eines Motivs."""

    model_config = {"frozen": True}

    degree_offset: int = 0
    """Stufenabstand relativ zur aktuellen Akkordstufe."""
    duration_ratio: float = Field(default=1.0, gt=0.0)
    """Dauer relativ zur Grundschrittweite (z.B. 1.0 = Viertel, 0.5 = Achtel)."""
    velocity: float = Field(default=0.7, ge=0.0, le=1.0)
    is_rest: bool = False
    """True = Stille / Pause an dieser Position."""


class Motif(BaseModel):
    """Ein wiederkehrbares musikalisches Motiv (Notensequenz)."""

    model_config = {"frozen": True}

    id: str
    name: str = ""
    notes: tuple[NoteOffset, ...] = ()
    step_duration_s: float = Field(default=0.8, gt=0.0)

    @property
    def duration_s(self) -> float:
        return sum(note.duration_ratio * self.step_duration_s for note in self.notes)

    def varied(self, kind: VariationType, *, transpose_degrees: int = 0, seed: SeedPath | None = None) -> Motif:
        """Erzeugt eine musikalische Variation des Motivs."""
        new_notes: list[NoteOffset] = []
        for note in self.notes:
            if note.is_rest:
                new_notes.append(note)
                continue

            deg = note.degree_offset
            dur = note.duration_ratio
            vel = note.velocity

            if kind == "transposed":
                deg += transpose_degrees
            elif kind == "inverted":
                deg = -deg + transpose_degrees
            elif kind == "rhythmic_stretch":
                dur *= 1.5
            elif kind == "fragment" and seed is not None:
                if seed.child("frag").sc % 2 == 0:
                    continue
                deg += transpose_degrees

            new_notes.append(
                NoteOffset(
                    degree_offset=deg,
                    duration_ratio=dur,
                    velocity=vel,
                    is_rest=note.is_rest,
                )
            )

        return Motif(
            id=f"{self.id}_{kind}",
            name=f"{self.name} ({kind})",
            notes=tuple(new_notes or self.notes),
            step_duration_s=self.step_duration_s,
        )


class PhraseSegment(BaseModel):
    """Ein Abschnitt innerhalb einer musikalischen Phrase."""

    model_config = {"frozen": True}

    motif: Motif
    start_time_s: float = Field(ge=0.0)
    variation: VariationType = "exact"
    transpose_degrees: int = 0


@dataclass(frozen=True, slots=True)
class Phrase:
    """Eine zusammenhaengende musikalische Phrase mit Pausen und Variationen."""

    phrase_id: str
    segments: tuple[PhraseSegment, ...]
    total_duration_s: float


def generate_motif(
    motif_id: str,
    field: HarmonicField,
    seed: SeedPath,
    *,
    length: int = 4,
    step_duration_s: float = 0.8,
) -> Motif:
    """Erzeugt ein zusammenhaengendes, musikalisch sinnvolles Motiv."""
    rng = np.random.default_rng(seed.child("motif", motif_id).sc)
    scale_size = len(field.degrees())

    notes: list[NoteOffset] = []
    curr_degree = 0

    dur_choices = [0.5, 0.75, 1.0, 1.5]
    dur_weights = [0.3, 0.2, 0.4, 0.1]

    for i in range(length):
        # 15% Chance fuer eine kurze Atempause (ausser bei der ersten Note)
        is_rest = (i > 0) and (rng.random() < 0.15)
        if is_rest:
            notes.append(NoteOffset(degree_offset=curr_degree, duration_ratio=1.0, is_rest=True))
            continue

        # Kleine Stufenabstaende (Voice Leading / Konsonanz)
        step = int(rng.choice([-2, -1, 0, 1, 2, 3], p=[0.15, 0.3, 0.1, 0.3, 0.1, 0.05]))
        curr_degree = max(-scale_size, min(scale_size, curr_degree + step))
        dur = float(rng.choice(dur_choices, p=dur_weights))
        vel = float(rng.uniform(0.55, 0.85))

        notes.append(NoteOffset(degree_offset=curr_degree, duration_ratio=dur, velocity=vel))

    return Motif(id=motif_id, name=f"Motif {motif_id}", notes=tuple(notes), step_duration_s=step_duration_s)


def generate_phrase(
    phrase_id: str,
    motif: Motif,
    seed: SeedPath,
    *,
    repetitions: int = 3,
    pause_s: float = 2.0,
) -> Phrase:
    """Ordnet ein Motiv zu einer Phrase mit Wiederholung & Variation an (Ruf-und-Antwort)."""
    rng = np.random.default_rng(seed.child("phrase", phrase_id).sc)
    segments: list[PhraseSegment] = []

    curr_t = 0.0
    variations: list[VariationType] = ["exact", "transposed", "inverted", "exact"]

    for i in range(repetitions):
        var_kind = variations[i % len(variations)]
        transpose = int(rng.choice([0, 2, -2, 4, -3])) if var_kind != "exact" else 0
        varied_motif = motif.varied(var_kind, transpose_degrees=transpose, seed=seed.child(f"var_{i}"))

        segments.append(
            PhraseSegment(
                motif=varied_motif,
                start_time_s=curr_t,
                variation=var_kind,
                transpose_degrees=transpose,
            )
        )
        curr_t += varied_motif.duration_s + pause_s

    return Phrase(phrase_id=phrase_id, segments=tuple(segments), total_duration_s=curr_t)

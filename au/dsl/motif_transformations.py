"""Motiv-Transformationen und Variationen (Plan 3, Paragraph 4.2).

Erzeugt wiedererkennbare Motiv-Transformationen (Transposition, Dehnung, Fragmentierung,
Inversion, Re-Artikulation) zur Vermeidung von Melodie-Monotonie.
"""

from __future__ import annotations

from dataclasses import dataclass

from au.core.seeds import SeedPath
from au.dsl.field import HarmonicField
from au.dsl.motif import Motif, NoteOffset


@dataclass(frozen=True, slots=True)
class TransformedMotif:
    original_motif_id: str
    transformation_kind: str
    notes: tuple[NoteOffset, ...]


def transform_motif(
    motif: Motif,
    field: HarmonicField,
    seed: SeedPath,
    kind: str = "transposed",
    *,
    step_shift: int = 2,
    stretch_factor: float = 1.5,
) -> TransformedMotif:
    """Wendet eine strukturierte musikalische Transformation auf ein Motiv an."""
    transformed_notes: list[NoteOffset] = []

    if kind == "transposed":
        for ev in motif.notes:
            transformed_notes.append(
                NoteOffset(
                    degree_offset=ev.degree_offset + step_shift,
                    duration_ratio=ev.duration_ratio,
                    velocity=ev.velocity,
                    is_rest=ev.is_rest,
                )
            )
    elif kind == "rhythmic_stretch":
        for ev in motif.notes:
            transformed_notes.append(
                NoteOffset(
                    degree_offset=ev.degree_offset,
                    duration_ratio=ev.duration_ratio * stretch_factor,
                    velocity=ev.velocity,
                    is_rest=ev.is_rest,
                )
            )
    elif kind == "fragment":
        for ev in motif.notes[:max(1, len(motif.notes) // 2)]:
            transformed_notes.append(ev)
    elif kind == "inverted":
        for ev in motif.notes:
            transformed_notes.append(
                NoteOffset(
                    degree_offset=-ev.degree_offset,
                    duration_ratio=ev.duration_ratio,
                    velocity=ev.velocity,
                    is_rest=ev.is_rest,
                )
            )
    else:
        transformed_notes = list(motif.notes)

    return TransformedMotif(
        original_motif_id=motif.id,
        transformation_kind=kind,
        notes=tuple(transformed_notes),
    )


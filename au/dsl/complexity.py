"""Renderbudget und Komplexitaetsstufen fuer den Kompositionslauf."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompositionBudget:
    duration_s: float
    name: str
    max_slots: int
    variants_per_role: int
    section_count: int
    audition_depth: int
    revision_passes: int


def budget_for_duration(duration_s: float, profile: str = "auto") -> CompositionBudget:
    duration = max(10.0, min(600.0, float(duration_s)))
    profiles = {
        "sketch": ("sketch", 4, 2, 2, 1, 0),
        "developing": ("developing", 6, 4, 4, 2, 1),
        "rich": ("rich", 8, 6, 4, 3, 2),
        "album": ("album", 10, 8, 6, 4, 2),
        "maximal": ("maximal", 12, 10, 8, 5, 3),
    }
    if profile in profiles:
        name, slots, variants, sections, audition, revisions = profiles[profile]
        return CompositionBudget(duration, name, slots, variants, sections, audition, revisions)
    if duration <= 20.0:
        return CompositionBudget(duration, "sketch", 4, 2, 2, 1, 0)
    if duration <= 60.0:
        return CompositionBudget(duration, "developing", 6, 4, 4, 2, 1)
    if duration <= 180.0:
        return CompositionBudget(duration, "rich", 8, 6, 4, 3, 2)
    if duration <= 360.0:
        return CompositionBudget(duration, "album", 10, 8, 6, 4, 2)
    return CompositionBudget(duration, "maximal", 12, 10, 8, 5, 3)

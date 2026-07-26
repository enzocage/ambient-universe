"""Produktions- und Strukturmuster fuer hierarchische Arrangements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PatternLevel(StrEnum):
    MOTIF = "motif"
    PHRASE = "phrase"
    SECTION = "section"
    FORM = "form"


@dataclass(frozen=True, slots=True)
class ProductionPattern:
    pattern_id: str
    name: str
    level: PatternLevel
    roles: tuple[str, ...]
    section_fit: tuple[str, ...]
    transforms: tuple[str, ...]
    relation: str
    tension: float


PRODUCTION_PATTERNS: tuple[ProductionPattern, ...] = (
    ProductionPattern("repeat_variation", "Wiederholung mit Variation", PatternLevel.MOTIF, ("bass_sequence", "arpeggiator", "signal_motif"), ("build", "peak"), ("transpose", "rhythm_stretch", "register_shift"), "same_core_new_surface", .45),
    ProductionPattern("addition_subtraction", "Addition und Subtraktion", PatternLevel.SECTION, ("foundation", "harmonic_drone", "arpeggiator", "texture"), ("intro", "build", "outro"), ("add_role", "remove_role", "thin_register"), "role_density", .55),
    ProductionPattern("call_response", "Frage und Antwort", PatternLevel.PHRASE, ("signal_motif", "arpeggiator", "resonant_object"), ("build", "peak"), ("answer_register", "answer_timbre", "answer_delay"), "motif_to_response", .65),
    ProductionPattern("layered_ostinato", "Überlagerte Ostinati", PatternLevel.PHRASE, ("bass_sequence", "arpeggiator", "subtle_percussive_background"), ("build", "peak"), ("short_cycle", "long_cycle", "accent_rotation"), "shared_downbeat", .7),
    ProductionPattern("anticipation_release", "Antizipation und Auflösung", PatternLevel.PHRASE, ("bass_sequence", "harmonic_drone", "arpeggiator"), ("build", "peak", "outro"), ("anticipate_root", "hold_over_change", "resolve_down"), "chord_to_pattern", .8),
    ProductionPattern("fill_vacuum", "Fill und Vakuum", PatternLevel.SECTION, ("subtle_percussive_background", "texture", "resonant_object"), ("build", "peak"), ("pre_fill", "silence_on_one", "impact_after_gap"), "transition_gap", .85),
    ProductionPattern("timbre_handover", "Klangfarbenübergabe", PatternLevel.SECTION, ("harmonic_drone", "moving_pad", "texture", "signal_motif"), ("intro", "build", "peak", "outro"), ("crossfade_family", "shared_pitch", "space_handover"), "same_motif_new_voice", .6),
    ProductionPattern("return_transform", "Rückkehr mit Transformation", PatternLevel.FORM, ("foundation", "bass_sequence", "signal_motif"), ("outro",), ("return_theme", "fragment", "dissolve"), "ending_answers_beginning", .72),
)


def patterns_for_context(*, level: PatternLevel, section: str, roles: tuple[str, ...]) -> tuple[ProductionPattern, ...]:
    role_set = set(roles)
    candidates = [
        pattern
        for pattern in PRODUCTION_PATTERNS
        if pattern.level == level
        and section in pattern.section_fit
        and role_set.intersection(pattern.roles)
    ]
    return tuple(sorted(candidates, key=lambda pattern: (-pattern.tension, pattern.pattern_id)))

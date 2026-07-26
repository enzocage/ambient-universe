"""Der Blueprint: DNA -> grobe Verschaltungshierarchie (plan.md Paragraph 8.2).

Diese Phase deckt die fuer den Kompositionsworkflow entscheidenden Ebenen ab:
L4-Rollen-Slots mit Budgets, koprime Perioden und Relation-Hinweise. Die
volle Zehn-Ebenen-Tiefe aus plan.md 8.2 (inklusive L7-L9-Feinplanung) folgt
mit dem jeweiligen Phasenausbau (9 und 10); hier steht, was Phase 6
(Vorschlags-Engine) tatsaechlich braucht, um Slots zu befuellen.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from au.dsl.dna import AlbumDNA
from au.dsl.field import HarmonicField


class RoleProfile(BaseModel):
    """Statische Eigenschaften einer Rolle (plan.md Paragraph 7.2)."""

    model_config = {"frozen": True}

    role: str
    band_hz: tuple[float, float]
    density: float
    lufs: float
    summary: str = ""


#: Das geschlossene Rollenvokabular (plan.md Paragraph 7.2).
ROLE_PROFILES: dict[str, RoleProfile] = {
    p.role: p
    for p in (
        RoleProfile(
            role="foundation",
            band_hz=(25, 120),
            density=0.02,
            lufs=-20,
            summary="Traegt, ohne aufzufallen.",
        ),
        RoleProfile(
            role="harmonic_drone",
            band_hz=(80, 800),
            density=0.05,
            lufs=-22,
            summary="Definiert das harmonische Feld hoerbar.",
        ),
        RoleProfile(
            role="moving_pad",
            band_hz=(200, 3000),
            density=0.08,
            lufs=-24,
            summary="Bewegung, Atmung, Waerme.",
        ),
        RoleProfile(
            role="granular_texture",
            band_hz=(400, 8000),
            density=0.12,
            lufs=-28,
            summary="Koernung, Lebendigkeit.",
        ),
        RoleProfile(
            role="atmospheric_noise",
            band_hz=(40, 14000),
            density=1.0,
            lufs=-34,
            summary="Kitt, Raumgefuehl.",
        ),
        RoleProfile(
            role="resonant_object",
            band_hz=(300, 6000),
            density=0.03,
            lufs=-24,
            summary="Einzelne koerperhafte Ereignisse.",
        ),
        RoleProfile(
            role="signal_motif",
            band_hz=(500, 5000),
            density=0.008,
            lufs=-21,
            summary="Erinnerbare, seltene Geste.",
        ),
        RoleProfile(
            role="subharmonic_pulse",
            band_hz=(30, 90),
            density=0.02,
            lufs=-23,
            summary="Sehr langsamer Puls, Koerperlichkeit.",
        ),
        RoleProfile(
            role="spectral_shimmer",
            band_hz=(2000, 12000),
            density=0.05,
            lufs=-30,
            summary="Oberer Glanz, Hoehe ohne Haerte.",
        ),
        RoleProfile(
            role="contrast_layer",
            band_hz=(100, 8000),
            density=0.06,
            lufs=-26,
            summary="Bricht bewusst die Erwartung.",
        ),
        RoleProfile(
            role="negative_layer",
            band_hz=(20, 20000),
            density=0.0,
            lufs=-96,
            summary="Geplante Stille/Aussparung.",
        ),
    )
}

#: Erste Primzahlen ab 30s — Grundlage der koprimen Periodenvergabe.
_PRIME_PERIODS_S: tuple[float, ...] = (37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83)


class RoleSlot(BaseModel):
    """Ein zu befuellender Platz im Blueprint."""

    model_config = {"frozen": True}

    slot_id: str
    role: str
    band_hz: tuple[float, float]
    density: float
    lufs: float
    phase_period_s: float
    candidates_per_slot: int = 5
    rationale: str = ""
    voice_module_hint: str | None = None
    """Optionaler Vorschlag fuer eine passende Stimme aus dem Katalog."""


class RelationHint(BaseModel):
    model_config = {"frozen": True}

    kind: str
    from_role: str
    to_role: str


class Blueprint(BaseModel):
    """Die aus einer DNA abgeleitete Verschaltungshierarchie."""

    model_config = {"frozen": True}

    dna_title: str
    field: HarmonicField
    role_slots: tuple[RoleSlot, ...]
    relation_hints: tuple[RelationHint, ...]
    masking_ceiling: float = 0.35
    roughness_ceiling: float = 0.28
    global_spaces: tuple[str, ...] = ("spc.reverb.fdn32#main",)

    def slot(self, slot_id: str) -> RoleSlot | None:
        return next((s for s in self.role_slots if s.slot_id == slot_id), None)

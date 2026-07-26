"""Vorschlags-Engine: Rollen-Slot -> mehrere Elementkandidaten (plan.md Phase 6).

Jeder Kandidat verfolgt eine andere These (plan.md 4.4-MI-Direktive: "fuenf
Kandidaten, die sich in ihrer Grundidee unterscheiden, nicht im Filter-
Cutoff"). Diese Phase variiert dafuer die Stimme selbst und die Grundzuege
der Ansteuerung (Dichte, Makrostellung), nicht nur einen Parameter.
"""

from __future__ import annotations

from dataclasses import dataclass

from au.core.manifest import Category
from au.core.registry import Registry
from au.core.seeds import SeedPath
from au.dsl.blueprint import RoleSlot
from au.dsl.dna import AlbumDNA
from au.dsl.element import ElementRecipe
from au.dsl.field import HarmonicField

#: Grobe Thesen, mit denen ein Kandidat sich von den anderen unterscheidet.
_THESES: tuple[tuple[str, float, float], ...] = (
    ("Warmer, koerperhafter Grundklang", 0.35, 0.15),
    ("Helle, glasige Erscheinung", 0.75, 0.05),
    ("Sparsames, seltenes Ereignis", 0.5, -0.6),
    ("Dichte, atmende Flaeche", 0.55, 0.6),
    ("Kuehler, distanzierter Klang", 0.25, -0.1),
)


@dataclass(frozen=True, slots=True)
class Candidate:
    recipe: ElementRecipe
    thesis: str


def _voices_for_slot(slot: RoleSlot, registry: Registry) -> list[str]:
    """Stimmen, deren Band den Slot ueberlappt."""
    candidates = registry.query(category=Category.GENERATOR, max_level=2, band_within=None)
    scored = []
    for m in candidates:
        low, high = m.guarantees.band_hz
        slot_low, slot_high = slot.band_hz
        overlap = min(high, slot_high) - max(low, slot_low)
        if overlap > 0:
            scored.append((overlap, m.id))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [mid for _, mid in scored] or [m.id for m in candidates]


def propose_candidates(
    slot: RoleSlot,
    dna: AlbumDNA,
    field: HarmonicField,
    registry: Registry,
    *,
    seed: SeedPath,
    n: int = 5,
) -> list[Candidate]:
    """Erzeugt ``n`` Kandidaten mit unterschiedlicher These fuer einen Slot."""
    voices = _voices_for_slot(slot, registry)
    if not voices:
        raise ValueError(f"Kein Modul im Katalog deckt das Band von {slot.role} ab.")

    out: list[Candidate] = []
    for i in range(n):
        thesis, brightness, density_shift = _THESES[i % len(_THESES)]
        voice = voices[i % len(voices)]
        candidate_seed = seed.element_candidate(slot.slot_id, i)

        lambda_per_min = max(0.5, 60.0 / max(4.0, slot.phase_period_s) * (1.0 + density_shift))
        duration_s = max(20.0, min(180.0, slot.phase_period_s * 1.5))

        recipe = ElementRecipe(
            id=f"cand_{slot.slot_id}_{i}",
            name=f"{slot.role} — {thesis}",
            voice_module_id=voice,
            voice_macros={"brightness": brightness},
            field=field,
            lambda_per_min=lambda_per_min,
            duration_s=duration_s,
            seed_root=int(candidate_seed.value & 0xFFFF_FFFF),
            tags=(slot.role,),
            thesis=thesis,
        )
        out.append(Candidate(recipe=recipe, thesis=thesis))
    return out

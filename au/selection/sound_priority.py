"""Deterministische Klangpriorisierung fuer die Vorschlags-Engine.

Der Katalog darf nicht wie eine ungeordnete Lostrommel behandelt werden. Dieses
Modul bewertet vorhandene Generator-Manifeste fuer eine konkrete Rolle und
liefert eine stabile Reihenfolge. Zufall darf spaeter nur innerhalb eines
gleichwertigen Scores permutieren.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from au.core.manifest import ModuleManifest
from au.modules.base import has_implementation



class PriorityTier(StrEnum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class SoundCandidateScore:
    module_id: str
    role: str
    score: float
    tier: PriorityTier
    role_fitness: float
    band_fitness: float
    technical_reliability: float
    reason: str


def _overlap_score(module: ModuleManifest, band_hz: tuple[float, float]) -> float:
    low, high = module.guarantees.band_hz
    target_low, target_high = band_hz
    overlap = max(0.0, min(high, target_high) - max(low, target_low))
    target_width = max(1.0, target_high - target_low)
    return min(1.0, overlap / target_width)


def _tier(score: float) -> PriorityTier:
    if score < 0.35:
        return PriorityTier.REJECTED
    if score >= 0.86:
        return PriorityTier.S
    if score >= 0.68:
        return PriorityTier.A
    if score >= 0.50:
        return PriorityTier.B
    return PriorityTier.C


def score_voice_module(
    module: ModuleManifest,
    *,
    role: str,
    band_hz: tuple[float, float],
    novelty_bonus: float = 0.0,
) -> SoundCandidateScore:
    """Bewertet ein Modul ohne Audio zu behaupten.

    Audio-Auditions koennen spaeter die objektive Klangbewertung ergaenzen. Die
    Katalogbewertung ist bewusst konservativ: Rollenpassung und Bandgarantie
    dominieren, Neuheit kann einen Kandidaten niemals ueber harte Untauglichkeit
    heben.
    """
    role_fit = 1.0 if role in module.suggested_roles else 0.18
    band_fit = _overlap_score(module, band_hz)
    technical = 1.0 if has_implementation(module.id) else 0.0

    raw = 0.48 * role_fit + 0.34 * band_fit + 0.18 * technical + novelty_bonus
    score = max(0.0, min(1.0, raw))
    tier = _tier(score)
    if technical <= 0.0:
        reason = "Implementierung oder Renderbarkeit fehlt."
    elif role_fit < 0.5:
        reason = "Nur generische Bandpassung; keine empfohlene Rollenpassung."
    elif band_fit < 0.25:
        reason = "Das garantierte Frequenzband ueberlappt die Rolle zu wenig."
    else:
        reason = "Rolle, Frequenzband und technische Verfuegbarkeit passen."
    return SoundCandidateScore(
        module_id=module.id,
        role=role,
        score=score,
        tier=tier,
        role_fitness=role_fit,
        band_fitness=band_fit,
        technical_reliability=technical,
        reason=reason,
    )


def prioritize_voice_modules(
    modules: list[ModuleManifest],
    *,
    role: str,
    band_hz: tuple[float, float],
    novelty_ids: frozenset[str] = frozenset(),
) -> tuple[SoundCandidateScore, ...]:
    """Liefert eine stabile, qualitaetsorientierte Modulreihenfolge.

    `novelty_ids` gibt neuen, noch nicht gehoerten Modulen einen kleinen
    Erkundungsbonus. Dieser Bonus wird erst nach den Eignungsfaktoren
    angewendet und kann keinen technisch ungueltigen Kandidaten freigeben.
    """
    scored = [
        score_voice_module(
            module,
            role=role,
            band_hz=band_hz,
            novelty_bonus=0.025 if module.id in novelty_ids else 0.0,
        )
        for module in modules
    ]
    return tuple(
        sorted(
            scored,
            key=lambda item: (-item.score, item.tier.value, item.module_id),
        )
    )

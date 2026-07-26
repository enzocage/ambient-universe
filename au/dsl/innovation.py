"""Wirkung des Innovations-Vektors (plan.md Paragraph 11).

Kein dekoratives Feld: jede Achse schaltet Modulklassen frei oder sperrt sie
und verschiebt die Gewichte, mit denen spaetere Ebenen (vor allem der
Kohaerenz-Solver in Phase 8) Kompromisse eingehen.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from au.core.registry import LicensePolicy, VocabularyPolicy
from au.dsl.dna import InnovationVector


@dataclass(frozen=True, slots=True)
class SolverWeights:
    """Gewichte der Zielfunktion des Kohaerenz-Solvers (plan.md Paragraph 7.4).

    Volle Implementierung des Solvers folgt in Phase 8; diese Struktur legt
    bereits fest, wie der Innovations-Vektor sie beeinflusst.
    """

    w_mask: float = 1.0
    w_rough: float = 1.0
    w_dens: float = 0.6
    w_loud: float = 0.8
    w_bal: float = 0.5
    w_ster: float = 0.4
    w_mono: float = 0.6
    w_nov: float = 0.2
    w_rel: float = 0.5


@dataclass(frozen=True, slots=True)
class InnovationEffect:
    """Das Ergebnis der Anwendung eines Innovations-Vektors."""

    vocabulary: VocabularyPolicy
    weights: SolverWeights
    license_policy: LicensePolicy
    surprise_budget_events: int
    """Erlaubte Anzahl erwartungswidriger Ereignisse pro Track (plan.md 11)."""
    allow_analysis_feedback: bool


def apply_innovation(
    vector: InnovationVector,
    base_vocabulary: VocabularyPolicy | None = None,
    base_weights: SolverWeights | None = None,
) -> InnovationEffect:
    """Wendet den Innovations-Vektor auf Vokabular und Solvergewichte an."""
    vocab = base_vocabulary or VocabularyPolicy()
    weights = base_weights or SolverWeights()

    allow: list[str] = list(vocab.allow)
    prefer: list[str] = list(vocab.prefer)

    if vector.timbral >= 0.7:
        allow += ["prc.spectral.*"]
    if vector.harmonic >= 0.7:
        weights = replace(weights, w_rough=weights.w_rough * 0.6)
        allow += ["sym.field.just_tuning", "sym.field.free_tuning"]

    allow_feedback = vector.procedural >= 0.7

    weights = replace(
        weights,
        w_nov=0.2 + 0.8 * vector.mean(),
        w_mono=max(0.1, 0.6 - 0.3 * vector.formal),
    )

    surprise_events = round(1 + 6 * vector.formal)

    return InnovationEffect(
        vocabulary=VocabularyPolicy(prefer=tuple(prefer), allow=tuple(allow), forbid=vocab.forbid),
        weights=weights,
        license_policy=LicensePolicy(allow_nc_weights=False),
        surprise_budget_events=surprise_events,
        allow_analysis_feedback=allow_feedback,
    )

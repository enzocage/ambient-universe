"""Kohaerenz-Solver: Layer platzieren, Relationen erfuellen (plan.md 7.4, Phase 8).

Verfahren: Greedy-Initialisierung nach Rollenprioritaet, dann deterministische
lokale Suche (Zeitverschiebung), die eine analytische Konfliktfunktion
minimiert. Voll spektrale Maskierung/Rauheit (die reale plan.md-Zielfunktion)
brauchen Mehrspur-Rendering und -Analyse; hier steht eine strukturelle
Naeherung ueber Band- und Zeitueberlappung, die real messbare Konflikte
erfasst, ohne den vollen DSP-Regelkreis vorauszusetzen. Ein empirischer
Verifikationstest (Rendering + Bandenergie-Korrelation) prueft, dass die
analytische Loesung tatsaechlich weniger Ueberlappung erzeugt.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from au.dsl.layer import LayerInstance
from au.dsl.relations import RelationSet

#: Rollenprioritaet fuer die Greedy-Phase (plan.md 7.4: foundation zuerst).
_ROLE_PRIORITY: tuple[str, ...] = (
    "foundation",
    "harmonic_drone",
    "moving_pad",
    "subharmonic_pulse",
    "granular_texture",
    "atmospheric_noise",
    "resonant_object",
    "spectral_shimmer",
    "signal_motif",
    "contrast_layer",
    "negative_layer",
)


@dataclass(frozen=True, slots=True)
class Conflict:
    layer_a: str
    layer_b: str
    band_overlap: float
    reason: str


@dataclass(frozen=True, slots=True)
class SolveResult:
    layers: tuple[LayerInstance, ...]
    conflicts: tuple[Conflict, ...]
    relation_violations: tuple[str, ...]
    score: float
    log: tuple[str, ...] = field(default_factory=tuple)

    @property
    def feasible(self) -> bool:
        return not self.relation_violations


def _role_rank(role: str) -> int:
    return _ROLE_PRIORITY.index(role) if role in _ROLE_PRIORITY else len(_ROLE_PRIORITY)


def _pairwise_conflicts(
    layers: list[LayerInstance], relations: RelationSet
) -> tuple[list[Conflict], list[str]]:
    conflicts: list[Conflict] = []
    violations: list[str] = []
    for i, a in enumerate(layers):
        for b in layers[i + 1 :]:
            related = relations.between(a.layer_id, b.layer_id)
            if related:
                for rel in related:
                    ok, reason = rel.check(a, b)
                    if not ok:
                        violations.append(f"{rel.kind}({a.layer_id}, {b.layer_id}): {reason}")
                continue
            # Ohne Relation: Ueberlappung in Zeit UND Band ist ein Konflikt
            # (plan.md 4.6-T-Regel: jede Overlap-Paarung braucht eine Relation).
            if a.overlaps_time(b) and a.overlaps_band(b):
                frac = a.band_overlap_fraction(b)
                conflicts.append(
                    Conflict(a.layer_id, b.layer_id, frac, "Ueberlappung ohne Relation")
                )
    return conflicts, violations


def _score(conflicts: list[Conflict]) -> float:
    return sum(c.band_overlap for c in conflicts)


def solve(
    layers: list[LayerInstance],
    relations: RelationSet,
    *,
    track_duration_s: float,
    seed: int = 0,
    iterations: int = 200,
    shift_candidates_s: tuple[float, ...] = (-8.0, -4.0, -2.0, 2.0, 4.0, 8.0, 16.0),
) -> SolveResult:
    """Platziert Layer per lokaler Suche, um Konflikte zu minimieren.

    Deterministisch bei gleichem ``seed``: die Reihenfolge, in der Layer zur
    Verschiebung ausgewaehlt werden, kommt aus einem seed-gebundenen RNG,
    nicht aus Systemzufall oder Zeit.
    """
    rng = random.Random(seed)
    ordered = sorted(layers, key=lambda layer: (_role_rank(layer.role), layer.layer_id))
    current = {layer.layer_id: layer for layer in ordered}
    log: list[str] = []

    conflicts, violations = _pairwise_conflicts(list(current.values()), relations)
    best_score = _score(conflicts)
    log.append(f"Start: Score {best_score:.3f}, {len(conflicts)} Konflikt(e)")

    ids = [layer.layer_id for layer in ordered]
    for step in range(iterations):
        if best_score <= 1e-9:
            break
        target_id = ids[rng.randrange(len(ids))]
        target = current[target_id]
        shift = shift_candidates_s[rng.randrange(len(shift_candidates_s))]
        new_entry = target.entry_time_s + shift
        if new_entry < 0 or new_entry + target.duration_s > track_duration_s:
            continue
        moved = target.model_copy(
            update={"entry_time_s": new_entry, "exit_time_s": new_entry + target.duration_s}
        )
        trial = dict(current)
        trial[target_id] = moved
        trial_conflicts, trial_violations = _pairwise_conflicts(list(trial.values()), relations)
        trial_score = _score(trial_conflicts)
        if trial_score < best_score or (trial_score == best_score and not trial_violations):
            current = trial
            best_score = trial_score
            conflicts, violations = trial_conflicts, trial_violations
            log.append(f"Schritt {step}: {target_id} um {shift:+.1f}s -> Score {best_score:.3f}")

    return SolveResult(
        layers=tuple(current[i] for i in ids),
        conflicts=tuple(conflicts),
        relation_violations=tuple(violations),
        score=best_score,
        log=tuple(log),
    )


def escalation_options(result: SolveResult) -> list[str]:
    """Konkrete Entspannungsoptionen bei Unloesbarkeit (plan.md 4.6, Eskalation)."""
    if result.feasible and not result.conflicts:
        return []
    options = [
        "Layer zeitlich entzerren (laengere Trackdauer oder frueherer Einsatz).",
        "Ein Element durch eine schmalbandigere Variante ersetzen.",
        "Eine explizite Relation (z.B. 'avoids' oder 'answers') zwischen den Konfliktparteien ergaenzen.",
        "Die Rolle einer der beiden Schichten streichen oder auf einen anderen Slot verschieben.",
    ]
    return options

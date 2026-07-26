"""Erklaerbarer Active-Learning-Selector fuer die naechste Hoerprobe."""

from __future__ import annotations

from dataclasses import dataclass

from au.learning.presentation_memory import PresentationMemory
from au.learning.rating import RatingStore


@dataclass(frozen=True, slots=True)
class LearningCandidate:
    candidate_id: str
    audio_fingerprint: str
    role: str
    context: str
    objective_quality: float
    novelty: float = 0.0
    uncertainty: float = 1.0
    coverage_gap: float = 0.0
    similarity_to_recent: float = 0.0


class ActiveLearningSelector:
    """Waehlt informative Beispiele, nicht bloss zufaellige Beispiele."""

    def __init__(self, ratings: RatingStore, memory: PresentationMemory) -> None:
        self.ratings = ratings
        self.memory = memory

    def value(self, candidate: LearningCandidate) -> float:
        if candidate.objective_quality < 0.35:
            return -1.0
        if self.memory.has_audio(candidate.audio_fingerprint):
            return -1.0
        rated = self.ratings.mean_for(candidate.candidate_id, role=candidate.role)
        taste_uncertainty = 1.0 if rated is None else max(0.0, 1.0 - abs(rated - 5.5) / 4.5)
        return (
            0.34 * candidate.uncertainty
            + 0.24 * candidate.novelty
            + 0.20 * candidate.coverage_gap
            + 0.12 * taste_uncertainty
            + 0.10 * candidate.objective_quality
            - 0.35 * candidate.similarity_to_recent
        )

    def select(self, candidates: list[LearningCandidate], limit: int = 12) -> tuple[LearningCandidate, ...]:
        ranked = sorted(candidates, key=lambda item: (-self.value(item), item.candidate_id))
        return tuple(item for item in ranked if self.value(item) >= 0.0)[:limit]

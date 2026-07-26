"""Revisionsschleife für die automatische Kompositionsverbesserung (plan2.md Stufe 11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from au.critics.base import Critic, RevisionProposal

if TYPE_CHECKING:
    from au.analysis.metrics import MusicalQualityReport


@dataclass(frozen=True, slots=True)
class RevisionResult:
    attempt: int
    proposals: tuple[RevisionProposal, ...]
    accepted: bool


def run_revision_loop(
    report: MusicalQualityReport, *, max_revisions: int = 2
) -> RevisionResult:
    """Führt die Revisionsschleife aus, falls das Quality-Gate Maengel feststellt."""
    critic = Critic()
    proposals = critic.evaluate(report)

    return RevisionResult(
        attempt=1 if proposals else 0,
        proposals=tuple(proposals),
        accepted=report.accepted or len(proposals) == 0,
    )

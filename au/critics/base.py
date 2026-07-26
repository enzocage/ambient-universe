"""Kritiker- und Revisionssystem (plan2.md Stufe 11).

Analysiert gerenderte Tracks und schlaegt typisierte Revisionen vor,
um musikalische oder technische Maengel zu beheben.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from au.analysis.metrics import MusicalQualityReport

RevisionKind = Literal[
    "replace_voice",
    "shift_register",
    "reduce_density",
    "repair_voice_leading",
    "rebalance_stem",
]


@dataclass(frozen=True, slots=True)
class RevisionProposal:
    """Eine konkrete, typisierte Revision."""

    kind: RevisionKind
    target_role: str
    rationale: str
    gain_adjustment: float = 1.0


class Critic:
    """Basis-Kritiker zur Evaluierung des Qualitätsberichts."""

    def evaluate(self, report: MusicalQualityReport) -> list[RevisionProposal]:
        revs: list[RevisionProposal] = []


        if not report.accepted:
            for reason in report.reasons:
                if "leise" in reason:
                    revs.append(
                        RevisionProposal(
                            kind="rebalance_stem",
                            target_role="master",
                            rationale="Signal-Lautheit anheben",
                            gain_adjustment=1.2,
                        )
                    )
                elif "Rauschen" in reason:
                    revs.append(
                        RevisionProposal(
                            kind="replace_voice",
                            target_role="texture",
                            rationale="Rauschdominierte Stimme ersetzen",
                        )
                    )
        return revs

"""Voice Leading Engine (plan2.md Stufe 6).

Berechnet Stimmfuehrungskosten und waehlt den bezueglich Intervallabstand
und gemeinsamen Toenen optimalen Folgenton.
"""

from __future__ import annotations


def voice_leading_cost(previous_midi: float, candidate_midi: float) -> float:
    """Berechnet die Stimmfuehrungskosten zwischen zwei Tonhoehen.
    
    Kleine Schritte (0-4 Halbtoene) erhalten niedrige Kosten, weite Spruenge hohe Kosten.
    """
    interval = abs(candidate_midi - previous_midi)
    if interval == 0:
        return 0.0  # Gemeinsamer Ton (optimal)
    if interval <= 4:
        return interval * 0.5  # Stufenweise Bewegung
    return float(interval * 2.0)  # Weiter Sprung (bestraft)


def select_best_voice_leading(
    previous_midi: float, candidate_midis: list[float] | tuple[float, ...]
) -> float:
    """Waehlt aus den Kandidaten die Tonhoehe mit den geringsten Stimmfuehrungskosten."""
    if not candidate_midis:
        return previous_midi
    return min(candidate_midis, key=lambda pitch: voice_leading_cost(previous_midi, pitch))

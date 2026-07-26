"""Tests fuer die Voice-Leading-Engine (plan2.md Stufe 6)."""

from __future__ import annotations

from au.integrator.voice_leading import select_best_voice_leading, voice_leading_cost


def test_voice_leading_cost() -> None:
    # Same pitch = zero cost
    assert voice_leading_cost(60.0, 60.0) == 0.0
    # Stepwise = low cost
    assert voice_leading_cost(60.0, 62.0) < voice_leading_cost(60.0, 72.0)


def test_select_best_voice_leading() -> None:
    prev = 60.0
    candidates = [48.0, 62.0, 75.0]
    best = select_best_voice_leading(prev, candidates)
    assert best == 62.0  # Closest step

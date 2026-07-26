"""Tests fuer die Prompt-zu-Intent Uebersetzung (plan2.md Stufe 4)."""

from __future__ import annotations

from au.integrator.intent import derive_musical_intent


def test_pairwise_prompt_intent_differentiation() -> None:
    warm_intent = derive_musical_intent("Warm, organisch, langsam atmend, gebettete Flächen")
    cold_intent = derive_musical_intent("Kalt, gläsern, metallisch, räumlich, eisige Obertöne")

    assert warm_intent.identity.warmth > cold_intent.identity.warmth
    assert cold_intent.identity.brightness > warm_intent.identity.brightness
    assert cold_intent.identity.hardness > warm_intent.identity.hardness


def test_rhythmic_prompt_intent() -> None:
    rhyth_intent = derive_musical_intent("Rhythmisch, sequenziert, elektronisch, aber ambient")
    assert rhyth_intent.complexity.rhythmic_complexity > 0.5

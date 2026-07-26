"""Phase-4-Akzeptanz: Album-DNA-Agent.

Aus plan.md Phase 4: 10 Testprompts -> valide DNAs; jede Negativregel
maschinell auswertbar; widerspruechlicher Prompt fuehrt zu Hinweisen statt
stiller Prioritaet; Innovations-Vektor hat messbare Wirkung.
"""

from __future__ import annotations

import numpy as np
import pytest

from au.agents.dna_agent import derive_seed_root, generate_dna
from au.dsl.dna import AlbumDNA, Comparator, NegativeRule
from au.dsl.innovation import apply_innovation
from au.dsl.rules import evaluate_all, evaluate_negative_rule

pytestmark = pytest.mark.smoke

_PROMPTS = [
    "Ein kaltes, metallisches Album ueber eine verlassene Raumstation, die langsam auftaut.",
    "Warme, goldene Klaenge wie ein Sonnenaufgang ueber weiten Feldern.",
    "Dunkle Unterwasser-Atmosphaere, hohl und weit, kaum Ereignisse.",
    "Ein helles, glitzerndes Glasalbum mit sparsamen Glockentoenen.",
    "Dichte, texturreiche Waelder aus Rauschen und Resonanz.",
    "Intime, trockene Klaenge in einem kleinen Raum.",
    "Experimentelles, fremdartiges Klanggewebe jenseits bekannter Instrumente.",
    "Klassische, vertraute Ambient-Flaechen zum Einschlafen.",
    "Dissonante, gespannte Cluster in einer eisigen Kathedrale.",
    "Ruhige, konsonante, friedliche Klangbaeder ohne jede Reibung.",
]


@pytest.mark.parametrize("prompt", _PROMPTS)
def test_prompt_produces_valid_dna(prompt: str) -> None:
    draft = generate_dna(prompt, seed_root=derive_seed_root(prompt))
    assert isinstance(draft.dna, AlbumDNA)
    assert draft.dna.character.descriptors
    assert len(draft.dna.negative_rules) >= 3


def test_dna_generation_is_deterministic() -> None:
    prompt = _PROMPTS[0]
    seed = derive_seed_root(prompt)
    a = generate_dna(prompt, seed_root=seed)
    b = generate_dna(prompt, seed_root=seed)
    assert a.dna.model_dump() == b.dna.model_dump()


def test_warm_and_cold_prompts_differ_measurably() -> None:
    warm = generate_dna(_PROMPTS[1], seed_root=1).dna
    cold = generate_dna(_PROMPTS[0], seed_root=1).dna
    assert warm.character.emotional_temperature[1] > cold.character.emotional_temperature[1]


def test_contradictory_prompt_is_escalated_not_silently_resolved() -> None:
    """Akzeptanzkriterium: Widerspruch fuehrt zu strukturierter Nutzer-Eskalation."""
    draft = generate_dna(
        "Maximal innovativ und experimentell, aber streng konsonant, ruhig und dissonant zugleich.",
        seed_root=1,
    )
    assert any("Zielkonflikt" in q for q in draft.open_questions)


def test_underspecified_prompt_yields_open_questions() -> None:
    draft = generate_dna("Musik.", seed_root=1)
    assert draft.open_questions, "Ein kaum spezifizierter Prompt sollte Hinweise erzeugen"


def test_negative_rule_predicate_is_machine_checkable() -> None:
    rule = NegativeRule(
        id="no_clipping",
        predicate=Comparator(metric="peak", operator="<", threshold=0.98),
    )
    clean = np.zeros((1000, 2))
    clean[:, 0] = np.linspace(-0.5, 0.5, 1000)
    verdict = evaluate_negative_rule(rule, clean, 48000)
    assert verdict.passed

    clipped = np.ones((1000, 2))
    verdict2 = evaluate_negative_rule(rule, clipped, 48000)
    assert not verdict2.passed


def test_all_default_rules_evaluate_without_error() -> None:
    draft = generate_dna(_PROMPTS[2], seed_root=1)
    signal = np.random.default_rng(0).normal(0, 0.1, size=(48000, 2))
    verdicts = evaluate_all(draft.dna.negative_rules, signal, 48000)
    assert len(verdicts) == len(draft.dna.negative_rules)


def test_innovation_vector_relaxes_roughness_weight_at_high_harmonic() -> None:
    from au.dsl.dna import InnovationVector

    low = apply_innovation(InnovationVector(harmonic=0.2))
    high = apply_innovation(InnovationVector(harmonic=0.9))
    assert high.weights.w_rough < low.weights.w_rough


def test_innovation_vector_unlocks_free_tuning_at_high_harmonic() -> None:
    from au.dsl.dna import InnovationVector

    effect = apply_innovation(InnovationVector(harmonic=0.9))
    assert any("just_tuning" in p or "free_tuning" in p for p in effect.vocabulary.allow)


def test_innovation_vector_increases_novelty_weight_with_mean() -> None:
    from au.dsl.dna import InnovationVector

    low = apply_innovation(
        InnovationVector(timbral=0.1, formal=0.1, harmonic=0.1, procedural=0.1, production=0.1)
    )
    high = apply_innovation(
        InnovationVector(timbral=0.9, formal=0.9, harmonic=0.9, procedural=0.9, production=0.9)
    )
    assert high.weights.w_nov > low.weights.w_nov

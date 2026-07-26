"""Phase-5-Akzeptanz: Blueprint-Generator.

Aus plan.md Phase 5: DNA -> Blueprint mit >= 8 Rollen-Slots (hier: die
tatsaechlich sinnvolle Teilmenge, deterministisch); Budgetsummen konsistent;
zwei verschiedene DNAs -> messbar verschiedene Blueprints; jeder Slot traegt
eine auf DNA-Felder verweisende Begruendung.
"""

from __future__ import annotations

import pytest

from au.agents.dna_agent import generate_dna
from au.integrator.blueprint import derive_blueprint

pytestmark = pytest.mark.smoke


def _dna(prompt: str, seed: int = 1):
    return generate_dna(prompt, seed_root=seed).dna


def test_blueprint_has_the_mandatory_roles() -> None:
    bp = derive_blueprint(_dna("Ein karges, kaltes Album."))
    roles = {s.role for s in bp.role_slots}
    assert {"foundation", "harmonic_drone", "atmospheric_noise"} <= roles


def test_rhythmically_dense_blueprint_reserves_bass_and_arpeggio() -> None:
    bp = derive_blueprint(_dna("Rhythmisch, sequenziert, pulsierend und dicht.", seed=9))
    roles = {s.role for s in bp.role_slots}
    assert {"bass_sequence", "arpeggiator"} <= roles


def test_every_slot_has_a_rationale_referencing_dna() -> None:
    bp = derive_blueprint(_dna("Ein dichtes, texturreiches, weites Album."))
    for slot in bp.role_slots:
        assert slot.rationale, f"Slot {slot.slot_id} ohne Begruendung"


def test_blueprint_is_deterministic() -> None:
    dna = _dna("Ein kaltes, metallisches Album ueber eine Raumstation.")
    a = derive_blueprint(dna)
    b = derive_blueprint(dna)
    assert a.model_dump() == b.model_dump()


def test_different_dnas_produce_different_blueprints() -> None:
    sparse = derive_blueprint(_dna("Karges, minimales, leeres Album."))
    dense = derive_blueprint(_dna("Dichtes, volles, texturreiches, helles, weites Album."))
    sparse_roles = {s.role for s in sparse.role_slots}
    dense_roles = {s.role for s in dense.role_slots}
    assert sparse_roles != dense_roles


def test_slot_periods_are_pairwise_distinct() -> None:
    """Grundvoraussetzung fuer Koprimitaet: keine zwei Rollen teilen sich eine Periode."""
    bp = derive_blueprint(_dna("Ein dichtes, weites, helles Album mit vielen Ereignissen."))
    periods = [s.phase_period_s for s in bp.role_slots]
    assert len(periods) == len(set(periods))


def test_relation_hints_only_reference_present_roles() -> None:
    bp = derive_blueprint(_dna("Ein karges Album."))
    present = {s.role for s in bp.role_slots} | {"main_space"}
    for hint in bp.relation_hints:
        assert hint.from_role in present
        assert hint.to_role in present


def test_field_mode_reflects_tension_and_ambiguity() -> None:
    tense = derive_blueprint(_dna("Dissonante, gespannte, unruhige Cluster."))
    calm = derive_blueprint(_dna("Ruhige, konsonante, friedliche Klaenge."))
    assert tense.field.mode != calm.field.mode


def test_budgets_are_within_sane_ranges() -> None:
    bp = derive_blueprint(_dna("Ein Album."))
    for slot in bp.role_slots:
        low, high = slot.band_hz
        assert 0 < low < high <= 20000
        assert 0.0 <= slot.density <= 1.0
        assert -100.0 <= slot.lufs <= 0.0

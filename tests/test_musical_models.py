"""Tests fuer die unified domain models (plan2.md Stufe 3)."""

from __future__ import annotations

from au.dsl.form import FormPlan, SectionPlan
from au.dsl.intent import ComplexityProfile, MusicalIntent, SonicIdentity
from au.dsl.orchestration import OrchestrationPlan, RegisterAllocation


def test_intent_model() -> None:
    intent = MusicalIntent(
        prompt="Warm & organisch",
        identity=SonicIdentity(warmth=0.9, brightness=0.3),
        complexity=ComplexityProfile(harmonic_complexity=0.7),
    )
    assert intent.identity.warmth == 0.9
    assert intent.target_lufs == -16.0


def test_form_plan_model() -> None:
    plan = FormPlan(
        total_duration_s=60.0,
        sections=(
            SectionPlan(section_id="s1", name="Intro", start_s=0.0, end_s=15.0, active_roles=("foundation",)),
            SectionPlan(section_id="s2", name="Peak", start_s=15.0, end_s=60.0, active_roles=("foundation", "harmonic_drone")),
        ),
    )
    assert plan.section_at(5.0).name == "Intro"
    assert plan.section_at(20.0).name == "Peak"


def test_orchestration_plan_model() -> None:
    orch = OrchestrationPlan(
        registers=(
            RegisterAllocation(role="foundation", freq_min_hz=20.0, freq_max_hz=250.0, center_midi=36.0),
        )
    )
    reg = orch.register_for("foundation")
    assert reg.center_midi == 36.0

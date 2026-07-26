from au.dsl.complexity import budget_for_duration


def test_duration_buys_real_composition_complexity() -> None:
    sketch = budget_for_duration(10.0)
    rich = budget_for_duration(180.0)
    maximal = budget_for_duration(600.0)
    assert sketch.name == "sketch"
    assert rich.variants_per_role > sketch.variants_per_role
    assert rich.max_slots > sketch.max_slots
    assert maximal.revision_passes >= rich.revision_passes


def test_manual_profile_is_available_at_any_duration() -> None:
    budget = budget_for_duration(10.0, "maximal")
    assert budget.name == "maximal"
    assert budget.variants_per_role == 10

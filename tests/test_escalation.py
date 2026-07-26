from au.dsl.escalation import build_escalation_graph


def test_escalation_has_vacuum_before_peak() -> None:
    graph = build_escalation_graph(("foundation", "bass_sequence", "arpeggiator"))
    labels = [step.label for step in graph.steps]
    assert labels.index("vacuum") < labels.index("peak")
    assert graph.validate_progression() == ()


def test_peak_keeps_known_roles_and_changes_at_most_two_dimensions() -> None:
    graph = build_escalation_graph(("foundation", "harmonic_drone", "bass_sequence"))
    peak = graph.step_for_phrase(5)
    assert "bass_sequence" in peak.active_roles
    for before, after in zip(graph.steps, graph.steps[1:], strict=False):
        assert len(set(after.dimensions) - set(before.dimensions)) <= 2

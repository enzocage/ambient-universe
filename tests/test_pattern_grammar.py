from au.dsl.pattern_grammar import PatternLevel, patterns_for_context


def test_peak_pattern_selection_prefers_relational_patterns() -> None:
    patterns = patterns_for_context(
        level=PatternLevel.PHRASE,
        section="peak",
        roles=("bass_sequence", "arpeggiator", "signal_motif"),
    )
    assert patterns
    assert patterns[0].pattern_id in {"anticipation_release", "layered_ostinato", "call_response"}


def test_outro_can_answer_the_beginning() -> None:
    patterns = patterns_for_context(
        level=PatternLevel.FORM,
        section="outro",
        roles=("foundation", "bass_sequence", "signal_motif"),
    )
    assert [pattern.pattern_id for pattern in patterns] == ["return_transform"]

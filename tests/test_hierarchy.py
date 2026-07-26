from au.dsl.hierarchy import build_default_hierarchical_score


def test_default_score_has_peak_and_lineage() -> None:
    score = build_default_hierarchical_score(
        duration_s=60.0,
        motif_id="main",
        active_roles=("foundation", "bass_sequence", "arpeggiator"),
    )
    assert score.form.peak_section_id == "section_peak"
    assert score.validate_lineage() == ()
    assert score.section_for(35.0).name == "peak"


def test_hierarchy_has_rise_and_release() -> None:
    score = build_default_hierarchical_score(
        duration_s=60.0,
        motif_id="main",
        active_roles=("foundation", "harmonic_drone"),
    )
    energies = score.form.energy_curve
    assert max(energies) > energies[0]
    assert energies[-1] < max(energies)

from au.dsl.ableton_workflow import build_production_workflow


def test_workflow_has_contrast_automation_and_resampling() -> None:
    workflow = build_production_workflow(
        duration_s=60.0,
        budget_name="rich",
        section_count=4,
        roles=("foundation", "bass_sequence", "arpeggiator", "harmonic_drone"),
        rack_modules={"foundation": "gen.drone.sub_bass", "bass_sequence": "gen.synth.ladder_bass", "arpeggiator": "gen.arpeggio.pulse_sequence", "harmonic_drone": "gen.fm.dual_operator"},
    )
    assert workflow.validate() == ()
    assert len(workflow.scenes) == 4
    assert any(scene.transition == "vacuum" or scene.density < 0.15 for scene in workflow.scenes)
    assert all(scene.automation for scene in workflow.scenes)
    assert len(workflow.resamples) >= 1

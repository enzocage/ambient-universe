from au.dsl.ableton_workflow import build_production_workflow


def test_budget_audit_rejects_fixed_scene_count() -> None:
    workflow = build_production_workflow(
        duration_s=60.0,
        budget_name="album",
        section_count=6,
        roles=("foundation", "bass_sequence"),
        rack_modules={"foundation": "gen.drone.sub_bass", "bass_sequence": "gen.synth.ladder_bass"},
    )
    assert workflow.validate_budget(expected_scenes=6, expected_roles=2) == ()

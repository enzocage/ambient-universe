from au.presets import get_preset_catalog


def test_catalog_has_thirty_synth_profiles_and_more_than_one_thousand_presets():
    catalog = get_preset_catalog()
    assert len(catalog.profiles) >= 30
    assert len(catalog) >= 1000
    assert len({p.id for p in catalog.presets}) == len(catalog)
    assert all(p.source == "internal-original" for p in catalog.presets)


def test_presets_are_role_selectable_and_renderable_backends_are_named():
    catalog = get_preset_catalog()
    for role in ("foundation", "arpeggiator", "bass_sequence"):
        selected = catalog.select(42, role)
        assert role in selected.roles
        assert selected.backend_module_id.startswith("gen.")

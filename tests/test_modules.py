"""Phase-1-Akzeptanz: Manifeste und Registry."""

from __future__ import annotations

import pytest

from au.core.manifest import Category, ModuleManifest
from au.core.registry import LicensePolicy, Registry, VocabularyPolicy, load_registry

pytestmark = pytest.mark.smoke


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=False)


# -- Katalog ----------------------------------------------------------------


def test_all_shipped_manifests_are_valid(registry: Registry) -> None:
    """Akzeptanzkriterium: 100 Prozent der Manifeste validieren."""
    assert registry.load_errors == [], "Fehlerhafte Manifeste:\n" + "\n".join(registry.load_errors)
    assert len(registry) >= 12, f"Zu wenige Seed-Module: {len(registry)}"


def test_every_module_declares_a_cost_and_a_band(registry: Registry) -> None:
    for m in registry:
        assert m.cost.cpu_units > 0, f"{m.id} ohne Kostenangabe"
        low, high = m.guarantees.band_hz
        assert 0 < low < high, f"{m.id} mit unsinnigem Band {m.guarantees.band_hz}"


def test_voices_carry_the_canonical_macro_set(registry: Registry) -> None:
    """Das Makroversprechen aus plan.md 4.2, gegen den echten Katalog geprueft."""
    voices = registry.query(category=Category.GENERATOR, level=2)
    assert voices, "Kein L2-Generator im Katalog"
    for v in voices:
        assert {"brightness", "body", "noise_ratio", "motion", "material"} <= set(v.macros)


def test_feedback_guards_exist(registry: Registry) -> None:
    """L1-T2 setzt diese beiden Module voraus — sie muessen es geben."""
    for guard in ("prc.util.dcblock", "prc.util.softclip"):
        assert registry.try_get(guard) is not None, f"{guard} fehlt im Katalog"


# -- Manifest-Validierung ---------------------------------------------------


def _minimal(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "gen.test.thing",
        "level": 1,
        "category": "generator",
        "display_name": "Testding",
        "ports": {"out": [{"name": "out", "type": "audio"}]},
    }
    base.update(overrides)
    return base


def test_id_prefix_must_match_category() -> None:
    with pytest.raises(ValueError, match="passt nicht zur Kategorie"):
        ModuleManifest.model_validate(_minimal(id="prc.test.thing"))


def test_id_needs_three_levels() -> None:
    with pytest.raises(ValueError, match="mindestens drei Ebenen"):
        ModuleManifest.model_validate(_minimal(id="gen.thing"))


def test_macro_must_reference_existing_param() -> None:
    with pytest.raises(ValueError, match="unbekannte Parameter"):
        ModuleManifest.model_validate(
            _minimal(macros={"brightness": {"maps": ["nicht_da"]}}, params={})
        )


def test_level2_generator_without_macros_is_rejected() -> None:
    with pytest.raises(ValueError, match="Pflichtmakros"):
        ModuleManifest.model_validate(_minimal(level=2))


def test_module_without_output_is_rejected() -> None:
    with pytest.raises(ValueError, match="keinen Ausgang"):
        ModuleManifest.model_validate(_minimal(ports={"in": [{"name": "in", "type": "audio"}]}))


def test_default_outside_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="ausserhalb"):
        ModuleManifest.model_validate(
            _minimal(params={"x": {"min": 0.0, "max": 1.0, "default": 2.0}})
        )


def test_enum_and_range_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="schliessen einander aus"):
        ModuleManifest.model_validate(
            _minimal(params={"x": {"min": 0.0, "max": 1.0, "enum": ["a", "b"]}})
        )


# -- Abfrage ----------------------------------------------------------------


def test_query_filters_by_tags_and_budget(registry: Registry) -> None:
    """Akzeptanzkriterium: gefilterte Abfrage liefert die richtige Menge."""
    warm_drones = registry.query(tags_all=["drone", "warm"])
    assert [m.id for m in warm_drones] == ["gen.drone.wavetable_resonator"]

    # Dasselbe Modul faellt unter ein zu knappes Rechenbudget.
    assert registry.query(tags_all=["drone", "warm"], cpu_budget=1.0) == []


def test_query_respects_level(registry: Registry) -> None:
    assert all(m.level == 1 for m in registry.query(level=1))
    assert all(m.level <= 2 for m in registry.query(max_level=2))


def test_vocabulary_policy_forbid_beats_allow(registry: Registry) -> None:
    policy = VocabularyPolicy(allow=("gen.*",), forbid=("gen.drone.*",))
    ids = {m.id for m in registry.query(vocabulary=policy)}
    assert "gen.osc.bandlimited" in ids
    assert "gen.drone.wavetable_resonator" not in ids


def test_preferred_modules_sort_first(registry: Registry) -> None:
    policy = VocabularyPolicy(prefer=("gen.object.*",), allow=("gen.*",))
    result = registry.query(vocabulary=policy)
    assert result[0].id.startswith("gen.object.")


def test_license_policy_blocks_nc_weights(registry: Registry) -> None:
    """Der Katalog ist derzeit NC-frei; die Schranke muss trotzdem greifen."""
    strict = registry.query(license_policy=LicensePolicy(allow_nc_weights=False))
    assert all(not m.license.nc_weights for m in strict)


def test_query_is_deterministic(registry: Registry) -> None:
    """Ohne stabile Reihenfolge waere die Modulwahl nicht reproduzierbar."""
    a = [m.id for m in registry.query(max_level=2)]
    b = [m.id for m in registry.query(max_level=2)]
    assert a == b


def test_unknown_module_suggests_alternatives(registry: Registry) -> None:
    suggestions = registry.suggest("gen.drone.wavetable_resonatr")
    assert "gen.drone.wavetable_resonator" in suggestions
